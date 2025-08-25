"""
Configuration utilities for the TMDL Live Editor.
Handles application settings and path management.
"""

import os
import json
import logging
import sys
import ctypes
from pathlib import Path

# Config file location
CONFIG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'app_config.json')

# Default configuration
DEFAULT_CONFIG = {
    "adomd_dll_path": None,
    "tabular_editor_path": r"C:\Program Files (x86)\Tabular Editor\TabularEditor.exe",
    "last_import_path": None,
    "last_export_path": None
}

def ensure_config_exists():
    """Ensure the config directory and file exist."""
    os.makedirs(CONFIG_DIR, exist_ok=True)
    
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
    
    return CONFIG_FILE

def load_config():
    """Load the application configuration."""
    config_file = ensure_config_exists()
    
    try:
        with open(config_file, 'r') as f:
            config = json.load(f)
        return config
    except Exception as e:
        logging.error(f"Error loading config: {e}")
        return DEFAULT_CONFIG.copy()

def save_config(config):
    """Save the application configuration."""
    config_file = ensure_config_exists()
    
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        return True
    except Exception as e:
        logging.error(f"Error saving config: {e}")
        return False

def find_adomd_dll():
    """
    Search for Microsoft.AnalysisServices.AdomdClient.dll in standard locations.
    Returns the path if found, None otherwise.
    """
    # Base directory for ADOMD.NET
    adomd_base = r"C:\Program Files\Microsoft.NET\ADOMD.NET"
    
    if not os.path.exists(adomd_base):
        logging.warning(f"ADOMD.NET base directory not found: {adomd_base}")
        return None
    
    # Look for version directories (e.g., 160, 170, etc.)
    try:
        # Find all subdirectories that look like version numbers
        version_dirs = [d for d in os.listdir(adomd_base) 
                        if os.path.isdir(os.path.join(adomd_base, d)) and d.isdigit()]
        
        # Sort in descending order to get the latest version first
        version_dirs.sort(reverse=True)
        
        for version in version_dirs:
            dll_path = os.path.join(adomd_base, version, "Microsoft.AnalysisServices.AdomdClient.dll")
            if os.path.exists(dll_path):
                logging.info(f"Found ADOMD.NET DLL: {dll_path}")
                return dll_path
        
        logging.warning("No ADOMD.NET DLL found in version directories")
        return None
    except Exception as e:
        logging.error(f"Error searching for ADOMD.NET DLL: {e}")
        return None

def get_adomd_dll_path():
    """
    Get the path to the ADOMD.NET DLL, searching for it if necessary.
    """
    config = load_config()
    
    # If we have a saved path and it exists, use it
    if config.get('adomd_dll_path') and os.path.exists(config['adomd_dll_path']):
        return config['adomd_dll_path']
    
    # Otherwise, search for the DLL
    dll_path = find_adomd_dll()
    
    # If found, save it to config
    if dll_path:
        config['adomd_dll_path'] = dll_path
        save_config(config)
    
    return dll_path

def ensure_dll_in_path(dll_path):
    """
    Ensures the DLL's directory is in the system path.
    This helps Python.NET find the DLL and its dependencies.
    """
    if not dll_path:
        return False
    
    dll_dir = os.path.dirname(dll_path)
    
    # Add to PATH environment variable if not already there
    if dll_dir not in os.environ['PATH']:
        os.environ['PATH'] = dll_dir + os.pathsep + os.environ['PATH']
        logging.info(f"Added {dll_dir} to PATH environment variable")
    
    # For Python 3.8+, also use AddDllDirectory
    if hasattr(os, 'add_dll_directory'):
        try:
            os.add_dll_directory(dll_dir)
            logging.info(f"Added {dll_dir} to DLL directories")
        except Exception as e:
            logging.warning(f"Failed to add DLL directory: {e}")
    
    return True

def load_adomd_dll():
    """
    Load the ADOMD.NET DLL and return both the path and a boolean indicating success.
    Handles finding the DLL, adding its directory to the path, and loading it with Python.NET.
    """
    try:
        # Get the DLL path
        dll_path = get_adomd_dll_path()
        if not dll_path:
            logging.error("ADOMD.NET DLL not found")
            return None, False
        
        # Ensure DLL directory is in the path
        ensure_dll_in_path(dll_path)
        
        # Try to pre-load the DLL using ctypes to handle dependencies
        try:
            ctypes.WinDLL(dll_path)
            logging.info(f"Pre-loaded DLL with ctypes: {dll_path}")
        except Exception as e:
            logging.warning(f"Failed to pre-load DLL with ctypes: {e}")
        
        # Successfully found and prepared the DLL
        return dll_path, True
    except Exception as e:
        logging.error(f"Error loading ADOMD.NET DLL: {e}")
        return None, False

def get_tabular_editor_path():
    """Get the path to Tabular Editor executable."""
    config = load_config()
    return config.get('tabular_editor_path')

def set_tabular_editor_path(path):
    """Set the path to Tabular Editor executable."""
    config = load_config()
    config['tabular_editor_path'] = path
    return save_config(config)

def get_last_import_path():
    """Get the last used import directory path."""
    config = load_config()
    return config.get('last_import_path')

def set_last_import_path(path):
    """Set the last used import directory path."""
    config = load_config()
    config['last_import_path'] = path
    return save_config(config)

def get_last_export_path():
    """Get the last used export directory path."""
    config = load_config()
    return config.get('last_export_path')

def set_last_export_path(path):
    """Set the last used export directory path."""
    config = load_config()
    config['last_export_path'] = path
    return save_config(config) 