import os
import re

from .manage_url import merge_urls
from .var_utils import get_assigned_variables
from ....parsers.python.parser import PythonBlockParser
from .feature_dependencies import arrangeChunks, getBlockDependencies, getCodeBlockFromFile, removeDuplicates


parser = PythonBlockParser()

def getWritePath(file_path, output_dir):
    path = file_path.split("/")
    write_dir = "output/"+output_dir+"/"

    if len(path) == 1 :
        dest = write_dir+path[0]
    
    else:
        
        file_name = path.pop()
        file_folder = path.pop()

        dest = f"{write_dir}{file_folder}"

        if not os.path.exists(dest):
            os.makedirs(dest)

        dest = f"{dest}/{file_name}"
    return dest


def writeCodeToFile(file_path,code,imports, writeAfter=False, output_dir=None):

    """
    write feature code to template file
    """

    dest = getWritePath(file_path,output_dir)

    if os.path.exists(dest):

        old_code = []
        old_imports = []

        # append to file
        with open(dest, "r+") as file:
            data = file.read()  # Step 1: Read existing content
        
            file.seek(0)        # Move to the beginning of the file
            file.truncate(0)    # Step 2: Clear the file

            old_content = parser.parse_code(data)
            for chunk in old_content:
                if chunk.startswith("import ") or chunk.startswith("from "):
                    # imports.extend([chunk])
                    old_imports.append(chunk)
                else:
                    old_code.append(chunk)

            # if writeAfter:
            #     write_data = f"{imports}\n{data}\n{code}"
            # else:
            #     write_data = f"{imports}\n{code}\n{data}"

            imports.extend(old_imports)
            old_code.insert(0,code)

            code = old_code

            # chunks = parser.parse_code(write_data)#split_code_into_sections(write_data)
            
            # for chunk in chunks:
            #     if chunk.startswith("import ") or chunk.startswith("from "):
            #         # imports.extend([chunk])
            #         imports.append(chunk)
            #     else:
            #         code.append(chunk)

            if len(imports) > 0:  # Step 3: Write new content
                imports = removeDuplicates(imports)
                imports = "\n".join(imports)
                file.write(imports + "\n")

            if code is not None:
                # TODO: we might need to rearrange chunks
                code = [chunk for chunk in code if chunk is not None]
                file.write("\n\n")
                code = removeDuplicates(code)
                code = "\n\n".join(code)
                file.write(code)  # Append old content to new content
    else:
        with open(dest,"w") as file:
            if(len(imports)>0):
                file.write("\n".join(imports))
                file.write("\n\n")
            if code is not None:
                file.write(code)

    # # TODO : sort code, problem with sorting in views.py
    if "urls.py" not in dest and "views.py" not in dest:
        sortFile(dest)


def extract_settings_references(code):
    pattern = r'settings\.\w+'
    confs = [i.replace("settings.","").strip() for i in re.findall(pattern, code)]

    return confs

def checkIfFeatureAlreadyInFile(file_path,feature):
    if os.path.exists(file_path) == False:
        return False
    
    with open(file_path) as file:
        chunks = parser.parse_code(file.read())
        names = []
        for chunk in chunks:
            chunk_name = get_assigned_variables(chunk,True)
            if len(chunk_name) > 0:
                names.append(chunk_name)

        # print("checking ",file_path," ",names, " feture ", feature)
        return feature in names
    
def get_temp_file_path(file_path, project_root,project_name,app_name):
    # print("working with ", file_path)
    file_path_list = file_path.split("/")
    file = file_path_list.pop().strip()

    main_path = "/".join(file_path_list)
    
    parent_dir = file_path_list.pop()

    main_path = main_path.split("/")[-1].strip()

    # print(app_name, " here ", parent_dir)
    # print(main_path, "  pth ",project_name)

    app_name = app_name.strip()
    parent_dir = parent_dir.strip()

    if project_name.strip() == main_path.strip():
        # TODO : convert this to write to root
        templtae_file_path = file
        

    elif app_name != parent_dir:
        # check if .sb_utils folder exist
        # if not create folder
        templtae_file_path = ".sb_utils/"+file

    else:
        templtae_file_path = "sb_app/"+file

    return templtae_file_path

# get template conf from OneStep       
def OneStep(
        file_path,
        feature,
        project_root,
        folders_in_project_root,
        writeToFile=True,
        app_name="/",
        use_email=False,
        settings_conf=[],
        project_name=None,
        output_dir = None,
        processed = []
        ):
    
    # feature_name = feature
    # print("running for feature ", feature, ' processed ', processed)
    packages = set()
    use_email = use_email
    # settings_conf = [] #change to ordered set

    # print("output dir from one fiel is ", output_dir)

    if os.path.exists(file_path):
        with open(file_path,"r") as file:
            data = file.read()
            file_dependencies = PythonBlockParser().parse_code(data)

            for chunk in file_dependencies:
                if chunk.startswith("import ") or chunk.startswith("from "):
                    if "django.core.mail" in chunk:
                        use_email = True

            # get feature
            feature_code = getCodeBlockFromFile(feature,file_dependencies)

            # get feature dependencies
            feature_dependencies = getBlockDependencies(feature_code,file_dependencies)

            # print("project path ", folders_in_project_root)

            # get feature imports
            deb_imports = [] #[f"from {e['packagePath']} import {e['imports']}" for e in feature_dependencies if e['packagePath'] != "."]
            
            for entry in feature_dependencies:
                package_path = entry['packagePath'].strip()
                imports = entry['imports'].strip()

                if package_path == imports:
                    deb_imports.append(f"import {imports}")
                elif package_path != ".":

                    # replace import here
                    # if import is coming from a custom package, replace path to .sb_utils
                    package_path_words = package_path.split(".")
                    file_name = package_path_words[-1]

                    if package_path_words[0] in folders_in_project_root:  #get all folders name in django project root folder
                        new_package_path = f".sb_utils.{file_name}" #change path here maybe use an absolute path
                        deb_imports.append(f"from {new_package_path} import {imports}")
                    else:
                        deb_imports.append(f"from {package_path} import {imports}")

            # This remove folder name from import and replace with .
            # we will unpack all of this into a sinlge django app
            # so we want to use . to refrence the app that we will unpack to as the parent dir
            
            for index,importLine in enumerate(deb_imports):
                line = importLine.split("import")[0]
                line = line.replace("from","").strip()

                if len(line) > 0 and line.startswith(".") == False:
                    folder_name = line.split(".")[0]
                    if folder_name in folders_in_project_root:
                        importLine = importLine.replace(line,line[len(folder_name):])

                        deb_imports[index] = importLine

            if writeToFile:
                template_file_path = get_temp_file_path(file_path,project_root,project_name,app_name)

                # write code to output
                # make write optional
                # add to processed here
                # print("writting  ",feature,"\n\n")
                writeCodeToFile(template_file_path,feature_code, deb_imports,output_dir=output_dir)
            
            if len(feature_dependencies) > 0:
                # loop through dependencies
                for feature_dep in feature_dependencies:
                    path,dep = [feature_dep['packagePath'], feature_dep['imports']]

                    # print("dependencies ",path," ",dep)
                    
                    if path != ".":
                        if path.startswith("."):
                            new_path = file_path.split("/")
                            new_path.pop()
                            new_path.append(f'{path[1:]}.py')
                            new_path = "/".join(new_path)
                            path = new_path
                        else:
                            package = path.split(".")[0]

                            if package != "django":
                                if package not in folders_in_project_root:
                                    packages.add(package)
                            else:
                                full_import = path + f".{dep}"

                                if full_import.startswith("django.conf.settings"):
                                    # print("found settings configuration ")
                                    # feature_code
                                    new_settings_conf = extract_settings_references(feature_code)
                                    settings_conf.extend(new_settings_conf)

                                # check for django settings import here
                                
                            path = path.split(".")
                            path = project_root + "/"+"/".join(path)+".py"

                        # if dep not in processed:
                        check_file_path = get_temp_file_path(path,project_root,project_name,app_name)
                        dest = getWritePath(check_file_path,output_dir)
                        if checkIfFeatureAlreadyInFile(dest,dep) == False:
                            feature_packages,use_email,settings_conf = OneStep(path,dep,project_root,folders_in_project_root,True,app_name,use_email,settings_conf, project_name,output_dir,processed)
                            packages = packages.union(feature_packages)
                    else:
                        # if dep not in processed:
                        check_file_path = get_temp_file_path(file_path,project_root,project_name,app_name)
                        dest = getWritePath(check_file_path,output_dir)

                        if checkIfFeatureAlreadyInFile(dest,dep) == False:
                            feature_packages, use_email, settings_conf = OneStep(file_path,dep,project_root,folders_in_project_root,True,app_name,use_email,settings_conf,project_name,output_dir,processed)
                            packages = packages.union(feature_packages)

    # print("processed : ", processed, "\n\n\n ##############################################")
    return [packages, use_email, settings_conf]

def getOldFile(filePath):
    with open(filePath) as file:
        return file.read()


# TODO: what is this function doing : its updating the actual django project file
# def writeToFile(filePath,content,fileName):

#     dest = filePath

#     if fileName not in filePath:
#         dest = f"{filePath}/{fileName}"

#     if os.path.exists(dest):  

#         data = getOldFile(dest)

#         if "urls.py" == fileName:
#             file_content = merge_urls(data.split("\n"),content.split("\n"))

#         else:
#             # TODO : handle conflicts here
#             write_data = f"{content}\n\n{data}" # node seperate with two \n e get Y

#             code = []
#             imports = []
#             file_content = ""
#             chunks = PythonBlockParser().parse_code(write_data)
            
#             for chunk in chunks:
#                 if chunk.startswith("import ") or chunk.startswith("from "):
#                     # individualImports = getIndividualImports(chunk)
#                     imports.append(chunk)
#                 else:
#                     code.append(chunk.strip())

#             if imports:  # Step 3: Write new content
#                 imports = removeDuplicates(imports)
#                 imports = "\n".join(imports)
#                 file_content += f"{imports} \n\n\n"

#             code = removeDuplicates(code)
#             code = "\n\n".join(code)

#             file_content += code  # Append old content to new content

#         with open(dest,"w") as file:
#             file.write(file_content)

#     else:
#         with open(dest,"w") as file:
#             file.write(content)

def getFileImportsAndCode(chunks):
    imports = []
    code = []
    
    for chunk in chunks:
        if chunk.startswith("import ") or chunk.startswith("from "):
            # individualImports = getIndividualImports(chunk)
            imports.append(chunk)
        else:
            code.append(chunk.strip())

    return [imports,code]

def writeToFile(filePath,content,fileName,conflicts=[]):

    dest = filePath

    if fileName not in filePath:
        dest = f"{filePath}/{fileName}"

    if os.path.exists(dest):  

        currentFileContent = getOldFile(dest)

        if "urls.py" == fileName:
            file_content = merge_urls(currentFileContent.split("\n"),content.split("\n"))

        else:
            # TODO : handle conflicts here
            file_content = ""

            currentFileChunks = parser.parse_code(currentFileContent)
            codeUpdateChunk = parser.parse_code(content) #new update from sb deploy
            
            imports, currentFileCode = getFileImportsAndCode(currentFileChunks)
            newImports, newCode = getFileImportsAndCode(codeUpdateChunk)
            
            # get chunks name from currentFileCode
            currentFileChunksNames = []
            for chunk in currentFileCode:
                name = get_assigned_variables(chunk,True)
                if isinstance(name,str):
                    currentFileChunksNames.append(name)
                else:
                    # add a default value just to retain chunk order
                    currentFileChunksNames.append(0)

            # process new code and decide on insert position
            # default insert position is 0
            for chunk in newCode:
                name = get_assigned_variables(chunk,True)
                if isinstance(name,str):
                    if name in currentFileChunksNames:
                        """ Conflict Identified """
                        conflictChunkPosition = currentFileChunksNames.index(name) #assuming name appears only once
                        oldCode = currentFileCode[conflictChunkPosition]

                        if oldCode != chunk:
                            # pop code
                            currentFileCode.pop(conflictChunkPosition)

                            # add conflict markers
                            conflictCode = f"<<<<<<< SpeedBuild update \n{oldCode}\n=======\n{chunk}\n>>>>>>>"
                            currentFileCode.insert(conflictChunkPosition, conflictCode)

                            conflicts.append(f"Merge conflict in {dest} : Failed to merge {name}")

                        continue

                currentFileCode.insert(0,chunk) # fresh non merge conflict code

            imports.extend(newImports) # merge current and new imports

            if imports:  # Step 3: Write new content
                imports = removeDuplicates(imports)
                imports = "\n".join(imports)
                file_content += f"{imports} \n\n\n"

            code = removeDuplicates(currentFileCode)
            code = "\n\n".join(code)

            file_content += code  # Append old content to new content

        with open(dest,"w") as file:
            file.write(file_content)

    else:
        with open(dest,"w") as file:
            file.write(content)

    return conflicts


def sortFile(file_name):
    with open(file_name,"r") as file:
        data = file.read()
        codeChunks = []
        imports = []

        chunks = PythonBlockParser().parse_code(data)

        for chunk in chunks:
            if chunk.startswith("import ") or chunk.startswith("from "):
                imports.append(chunk)
            else:
                codeChunks.append(chunk)

        arranged_chunks = []
        processed = []
    
    file_imports = "\n".join(imports)
    processedChunks = arrangeChunks(codeChunks,arranged_chunks,processed)
    file_code = "\n\n".join(processedChunks)

    with open(file_name,"w") as sortedFile:
        newData = f"{file_imports}\n\n{file_code}"
        sortedFile.write(newData)