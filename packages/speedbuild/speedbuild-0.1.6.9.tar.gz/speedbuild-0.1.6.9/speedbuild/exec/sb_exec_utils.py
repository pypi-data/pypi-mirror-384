import os
import sys
import venv
import subprocess
from pathlib import Path


def create_virtual_environment(venv_path, python_executable=None):
    """
    Create a virtual environment programmatically.
    
    Args:
        venv_path (str): Path where the virtual environment will be created
        python_executable (str, optional): Path to specific Python executable to use
    
    Returns:
        bool: True if successful, False otherwise
    """

    venv_path = venv_path+"/venv"

    if not os.path.exists(venv_path):
        os.makedirs(venv_path)
    try:
        # Method 1: Using the venv module (Python 3.3+)
        print(f"Creating virtual environment at: {venv_path}")
        
        # Create the venv directory if it doesn't exist
        venv_dir = Path(venv_path)
        venv_dir.parent.mkdir(parents=True, exist_ok=True)
        
        # Create virtual environment
        if python_executable:
            # Use specific Python executable
            result = subprocess.run([
                python_executable, "-m", "venv", str(venv_path)
            ], capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"Error creating venv: {result.stderr}")
                return False
        else:
            # Use current Python interpreter
            venv.create(venv_path, with_pip=True)
        
        print(f"Virtual environment created successfully at: {venv_path}")
        
        # Get activation script path
        if sys.platform == "win32":
            activate_script = os.path.join(venv_path, "Scripts", "activate.bat")
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        else:
            activate_script = os.path.join(venv_path, "bin", "activate")
            pip_path = os.path.join(venv_path, "bin", "pip")
        
        print(f"Activation script: {activate_script}")
        print(f"Pip executable: {pip_path}")
        
        return True
        
    except Exception as e:
        print(f"Error creating virtual environment: {e}")
        return False
    

def install_packages_in_venv(venv_path, packages):
    """
    Install packages in the virtual environment.
    
    Args:
        venv_path (str): Path to the virtual environment
        packages (list): List of package names to install
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Get pip path based on OS
        if sys.platform == "win32":
            pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
        else:
            pip_path = os.path.join(venv_path, "bin", "pip")
        
        # Install packages
        for package in packages:
            print(f"Installing {package}...")
            result = subprocess.run([
                pip_path, "install", package
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"Successfully installed {package}")
            else:
                print(f"Failed to install {package}: {result.stderr}")
                return False
        
        return True
    except Exception as e:
        print(f"Error installing packages: {e}")
        return False