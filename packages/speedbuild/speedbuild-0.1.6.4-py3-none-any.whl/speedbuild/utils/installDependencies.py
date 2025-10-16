import subprocess
import sys
import os

def install_dependencies(dependencies, venv_path=None):
    """Install dependencies inside a virtual environment if provided, otherwise install globally."""
    
    # Determine the correct pip executable
    if venv_path:
        pip_executable = os.path.join(venv_path, "bin", "pip") if os.name != "nt" else os.path.join(venv_path, "Scripts", "pip.exe")
        if not os.path.exists(pip_executable):
            print(f"Error: Virtual environment not found at {venv_path}")
            return
    else:
        pip_executable = sys.executable.replace("python", "pip")  # Use the system's pip

    # Install dependencies
    for package in dependencies:
        try:
            subprocess.run([pip_executable, "install", package], check=True)
            print(f"Successfully installed {package}")
        except subprocess.CalledProcessError:
            print(f"Failed to install {package}")

