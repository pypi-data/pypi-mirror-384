import time
import requests

from .cli_utils import get_sb_config,updateAuthToken
from .ws_utils import caculateTimeDifference


max_access_lifespan = 5
base_url = "https://backend.speedbuild.dev/"


def askUserToLogin():
    print("Your session has expired\nYou need to login")


def getNewAccessToken(refreshToken):
    data = {"refresh":refreshToken}

    isValid, resData = manageServerCall('POST','api/token/refresh/',data)
    
    if isValid:
        return resData['access']
    
    # refesh token has expired
    # prompt the user to login
    return askUserToLogin()

def getRequestHeaders():
    user_data = get_sb_config()
    if "jwt_tokens" not in user_data:
        return None
    
    user_data = user_data['jwt_tokens']

    # check if user_data has access and refresh token
    if 'access_token' not in user_data.keys() or 'refresh_token' not in user_data.keys():
        return None
    
    diff = caculateTimeDifference(user_data['time_created'])
    
    if diff > max_access_lifespan:
        # access token has expired
        # request new access token with current refresh token
        refresh_token = user_data['refresh_token']
        access_token = getNewAccessToken(refresh_token)

        if access_token != None:
            # refresh and access token is valid
            # save new access token to json file
            # user_data['access_token'] = access_token
            # user_data["time_created"] = time.time()
            # saveUserDataToLocalStorage(user_data)
            updateAuthToken({
                "access_token" :access_token,
                "refresh_token":refresh_token,
                "time_created":time.time()
            })
        else:
            # refresh token has expired
            print("Session has expired please login")
    else:
        access_token = user_data['access_token']

    headers = {
        "Authorization" : f"Bearer {access_token}",
    }

    return headers


def manageServerCall(method,path,data={},files={},useAuthentication=False):
    url = base_url + path
    headers = {} #{"Content-Type": "application/json"}

    if useAuthentication:
        headers = getRequestHeaders()

        if headers == None:
            print("You need to login")
            return 0


    if method == "GET":
        res = requests.get(url,headers=headers)
    elif method == "POST":
        res = requests.post(url,data=data,files=files,headers=headers)
    elif method == "DELETE":
        res = requests.delete(url,headers=headers)


    if res.ok:
        return [True,res.json()]
    
    elif 'detail' in res.json().keys():
        return [False,None]

    raise Exception(f"Server responded with status code {res.status_code} and error {res.reason}")


def pingServer():
    valid,res = manageServerCall('POST','sb/log-action/',{'command':'ping'},{},True)
    if valid:
        print(res)

def logUserAction(command):
    manageServerCall('POST','sb/log-action/',{'command':command},{},True)