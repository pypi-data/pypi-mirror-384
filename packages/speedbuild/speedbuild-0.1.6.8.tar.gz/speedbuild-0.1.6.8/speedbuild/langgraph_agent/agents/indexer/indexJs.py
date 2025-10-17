import os
from pydantic import BaseModel,Field

from langchain.chat_models import init_chat_model
from langgraph.graph import START, END, StateGraph, MessagesState
from langchain_core.messages import AIMessage, SystemMessage, HumanMessage

from .indexJSSystemPrompt import system_prompt

class LLMOutput(BaseModel):
    category: str = Field(description="The category of the file")

class ExtendedMessagesState(MessagesState):
    # Add custom fields while keeping messages
    formatted_output: dict = {}
    structured_response: LLMOutput = None

class Indexer():
    def __init__(self,model,provider,key_name,api_key):
        # TODO : set model API key
        os.environ[key_name] = api_key
        
        llm = init_chat_model(model=model, model_provider=provider)
        self.llm = llm.with_structured_output(LLMOutput)

    def llm_call(self,state:ExtendedMessagesState):
        response = self.llm.invoke(state["messages"])

        return {
            "messages": [AIMessage(content=response.category)],
            "structured_response": response
        }

    def format_node(self,state: ExtendedMessagesState):
        response = state["structured_response"]
        formatted = {"category": response.category}
        return {"formatted_output": formatted}
    
    def setup(self):
        builder = StateGraph(ExtendedMessagesState)
        builder.add_node("llm",self.llm_call)
        builder.add_node('format_node',self.format_node)

        builder.add_edge(START, 'llm')
        builder.add_edge('llm','format_node')
        builder.add_edge('format_node',END)

        self.model = builder.compile()

    def initialize_with_system_message(self,user_input: str, system_prompt: str):
        return [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_input)
        ]
    
    def getFileInfo(self,filename):
        if not os.path.exists(filename):
            return None
        
        info = "file name : " + os.path.basename(filename) + "\n\n"

        # TODO : shorten contents of long files
        with open(filename,"r") as file:
            content = file.read()
            info += f"file content : ** {content} **"

        return info
    
    def index(self,filename):
        user_input = self.getFileInfo(filename)
        if user_input is None:
            return None
        
        messages = self.initialize_with_system_message(user_input,system_prompt)
        res =  self.model.invoke({"messages":messages})
        return res['formatted_output']

# if __name__ == "__main__":
#     indexer = Indexer("gpt-5","openai")
#     indexer.setup()
#     indexer.index("filename",system_prompt)
