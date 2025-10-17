import os
import zipfile
from pathlib import Path

from ....cli_output.output import StatusManager
from ....langgraph_agent.agents.workflow.tools import executeCommand
from ....langgraph_agent.agents.workflow.claude_workflow import SpeedBuildWorkflow


home = str(Path.home())
test_environment_path = f"{home}/.sb/environment/express"

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


def debug_and_customize_template_code(command,prompt=None):

    """
    Debug and customize template code by analyzing command output and errors.
    This function creates a debugging workflow to analyze and fix issues with a given command.
    It uses the SpeedBuildWorkflow debugger to iteratively analyze errors and provide debugging steps.

    Args:
        command (str): The shell command to debug and customize
        prompt (str, optional): Additional prompt/context for code customization. Defaults to None.

    Returns:
        bool: True if debugging completed successfully, False if debugging ended without resolution

    Note:
        - Uses SpeedBuildWorkflow debugger with GPT-5 model
        - Captures command output and error messages
        - Creates debugging context with original command, output and errors
        - Runs an iterative debugging workflow until resolution or failure
    """

    llm_agent = SpeedBuildWorkflow("gpt-4o","openai","express")

    if prompt == None: # normal debugging
        # Get initial error and command output
        _,stdout,stderr = llm_agent.run_shell_command(command)

        if len(stderr.strip()) == 0:
            # return if there is no error to debug
            return
        
        llm_agent.last_error = stderr 
        llm_agent.last_command_output = stdout
        llm_agent.original_command = command

        # Create workflow for debugging a specific command
        llm_agent.create_debugger_workflow()

        llm_agent.run()

        if not llm_agent.success:
            print("workflow ended without resolution")
            return False
            
    else: # customization workflow here
        llm_agent.create_debugger_workflow("customization")

        print("processing prompt : ",prompt)
        project_files = getTemplateFileNames(test_environment_path)
        llm_agent.last_command_output = f"""
        customization prompt : **{prompt}**
        project files : {project_files}
        """

        llm_agent.run()

        if not llm_agent.success:
            print("workflow ended without resolution")
            return False
        
    print("completed successfully!")
    return True


def debugTemplate(path_to_template):
    logger = StatusManager()
    home = str(Path.home())

    test_environment_path = os.path.join(home,".sb","environment","express")

    if os.path.exists(test_environment_path):
        os.makedirs(test_environment_path,exist_ok=True)

    # extract and move template code into test environment
    logger.start_status("Unpacking template")
    with zipfile.ZipFile(path_to_template, 'r') as zip_ref:
        zip_ref.extractall(test_environment_path)
        logger.stop_status("Unpacking Completed")

    # # Install node dependencies
    logger.start_status("Installing package dependencies in test environment")
    _, error = executeCommand(command="npm install",framework="express")

    if len(error) > 0:
        error = "\n".join(error)
        logger.stop_status()
        raise ValueError(f"Could not Install node dependencies, command executed with error : {error}")
    
    logger.stop_status("Dependencies Installed")

    # TODO : check response to see if debug_and_customize_template_code was successful

    # Test template code
    logger.print_message("Checking and debugging template code for errors")
    debug_and_customize_template_code("npm run dev")