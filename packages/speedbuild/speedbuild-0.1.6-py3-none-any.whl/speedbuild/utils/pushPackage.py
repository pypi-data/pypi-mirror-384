import requests

from .server_address import url_address

def pushPythonPackageToServer(cache):
    url = url_address + "sb/packages/"
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(
            url,
            json={"packages": cache},
            headers=headers,
            timeout=10
        )
        response.raise_for_status()
        return response.json() if response.status_code == 200 else None
    except (requests.RequestException, Exception):
        return None
