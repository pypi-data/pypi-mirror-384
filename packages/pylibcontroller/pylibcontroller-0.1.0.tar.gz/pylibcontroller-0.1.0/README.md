# PyLibController

A Python library manager that automatically installs missing libraries at runtime.

## Installation

```bash
pip install pylibcontroller
```

## Usage

```python
from pylibcontroller import LibController

# Create a LibController instance
lib_controller = LibController(auto_install=True)

try:
    # Try to import required libraries
    lib_controller.require("requests", "pandas")
    
    # If we get here, the libraries are available
    import requests
    import pandas as pd
    
    # Your code using the libraries goes here
    print("All required libraries are available!")
    
except Exception as e:
    print(f"Error: {e}")
```

## Features

- Automatic library installation
- Error handling with custom error messages
- Multiple library checking at once
- Script auto-restart capability
- Customizable pip command

## License

MIT License
