import os
import yaml
import zipfile
from pathlib import Path

from ....utils.utils import getCurrentDjangoFiles
from .extract import getTemplateFileNames
from .feature_dependencies import removeDuplicates
from ....parsers.python.parser import PythonBlockParser

from ....utils.sb_agent import agent
from ....utils.query_split import query_splitter
from .write_dependency import sortFile, writeToFile
from ....utils.state import clearProjectState, copyFileToState, getOrCreateProjectSBId, updateState

user_home = str(Path.home())

def read_yaml(file_path):
    with open(file_path, "r") as file:
        data = yaml.safe_load(file)
    return data


def getAppFileContent(appName,fileName,project_path):
    """
    Reads a Python file, separates import statements from the rest of the code, and returns them as two lists.

    Args:
        appName (str): The name of the application (used to construct the file path).
        fileName (str): The path to the file to be read.
        project_path (str): The root path of the project.

    Returns:
        list: A list containing two elements:
            - imports (list): A list of import statements found in the file.
            - code (list): A list of code blocks that are not import statements.

    Note:
        This function uses PythonBlockParser().parse_code to split the file content into code chunks.
    """
    imports = []
    code = []

    fileToUpdate = fileName.split("/")[-1]
    filePath = f"{project_path}/{appName}/{fileToUpdate}"

    with open(fileName, "r") as file:
        data = file.read()
        data = PythonBlockParser().parse_code(data)
        for chunk in data:
            if chunk.startswith("import ") or chunk.startswith("from "):
                # individualImports = getIndividualImports(chunk)
                imports.append(chunk)
            else:
                code.append(chunk)

    return [imports,code]


def processFile(fileName,appName,project_path,template_path,feature_app_name=None,django_root=None,processed_file_path={},project_id=None,file_written=[],conflicts=[]):
    imports = []
    code = []

    #get new feature code
    with open(fileName,"r") as file:
        data = file.read()
        data = PythonBlockParser().parse_code(data)

        for chunk in data:
            if chunk.startswith("import ") or chunk.startswith("from "):
                # individualImports = getIndividualImports(chunk)
                imports.append(chunk)
            else:
                code.append(chunk)
    
    #get existing file content
    fileImports, fileCode = getAppFileContent(appName,fileName,project_path)

    # print("filename is this ", fileName)

    # old implementation
    fileCode.extend(code)
    fileImports.extend(imports)
    fileCode = removeDuplicates(fileCode)
    fileImports = removeDuplicates(fileImports)

    #merge current and new code import
    # fileImports.extend(imports)
    # fileImports = removeDuplicates(fileImports)

    """
    🧩 You're Laying the Right Foundation
    Here’s what your sketch is doing, in essence:

    Get all "current" code chunk names (fileCode).

    For each chunk in the new version (code):

    If its name already exists in fileCode → there's a potential conflict.

    Else → it's a new chunk and can be appended.

    Perfectly valid.
    """

    # #merge current and new code while checking for conflicts
    # current_chunk_names = [get_assigned_variables(chunk) for chunk in fileCode]

    # for chunk in code:
    #     chunk_name = get_assigned_variables
    #     if chunk_name in current_chunk_names:
    #         pass
    #         # add chunk to current with conflict marker
    #     else:
    #         fileCode.append(chunk)


    fileToUpdate = fileName.split("/")[-1]
    filePath = f"{project_path}/{appName}"

    "get all files in filePath"

    # TODO make this dynamic, get all python file in app folder
    django_files = getCurrentDjangoFiles(filePath)#["models.py","urls.py","views.py","admin.py"]

    if "sb_app" not in fileName: # also check if filename is custom django names else write file in sb_utils folder

        new_file_path = fileName.replace(template_path,"")
        if new_file_path.startswith("/"):
            new_file_path = new_file_path[1:]

        # print(new_file_path.split("/"), " my filename is this\n\n")

        filePath = filePath.split("/")

        write_to_project_root = len(new_file_path.split("/")) > 1
        # filePath.pop()

        if write_to_project_root:
            # print("update ", fileToUpdate)

            if fileToUpdate not in django_files:
                filePath.append("sb_utils")
                #  update import here
                # writing to sb utils
                new_imports = []
                for line in fileImports:
                    path,dependency = line.split("import ")
                    path = path.replace("from","").replace(".sb_utils","").strip()
                    if path.startswith("."):
                        path = path[1:]


                    if f"{path}.py" in django_files:
                        new_imports.append(f"from {appName}.{path} import {dependency}")
                        continue

                    if "sb_utils" in filePath:
                        line = line.replace(".sb_utils","")

                    new_imports.append(line)
                    # elif line.startswith("import "):
                    #     new_imports.append(line)
                    # else:
                    #     pass

                fileImports = new_imports
        else:
            if django_root:
                # print(" we dey here oo help us #########################")
                # print(fileName)
                # print(f"{project_path}/{django_root}")
                filePath = [project_path,django_root]
            # settings files
            # TODO files to add to the main django folder

        filePath = "/".join(filePath)
        

        if not os.path.exists(filePath):
            os.makedirs(filePath)

    
    # update imports to remove unnecessary imports
    new_imports = []
    for line in fileImports:
        if ".sb_utils" in line:
            path,dependency = line.split("import")
            path = path.replace("from","").strip()
            path = path.replace(".sb_utils.","").strip()
            # print("sb_utils path is ", path)

            if f"{path}.py" in django_files:
                if f"{path}.py" != fileToUpdate:
                    new_imports.append(f"from .{path} import {dependency}")
                continue

            elif path in processed_file_path.keys():
                main_path = processed_file_path[path]
                new_imports.append(f"from {main_path}.{path} import {dependency}")
                continue

        new_imports.append(line)
    fileImports = new_imports

    importAsString = "\n".join(fileImports)
    codeAsString = "\n".join(fileCode)
    fileContent = importAsString + "\n\n" + codeAsString

    # print("############################# new path is ",filePath)

    # TODO : start here

    dest = f"{filePath}/{fileToUpdate}"

    file_state_key = dest.replace(project_path,"")

    # print("file path is ",filePath)
    # print("file name is ", fileName)
    # print("state key is ", file_state_key)
    # print("file to update ", fileToUpdate)

    # state before write
    if project_id:
        if fileToUpdate not in file_written:
            # copy file ]to prev state
            copyFileToState(project_id,dest,"prev")

            action = "update"
            if not os.path.exists(dest):
                action = "create"

            # update state.json to state file updated
            updateState(project_id,action,file_state_key)

            # add to file_written
            file_written.append(fileToUpdate)

    conflicts = writeToFile(filePath,fileContent,fileToUpdate,conflicts)
    if fileToUpdate == "models.py":
        sortFile(f"{filePath}/{fileToUpdate}")

    # state after write
    if project_id:
        # copy file to last_sb_update state
        copyFileToState(project_id,dest,"last_sb_update")

    return [file_written,conflicts]


def getTemplateFilteredFiles(template_unpack_path,feature_name):
    root_files = []
    filtered_files = []
    files = getTemplateFileNames(template_unpack_path)
 
    for i in files:
        if i not in ["settings.py", f"sb_{feature_name}.yaml"] and i.endswith("md") == False:
            if len(i.split("/")) == 1:
                # add to root_files also add to filtered_files
                root_files.append(i)
                filtered_files.append(i)

            elif len(i.split("/")) > 1:
                filtered_files.append(i)

    filtered_files = sorted(filtered_files, key=lambda x: not x.startswith('.sb_utils')) 
    return [filtered_files,root_files]

        
def getFeatureFromTemplate(template_path,project_root,template_name,django_root,app_name):
    """
    1) Ask for which app to implement feature. -- done
    2) Ask for Customization prompt and customize code. -- done
    3) Copy code and save in the right files (do proper refrencing).
    """

    if app_name is None:
        app_name = input("Which django app do you want to implement feature in : ")
    
    app_path = f"{project_root}/{app_name}"

    conflicts = []


    # feature_name = template_path.split("/")[-1].split(".")[0]
    feature_name = [word for word in template_path.split("/") if ".zip" not in word][-1]

    # print("feature name is ",feature_name)

    
    # path_to_template = f"{project_root}/.sb/{template_name}"

    path_to_template = f"{user_home}/.sb/sb_extracted" #{template_name}"
    
    if not os.path.exists(path_to_template):
        os.makedirs(path_to_template, exist_ok=True)

    processed_file_path = {}

    # print("app path is ", app_path)

    if os.path.exists(app_path) and os.path.isdir(app_path):
        print("\n\n------- Generating Feature -------\n\n")

        print(f"Getting template from {template_path}")

        # # unpack template to .sb folder
        # sb_dir = f"{project_root}/.sb"
        # os.makedirs(sb_dir, exist_ok=True)

        # # clear old content from folder
        # clear_folder(sb_dir)

        template_unpack_path = f"{path_to_template}/{feature_name}"
        os.makedirs(template_unpack_path, exist_ok=True)

        # unpack
        # TODO : clear previous zip content, before unzipping again
        print("Unpacking template")
        with zipfile.ZipFile(template_path, 'r') as zip_ref:
            zip_ref.extractall(template_unpack_path)

        # Get and read template configuration file
        # feature_name = template_path.split("_")[-1].replace(".zip","").strip()
        feature_name = feature_name.replace("speed_build_","")
        template_root = f"{path_to_template}/{template_name}"
        config_file_path = f"{template_root}/sb_{feature_name}.yaml"
        data = read_yaml(config_file_path)

        feature_app_name = data['feature_file_path'].split("/")[0]

        # proceed_with_customization = False
        filtered_files = []
        root_files = []

        # if prompt is None:
        #     while True:
        #         customize = input("would you like to customize feature (yes or no[default]) : ")
        #         customize = customize.strip()

        #         if customize.lower() in ["yes","no","y","n"]:
        #             if customize.lower() == "yes":
        #                 prompt = input("Enter Customization prompt (be as detailed as possible) : \n")
        #             break
        #         else:
        #             print("Enter a valid response")
        #             continue

        # if prompt is not None:
        #     # if prompt is None:
        #     #     prompt = input("Enter Customization prompt (be as detailed as possible) : \n")
        #     # make agent call here
        #     # pass prompt and a list of all files in template
    
        #     # TODO : leave commented for now
        #     actions = query_splitter(prompt)

        #     filtered_files,root_files = getTemplateFilteredFiles(template_unpack_path,feature_name)

        #     for root_file in root_files:
        #         path_name = root_file.replace(".py","").strip()
        #         processed_file_path[path_name] = django_root 

        #     root_files.extend(filtered_files) # merge files NB, made sure root files appear first
        #     filtered_files = root_files

        #     # print("all actions are \n", actions)
        #     for step in actions:
        #         agent(filtered_files,step,app_path,feature_name)
        # else:
        #     pass

        files = getTemplateFileNames(template_unpack_path)

        for i in files:
            if i not in ["settings.py", f"sb_{feature_name}.yaml"] and i.endswith("md") == False:
                if len(i.split("/")) == 1:
                    root_files.append(i)

                elif len(i.split("/")) > 1:
                    filtered_files.append(i)

        filtered_files = sorted(filtered_files, key=lambda x: not x.startswith('.sb_utils')) 

        for root_file in root_files:
            path_name = root_file.replace(".py","").strip()
            processed_file_path[path_name] = django_root 

        root_files.extend(filtered_files) # merge files NB, made sure root files appear first
        filtered_files = root_files

        # TODO: print feature description, along with dependencies and fields

        # print(filtered_files)

        project_id = getOrCreateProjectSBId(project_root)

        # clear project state 
        clearProjectState(project_id)

        file_written = []

        # TODO : get filtered files again so u get new files llm created
        filtered_files,root_files = getTemplateFilteredFiles(template_unpack_path,feature_name)

        for file in filtered_files:
            file_path = f"{template_root}/{file}"
            # print(file_path)
            file_written,conflicts = processFile(file_path,app_name,project_root,template_root,feature_app_name,django_root,processed_file_path,project_id,file_written,conflicts)

    else:
        raise ValueError(f"No app with name {app_name} in {project_root}")
        return None
    
    return [app_name,template_root,conflicts]
