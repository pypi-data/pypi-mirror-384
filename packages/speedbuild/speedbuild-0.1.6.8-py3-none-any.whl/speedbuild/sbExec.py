import os
import sys
import venv
import shutil
from pathlib import Path

from .break_prompt import splitPrompt
from .src.Django.utils.deploy import read_yaml
from .src.Django.utils.venv_utils import get_activated_venv
from .utils.installDependencies import install_dependencies

from .move_django_to_target import moveFilesToTargetProject

from .langgraph_agent.agents.workflow.tools import updateFile

from .langgraph_agent.agents.workflow.claude_workflow import SpeedBuildWorkflow

from .exec.runCommand import PythonExecutor
from .exec.sb_exec_utils import create_virtual_environment,install_packages_in_venv
from .old_sb import implementFeature

def clear_folder(folder_path):
    for file_name in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file_name)
        if os.path.isfile(file_path) or os.path.islink(file_path):  
            os.remove(file_path)  # Delete files & symlinks
        elif os.path.isdir(file_path):  
            shutil.rmtree(file_path)  # Delete directories


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

def getProjectFiles(path):
    file_paths = []
    for root, _, files in os.walk(path):
        if "node_modules" in root or "__pycache__" in root or "migrations" in root:
            continue
        for file in files:
            # Get the absolute path by joining root and file
            absolute_path = os.path.join(root, file)
            file_name = absolute_path.replace(path,"").lstrip("/")
            if os.path.basename(file_name) not in ["__init__.py","apps.py",".speedbuild","manage.py"] and file_name.endswith("sqlite3")==False:
                file_paths.append(file_name)
    return file_paths


class SpeedBuildTestAgent():
    def __init__(self):
        self.home = str(Path.home())
        self.environment_sb_path = f"{self.home}/.sb/environment/"
        self.executor = PythonExecutor()
        venv_path = f"{self.home}/.sb/environment/django/venv"

        if sys.platform == "win32":
            python_path =  os.path.join(venv_path, "Scripts", "python.exe")
        else:
            python_path = os.path.join(venv_path, "bin", "python")

        # Modify environment to use the venv
        self.env = os.environ.copy()
        self.env['VIRTUAL_ENV'] = venv_path
        
        if sys.platform == "win32":
            self.env['PATH'] = f"{os.path.join(venv_path, 'Scripts')};{self.env['PATH']}"
        else:
            self.env['PATH'] = f"{os.path.join(venv_path, 'bin')}:{self.env['PATH']}"


    def installAndCreateDjangoProject(self,venv):
        res = create_virtual_environment(venv)
        installation_successful = install_packages_in_venv(f"{venv}/venv",["django"])
        # print("## virtual environment is ",self.env)
        if installation_successful:

            self.venv_path = f"{venv}/venv"
            print("### here")
            # create django project
            res = self.executor.runCommand(
                ["django-admin","startproject","speedbuild_project"],
                True,
                env=self.env,
                cwd="/home/attah/.sb/environment/django"
            )

            print(res)

            # create django app
            res = self.executor.runCommand(
                ["python","manage.py","startapp","speedbuild_app"],
                True,
                env=self.env,
                cwd="/home/attah/.sb/environment/django/speedbuild_project"
            )

            print(res)

            # add urls.py file
            shutil.copy("/home/attah/Documents/sb_final/speedbuild/exec/app_urls.py", "/home/attah/.sb/environment/django/speedbuild_project/speedbuild_app/urls.py")

            # include new urls file in main urls file
            shutil.copy("/home/attah/Documents/sb_final/speedbuild/exec/main_urls.py", "/home/attah/.sb/environment/django/speedbuild_project/speedbuild_project/urls.py")

            # do customization / test customization

            # move code to main project


    def createTestEnvironment(self,framework):
        environment_path = f"{self.environment_sb_path}{framework}"

         # clear out existing project
        print(environment_path, "hert ")
        clear_folder(environment_path)

        if not os.path.exists(environment_path):
            os.makedirs(environment_path,exist_ok=True)

        action = self.installAndCreateDjangoProject(environment_path)

        return environment_path+"/speedbuild_project"


    def testAndFixErrors(self):
        # run server -- check for error / test feature, troubleshoot and fix issues
        pass


    def deployFeatureInTestEnvironment(self,template_path,project_path):
        """Call speedbuild function to deploy code in test environment and also add speedbuild_app to installed apps"""

        implementFeature(template_path,project_path,"speedbuild_app",None,True,self.venv_path)
        print("Feature Implemented")


    def migrateTestAndFixErrors(self,max_debugger_count=3):
        commands = [
            "python manage.py makemigrations",
            "python manage.py migrate",
            "python manage.py runserver"
        ]

        llm_agent = SpeedBuildWorkflow("gpt-4o","openai","django")

        # if prompt == None: # normal debugging
        
        # Create workflow for debugging a specific command
        llm_agent.create_debugger_workflow()
            
        # # Run the initial failing command to get the first error
        # llm_agent.run(context)

        for command in commands:
           # Get initial error and command output
            no_errors,stdout,stderr = llm_agent.run_shell_command(command)

            if no_errors == False:
                llm_agent.last_error = stderr 
                llm_agent.last_command_output = stdout
                llm_agent.original_command = command

                llm_agent.run()

    def TestFeature(self,framework,template_path):
        project_path = self.createTestEnvironment(framework)

        # deploy template [add speedbuild_app to INSTALLED_APPS settings file]
        self.deployFeatureInTestEnvironment(template_path,project_path)

        # fix error
        self.migrateTestAndFixErrors()


    def customize_feature_code(self,prompt,files,root_path):
        llm_agent = SpeedBuildWorkflow("gpt-4o","openai","django")
        # if prompt == None: # normal debugging
        
        # Create workflow for debugging a specific command
        llm_agent.create_debugger_workflow("customization")

        llm_agent.last_command_output = f"""
        customization prompt : **{prompt}**
        project root path : **{root_path}***
        project files : {files}
        """

        llm_agent.run()

        if llm_agent.success:
            print("Customization successful")
            return True
        else:
            print("workflow ended without resolution")
            return False


def testCustomizeAndDeployDjangoFeature(feature_template,target_destination,target_app_name,customize=False):
    files = getProjectFiles(target_destination)
    target_project_name = None

    for file in files:
        if os.path.basename(file) == "settings.py":
            target_project_name = os.path.dirname(file)
    
    if target_project_name == None:
        raise ValueError("Could not detect project name, could not locate the settings.py file")
    
    
    test_environment =  f"{str(Path.home())}/.sb/environment/django/speedbuild_project"
    djangoAgent = SpeedBuildTestAgent()

    djangoAgent.TestFeature("django",feature_template)

    # ask for customization prompt
    if customize:
        prompt = input("Enter customization prompt, be as detailed as possible : \n")

        # TODO : break prompt into simple steps
        customize_prompts = splitPrompt(prompt)

        for prompt in customize_prompts:
            print("Processing",prompt)
            files = getProjectFiles(test_environment) 
            status = djangoAgent.customize_feature_code(prompt,files,test_environment)

        # TODO : if could not customize break out 

    # move feature code to target destination
    moveFilesToTargetProject(
        test_environment,
        target_destination,
        target_project_name,
        target_app_name
    )

    # install packages in target destination
    print("Installing Feature dependencies")
    config_name = feature_template.replace("speed_build_","")
    template_root = f"{str(Path.home())}/.sb_zip"
    venv = get_activated_venv()
    if ":" in feature_template:
        template_name, version = feature_template.split(":")

        yaml_path = f"{template_root}/{template_name.strip()}/{version.strip()}/sb_{config_name}.yaml"
    else:
        version = "lts"
        yaml_path = f"{template_root}/{feature_template}/{version}/sb_{config_name}.yaml"
    
    if not os.path.exists(yaml_path):
        raise ValueError(f"Template {template_name} version {version} does not exist")
    
    template_yaml = read_yaml(yaml_path)

    install_dependencies(template_yaml['dependencies'],venv)

if __name__ == "__main__":
    testCustomizeAndDeployDjangoFeature("speed_build_RegisterWithOauth","/home/attah/Documents/speedbuild/test_environment/mybookshop","shop",True)