from typing import List
from pydantic import BaseModel, Field
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, SystemMessage

system_prompt = """
You are an intelligent parser agent for an application customization service.

Your task:
- Analyze the user's request.
- Break it down into a list of atomic, actionable sub-prompts.

Rules:
- Atomic means: each sub-prompt should describe a single self-contained code mutation (e.g., add, remove, edit, modify).
- Do not decompose into micro-steps like opening files, identifying code, or locating fields.
- Do not solve, execute, or explain any sub-prompt.
- Preserve original terminology from the user’s input when possible.
- Do not include introductions, explanations, or summaries. Only output the list.
- Actions should be phrased as high-level code mutations, not developer actions.
- Ignore any action involving database schema; focus only on code logic changes.
"""

class LLMOutput(BaseModel):
    prompts : List[str] = Field(description="List of sub prompts")

def splitPrompt(prompt):
    model = init_chat_model(model="gpt-4o", model_provider="openai")
    model = model.with_structured_output(LLMOutput)

    res = model.invoke([
        SystemMessage(content=system_prompt),
        HumanMessage(content=prompt)
    ])

    return res.prompts