import sys
import subprocess
import importlib
from typing import List, Union, Optional
from .error_handler import LibraryError
from .utils.package_manager import install_package

class LibController:
    def __init__(self, auto_install: bool = True, pip_command: str = "pip"):
        """
        Initialize the LibController.
        
        Args:
            auto_install (bool): Whether to automatically install missing packages
            pip_command (str): The pip command to use (e.g., "pip", "pip3")
        """
        self.auto_install = auto_install
        self.pip_command = pip_command
        self._installed_packages = set()
    
    def require(self, *libraries: str) -> None:
        """
        Ensure that the specified libraries are available.
        
        Args:
            *libraries: Variable number of library names to check
        
        Raises:
            LibraryError: If a library cannot be imported or installed
        """
        missing_libs = []
        
        for lib in libraries:
            try:
                # Try importing the library
                importlib.import_module(lib)
                self._installed_packages.add(lib)
            except ImportError:
                if self.auto_install:
                    missing_libs.append(lib)
                else:
                    raise LibraryError(f"Library '{lib}' is not installed and auto-install is disabled")
        
        if missing_libs:
            self._install_libraries(missing_libs)
            
            # Retry imports after installation
            for lib in missing_libs:
                try:
                    importlib.import_module(lib)
                    self._installed_packages.add(lib)
                except ImportError as e:
                    raise LibraryError(f"Failed to import '{lib}' after installation: {str(e)}")
    
    def _install_libraries(self, libraries: List[str]) -> None:
        """
        Install the specified libraries using pip.
        
        Args:
            libraries: List of library names to install
            
        Raises:
            LibraryError: If installation fails
        """
        for lib in libraries:
            success = install_package(lib, self.pip_command)
            if not success:
                raise LibraryError(f"Failed to install library '{lib}'")
    
    def restart_script(self) -> None:
        """
        Restart the current Python script.
        """
        python = sys.executable
        script = sys.argv[0]
        args = sys.argv[1:]
        
        subprocess.Popen([python, script] + args)
        sys.exit()
