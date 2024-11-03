# src/utils.py

import json
import os
from typing import Any, Optional
import time

def save_cookies(cookies: Any, filepath: str = "cookies.json") -> None:
    """Save cookies to a file"""
    try:
        with open(filepath, "w") as f:
            json.dump(cookies, f)
    except Exception as e:
        print(f"Error saving cookies: {e}")

def load_cookies(filepath: str = "cookies.json") -> Optional[Any]:
    """Load cookies from a file"""
    if not os.path.exists(filepath):
        return None
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading cookies: {e}")
        return None

def get_env_variable(var_name: str) -> str:
    """Get an environment variable or raise an error if it's not set"""
    value = os.getenv(var_name)
    if not value:
        raise ValueError(f"Environment variable {var_name} not set.")
    return value
