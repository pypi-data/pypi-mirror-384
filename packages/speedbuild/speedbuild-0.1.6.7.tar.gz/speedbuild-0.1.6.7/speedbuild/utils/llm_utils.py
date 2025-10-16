from ..auth.cli_utils import get_sb_config


openai = ["gpt-4o-2024-08-06"]
# anthropic = []

def getLLMConnectInfo():
    config = get_sb_config()
    if "default_model" not in config.keys() and "llm_keys" not in config.keys:
        return None
    
    model = config['default_model']
    llm_keys = config['llm_keys']

    if model in openai:
        if "openai" in llm_keys.keys():
            return ["openai",llm_keys['openai'],model]
        
        print("Sent OpenAI API key to proceed")
        
    else:
        return 0