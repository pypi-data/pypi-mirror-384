import os
import ast

from .src.Django.utils.manage_url import merge_urls
from .parsers.python.parser import PythonBlockParser
from .src.Django.utils.django_utils import django_defaults
from .src.Django.utils.var_utils import get_assigned_variables

parser = PythonBlockParser()

def getProjectFiles(path):
    file_paths = []
    for root, _, files in os.walk(path):
        if "node_modules" in root or "__pycache__" in root or "migrations" in root:
            continue
        for file in files:
            # Get the absolute path by joining root and file
            absolute_path = os.path.join(root, file)
            file_name = absolute_path.replace(path,"").lstrip("/")
            if file_name not in ["__init__.py","apps.py"]:
                file_paths.append(file_name)
    return file_paths

def getImportsFromChunks(chunks):
    imports = []
    code = []

    for chunk in chunks:
        if chunk.startswith("import ") or chunk.startswith("from "):
            imports.append(chunk)
        else:
            code.append(chunk)

    return [imports,code]


def getFileData(file_path,context=None):

    if not os.path.exists(file_path):
        return [[],[],{}]
    
    with open(file_path,"r") as file:
        data = file.read()
        if context is not None:
            # get source project context
            source_project_name,source_app_name,project_name,app_name = getProjectContext(context)

            # match and replace
            data = data.replace(source_project_name,project_name).replace(source_app_name,app_name)

        chunks = parser.parse_code(data)

        imports, chunks = getImportsFromChunks(chunks)
        var_mappings = {}

        for chunk in chunks:
            var_name = get_assigned_variables(chunk,True)
            if isinstance(var_name,str):
                var_mappings[var_name] = chunk

        return imports,chunks,var_mappings
    

def getProjectContext(context):
    return [
        context['source_project_name'],
        context['source_app_name'],
        context['project_name'],
        context['app_name']
    ]


def mergeFile(source,target_file,project_context):
    source_import,source_code,_ = getFileData(source,project_context)
    target_file_imports,target_file_code,target_file_var_mapping = getFileData(target_file)

    # merge imports
    for statement in source_import:
        if statement not in target_file_imports:
            target_file_imports.append(statement)

    # merge code
    for chunk in source_code:
        if chunk not in target_file_code:
            chunk_name = get_assigned_variables(chunk,True)

            if isinstance(chunk_name,str) and chunk_name in target_file_var_mapping.keys():
                target_file_chunk_with_chunk_name = target_file_var_mapping[chunk_name]

                if target_file_chunk_with_chunk_name != chunk:
                    target_file_chunk_pos = target_file_code.index(target_file_chunk_with_chunk_name)

                    conflictCode = f"<<<<<<< SpeedBuild update \n{target_file_chunk_with_chunk_name}\n=======\n{chunk}\n>>>>>>>"
                    target_file_code[target_file_chunk_pos] = conflictCode
            elif chunk not in target_file_code: 
                target_file_code.append(chunk)
    
    code = ""
    if len(target_file_imports) > 0:
        code = "\n".join(target_file_imports) + "\n\n"

    code += "\n\n".join(target_file_code)

    # write to file
    output_dir = os.path.dirname(target_file)
    if not os.path.exists(output_dir):
        print("making ", output_dir)
        os.makedirs(output_dir)

    with open(target_file,"w") as file:
        file.write(code)

def handleUrlFileMerge(source_url,target_url, project_context):

    # get source project context
    source_project_name,source_app_name,project_name,app_name = getProjectContext(project_context)

    with open(source_url,"r") as file:
        source_url_data = file.read()
        # replace project and app name in source url
        source_url_data = source_url_data.replace(source_project_name,project_name).replace(source_app_name,app_name).split("\n")

    if os.path.exists(target_url):
        with open(target_url,"r") as file:
            target_url_data = file.read().split("\n")

        code = merge_urls(source_url_data,target_url_data)
        # print(code)
    else:
        print("no url file")
        code = source_url_data
    
    with open(target_url,"w") as file:
        file.write(code)

def getProjectApps(apps):
    cleaned = []
    for app in apps:
        if not app.startswith("django.") and app != "speedbuild_app":
            cleaned.append(app)
    return cleaned

def mergeMiddleware(middleware, target_middleware):
    for i in range(len(middleware)):
        item = middleware[i]
        if item not in target_middleware:
            if i == 0:
                target_middleware.insert(0, item)
            elif i == len(middleware) - 1:
                target_middleware.append(item)
            else:
                added = False
                # Try to insert after the closest previous middleware already in target_middleware
                for x in reversed(middleware[:i]):
                    if x in target_middleware:
                        pos = target_middleware.index(x)
                        target_middleware.insert(pos + 1, item)
                        added = True
                        break
                if not added:
                    target_middleware.append(item)
    return target_middleware

def handleDjangoSettingsFile(settings_path,target_settings_file,project_context):

    # imports installed_apps, middleware configurations
    imports, _, code_var_mappings = getFileData(settings_path,project_context)
    target_imports, target_chunks, target_code_var_mappings = getFileData(target_settings_file)

    MIDDLEWARE = ast.literal_eval(code_var_mappings["MIDDLEWARE"].split("=", 1)[1].strip())
    INSTALLED_APPS = getProjectApps(ast.literal_eval(code_var_mappings["INSTALLED_APPS"].split("=", 1)[1].strip()))

    target_MIDDLEWARE = ast.literal_eval(target_code_var_mappings["MIDDLEWARE"].split("=", 1)[1].strip())
    target_INSTALLED_APPS = ast.literal_eval(target_code_var_mappings["INSTALLED_APPS"].split("=", 1)[1].strip())

    # TODO : add project app if its not already in installed apps
    installed_app_pos = target_chunks.index(target_code_var_mappings["INSTALLED_APPS"])
    middleware_pos = target_chunks.index(target_code_var_mappings["MIDDLEWARE"])

    for app in INSTALLED_APPS:
        if app not in target_INSTALLED_APPS:
            target_INSTALLED_APPS.append(app)

    MIDDLEWARE_merged = mergeMiddleware(MIDDLEWARE,target_MIDDLEWARE)

    target_INSTALLED_APPS = ",\n\t".join([f'"{app}"' for app in target_INSTALLED_APPS]) #match and replace
    MIDDLEWARE_merged = ",\n\t".join([f'"{middleware}"' for middleware in MIDDLEWARE_merged]) #match and replace

    target_chunks[installed_app_pos] = f"INSTALLED_APPS = [\n\t{target_INSTALLED_APPS}\n]"
    target_chunks[middleware_pos] = f"MIDDLEWARE = [\n\t{MIDDLEWARE_merged}\n]"

    for statement in imports: #match and replace
        if statement not in target_imports:
            target_imports.append(statement)

    for i in code_var_mappings.keys(): #match and replace
        if i not in django_defaults:
            chunk = code_var_mappings[i]
            if i in target_code_var_mappings.keys() and chunk != target_code_var_mappings[i]:
                index = target_chunks.index(target_code_var_mappings[i])
                conflictCode = f"<<<<<<< SpeedBuild update \n{target_code_var_mappings[i]}\n=======\n{chunk}\n>>>>>>>"
                target_chunks[index] = conflictCode
            else:
                target_chunks.append(chunk)

    merged_code = ""
    if len(target_imports) > 0:
        merged_code = "\n".join(target_imports) + "\n\n"

    merged_code += "\n\n".join(target_chunks)

    with open(target_settings_file,"w") as file:
        file.write(merged_code)

def moveFolderFiles(source_path,target_root,project_context):
    app_files = getProjectFiles(source_path)

    for file in app_files:
        if file == "urls.py":
            handleUrlFileMerge(f"{source_path}/urls.py",f"{target_root}/urls.py",project_context)
        elif file == "settings.py":
            handleDjangoSettingsFile(f"{source_path}/settings.py",f"{target_root}/settings.py",project_context)
        else:
            mergeFile(f"{source_path}/{file}",f"{target_root}/{file}",project_context)

def moveFilesToTargetProject(source_path,target_root,project_name,app_name):
    test_environment_app_name = "speedbuild_app"
    test_environment_project_name = "speedbuild_project"

    project_context = {
        "source_project_name":test_environment_project_name,
        "source_app_name":test_environment_app_name,
        "project_name":project_name,
        "app_name":app_name
    }

    # move app files
    moveFolderFiles(f"{source_path}/{test_environment_app_name}",f"{target_root}/{app_name}",project_context)

    # move project files
    moveFolderFiles(f"{source_path}/{test_environment_project_name}",f"{target_root}/{project_name}",project_context)

# moveFilesToTargetProject(
#     "/home/attah/.sb/environment/django/speedbuild_project",
#     "/home/attah/Documents/speedbuild/test_environment/mybookshop",
#     "mybookshop", #make this dynamic; find the folder with the settings.py file
#     "shop"
# )