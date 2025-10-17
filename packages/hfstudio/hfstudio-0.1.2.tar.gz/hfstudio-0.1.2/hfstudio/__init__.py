"""HFStudio - Local and API-based Text-to-Speech Studio"""

import json
import os
from pathlib import Path

def _get_version():
    """Read version from frontend/package.json"""
    # Get the project root (one level up from this package)
    package_root = Path(__file__).parent.parent
    package_json_path = package_root / "frontend" / "package.json"
    
    with open(package_json_path, 'r') as f:
        package_data = json.load(f)
        return package_data['version']

__version__ = _get_version()