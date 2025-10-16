import os
import sys
import json
from pathlib import Path

user_home = str(Path.home())
config_path = f"{user_home}/.sb/config.json"

def get_sb_config():
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        with open(config_path,"w") as file:
            file.write("{}")

        return {}

    with open(config_path,"r") as file:
        data = json.loads(file.read())
        return data

def save_config(config):
    if not os.path.exists(config_path):
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
    with open(config_path, "w") as file:
        json.dump(config, file, indent=4)

def get_config():
    config = get_sb_config()
    # print(json.dumps(config, indent=4))
    return config

def setAPIKey(key_type,api_key):
    config = get_sb_config()

    keys_dictionary = {}
    if "llm_keys" in config.keys():
        keys_dictionary = config['llm_keys']

    if len(api_key) == 0 and key_type in keys_dictionary.keys():
        del keys_dictionary[key_type]
    else:
        keys_dictionary[key_type] = api_key

    
    config['llm_keys'] = keys_dictionary

    save_config(config)

def updateDefaultLLMModel(model_name):
    config = get_sb_config()
    config['default_model'] = model_name
    save_config(config)

def updateAuthToken(token_value):
    config = get_sb_config()

    keys_dictionary = {}
    if "jwt_tokens" in config.keys():
        keys_dictionary = config['jwt_tokens']

    if len(token_value) == 0:
        del config['jwt_tokens']
    else:
        config['jwt_tokens'] = token_value

    save_config(config)