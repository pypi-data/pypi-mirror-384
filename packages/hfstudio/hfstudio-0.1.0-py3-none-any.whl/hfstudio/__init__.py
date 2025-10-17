"""HFStudio - Local and API-based Text-to-Speech Studio"""

import json
import os
from pathlib import Path

def _get_version():
    """Read version from frontend/package.json"""
    try:
        # Get the package root directory (two levels up from this file)
        package_root = Path(__file__).parent.parent.parent
        package_json_path = package_root / "frontend" / "package.json"
        
        if package_json_path.exists():
            with open(package_json_path, 'r') as f:
                package_data = json.load(f)
                return package_data.get('version', '0.1.0')
        else:
            return '0.1.0'
    except Exception:
        return '0.1.0'

__version__ = _get_version()