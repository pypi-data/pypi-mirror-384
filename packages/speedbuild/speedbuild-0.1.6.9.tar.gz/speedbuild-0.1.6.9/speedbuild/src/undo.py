import os
import json
import shutil
import tempfile
from ..utils.state import getProjectPathFromId


def swap_folder_contents(folder_a, folder_b):
    if not os.path.isdir(folder_a) or not os.path.isdir(folder_b):
        raise ValueError("Both paths must be existing folders.")

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Move contents of A -> temp
        for item in os.listdir(folder_a):
            shutil.move(os.path.join(folder_a, item), temp_dir)

        # Move contents of B -> A
        for item in os.listdir(folder_b):
            shutil.move(os.path.join(folder_b, item), folder_a)

        # Move contents of temp -> B
        for item in os.listdir(temp_dir):
            shutil.move(os.path.join(temp_dir, item), folder_b)


def updateStateDotJSON(path,actions,undo):
    if os.path.exists(path):
        with open(path,"w") as file:
            json.dump({
            "action": actions,
            "undo": not undo
        }, file, indent=4)
    else:
        raise ValueError(f"Something went wrong, cannot find {path}")


def getFileStateAndCurrentPath(fileName,project_state_path,current_project_path):
    current_file_path = os.path.join(current_project_path, fileName.lstrip("/")) #this take file name plus folder name

    # fileName = fileName.lstrip("/").split("/")[-1] #get only filename, cause we dont store parent folders in state
    last_sb_state_file_path = os.path.join(project_state_path, "last_sb_update", fileName)
    prev_state_file_path = os.path.join(project_state_path, "prev", fileName)

    return [prev_state_file_path,last_sb_state_file_path,current_file_path]
                    

def FileIsSameAsPrevState(prev_file_state, last_update_file):
    """
    Compare the contents of file_name in the current project path and in the 'prev' directory.
    Returns True if the files are exactly the same, False otherwise.
    """

    if not os.path.exists(prev_file_state) or not os.path.exists(last_update_file):
        return False

    with open(prev_file_state, "rb") as f1, open(last_update_file, "rb") as f2:
        return f1.read() == f2.read()
    
def getTemplateFileNames(path):
    file_paths = []
    for root, _, files in os.walk(path):
        if "node_modules" in root:
            continue
        for file in files:
            # Get the absolute path by joining root and file
            absolute_path = os.path.join(root, file)
            file_paths.append(absolute_path.replace(path,"").lstrip("/"))
    return file_paths


def undoSBDeploy():

    current_project_path = os.getcwd()

    config_path = os.path.join(current_project_path,".speedbuild")

    if not os.path.exists(config_path):
        print("Undo was Unsuccessful")
        return
    
    with open(config_path,"r") as sbFile:
        project_id = sbFile.read()
    
    # get project path
    project_state_path = getProjectPathFromId(project_id)
    undo_actions = {}

    state_file_path = f"{project_state_path}/state.json"
    state_prev_folder = os.path.join(project_state_path, "prev")
    state_last_sb_update_folder = os.path.join(project_state_path, "last_sb_update")

    if os.path.exists(state_file_path):
        with open(state_file_path,"r") as file:
            data = json.loads(file.read())

            actions = data['action']
            undo = data['undo']

            # If one file in prev state is not matching current project state, Abort undo
            files_in_prev = getTemplateFileNames(state_prev_folder)#os.listdir(state_prev_folder)
            proceed_with_undo = True

            for step in actions.keys():
                # fileName = step.lstrip().split("/")[-1]
                if step in files_in_prev:
                    # check if its same
                    prev_state_file_path,last_sb_state_file_path,current_file_path = getFileStateAndCurrentPath(step,project_state_path,current_project_path)
 
                    if os.path.exists(current_file_path):
                        if not FileIsSameAsPrevState(current_file_path,last_sb_state_file_path):
                            proceed_with_undo = False

            if not proceed_with_undo:
                print("Files has changed too much to proceed with undo")
                return
            
            for step in actions.keys():
                last_file_action = actions[step]

                prev_state_file_path,last_sb_state_file_path,current_file_path = getFileStateAndCurrentPath(step,project_state_path,current_project_path)

                if last_file_action == "update" or last_file_action == "delete":
                    with open(current_file_path,"w") as file:
                        with open(prev_state_file_path,"r") as prevFile:
                            file.write(prevFile.read())

                        # update state action
                        undo_actions[step] = "update" if last_file_action=="update" else "create"

                elif last_file_action == "create":
                    #delete file
                    if os.path.exists(current_file_path):
                        os.remove(current_file_path)

                    # update state action
                    undo_actions[step] = "delete"

    # swap prev and last_update folder
    swap_folder_contents(state_prev_folder,state_last_sb_update_folder)

    # update state.json
    updateStateDotJSON(state_file_path,undo_actions,data['undo']) 

    print("finished here")