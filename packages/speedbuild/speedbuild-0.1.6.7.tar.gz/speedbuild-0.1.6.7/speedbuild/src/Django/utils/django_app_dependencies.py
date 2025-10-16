import os
import json
import time
import shutil
import tempfile
import threading
import subprocess
import importlib.util
import concurrent.futures

from pathlib import Path
from importlib import metadata

from ....utils.pushPackage import pushPythonPackageToServer

CACHE_FILE = str(Path.home()) + "/.sb/sb_app_mapping_cache.json"
CACHE_LOCK = threading.Lock()  # For thread-safe cache operations
MAX_WORKERS = 5  # Reduced from 5 to avoid resource exhaustion
TIMEOUT = 120  # Seconds to wait before considering a package installation hung

def load_django_settings(settings_path):
    """Loads the Django settings module dynamically."""
    spec = importlib.util.spec_from_file_location("settings", settings_path)
    settings_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(settings_module)
    return settings_module

def create_temp_env():
    """Creates a temporary virtual environment and returns its path."""
    temp_dir = tempfile.mkdtemp()
    venv_path = os.path.join(temp_dir, "venv")
    try:
        # Add timeout to avoid hanging
        result = subprocess.run(
            ["python", "-m", "venv", venv_path], 
            check=True, 
            timeout=30  # 30 seconds should be enough for venv creation
        )
        return temp_dir, venv_path
    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
        print(f"Error creating virtual environment: {str(e)}")
        shutil.rmtree(temp_dir)
        raise

def get_site_packages_path(venv_path):
    """Returns the site-packages path for the virtual environment."""
    python_bin = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", "python")
    try:
        output = subprocess.run(
            [python_bin, "-c", "import site; print(site.getsitepackages()[0])"],
            capture_output=True,
            text=True,
            timeout=10  # 10 seconds timeout
        )
        return output.stdout.strip()
    except subprocess.TimeoutExpired:
        print(f"Timeout getting site-packages path for environment: {venv_path}")
        raise

def install_package(venv_path, package_name):
    """Installs a package in the temporary virtual environment."""
    pip_bin = os.path.join(venv_path, "Scripts" if os.name == "nt" else "bin", "pip")
    try:
        print(f"Starting installation of {package_name}...")
        process = subprocess.run(
            [pip_bin, "install", package_name], 
            check=True, 
            timeout=TIMEOUT,  # Timeout to prevent hanging
            capture_output=True,
            text=True
        )
        print(f"Successfully installed {package_name}")
        return True
    except subprocess.TimeoutExpired:
        print(f"Installation of {package_name} timed out after {TIMEOUT} seconds")
        return False
    except subprocess.SubprocessError as e:
        print(f"Error installing {package_name}: {str(e)}")
        return False

def detect_installed_apps(site_packages_path):
    """Detect likely Django apps in site-packages."""
    try:
        apps = []
        for item in os.listdir(site_packages_path):
            full_path = os.path.join(site_packages_path, item)

            # Ignore metadata folders
            if item.endswith(".dist-info") or item.endswith(".egg-info"):
                continue

            # Include real directories
            if os.path.isdir(full_path):
                # Check for __init__.py to confirm it's a module
                # if os.path.isfile(os.path.join(full_path, "__init__.py")):
                #     apps.append(item)
                apps.append(item)
        return apps
    except Exception as e:
        print(f"Error detecting installed apps: {str(e)}")
        return []

def safe_load_json(file_path):
    """Safely load JSON from a file with retries."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with open(file_path, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            if attempt < max_retries - 1:
                time.sleep(0.5)  # Wait before retrying
            else:
                return {}
        except FileNotFoundError:
            return {}

# here
def save_cache(data):
    """
    Saves the provided data to a cache file, merging it with any existing cached data.
    Args:
        data (dict): The data to be saved to the cache. This will be merged with the existing cache.
    Raises:
        Exception: If there is an error while writing to the cache file, an error message is printed.
    """
    """Saves the app mapping to a cache file."""
    with CACHE_LOCK:
        # First load existing cache to merge with new data
        existing_cache = safe_load_json(CACHE_FILE)

        if existing_cache == {}:
            os.makedirs(CACHE_FILE, exist_ok=True)

        # Only update if there is a difference
        if any(existing_cache.get(k) != v for k, v in data.items()):
            # existing_cache.update(data)
            # send data to server for update and pull all package data
            res = pushPythonPackageToServer(data)
            if res is not None:
                # set existing_cache to server response
                existing_cache = res
            else:
                # merge offline data
                # Merge and save
                existing_cache.update(data)

        try:
            with open(CACHE_FILE, "w") as f:
                json.dump(existing_cache, f, indent=4)
        except Exception as e:
            print(f"Error saving cache: {str(e)}")

def load_cache():
    """Loads the app mapping from cache if available."""
    with CACHE_LOCK:
        return safe_load_json(CACHE_FILE)

def process_single_package(package_name):
    """Process a single package in its own virtual environment."""
    print(f"Processing package: {package_name}")
    cache = load_cache()
    
    # Skip if already in cache
    if package_name in cache:
        print(f"Using cached data for {package_name}")
        return package_name, cache[package_name]
    
    temp_dir = None
    try:
        temp_dir, venv_path = create_temp_env()
        site_packages = get_site_packages_path(venv_path)
        
        success = install_package(venv_path, package_name)
        if not success:
            print(f"Installation failed for {package_name}")
            return package_name, []
            
        installed_apps = detect_installed_apps(site_packages)
        print(f"Found apps for {package_name}: {installed_apps}")
        
        # Update cache with this result
        cache_update = {package_name: installed_apps}
        save_cache(cache_update)
            
        return package_name, installed_apps
    except Exception as e:
        print(f"Error processing {package_name}: {str(e)}")
        return package_name, []
    finally:
        # Cleanup temp environment
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                print(f"Cleaned up environment for {package_name}")
            except Exception as e:
                print(f"Failed to clean up {temp_dir}: {str(e)}")


def get_package_version(package_name):
    try:
        return metadata.version(package_name)
    except metadata.PackageNotFoundError:
        return "unknown"

def get_django_app_from_packages_parallel(package_names, max_batch_size=10):
    """
    Process multiple package names in parallel to retrieve Django applications.
    This function processes a list of package names to identify Django applications within them,
    utilizing parallel processing for efficiency. It implements caching to avoid reprocessing
    previously analyzed packages.
    Args:
        package_names (list): A list of package names to process.
        max_batch_size (int, optional): Maximum number of packages to process in parallel. 
            Defaults to 10.
    Returns:
        dict: A dictionary mapping package names to lists of discovered Django applications.
            For packages that fail processing or timeout, an empty list is returned.
    Example:
        >>> packages = ['django-allauth', 'django-rest-framework']
        >>> results = get_django_app_from_packages_parallel(packages)
        >>> print(results)
        {'django-allauth': ['allauth', 'allauth.account'], 'django-rest-framework': ['rest_framework']}
    Note:
        - Uses threading for parallel processing
        - Implements timeout handling to prevent hanging
        - Caches results for future lookups
        - Processes packages in batches to manage resource usage
    """
    cache = load_cache()
    results = {}
    # packages_to_process = [pkg for pkg in package_names if pkg not in cache]
    packages_to_process = []
    
    # Add cached results directly
    for pkg in package_names:
        if pkg in cache:
            results[pkg] = {"pkg":cache[pkg],"version":get_package_version(pkg)}
            # print(get_package_version(pkg), pkg, "package version")
        else:
            packages_to_process.append(pkg)
        
    
    # Process in smaller batches to prevent resource exhaustion
    for i in range(0, len(packages_to_process), max_batch_size):
        batch = packages_to_process[i:i+max_batch_size]
        print(f"Processing batch of {len(batch)} packages")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            future_to_package = {
                executor.submit(process_single_package, pkg): pkg 
                for pkg in batch
            }
            
            for future in concurrent.futures.as_completed(future_to_package):
                try:
                    package_name, installed_apps = future.result(timeout=TIMEOUT + 30)
                    
                    results[package_name] = {"pkg":installed_apps,"version":get_package_version(pkg)}#installed_apps
                except concurrent.futures.TimeoutError:
                    package = future_to_package[future]
                    print(f"Processing timed out for package: {package}")
                    results[package] = {"pkg":[],"version":None}
                except Exception as e:
                    package = future_to_package[future]
                    print(f"Exception for package {package}: {str(e)}")
                    results[package] = {"pkg":[],"version":None}
    
    return results

def get_installed_packages(venv_path):
    """Get list of installed packages in the given virtual environment."""
    pip_path = os.path.join(venv_path, "bin", "pip")  # Linux/macOS

    if os.name == "nt":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")  # Windows

    try:
        result = subprocess.run(
            [pip_path, "list"], 
            capture_output=True, 
            text=True,
            timeout=30  # 30 seconds timeout
        )
        lines = result.stdout.splitlines()[2:]  # Skip headers
        packages = {line.split()[0] for line in lines}  # Extract package names
        return packages
    except subprocess.TimeoutExpired:
        print("Timeout getting installed packages")
        return set()
    except Exception as e:
        print(f"Error getting installed packages: {str(e)}")
        return set()

def getDjangoAppsPackage(settings_path, venv):
    """
    Maps Django installed apps to their corresponding Python packages.
    This function analyzes the Django settings file to find installed apps and determines
    which Python packages provide those apps. It handles both direct app imports and
    regular Python package imports.
    Args:
        settings_path (str): Path to the Django settings.py file
        venv (str): Path to the Python virtual environment to analyze
    Returns:
        dict: A mapping of Django app names to lists of package names that provide them.
              Returns empty dict if settings file is not found or cannot be loaded.
              Format: {'app_name': ['package1', 'package2']}
    Raises:
        No exceptions are raised - errors are handled internally and logged to stdout
    Example:
        >>> getDjangoAppsPackage('/path/to/settings.py', '/path/to/venv')
        {'django.contrib.admin': ['django'],
         'django.contrib.auth': ['django'],
         'myapp': ['my-package']}
    """
    if not os.path.exists(settings_path):
        print(f"Error: Settings file '{settings_path}' not found!")
        return {}

    # Load Django settings
    try:
        settings_module = load_django_settings(settings_path)
        installed_apps = getattr(settings_module, "INSTALLED_APPS", [])
    except Exception as e:
        print(f"Error loading Django settings: {str(e)}")
        return {}

    # Get all installed packages
    packages = get_installed_packages(venv)
    
    # Process packages in parallel
    package_app_mapping = get_django_app_from_packages_parallel(packages)
    
    # Map Django apps to their packages
    app_mapping = {}
    for package, django_apps in package_app_mapping.items():
        for app in django_apps['pkg']:
            if app in installed_apps:  # or is a regular import
                if app in app_mapping:
                    app_mapping[app]['pkg'].append(package)
                else:
                    app_mapping[app] = {"pkg":[package]}

                    # check if version is not None or Unkmown
                    pkg_version = django_apps['version'] 
                    if pkg_version != None or pkg_version != "unknown":
                        app_mapping[app]['version'] = pkg_version 

    return app_mapping

# Example usage
# if __name__ == "__main__":
#     # For testing
#     settings_path = "path/to/your/settings.py"
#     venv_path = "path/to/your/venv"
    
    # Uncomment to run
    # app_mapping = getDjangoAppsPackage(settings_path, venv_path)
    # print(json.dumps(app_mapping, indent=2))