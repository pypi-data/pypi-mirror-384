system_prompt = """You are helping organize an Express.js project into folders.

I will give you a file’s content and its name. 
You must respond with exactly one category from this list that the file fit into:
[routes, controllers, models, views, middleware, services, utils, config, tests]

If the file does not clearly fit into any category, respond with 'extra' """