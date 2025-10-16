from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.graph import START,END,StateGraph, MessagesState
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from .pydantic_model import LLMOutput
from .tools import getFileContent,executeCommand,updateFile

from .system_prompt import system_prompt
from .express_system_prompt import system_prompt as express_system_prompt


class ExtendedMessagesState(MessagesState):
    formatted_output: dict = {}
    structured_response: LLMOutput = None


class SpeedBuildLLMGraph():
    def __init__(self,model,model_provider):
        llm = init_chat_model(model=model,model_provider=model_provider)
        llm_with_tools = llm.bind_tools([getFileContent,executeCommand,updateFile])
        self.llm = llm_with_tools #.with_structured_output(LLMOutput)

        self.first_request = True

        # create graph
        self.setup()

    # def format_node(state: ExtendedMessagesState):
    #     response = state["structured_response"]
    #     formatted = {
    #         "action": response.action,
    #         "write_action": response.write_action,
    #         "line": response.line,
    #         "code": response.code,
    #         "command": response.command,
    #         "file_path": response.file_path,
    #     }

    #     return {"formatted_output": formatted}
    
    def get_messages(self,user_input: str, is_start=False,framework=None):
        if is_start:
            self.first_request = False
            return [
                SystemMessage(content=system_prompt if framework == None else express_system_prompt), #TODO : make this dynamic
                HumanMessage(content=user_input)
            ]
        return [HumanMessage(content=user_input)]
    
    def debugger(self,state:MessagesState):
        # response = self.llm.invoke(state["messages"])

        # return {
        #     # TODO
        #     "messages": [AIMessage(content=response.setup)],
        #     "structured_response": response
        # }
        return {"messages": [self.llm.invoke(state["messages"])]}
    
    
    def process_llm_command(self,state:ExtendedMessagesState):
        "process and test command"
        return {
            "messages": state["messages"].append(HumanMessage(content="response.setup"))
        }
    
        # or return end
    
    def setup(self):
        # state = ExtendedMessagesState()
        builder = StateGraph(MessagesState)

        # nodes
        builder.add_node("debugger",self.debugger)
        builder.add_node("tools", ToolNode([getFileContent,executeCommand,updateFile]))

        # edges
        builder.add_edge(START,"debugger")
        builder.add_conditional_edges(
            "debugger",
            tools_condition,
        )
        builder.add_edge("tools","debugger")
        builder.add_edge("debugger",END)
        # builder.add_edge("tools","format_node")
        # builder.add_edge("format_node","process_command")
        # builder.add_edge("process_command", "llm_call")

        # builder.add_conditional_edges()

        # build graph
        self.graph = builder.compile()
        return True


    def run(self,query,framework=None):
        messages = self.get_messages(query,self.first_request,framework)
        response = self.graph.invoke({'messages':messages})

        return response