import json
import sys

from .auth import manageAuth
from .cli_utils import setAPIKey,updateDefaultLLMModel,get_config

supported_models = ["gpt-4o-2024-08-06","sonnet-3.7"]
supported_providers = ["openai","anthropic","google"]

async def sbAuth():
    # remove auth keyword
    sys.argv.pop(1)
    command = None

    try:
        command = sys.argv[1]
        if command == "llm" and len(sys.argv) > 2:
            subcommand = sys.argv[2]
            
            if subcommand == "provider":
                if len(sys.argv) == 5:
                    provider = sys.argv[3].lower()
                    api_key = sys.argv[4]

                    if provider in supported_providers:
                        print("setting provider for provider ",provider," with api key ",api_key)
                        setAPIKey(provider,api_key)
                    else:
                        print("Please choose form our LLM supported providers ",supported_providers)
                else:
                    print("speedbuild llm provider <provider_name> <provider_api_key>")

            elif subcommand == "model":
                if len(sys.argv) == 4:
                    model = sys.argv[3].lower()
                    if model in supported_models:
                        print("setting default model to ", model)
                        updateDefaultLLMModel(model)
                    else:
                        print("choose from our supported models : ",supported_models)
                else:
                    print("speedbuild llm <model_name>")


        elif command == "config":
            get_config()

        elif command == "login":
            print("logining in user")
            await manageAuth()
        elif command == "register":
            await manageAuth("register")
        else:
            raise IndexError
        
    except IndexError:
        if command is not None and command == "llm":
            print("Please Enter a valid action for llm")
            print("  - speedbuild auth llm model        :\tManage LLM model")
            print("  - speedbuild auth llm provider     :\tManage LLM Provider Access")
        else:
            print("Please Enter a valid action for auth")
            print("  - speedbuild auth config      :\tSee SpeedBuild Config and API Keys")
            print("  - speedbuild auth login       :\tAuthenticate with server")
            print("  - speedbuild auth register    :\tCreate new SpeedBuild account")
            print("  - speedbuild auth llm         :\tManage LLM Configurations")