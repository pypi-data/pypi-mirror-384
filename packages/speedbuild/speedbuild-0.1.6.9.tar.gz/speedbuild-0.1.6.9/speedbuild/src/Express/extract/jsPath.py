import os
import shutil
from pathlib import Path
from rich.prompt import Prompt

from ....src.Express.deploy.debug import debugTemplate

from .extractJs import handleExtraction
from .move_file import list_all_files, moveFile
from ....cli_output.output import StatusManager
from ....langgraph_agent.agents.indexer.indexJs import Indexer
from .handle_js_route import getRoutePathAndMethodsOrReturnNone
from ....parsers.javascript_typescript.jsParser import JsTxParser
from ....utils.template_update import checkTemplateForVersionUpdate


def clear_folder(folder_path):
    """
    Clear all contents of a specified folder, removing files, symlinks, and subdirectories.

    Args:
        folder_path (str): Path to the folder to be cleared.

    Returns:
        None

    Raises:
        OSError: If there are permission issues or other OS-level errors when deleting files.
        FileNotFoundError: If the specified folder path does not exist.

    Examples:
        >>> clear_folder('/path/to/folder')
        # All contents of the folder will be deleted
    """
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) or os.path.islink(file_path):  
            os.remove(file_path)  # Delete files & symlinks
        elif os.path.isdir(file_path):  
            shutil.rmtree(file_path)  # Delete directories


async def startExpressExtraction(path,file_name,project_root):
    """
    Extracts and processes Express.js route handlers from JavaScript files.
    This function parses JavaScript code, extracts route handlers matching a specified path,
    processes dependencies, and organizes extracted files into appropriate folders.
    Args:
        path (str): The route path to extract (e.g., "/api/users")
        file_name (str): Path to the JavaScript source file
        project_root (str): Root directory of the project
    Returns:
        None
    Raises:
        ValueError: If the specified route path is not found in the source file
    The function performs the following steps:
    1. Parses JavaScript code to extract chunks and dependencies
    2. Processes and maps dependencies
    3. Locates and extracts the route handler matching the specified path
    4. Indexes and categorizes extracted files
    5. Moves files to appropriate folders based on categorization
    6. Creates a zip archive of the extracted template
    """
    parser = JsTxParser()
    logger = StatusManager()

    logger.print_message("Extracting Feature Code")
    logger.start_status("Starting Extraction")

    extracted = False
    entry_file = None
    extra_dependencies = []
    dep_to_path_mappings = {}

    _,chunks,_,import_deps = await parser.parse_code(file_name)

    for item in import_deps:
        element = import_deps[item]
        for depItem in element:
            if depItem["alias"] != None:
                deps = [depItem['alias']]
            elif "ext_deps" in depItem.keys() and len(depItem["ext_deps"]) > 0:
                deps = depItem['ext_deps']
            else:
                deps = [depItem['dep']]
            
            extra_dependencies.extend(deps)

            # create dep to path mapping
            for singleDep in deps:
                dep_to_path_mappings[singleDep] = item

    for chunk in chunks:
        words = chunk.split(".")
        if len(words) > 1:
            route_info = getRoutePathAndMethodsOrReturnNone(chunk,chunks)
            if route_info is not None:
                if route_info[0] == path:
                    entry_file = await handleExtraction(project_root,chunk,file_name)
                    extracted = True
                    break
    
    if not extracted:
        # Not found
        raise ValueError("Route specified was not found in ",file_name)

    logger.update_status("Indexing Feature files")    
    # sort and index extracted files here
    indexer = Indexer(
        "gpt-5",
        "openai",
        'OPENAI_API_KEY',
        os.environ.get("OPENAI_API_KEY","")
    )
    indexer.setup()
    indexer_ignore = ["package.json"]

    if entry_file is not None:
        indexer_ignore.append(entry_file)
        

    # step 1 : get all extracted files
    all_files = list_all_files("./output")
    for file in all_files:
        if os.path.relpath(os.path.abspath(file),os.path.join(project_root,"output")) in indexer_ignore:
            continue

        # step 2 : find out what folder they are suppose to be in\
        logger.update_status(f"Indexing file : {os.path.basename(file)}")    
        res = indexer.index(file)
        folder = res['category']

        path_in_file = file.split("/")
        if folder not in path_in_file: # check if file is already in the right folder
            # step 3 : move them to correct folder and step 4 : update file refrence in other files 
            # write_path = os.path.join(".")
            await moveFile(file,os.path.join(os.path.abspath("./output"),folder))

    # package into zip
    home = str(Path.home())
    template_path = os.path.join(home,".sb_zip")#f"{home}/.sb_zip"
    output_dir = os.path.join(project_root,"output")#f"{project_root}/output"

    if not os.path.exists(template_path):
        os.makedirs(template_path,exist_ok=True)

    
    logger.stop_status()

    template_name = Prompt.ask("[bold green]Enter Template Name [/bold green]")
    # input("What do you want to name this template : ")

    if not template_name.startswith("speedbuild_"):
        template_name = f"speed_build_{template_name}"

    template_path = os.path.join(template_path,template_name)#f"{template_path}/{template_name}"
    
    shutil.make_archive(template_path, 'zip', output_dir)

    clear_folder(output_dir)

    checkTemplateForVersionUpdate(template_path)

    # debug template code
    # TODO : only do this if template version changes
    # try:
    test_environment_path = os.path.join(home,".sb","environment","express")#f"{home}/.sb/environment/express"
    extracted_template_path = os.path.join(template_path,"lts.zip")

    debugTemplate(extracted_template_path)

    extracted_template_path = extracted_template_path.replace(".zip","")

    # clear and delete node modules folder
    clear_folder(os.path.join(test_environment_path,"node_modules"))
    os.rmdir(output_dir)
    # delete package_lock.json
    os.remove(os.path.join(test_environment_path,"package-lock.json"))

    # overwrite zip file
    shutil.make_archive(extracted_template_path, 'zip', test_environment_path)
    # except:
    #     pass

    logger.print_message(f"Extraction Complete : template saved with name `{template_name}`")