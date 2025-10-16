import os
from pathlib import Path

from .src.Django.deploy_features import convertFromTemplateToFeature
from .utils.utils import getAbsolutePath
# import sys
# import asyncio
# from pathlib import Path

# from .src.Django.deploy_features import convertFromTemplateToFeature
from .src.Django.extract_features import create_temp_from_feature

# from .auth.auth import manageAuth
# from .utils.pull_template import pullInitialTemplates

# from .auth.sb_user import sbAuth
# from .src.undo import undoSBDeploy
# from .auth.serverCall import pingServer
# from .utils.package_utils import getPackageNameMapping
# from .utils.utils import extract_views_from_urls, findFilePath, getAbsolutePath, pullPythonPackageJSON

# def createTemplate(file_path, feature,project_name,packageToNameMapping,project_root):

#     if file_path.endswith("/"):
#         file_path = file_path[:len(file_path)-1]

#     file_path = file_path.replace(project_root,"")

#     print("\n##### Extracting Feature : ",feature," #####")

#     if not os.path.exists(file_path):
#         print("invalid feature")
#         return

#     create_temp_from_feature(
#         project_root,
#         project_name,
#         feature,
#         file_path,
#         packageToNameMapping
#     )

# def implementFeature(template_path,project_path=None,appName=None,prompt=None, addToInstalledApps=None,venv=None):
#     project_root = getAbsolutePath(".")

#     if project_path:
#         project_root = project_path

#     if ":" in template_path:
#         # User specified feature version
#         template_path_words = template_path.split(":")

#         if len(template_path_words) == 2:
#             template_name,version = template_path_words
#             template_path = f"{template_name}/{version}.zip"
#         else:
#            print("invalid template version")
#            return 
#     else:
#         # version was not specified, default to lts
#         template_name = template_path
#         template_path += "/lts.zip"

#     home = str(Path.home())
#     template_path = f"{home}/.sb_zip/{template_path}"

#     print("finished processing ",template_path, " template name is ", template_name)

#     if not os.path.exists(template_path):
#         print("invalid template")
#         return
    
#     # template_path = getAbsolutePath(args.template_path)
#     # template_name = template_path.split("/")[-1].replace(".zip","").strip()
#     # just commented tihs out; Investigate this
#     # extract_path = f"{home}/.sb/sb_extracted/{template_name}"
    
#     print("deploying feature")
#     convertFromTemplateToFeature(project_root,template_path,template_name,appName,prompt,addToInstalledApps,venv)

# def list_features():
#     user_home = str(Path.home())
#     templates_dir = f"{user_home}/.sb_zip"
#     if not os.path.exists(templates_dir):
#         os.makedirs(templates_dir)
#     templates = os.listdir(templates_dir)
#     count = 1
#     print("## ALL EXTRACTED FEATURES ##\n")
#     for template in templates:
#         if template.startswith("speed_build"):
#             print(f"    {count}) {template}")
#             count += 1
#     print("\n")


# def handleExtract(subfolder=None,feature=None,project_path=""):
#     project_root = project_path
#     # get project name from root project path
#     project_name = [i.strip() for i in project_path.split("/") if len(i.strip()) > 0][-1]

#     if subfolder:
#         project_path += subfolder

#     if not project_path.endswith("/"):
#         project_path += "/"

#     if feature is not None:
#         # print("here with",feature)
#         if project_path.endswith("/"):
#             project_path = project_path[:len(project_path)-1]

#         # get package to name mapping
#         packageToNameMapping = getPackageNameMapping(project_root)
#         print("\n#####  Extracting ",feature, "from ",project_path,"  #####\n")
#         createTemplate(project_path, feature,project_name,packageToNameMapping,project_root)
#         return
    
#     elif subfolder and feature == None:
#         if project_path.endswith("/"):
#             project_path = project_path[:len(project_path)-1]

#         if project_path.endswith(".py"):
#             paths = project_path.split("/")
#             paths.pop()
#             project_path = "/".join(paths)

#         if not project_path.endswith("/"): 
#             project_path += "/"

#         # print(project_path, " new edited path")

#     urls_path = findFilePath(project_path,"urls.py")


#     packageToNameMapping = getPackageNameMapping(project_root)
#     # print(packageToNameMapping, " for app")

#     for filePath in urls_path:
#         print(f"\n{"#"*15} {filePath} {"#"*15}\n")
#         abs_path = project_path + filePath
#         views = extract_views_from_urls(abs_path)

#         dir_name = filePath.split("/")[0]

#         print("directory name is ",dir_name)
#         # return

#         for view in views:
#             view = view.split(".")

#             print("view list is ",view)

#             if len(dir_name) == 0:
#                 dir_name = "."

#             file_name = view[1]
#             feature_name = view[2]

#             # TODO Fix : we are assuming urls path are like :
#             # path("home",views.home,name="home")
#             # we are assuming the user is import views like 
#             # from . import views

#             # if feature_name.endswith("/"):
#             #     feature_name = feature_name[:len(feature_name)-1]

#             # print("feature is ", feature_name)
#             print("here we are")
#             print(f"folder : {dir_name} file : {file_name}.py feature is {feature_name} ",project_path)
#             createTemplate(project_path+f"{dir_name}/views.py", feature_name,project_name,packageToNameMapping,project_root)


# def main(action,secPath,feature,project_path):
#     if action == "list":
#         list_features()
    
#     elif action == "extract":
#         handleExtract(secPath,feature,project_path)
    
#     elif action == "deploy":
#         if secPath is not None:
#             # print("deploying ", secPath)
#             implementFeature(secPath)
#         else:
#             print("Specify a template to deploy\n")
#             print("  You can see all extracted templates by running")
#             print("  sb.py list ")
    # elif action == "undo":
    #     print("performing undo")
    #     undoSBDeploy()
    # elif action == "auth":
    #     asyncio.run(sbAuth())
    # elif action == "ping":
    #     pingServer()
    # elif action == "setup":
    #     print("Seting up speedbuild")
    #     pullInitialTemplates()
    #     pullPythonPackageJSON()
    #     asyncio.run(manageAuth("register"))
#     else:
#         print("Please Enter a valid action")
#         print("  - speedbuild setup   :\tInitial Setup")
#         print("  - speedbuild extract :\tto extract templates")
#         print("  - speedbuild list    :\tto see extracted templates")
#         print("  - speedbuild deploy  :\tto deploy template to a different project")
#         print("  - speedbuild auth    :\tto manage authentication and LLM configuration")


# def start():
#     project_path = getAbsolutePath(".")
#     if not project_path.endswith("/"):
#         project_path += "/"

#     args = sys.argv[1:] + [None] * 3  # Pad with None for missing values
#     action, secondaryPath, feature = args[:3]

#     main(action, secondaryPath, feature, project_path)

# if __name__ == "__main__":
#     start()
    
def createTemplate(file_path, feature,project_name,packageToNameMapping,project_root):

    if file_path.endswith("/"):
        file_path = file_path[:len(file_path)-1]

    file_path = file_path.replace(project_root,"")

    print("\n##### Extracting Feature : ",feature," #####")

    if not os.path.exists(file_path):
        print("invalid feature")
        return

    create_temp_from_feature(
        project_root,
        project_name,
        feature,
        file_path,
        packageToNameMapping
    )


def implementFeature(template_path,project_path=None,appName=None,prompt=None, addToInstalledApps=None,venv=None):
    project_root = getAbsolutePath(".")

    if project_path:
        project_root = project_path

    if ":" in template_path:
        # User specified feature version
        template_path_words = template_path.split(":")

        if len(template_path_words) == 2:
            template_name,version = template_path_words
            template_path = f"{template_name}/{version}.zip"
        else:
           print("invalid template version")
           return 
    else:
        # version was not specified, default to lts
        template_name = template_path
        template_path += "/lts.zip"

    home = str(Path.home())
    template_path = f"{home}/.sb_zip/{template_path}"

    print("finished processing ",template_path, " template name is ", template_name)

    if not os.path.exists(template_path):
        print("invalid template")
        return
    
    # template_path = getAbsolutePath(args.template_path)
    # template_name = template_path.split("/")[-1].replace(".zip","").strip()
    # just commented tihs out; Investigate this
    # extract_path = f"{home}/.sb/sb_extracted/{template_name}"
    
    print("deploying feature")
    convertFromTemplateToFeature(project_root,template_path,template_name,appName,addToInstalledApps,venv)