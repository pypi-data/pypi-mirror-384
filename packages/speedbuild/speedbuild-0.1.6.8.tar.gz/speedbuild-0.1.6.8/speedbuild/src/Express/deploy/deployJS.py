"""
Deploy, Test and Customize Express SpeedBuild Features
"""
import os
import time
from pathlib import Path
from rich.prompt import Prompt

from ....break_prompt import splitPrompt
from ....cli_output.output import StatusManager
from .moveToTarget import moveTemplateFilesToTargetProject
from .debug import debug_and_customize_template_code,debugTemplate,test_environment_path

home = str(Path.home())
async def deployExpressFeature(template_name,deploy_project_root,customize_prompt=False):
    """
    Deploys an Express.js feature template to a specified project root directory.
    This function handles the deployment process of Express.js feature templates, including
    testing, and optional customization of the template code.

    Args:
        template_name (str): Name of the Express.js template to deploy
        deploy_project_root (str): Root directory path where the template will be deployed
        customize (bool, optional): Flag to enable template customization. Defaults to False

    Raises:
        ValueError: If the specified template does not exist in the templates directory

    Example:
        deployExpressFeature("auth-template", "/path/to/project", customize=True)

    Note:
        - The function creates a test environment if it doesn't exist
        - Templates are tested before deployment using 'npm run dev'
        - If customization is enabled, user will be prompted for customization details
    """

    logger = StatusManager()

    logger.print_message("Starting Feature deployment")

    templates_path = os.path.join(home,".sb_zip")

    # create test environment if it does not already exist.
    if not os.path.exists(test_environment_path):
        os.makedirs(test_environment_path, exist_ok=True)

    # get template
    # done : remember to update this when u've implemented template versioning for express
    template_version = "lts"
    if ":" in template_name:
        template_name, template_version = template_name.split(":")

    path_to_template = os.path.join(templates_path,template_name,template_version,".zip")

    # check if template exists
    if not os.path.exists(path_to_template):
        raise ValueError(f"Template with the name {template_name} and version {template_version} does not exist")
    
    debugTemplate(path_to_template)

    # check for and perform customization
    if customize_prompt:
        prompt = Prompt.ask("[cyan]How do you want to customize feature code (be as detailed as possible)[/cyan]")
        logger.print_message("Customizing code, please wait")

        # done : break customization prompt into sub prompts
        customize_prompts = splitPrompt(prompt)
        for prompt in customize_prompts:
            debug_and_customize_template_code(None,prompt)
            time.sleep(0.5)

        logger.print_message("Checking for errors")
        # debug customization logic
        debug_and_customize_template_code("npm run dev")

    logger.stop_status()
    # done : transplant template code into target environment
    await moveTemplateFilesToTargetProject(deploy_project_root)
    logger.print_message("Feature deployment complete")
