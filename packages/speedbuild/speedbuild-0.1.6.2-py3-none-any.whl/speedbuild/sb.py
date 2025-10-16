import os
import sys
import asyncio
from pathlib import Path

from .auth.cli_utils import get_config

from .cli_output.output import StatusManager

from .auth.sb_user import sbAuth
from .auth.auth import manageAuth
from .auth.serverCall import pingServer

from .utils.utils import pullPythonPackageJSON
from .utils.pull_template import pullInitialTemplates
from .utils.package_utils import getPackageNameMapping

from .old_sb import createTemplate, implementFeature

from .src.undo import undoSBDeploy
from .src.Express.deploy.deployJS import deployExpressFeature
from .src.Express.extract.jsPath import startExpressExtraction

from rich.prompt import Prompt

def extractFeature(home_path,project_root,args):
    try:
        target = args[2]
        extract_from = args[3]
        framework = args[4]

        framework = framework.replace("--","").lower()

        # logger = StatusManager()

        if framework == "django":
            # Extract django feature
            # logger.start_status("Extracting django feature")
            project_name = os.path.basename(project_root)
            packageToNameMapping = getPackageNameMapping(project_root)
            createTemplate(extract_from, target,project_name,packageToNameMapping,project_root)
            
        elif framework == "express":
            #Extract Express feature
            asyncio.run(startExpressExtraction(target,extract_from,project_root))

    except IndexError:
        print("Usage : python final.py <what_to_extract> <extraction_entry_point> --framework")


def deployFeature(home_path,project_root,args):
    try:
        template = args[2]
        framework = args[3]
        framework = framework.replace("--","").lower()
        print(f"Deploying {template}")
        
        customization_request = Prompt.ask("[cyan bold] Will you like to customize this feature (yes/no) [/cyan bold]")
        while customization_request.lower().strip() not in ['yes','no']:
            customization_request = Prompt.ask("[cyan] Please enter a valid response (yes/no)[/cyan]")

        customization_request = customization_request.strip() == "yes"

        if framework == "django":
            implementFeature(template)
        elif framework == "express":
            asyncio.run(deployExpressFeature(template,project_root,customization_request)) #true is so we customize otherwise use false

    except IndexError:
        print("Usage : python final.py deploy <template_name>")

def listExtractedFeature(args):
    print("Listing All Extracted Templates")
    user_home = str(Path.home())
    templates_dir = f"{user_home}/.sb_zip"

    if not os.path.exists(templates_dir):
        os.makedirs(templates_dir)

    count = 1
    templates = os.listdir(templates_dir)

    for template in templates:
        if template.startswith("speed_build"):
            print(f"    {count}) {template}")
            count += 1
    print("\n")

def start():
    args = sys.argv
    home = str(Path.home())
    current_path = os.path.abspath(".")


    try:
        # TODO : remove this
        api_key = os.environ.get("OPENAI_API_KEY",None)
        if api_key == None:
            config = get_config()
            if "openai" in config['llm_keys'].keys():
                os.environ["OPENAI_API_KEY"] = config["llm_keys"]['openai']
    except:
        pass

    try:
        command = args[1]

        if command == "extract":
            # sb.py extract / views.py --express
            extractFeature(home,current_path,args)

        elif command == "deploy":
            # sb.py deploy template_name
            deployFeature(home,current_path,args)

        elif command == "list":
            listExtractedFeature(args)

        elif command == "undo":
            print("performing undo")
            undoSBDeploy()

        elif command == "auth":
            asyncio.run(sbAuth())

        elif command == "ping":
            pingServer()
            
        elif command == "setup":
            print("Seting up speedbuild")
            pullInitialTemplates()
            pullPythonPackageJSON()
            asyncio.run(manageAuth("register"))

    except IndexError as e:
        print("Available commands :\n- extract\n- deploy\n- list\n- undo\n- auth\n- ping\n- setup")