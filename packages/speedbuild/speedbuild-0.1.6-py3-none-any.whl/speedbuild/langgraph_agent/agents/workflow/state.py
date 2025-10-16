import json
from typing import Optional
from pydantic import BaseModel, Field


class DebuggerOutput(BaseModel):
    """
    {
        action:"read file | update file | run command | end",
        description:"",
        file_path : "" | none,
        command : "" | None,
        file_action : "add | replace | remove"
        file_lines : "1(single line ) | 10-20 (multi line)" | None
        new_code:""
    }
    """
    action: str = Field(description="Action to perform")
    description: str = Field(description="Action to perform")
    file_path: Optional[str] = Field(description="Action to perform", default=None)
    command: Optional[str] = Field(description="Action to perform", default=None)
    file_action: Optional[str] = Field(description="Action to perform", default=None)
    file_lines: Optional[str] = Field(description="Action to perform", default=None)
    new_code: Optional[str] = Field(description="Action to perform", default=None)


def formatLLMOutput(data : DebuggerOutput, stringify=False):
    formatted =  {
        "action":data.action,
        "description":data.description,
        "file_path":data.file_path,
        "command":data.command,
        "file_action":data.file_action,
        "file_lines":data.file_lines,
        "new_code":data.new_code
    }

    if stringify:
        return json.dumps(formatted)
    
    return formatted