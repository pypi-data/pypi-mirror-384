"""move template code to target file"""
import os
import json
from pathlib import Path

from ....utils.state import clearProjectState, copyFileToState, getOrCreateProjectSBId, updateState

from ....parsers.javascript_typescript.js_var_names import get_variable_name_and_type

from .merge_js_entry import mergeEntryFiles
from ....cli_output.output import StatusManager
from ....parsers.javascript_typescript.jsParser import JsTxParser
from ....src.Express.extract.reverseImport import convertToImportStatements


parser = JsTxParser()
home = str(Path.home())
test_environment = os.path.join(home,".sb","environment","express")

def getTemplateFileNames(path):
    file_paths = []
    for root, _, files in os.walk(path):
        if "node_modules" in root:
            continue
        for file in files:
            # Get the absolute path by joining root and file
            absolute_path = os.path.join(root, file)
            file_paths.append(absolute_path)
    return file_paths


def processPackageDotJson(path):
    package_path = os.path.join(path,"package.json")
    if not os.path.exists(package_path):
        raise ValueError("Cannot find package.json in test environment")
    
    with open(package_path,"r") as file:
        data = json.loads(file.read())
        return [
            data['main'],
            data['dependencies'],
            data['dev-dependencies'] if "dev-dependencies" in data.keys() else None
        ]
    
    raise ValueError("Invalid package.json content")

def writeExpressCodeToFile(dest,import_deps,chunks):
    
    with open(dest,"w") as file:
        code = ""
        if len(import_deps) > 0:
            import_statements = convertToImportStatements(import_deps)
            code += "\n".join(import_statements)

        if len(chunks) > 0:
            code += "\n\n"
            code += "\n\n".join(chunks)

        file.write(code)

async def moveTemplateFilesToTargetProject(destination_addr):
    logger = StatusManager()

    logger.start_status("Moving Template Files to target project")

    template_files = getTemplateFileNames(test_environment)
    entry_file, dependencies, devDependencies = processPackageDotJson(test_environment)

    destination_deploy_addr = os.path.join(destination_addr,"speedbuild") #TODO : make dynamuc

    # managing state
    project_id = getOrCreateProjectSBId(destination_addr)
    clearProjectState(project_id) # clear project state 

    
    
    template_files_in_destination_folder = []
    file_written = []

    for file in template_files:
        if os.path.basename(file) not in ['package.json',"package-lock.json",entry_file]:
            logger.update_status(f"Moving : {os.path.basename(file)}")
            file_path = file.replace(test_environment,"").lstrip("/")
            # full_dest_path = f"{destination_addr}/{file_path}"
            full_dest_path = os.path.join(destination_deploy_addr,file_path)

            file_state_key = full_dest_path[len(destination_addr):].lstrip("/")

            action = "update" # state file action

            if not os.path.exists(full_dest_path):
                os.makedirs(os.path.dirname(full_dest_path),exist_ok=True)
                chunks = []
                import_deps = {}
                chunk_var_mapping = {}
                action = "create" # update state file action to create if file does not exist
            else:
                _,chunks,chunk_var_mapping,import_deps = await parser.parse_code(full_dest_path)
            

            # print("file state file is ",file_state_key)

            # saving current destination file state
            if project_id:
                if full_dest_path not in file_written:
                    # copy file to prev state
                    copyFileToState(project_id,full_dest_path,destination_addr,"prev")
                    
                    # update state.json to state file updated
                    updateState(project_id,action,file_state_key)

                    # add to file_written
                    file_written.append(full_dest_path)


            # get template contents
            _,template_chunks,_,template_import_deps = await parser.parse_code(f"{test_environment}/{file_path}")
            
            # merge chunks
            for chunk in template_chunks:

                if chunk not in chunks:
                    chunk_name = get_variable_name_and_type(chunk) # returns a list : [type, var_name]
      
                    if chunk_name != None and chunk_name[1] in chunk_var_mapping and chunk != chunk_var_mapping[chunk_name[1]]:
                        index = chunks.index(chunk_var_mapping[chunk_name[1]])
                        conflictCode = f"<<<<<<< SpeedBuild update \n{chunk_var_mapping[chunk_name[1]]}\n=======\n{chunk}\n>>>>>>>"
                        chunks[index] = conflictCode
                    else:
                        chunks.append(chunk)

            # merge import 
            # TODO : import issue here
            for importStatement in template_import_deps:
                if importStatement not in import_deps:
                    import_deps[importStatement]= template_import_deps[importStatement]

            # write code to destination
            template_files_in_destination_folder.append(full_dest_path)
            writeExpressCodeToFile(full_dest_path,import_deps,chunks)

            # state after write
            if project_id:
                # copy file to last_sb_update state
                copyFileToState(project_id,full_dest_path,destination_addr,"last_sb_update")

    # merge project entry files
    logger.update_status("Processing package.json")
    dest_entry_file, _, _ = processPackageDotJson(destination_addr)

    logger.stop_status()

    entry_file_path = os.path.join(destination_addr,dest_entry_file)
    action = "update" # state file action
    if project_id:
        # copy entry file to prev state
        copyFileToState(project_id,entry_file_path,destination_addr,"prev")

        file_state_key = entry_file_path[len(destination_addr):].lstrip("/")
        
        # update state.json to state file updated
        updateState(project_id,action,file_state_key)

    import_deps,chunks = await mergeEntryFiles(
        entry_file_path,
        os.path.join(test_environment,entry_file),
        template_files_in_destination_folder,
        logger
    )

    # write entry 
    writeExpressCodeToFile(entry_file_path,import_deps,chunks)

    # state after write
    if project_id:
        # copy file to last_sb_update state
        copyFileToState(project_id,entry_file_path,destination_addr,"last_sb_update")

    # process package.json
    dest_package_json = os.path.join(destination_addr,"package.json")

    if project_id:
        # copy entry file to prev state
        copyFileToState(project_id,dest_package_json,destination_addr,"prev")

        file_state_key = dest_package_json[len(destination_addr):].lstrip("/")
        
        # update state.json to state file updated
        updateState(project_id,action,file_state_key)

    if not os.path.exists(dest_package_json):
        raise ValueError("can't find target project package.json")
    
    with open(dest_package_json,"r+") as file:
        data = json.loads(file.read())

        if dependencies is not None and len(dependencies.keys()) > 0:
            for dep in dependencies:
                if dep not in data['dependencies']:
                    data['dependencies'][dep] = dependencies[dep]

        if devDependencies is not None and len(devDependencies.keys()) > 0:
            for dep in devDependencies:
                if dep not in data['devDependencies']:
                    data['devDependencies'][dep] = devDependencies[dep]

        # clear file and write new file content
        file.seek(0)
        file.truncate()
        file.write(json.dumps(data,indent=4))
    
    if project_id:
        # copy file to last_sb_update state
        copyFileToState(project_id,dest_package_json,destination_addr,"last_sb_update")
    
    logger.print_message("Template files moved to target project")


# TODO : remove state repetition from this file