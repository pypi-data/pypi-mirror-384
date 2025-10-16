import json
import time
import random
import string
import websockets
import webbrowser

from .cli_utils import updateAuthToken
from ..utils.server_address import ws_address, app_address

def caculateTimeDifference(past_time):
    current_time = time.time()
    diff_in_seconds = current_time - past_time
    diff_in_minutes = diff_in_seconds // 60

    return diff_in_minutes

def getLocalUserData():
    try:
        with open(".probe/userData.json","r") as userDataFile:
            data = json.loads(userDataFile.read())
            return data
    except FileNotFoundError:
        raise UserWarning("You need to login to proceed\nrun 'probe login'")

def saveUserDataToLocalStorage(data):
    with open(".probe/userData.json","w") as userDataFile:
        json.dump(data, userDataFile, indent=4)

def generate_ws_token(length=6):
    # Define the possible characters (letters and digits)
    characters = string.ascii_letters + string.digits
    # Randomly choose `length` characters from the set
    random_string = ''.join(random.choice(characters) for _ in range(length))
    # Add current timestamp (in seconds) to make it more unique
    timestamp = str(int(time.time()))
    return f"{random_string}_{timestamp}"

async def openAuthPage(code,page="login"):
    if page == "login":
        address = f"{app_address}login?token={code}"
    else:
        address = f"{app_address}register?token={code}"

    webbrowser.open(address)
    response = await connect_to_websocket(f"{ws_address}chat/{code}/")
    # print(response)
    userData = {
        "access_token":response['message']['access'],
        "refresh_token":response['message']['refresh'],
        "time_created":time.time()
    }

    updateAuthToken(userData)

    # saveUserDataToLocalStorage(userData)
    print("Login Successful")


async def connect_to_websocket(WEBSOCKET_URI,data=None):
    headers = {
       "Origin": "https://backend.speedbuild.dev",  # Same origin as the server
    }

    async with websockets.connect(WEBSOCKET_URI,additional_headers=headers) as websocket:
        # print("Connected to WebSocket server")

        # data = {"message":"Hello, WebSocket!"}

        if data != None:
            # Send a message
            await websocket.send(json.dumps(data))
            print(f"Message sent: {data}, WebSocket!")

        # Keep listening for messages until "terminate" is received
        while True:
            response = await websocket.recv()
            print(f"Message received: {response}")
            data = json.loads(response)
            
            # Check if the received message contains the termination command
            if data['message']['status'].lower() == "terminate":
                # print("Termination message received. Closing connection.")
                return data
            
            # elif data['message'].lower() == "notify":
            #     print("notifying")