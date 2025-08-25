#!/usr/bin/env python
# test_structure.py

"""
Test script to verify the project structure is correct.
This doesn't require external dependencies like ADOMD.NET.
"""

import os
import sys
import importlib.util

def check_module(module_path):
    """Check if a module exists without importing it."""
    try:
        spec = importlib.util.find_spec(module_path)
        return spec is not None
    except ModuleNotFoundError:
        return False

def main():
    print("Checking TMDL Live Editor project structure...")
    print("-" * 50)
    
    # Check directories
    directories = ['gui', 'backend', 'utils', 'cli', 'tests', 'data', 'logs']
    for directory in directories:
        exists = os.path.isdir(directory)
        print(f"Directory '{directory}': {'✓' if exists else '✗'}")
    
    print("-" * 50)
    
    # Check key files
    files = [
        'tmdl_editor_gui.py',
        'tmdl_editor.py',
        'README.md',
        'Implementation_Plan.md',
        'requirements.txt',
        'gui/main_window.py',
        'gui/grouping_editor.py',
        'gui/model_explorer.py',
        'gui/theme_manager.py',
        'backend/model_connector.py',
        'backend/dax_info_views.py',
        'backend/tabular_editor_cli.py',
        'backend/model_updater.py',
        'utils/logger.py',
        'utils/io_excel.py',
        'utils/io_json.py',
        'cli/tmdl_cli.py',
        'tests/run_tests.py',
        'tests/test_app.py'
    ]
    
    for file in files:
        exists = os.path.isfile(file)
        print(f"File '{file}': {'✓' if exists else '✗'}")
    
    print("-" * 50)
    
    # Check imports (without actually importing)
    print("Checking module imports (without importing):")
    modules = [
        'gui',
        'gui.main_window',
        'gui.grouping_editor',
        'gui.model_explorer',
        'gui.theme_manager',
        'backend',
        'backend.model_connector',
        'backend.dax_info_views',
        'backend.tabular_editor_cli',
        'backend.model_updater',
        'utils',
        'utils.logger',
        'utils.io_excel',
        'utils.io_json',
        'cli',
        'cli.tmdl_cli',
        'tests'
    ]
    
    for module in modules:
        can_import = check_module(module)
        print(f"Module '{module}': {'✓' if can_import else '✗'}")
    
    # Report
    print("-" * 50)
    print("Structure check complete.")
    print("Note: This doesn't test if the code actually runs correctly.")
    print("For that, you'll need to install all dependencies and run the application.")

if __name__ == "__main__":
    main() 