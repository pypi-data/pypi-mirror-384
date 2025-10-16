import os
import uuid
import json
import shutil
from pathlib import Path

def getAllProjectId():
    home = str(Path.home())
    path_to_sb_state = home + "/.sb/state"
    if not os.path.exists(path_to_sb_state):
        os.makedirs(path_to_sb_state,exist_ok=True)

    # get all projects
    allProjects = os.listdir(path_to_sb_state)
    return allProjects

def getProjectPathFromId(id):
    home = str(Path.home())
    project_path = home + "/.sb/state/"+id

    return project_path

def getInitialStateContent():
    return {
        "action":{},
        "undo":False
    }

def readStateJSON(project_id):
    project_path = getProjectPathFromId(project_id)
    state_path = project_path + "/state.json"

    if not os.path.exists(state_path):
        os.makedirs(project_path,exist_ok=True)
        with open(state_path,"w") as file:
            json.dump(getInitialStateContent(), file)

    with open(state_path,"r") as file:
        data = json.loads(file.read())
        return data

def updateState(project_id,action,filename):
    state = readStateJSON(project_id)

    project_path = getProjectPathFromId(project_id)
    state_path = project_path + "/state.json"

    actions = state['action']
    actions[filename] = action

    undo = state['undo']

    with open(state_path, "w") as file:
        json.dump({
            "action": actions,
            "undo": undo
        }, file, indent=4)

def generateNewProjectId():
    all_ids = set(getAllProjectId()) 
    for _ in range(1000):
        new_id = uuid.uuid4().hex[:16]
        if new_id not in all_ids:
            return new_id
    # Fallback – extremely rare
    return f"{new_id}:c{list(all_ids).count(new_id)}"

def clearProjectState(project_id):
    project_path = getProjectPathFromId(project_id)

    if os.path.exists(project_path):
        shutil.rmtree(project_path)

    # create fresh state.json file
    state_path = project_path + "/state.json"
    os.makedirs(project_path, exist_ok=True)
    with open(state_path,"w") as file:
        json.dump(getInitialStateContent(), file)

def getOrCreateProjectSBId(project_path):
    if not project_path.endswith("/"):
        project_path += "/"
    speedbuild_file_path = project_path + ".speedbuild"

    if os.path.exists(speedbuild_file_path):
        with open(speedbuild_file_path) as file:
            sb_id = file.read()
    else:
        # generate new id
        sb_id = generateNewProjectId()

        # create new .speedbuild file in project root
        with open(speedbuild_file_path,"w") as file:
            file.write(sb_id)

    return sb_id

def copyFileToState(project_id, source,project_root="", destination="prev"):
    sb_project_path = getProjectPathFromId(project_id)
    dest_dir = os.path.join(sb_project_path, destination)

    os.makedirs(dest_dir, exist_ok=True)

    relative_source_path = source[len(project_root):].lstrip("/")
    dest_file = os.path.join(dest_dir, relative_source_path)
    dest_file_folder = os.path.dirname(dest_file)

    if not os.path.exists(dest_file_folder):
        os.makedirs(dest_file_folder,exist_ok=True)

    if os.path.exists(source):
        shutil.copy2(source, dest_file)
    return dest_file
