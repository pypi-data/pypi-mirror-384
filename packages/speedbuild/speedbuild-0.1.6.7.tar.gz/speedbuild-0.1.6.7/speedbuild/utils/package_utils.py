import json
import importlib
import os

from .utils import findFilePath
from ..src.Django.utils.venv_utils import get_activated_venv
from ..src.Django.utils.django_app_dependencies import getDjangoAppsPackage

def is_standard_library(module_name):
    return importlib.util.find_spec(module_name) is not None

def get_package_name(import_name,data):

    import_name = import_name.split(" ")[0]

    if import_name in  data.keys():
        return[import_name,"str"]
        
    for key in data:
        if import_name in data[key]:
            return [key,"str"]
    
    # could not find package
    return [import_name,"None"]
        
    # exclude_path = ['pip','dateutil', '__pycache__']

    # with open("sb_app_mapping_cache.json","r") as cacheFile:
    #     data = json.loads(cacheFile.read())
    #     import_name = import_name.split(" ")[0]

    #     if import_name in  data.keys():
    #         return[import_name,"str"]
            
    #     for key in data:
    #         if import_name in data[key]:
    #             return [key,"str"]
        
    #     # could not find package
    #     return [import_name,"None"]
    
def getPackageNameMapping(project_path):

    venv = get_activated_venv()
    findFilePath(project_path, "urls.py")

    # use conditional statement to check if file is found
    project_name = findFilePath(project_path, "asgi.py")

    if len(project_name) == 0:
        raise(ValueError("Cannot find django project settings file"))
    
  
    project_name = project_name[0].split("/")[0]
    settings_path = f"{project_name}/settings.py"
    settings_path = os.path.join(project_path, settings_path)

    template_django_apps = getDjangoAppsPackage(settings_path,venv)
    return template_django_apps