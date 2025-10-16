import io
import os
import zipfile
import requests

from pathlib import Path

from .server_address import url_address

def pullInitialTemplates():
    output_folder = str(Path.home()) + "/.sb_zip"
    os.makedirs(output_folder, exist_ok=True)

    try:
        res = requests.get(url_address + "sb/initial-templates/", stream=True, timeout=10)
        res.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return

    file_bytes = io.BytesIO(res.content)
    try:
        with zipfile.ZipFile(file_bytes) as z:
            z.extractall(output_folder)
    except zipfile.BadZipFile:
        pass
        print("Downloaded file is not a valid zip archive.")