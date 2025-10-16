import subprocess
from typing import Optional

def install_package(package_name: str, pip_command: str = "pip") -> bool:
    """
    Install a Python package using pip.
    
    Args:
        package_name: Name of the package to install
        pip_command: The pip command to use (default: "pip")
        
    Returns:
        bool: True if installation was successful, False otherwise
    """
    try:
        subprocess.check_call(
            [pip_command, "install", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False
