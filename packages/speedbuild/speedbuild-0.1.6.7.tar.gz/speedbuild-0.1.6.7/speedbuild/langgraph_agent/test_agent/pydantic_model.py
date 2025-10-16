from typing import Optional
from pydantic import BaseModel, Field

class LLMOutput(BaseModel):
    """
    Represents the output of a language model (LLM) action.

    Attributes:
        action (str): Action to perform.
        write_action (Optional[str]): Specifies the code write action to perform (add, replace, or remove).
        line (Optional[str]): Line(s) of code to replace or remove.
        code (str): New code to write to the file.
        command (Optional[str]): CLI command to execute.
        file_path (Optional[str]): Path of the file to read.
    """
    action: str = Field(description="Action to perform")
    write_action: Optional[str] = Field(
        default=None, 
        description="What code write action to perform (add, replace or remove)"
    )
    line: Optional[str] = Field(
        default=None, 
        description="line(s) of code to replace or remove"
    )
    code: str = Field(
        default=None, 
        description="New code to write to file"
    )
    command: Optional[str] = Field(
        default=None,
        description="CLI command to execute"
    )
    file_path: Optional[str] = Field(
        default=None,
        description="path of file to read"
    )