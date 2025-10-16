from .ws_utils import openAuthPage, generate_ws_token

async def manageAuth(page="login"):
    code = generate_ws_token()
    await openAuthPage(code,page)