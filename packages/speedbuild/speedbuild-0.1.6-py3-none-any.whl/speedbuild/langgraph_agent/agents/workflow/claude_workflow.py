import os
from ....cli_output.output import StatusManager
from langgraph.errors import GraphRecursionError
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import START, END, StateGraph, MessagesState
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from typing import Dict, Any, Literal
import hashlib

from .system_prompt import system_prompt
from .express_system_prompt import system_prompt as debug_system_prompt
from .express_customization_prompt import system_prompt as customize_express_prompt
from .django_customization_prompt import system_prompt as django_customization_system_prompt


from .tools import executeCommand, getFileContent, updateFile

from .state import DebuggerOutput, formatLLMOutput


class ExtendedMessagesState(MessagesState):
    # Current execution state
    formatted_output: Dict[str, Any] = {}
    structured_response: DebuggerOutput = None


class SpeedBuildWorkflow():
    def __init__(self,model,model_provider,framework):
        self.first_request = True
        self.framework = framework
        
        self.last_command_output: str = ""
        self.last_error: str = ""
        
        # Retry tracking
        self.error_history: Dict[str, int] = {}  # error_signature -> attempt_count
        self.total_iterations: int = 0
        
        # Control flags
        self.success: bool = False
        self.need_human: bool = False
        self.original_command: str = None  # The command we're trying to fix
        
        # Configuration
        self.max_retries_per_error: int = 10
        self.max_total_iterations: int = 20 
        
        llm = init_chat_model(model=model,model_provider=model_provider)
        self.llm = llm.with_structured_output(DebuggerOutput)

        self.max_recursion_count = 20  # Adjust based on your typical project complexity
        self.recursion_count = 30

        self.workflow_type = None

        self.checkpointer = InMemorySaver()

        self.logger = StatusManager()

    def hash_error(self,error_message: str) -> str:
        """Create a consistent signature for similar errors"""
        # Remove line numbers, file paths, and other variable parts
        normalized = error_message.lower()
        # Add more sophisticated normalization as needed
        return hashlib.md5(normalized.encode()).hexdigest()[:8]

    def read_file(self,file_path: str) -> tuple[bool, str]:
        """Returns (success, content_or_error)"""
        try:
            file_path = file_path.split("/")
            file_name = file_path.pop(-1)
            file_path = "/".join(file_path)

            content = getFileContent(file_path,file_name)
            return True, content
        except Exception as e:
            return False, str(e)
    

    def run_shell_command(self,command: str) -> tuple[bool, str, str]:
        """Returns (success, stdout, stderr)"""
        # try:
            # success = result.returncode == 0
        stdout, stderr = executeCommand(command,self.framework)
        return len(stderr.strip()) == 0,stdout,stderr #success, result.stdout, result.stderr
        # except Exception as e:
        #     print("we dey here with error ", e)
        #     return False, "", str(e)

    def createUpdateOrDeleteFile(self,action: str, file_path: str, code: str, lines: str) -> tuple[bool, str]:
        """Returns (success, error_message)"""

        # file_path = file_path.split("/")
        file_name = os.path.basename(file_path)
        file_path = os.path.dirname(file_path)

        # print(f"\n\n\naction: {action}\n file_path : {file_path} \n code : {code}\n lines : {lines}\n\n\n")

        try:
            res = updateFile(file_path,file_name,action,code,lines)
            return True, res
        except Exception as e:
            print("update file exception ", e)
            return False, str(e)
        
    def get_messages(self,is_start=False):

        if self.workflow_type == None:
            agent_system_prompt = debug_system_prompt
        else:
            agent_system_prompt = customize_express_prompt if self.framework == "express" else django_customization_system_prompt

        return [
            SystemMessage(content=agent_system_prompt)
        ]
        # if is_start:
        #     self.first_request = False
        #     return [
        #         SystemMessage(content=system_prompt if framework == None else express_system_prompt), #TODO : make this dynamic
        #         HumanMessage(content=user_input)
        #     ]
        # return [HumanMessage(content=user_input)]
    

    def ask_llm(self,state: ExtendedMessagesState) -> ExtendedMessagesState:

        if self.last_command_output and len(self.last_command_output) > 0:
            state["messages"].append(HumanMessage(content=self.last_command_output))
            self.last_command_output = None

        # Build context message with current state
        if self.workflow_type == None:
            context = f"Error : {self.last_error}"
            state["messages"].append(HumanMessage(content=context))

        # print("state",state["messages"])

        response = self.llm.invoke(state["messages"])

        return {
            "messages": [AIMessage(content=formatLLMOutput(response,True))],
            "structured_response": response
        }

    def format_llm_response(self,state: ExtendedMessagesState) -> ExtendedMessagesState:
        """Format LLM response into structured format"""

        response = state["structured_response"]
        return {"formatted_output": formatLLMOutput(response)}


    def execute_instruction(self,state: ExtendedMessagesState) -> ExtendedMessagesState:
        """Execute the LLM instruction and update state"""
        
        response = state['formatted_output']
        action = response['action']
        description = response['description']

        self.logger.update_status(f"{description}")
        self.total_iterations += 1
        
        success = False
        error_msg = ""

        if action == "read_file":
            if response['file_path']:
                success, result = self.read_file(response["file_path"])
                if success:
                    self.last_command_output = f"File content: {result}" #TODO ,chunk files so we read big files in batches
                    # print(f"Read file successfully: {response['file_path']}")
                else:
                    error_msg = result

        elif action == "run_command":
            if response['command']:
                success, stdout, stderr = self.run_shell_command(response['command'])
                self.last_command_output = f"command : {response['command']}\n\n output : {stdout}"
                if not success:
                    error_msg = stderr

        elif action == "update_file":
            file_action = response['file_action']
            file_path = response['file_path']

            if file_action and file_path:
                lines = response['file_lines']
                code = response['new_code']

                # action: str, file_path: str, code: str, lines: str)

                # print(f"action: {file_action}\n file_path : {file_path} \n code : {code}\n lines : {lines}")
                success, error_msg = self.createUpdateOrDeleteFile(file_action, file_path, code, lines)
                if success:
                    self.last_command_output = f"File {file_action} completed: {file_path} new code : {code}"

        elif action == "end":
            self.success = True
            return state
        
        # Update error tracking
        if not success:
            self.last_error = error_msg
            error_key = self.hash_error(error_msg)
            self.error_history[error_key] = self.error_history.get(error_key, 0) + 1
            print(f"Error occurred: {error_msg}")
        else:
            self.last_error = ""
        
        return state

    def should_continue(self,state: ExtendedMessagesState) -> Literal["ask_llm", "human_intervention", "test_original_command", "__end__"]:
        """Determine next step based on current state"""
        
        # Check if explicitly marked as done
        if self.success:
            return "__end__"
        
        # Check if we need human intervention
        if self.need_human:
            return "human_intervention"
        
        # Check total iteration limit
        if self.total_iterations >= self.max_total_iterations:
            print("Hit maximum iteration limit")
            self.need_human = True
            return "human_intervention"
        
        # Check if we've tried the same error too many times
        if self.last_error:
            error_key = self.hash_error(self.last_error)
            if self.error_history.get(error_key, 0) >= self.max_retries_per_error:
                print(f"Hit retry limit for error: {self.last_error[:100]}...")
                self.need_human = True
                return "human_intervention"
        
        # If no error, test the original command
        if not self.last_error and self.original_command is not None:
            return "test_original_command"
        
        # Continue debugging
        return "ask_llm"

    def test_original_command(self,state: ExtendedMessagesState) -> ExtendedMessagesState:
        """Test if the original failing command now works"""
        
        # print(f"Testing original command: {self.original_command}")
        success, stdout, stderr = self.run_shell_command(self.original_command)
        
        if success:
            self.success = True
            self.last_command_output = stdout
            self.logger.stop_status()
        else:
            # print("❌ Original command still failing")
            self.last_error = stderr
            # Update error tracking for the original command failure
            error_key = self.hash_error(stderr)
            self.error_history[error_key] = self.error_history.get(error_key, 0) + 1
        
        return state

    def human_intervention(self,state: ExtendedMessagesState) -> ExtendedMessagesState:
        """Handle human intervention"""

        self.logger.stop_status()
        print("\n" + "="*50)
        print("🚨 HUMAN INTERVENTION NEEDED")
        print("="*50)
        print(f"Original command: {self.original_command}")
        print(f"Last error: {self.last_error}")
        print(f"Iterations attempted: {self.total_iterations}")
        print(f"Error history: {self.error_history}")
        print("="*50)
        
        # In a real implementation, you might:
        # - Send a notification
        # - Wait for human input
        # - Provide options to continue, restart, or abort
        
        user_input = input("Continue debugging? (y/n/restart): ").lower()
        
        if user_input == 'y':
            self.need_human = False
            # Reset some counters if needed
        elif user_input == 'restart':
            self.error_history.clear()
            self.total_iterations = 0
            self.need_human = False
        else:
            self.success = True  # End the workflow
        
        return state
    

    # Build the graph
    def create_debugger_workflow(self,workflow_type=None) -> StateGraph:
        """Create the complete debugger workflow"""

        self.workflow_type = workflow_type
        
        builder = StateGraph(ExtendedMessagesState)
        
        # Add nodes
        builder.add_node("ask_llm", self.ask_llm)
        builder.add_node("format_llm_response", self.format_llm_response)
        builder.add_node("execute_instruction", self.execute_instruction)
        builder.add_node("test_original_command", self.test_original_command)
        builder.add_node("human_intervention", self.human_intervention)
        
        # Add edges
        builder.add_edge(START, "ask_llm")
        builder.add_edge("ask_llm", "format_llm_response")
        builder.add_edge("format_llm_response", "execute_instruction")
        # Conditional routing from execute_instruction
        builder.add_conditional_edges(
            "execute_instruction",
            self.should_continue,
            {
                "ask_llm": "ask_llm", # start again
                "human_intervention": "human_intervention", 
                "test_original_command": "test_original_command",
                "__end__": END
            }
        )

        # # Conditional routing from test_original_command
        builder.add_conditional_edges(
            "test_original_command",
            self.should_continue,
            {
                "ask_llm": "ask_llm", # start again
                "human_intervention": "human_intervention",
                "__end__": END
            }
        )

        # # Conditional routing from human_intervention
        builder.add_conditional_edges(
            "human_intervention", 
            self.should_continue,
            {
                "ask_llm": "ask_llm", # start again
                "__end__": END
            }
        )


        self.graph = builder.compile(checkpointer=self.checkpointer)
    
    
    def run(self):
        self.logger.start_status("Debugging" if self.workflow_type == None else "Customizing")
        messages = self.get_messages(self.first_request)
        # Here you'd call your LLM
        # return self.graph.invoke({"messages":messages})

        current_state = {"messages":messages}
        config = {"configurable": {"thread_id": "abcd123"}}
    
        for i in range(self.max_recursion_count):
            try:
                result = self.graph.invoke(current_state, config={"recursion_limit": self.recursion_count, **config})
                
                if self.success or self.need_human:
                    self.logger.stop_status()
                    return result
                    
                current_state = result
                # print(f"Completed chunk {i+1}, continuing...")
                
            except GraphRecursionError:
                # print(f"Chunk {i+1} hit limit, continuing...")
                continue
        self.logger.stop_status()
    

# ---

# graph = builder.compile(checkpointer=...)
# config = {"configurable": {"thread_id": "abcd123"}}
# try:
#     res = self.graph.invoke({"query": query}, config={"recursion_limit": 1, **config})
# except GraphRecursionError:
#     # I want to read the state here
#     logger.exception(f"The invocation to graph reached the recursion limit")
#     state = self.graph.get_state(config)
    

# def run(self, query, original_command=None):
#     """Simple chunked execution"""
    
#     current_state = self.initialize_state(query, original_command)
#     max_chunks = 20  # Adjust based on your typical project complexity
#     chunk_size = 30
    
#     for i in range(max_chunks):
#         try:
#             result = self.graph.invoke(current_state, config={"recursion_limit": chunk_size})
            
#             if result.get('success') or result.get('need_human'):
#                 return result
                
#             current_state = result
#             print(f"Completed chunk {i+1}, continuing...")
            
#         except GraphRecursionError:
#             print(f"Chunk {i+1} hit limit, continuing...")
#             continue
    
#     # Fallback to human intervention
#     return {**current_state, "need_human": True, "last_error": "Complex project requires human review"}