import os
import ast
import requests
from pathlib import Path
from typing import List, Tuple

from .server_address import url_address
from ..src.Django.utils.django_app_dependencies import save_cache


def getCurrentDjangoFiles(path):
    python_files = [file for file in os.listdir(path) if file.endswith(".py")]
    return python_files

def pullPythonPackageJSON():
    try:
        res = requests.get(url_address + "sb/packages/", timeout=10)
        res.raise_for_status()
        print(res.json())

        save_cache(res.json())

    except requests.exceptions.HTTPError as http_err:
        raise ValueError(f"HTTP error occurred: {http_err} - Status code: {res.status_code}")
    except requests.exceptions.ConnectionError:
        raise ValueError("Connection error. Is the server running?")
    except requests.exceptions.Timeout:
        raise ValueError("Request timed out.")
    except Exception as err:
        raise ValueError (f"An error occurred: {err}")


def extract_views_from_urls(urls_file_path: str) -> List[Tuple[str, str]]:
    print(f"Extracting views from {urls_file_path}")
    with open(urls_file_path, "r") as f:
        data = f.read()
        data = data.replace(".as_view()", "")

        tree = ast.parse(data, filename=urls_file_path)

        view_names = []
        import_alias_map = {}

        # Step 1: Capture import statements to trace views
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module
                if module == None:
                    module = ""
                for alias in node.names:
                    import_alias_map[alias.asname or alias.name] = f"{module}.{alias.name}"
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    import_alias_map[alias.asname or alias.name] = alias.name

        # Step 2: Find calls to `path()` or `re_path()`
        for node in ast.walk(tree):
            
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("path", "re_path"):
                
                if len(node.args) >= 2:
                    view = node.args[1]
                    if isinstance(view, ast.Attribute):

                        # Something like views.HomeView
                        value_id = view.value.id if isinstance(view.value, ast.Name) else None

                        attr = view.attr
                        full_path = import_alias_map.get(value_id)
                        if full_path:
                            view_names.append(f"{full_path}.{attr}")
                    elif isinstance(view, ast.Name):
                        # Direct function/class reference
                        view_path = import_alias_map.get(view.id)
                        if view_path:
                            view_names.append(view_path)

    return view_names


def findFilePath(path,filename):
    # print("searching ",path)
    file_paths = []
    for root, _, files in os.walk(path):
        for file in files:
            # Get the relative path to the base directory
            if filename in file:
                relative_path = os.path.relpath(os.path.join(root, file), path)
                file_paths.append(relative_path)

    return file_paths


def getAbsolutePath(relative_path):
    relative_path = Path(relative_path)
    absolute_path = relative_path.resolve()

    return str(absolute_path)

def get_template_output_path(feature_name):
    user_dir = str(Path.home())
    user_dir += "/.sb_zip"

    if not os.path.exists(user_dir):
        os.makedirs(user_dir)

    output_zip = f"{user_dir}/speed_build_{feature_name}"  # No .zip extension needed

    return output_zip