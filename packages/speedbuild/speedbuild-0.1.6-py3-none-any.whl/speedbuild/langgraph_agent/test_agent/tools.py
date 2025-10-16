import os
import sys
from pathlib import Path

from ...newExec import PythonExecutor
# from ...exec.runCommand import PythonExecutor


# Read File
def getFileContent(filePath : str,fileName : str)->str:
    """Return the content of a file

    Args:
        filePath: first str
        fileName: second str
    """
    dest = f"{filePath}/{fileName}"
    
    # remove this
    if not dest.startswith("/home/attah/Documents/speedbuildjs/"):
        dest = f"/home/attah/Documents/speedbuildjs/{dest}"

    code = ""
    count = 1

    print("reading file ",dest)
    
    if os.path.exists(dest):
        with open(dest, "r") as file:
            data = file.read()
            lines = data.split("\n")
            for line in lines:
                code += f"{count} {line}\n"
                count += 1
            return code 
    else:
        print("does not exists")
        raise ValueError("File Does Not Exist")
    

def performUpdate(code:str,action:str,update:str,line:str):
    """
    Updates a given code string by performing add, remove, or replace actions on specified lines.

    Args:
        code (str): The original code as a string.
        action (str): The action to perform. Can be "add", "remove", or "replace".
        update (str): The code to add or replace. Ignored for "remove" action.
        line (str): The line number or range (e.g., "3" or "2-5") to apply the action.

    Returns:
        str: The updated code as a string.

    Notes:
        - For a line range (e.g., "2-5"), the action is applied to all lines in the range.
        - For a single line, the action is applied to that line.
        - "add" inserts the update code at the specified position.
        - "remove" deletes the specified line(s).
        - "replace" replaces the specified line(s) with the update code.
    """
    code_lines = code.split("\n")
    update_code = None if update == None else update.split("\n")

    if line != None:
        if "-" in line:
            new_code = []
            start, end = line.split("-")
            start = int(start)
            end = int(end)
            remove_line = []

            for index,line in enumerate(code_lines):
                lineNum = int(index) + 1
                if lineNum not in range(start,end+1):
                    new_code.append(line)
                else:
                    remove_line.append(line)
                    if action == "replace" and lineNum == end:
                        new_code.extend(update_code)
        else:
            pos = int(line)
            print("positomn ",pos, " ", len(code_lines))

            if action == "add":
                code_lines.insert(pos,"\n".join(update_code))
            else:
                if pos >= len(code_lines):
                    pos = -1

                code_lines.pop(pos)
                if action == "replace":
                    code_lines.extend(update_code)

            new_code = code_lines
            print("New code is == ",new_code)

        return "\n".join(new_code)

# Instead of write to file, lets call it update file

# Write File
def updateFile(filePath : str,fileName : str, action:str, update : str=None,line:str=None):

    """
    Updates a file at the specified path by performing the given action.

    Args:
        filePath (str): The directory path where the file is located.
        fileName (str): The name of the file to update.
        action (str): The action to perform on the file. Accepted values are "add", "replace", "remove", or "create".
        update (str, optional): The content to add or replace in the file. Required for "add", "replace", and "create" actions.
        line (str, optional): The specific line to target for the update. Used for "replace" or "remove" actions.
    
    Returns:
        str: An error message if the file is not found or the action is not recognized; otherwise, None.
    
    Notes:
        - For "add", "replace", and "remove" actions, the file must already exist.
        - For "create" action, a new file is created with the provided content.
        - The function relies on a helper function `performUpdate` to process the file content.
    """
    
    full_path = filePath
    if full_path.endswith("/") == False:
        full_path += "/"
    
    full_path += fileName
    
    if not full_path.startswith("/home/attah/Documents/speedbuildjs"):
        full_path = f"/home/attah/Documents/speedbuildjs/{full_path}" #remove this

    print("full path ",full_path)
    print(action,line)
    print("#"*10)
    print(update)
    print("#"*10)

    accepted_actions = ["add","replace","remove"]

    if os.path.exists(full_path):
        if action in accepted_actions:
            try:
                with open(full_path,"r+") as file:
                    code = file.read()
                    updated_code = performUpdate(code,action,update,line)
                    
                    file.seek(0)        # Move to the beginning of the file
                    file.truncate(0)    # Step 2: Clear the file
                    file.write(updated_code)

            except (FileNotFoundError, FileExistsError):
                return f"Could not find file {full_path}"
        else:
            return "Action not recognised; action could not be carried out"
    else:
        if action == "create":
            os.makedirs(full_path,exist_ok=True)
            with open(full_path,"w") as file:
                file.write(update)

    return "File Update was successful"

# Execute Command
def executeCommand(command : str, framework:str):
    """
    Executes a given shell command using the PythonExecutor.

    Args:
        command (str): The shell command to execute as a string.
        framework (str) : django or express

    Behavior:
        - Splits the command string into a list of arguments.
        - Determines if the command should be self-exiting based on whether the last argument is "runserver".
        - Executes the command in a specified working directory and environment.
        - Return the standard output and standard error of the executed command.
    """

    print("executing command ",command,"\n\n\n\n")

    home = str(Path.home())
    env = None
    wkdir = None

    if framework == "django":
        wkdir = f"{home}/.sb/environment/django/speedbuild_project"
        venv_path = f"{home}/.sb/environment/django/venv"

        if sys.platform == "win32":
            python_path =  os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")

        # Modify environment to use the venv
        env = os.environ.copy()
        env['VIRTUAL_ENV'] = venv_path

        if sys.platform == "win32":
            env['PATH'] = f"{os.path.join(venv_path, 'Scripts')};{env['PATH']}"
        else:
            env['PATH'] = f"{os.path.join(venv_path, 'bin')}:{env['PATH']}"
    elif framework == "express":
        wkdir = f"{home}/.sb/environment/express" #TODO : change this to be dynamic
    else:
        return

    commandExecutor = PythonExecutor()
    command = command.split(" ")

    selfExiting = False if  command[-1] == "runserver" or command[-1] == "dev" else True

    stdout, stderr = commandExecutor.runCommand(command=command,cwd=wkdir,env=env,self_exit=selfExiting)

    stdout = "\n".join(stdout)
    stderr = "\n".join(stderr)

    return [stdout,stderr]

    if len(stderr) > 0:
        return f"ERROR Message : {stderr}"
    
    if len(stdout) > 0:
        return f"Standard Output : {stdout}"


# if __name__ == "__main__":
#     file_path = "/home/attah/Documents/sb_final/speedbuild/"
#     file_name = "views.py"n

#     update = """def hello():
#     print("Say Buhari")
#     print("Tinubu go kill us")
#     print('RIP Buhari')"""
    
#     update = "print('RIP Buhari')"

#     # updateFile(file_path,file_name,"remove",None,"14-19")
#     # print(getFileContent(file_path,file_name))
#     executeCommand("python manage.py runserver")