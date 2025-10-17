import os
from pathlib import Path
from openai import OpenAI
from typing import Optional, Union, List
from ..parsers.python.parser import PythonBlockParser
from pydantic import BaseModel
from ..src.Django.utils.feature_dependencies import removeDuplicates
from .customize_system_prompt import system_prompt
from ..utils.llm_utils import getLLMConnectInfo
from ..utils.update_template_code import addOrUpdateCode



memory = [
    {"role": "system", "content": system_prompt},
]

parser = PythonBlockParser()

class CodeChange(BaseModel):
    action: str
    new_code: str
    comment: Optional[str] = None
    old_code: Optional[str] = None

class SpeedBuildFormat(BaseModel):
    status: str
    action: str
    file_name: str
    # content: Optional[List[CodeChange]] = None
    content: Optional[Union[str, List[CodeChange]]] = None
    comment: Optional[str] = None


def getLLMClient():
    llm_config = getLLMConnectInfo()
    if llm_config == None:
        raise ValueError("Please add an LLM API Key to proceed with customization")
    elif llm_config == 0:
        raise ValueError("This Version of Speedbuild only support OpenAI")
    
    api_key = llm_config[1]
    model = llm_config[2]

    client = OpenAI(api_key=api_key)

    return [model,client]

def makeLLMCall(user_input):
    model,client = getLLMClient()
    memory.append({"role": "user","content": user_input})
    completion = client.beta.chat.completions.parse(
        model=model,
        messages=memory,
        response_format=SpeedBuildFormat,
    )

    # Extract the assistant's response
    assistant_response = completion.choices[0].message.parsed #completion.choices[0].message.content

    # Add the assistant's response to memory
    memory.append({"role": "assistant", "content": f"{assistant_response.file_name} : {assistant_response.action} \n {assistant_response.content}"})

    return assistant_response

def getFileContent(filePath,fileName,template_name)->str:
    dest = f"{filePath}/{fileName}"
    print("file ",dest)
    
    if os.path.exists(dest):
        with open(dest, "r") as file:
            data = file.read()
            return data 
    else:
        return "File Does Not Exist"

# Todo edit here
def writeToFile(filePath,content,fileName):
    dest = f"{filePath}/{fileName}"
    print("Saving to file ",dest)
    if os.path.exists(dest):
        # append to file
        with open(dest, "r+") as file:
            data = file.read()  # Step 1: Read existing content
        
            file.seek(0)        # Move to the beginning of the file
            file.truncate(0)    # Step 2: Clear the file

            write_data = f"{content}\n{data}"
            chunks = parser.parse_code(write_data) #split_code_into_sections(write_data)
            code = []
            imports = []
            
            for chunk in chunks:
                if chunk.startswith("import ") or chunk.startswith("from "):
                    imports.append(chunk)
                    # individualImports = getIndividualImports(chunk)
                    # imports.extend(individualImports)
                else:
                    code.append(chunk)

            if imports:  # Step 3: Write new content
                imports = removeDuplicates(imports)
                imports = "\n".join(imports)
                file.write(imports + "\n")

            file.write("\n\n")
            code = removeDuplicates(code)
            code = "\n".join(code)
            file.write(code)  # Append old content to new content
    else:
        with open(dest,"w") as file:
            file.write(content)

def agent(files,prompt,project_root,template_name):
    file_processed = set()
    read_path = project_root.split("/")
    read_path.pop()
    read_path = "/".join(read_path)
    print("read path is ", read_path)

    home = str(Path.home())
    # /home/attah/.sb/sb_extracted/speed_build_UserOnboarding/sb_app
    root_path = f"{home}/.sb/sb_extracted/speed_build_{template_name}"

    while len(file_processed) < len(files):
        old_code = prompt
        prompt = "task_description: " + prompt + "\n" + f"files : {files}"
        response = makeLLMCall(prompt)
        
        status = response.status
        file_name = response.file_name
        action = response.action

        print(f"{file_name} : {action}")
        print(f"{response.status} {response.comment} == \n\n{response.content}\n\n")
        
        if status == "request_file":
            file_content = getFileContent(root_path,file_name,template_name)
            prompt = file_content
            
        elif status == "success":
            dest = f"{read_path}/.sb/{template_name}"
            code_content = response.content
            comment = response.comment

            # TODO reedit file to replace or add new code
            if code_content != None:
                if file_name in files:
                    new_chunk = parser.parse_code(old_code)
                    for code in code_content:
                        old_code = code.old_code

                        if "sb_app" in file_name:
                            code = code.new_code.replace("sb_app.",".")
                        else:
                            code = code.new_code
                            
                        new_chunk = addOrUpdateCode(new_chunk,code, old_code)

                    edited_or_new_code = "\n".join(new_chunk)

                else:
                    edited_or_new_code = []
                    
                    for block in code_content:
                        code = block.new_code
                        if "sb_app" in file_name:
                            code = code.replace("sb_app.",".")

                        edited_or_new_code.append(block.new_code)

                    edited_or_new_code = "\n".join(edited_or_new_code)
                # if "sb_app" in file_name and code_content is not None:
                #     code_content = code_content.replace("sb_app.",".")

                # file_name = file_name.split("/")[-1]
                writeToFile(root_path,edited_or_new_code,file_name) #project_root
                print(f"{file_name} : {comment}")
                # add file_name to file_processed
                file_processed.add(file_name)
                prompt = "next"
            
        elif status == "delete":
            # delete file
            pass

        elif status == "done":
            print(f"Completed : {response.comment}")
            break #stop loop
            
        continue