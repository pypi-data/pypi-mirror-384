from openai import OpenAI
from pydantic import BaseModel

from typing import List 

from .sb_agent import getLLMClient
from .task_prompt import prompt as system_prompt


memory = [
    {"role": "system", "content": system_prompt},
]

class SpeedBuildFormat(BaseModel):
    actions: List[str]

def makeLLMCall(user_input):
    
    model, client = getLLMClient()

    memory.append({"role": "user","content": user_input})
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=memory,
        response_format=SpeedBuildFormat,
    )

     # Extract the assistant's response
    assistant_response = completion.choices[0].message.parsed #completion.choices[0].message.content

    # Add the assistant's response to memory
    memory.append({"role": "assistant", "content": f"{assistant_response.actions}"})

    return assistant_response

def query_splitter(query):
    response = makeLLMCall(query)
    print(response, " response is video")
    return response.actions