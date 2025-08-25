#!/usr/bin/env python
# tmdl_editor_gui.py

"""
TMDL Live Editor (Python Edition)
A local Python desktop application for modifying the TMDL (Tabular Model Definition Language)
of a live Power BI Desktop model via the XMLA endpoint.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMessageBox, QSplashScreen
from PyQt5.QtCore import QDir, Qt
from PyQt5.QtGui import QPixmap

# Add the project root to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import application components
from utils.logger import setup_logger
from utils.config import load_adomd_dll
from backend.model_connector import load_dll
from gui.main_window import MainWindow

def setup_directories():
    """Ensure required directories exist."""
    app_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Create logs directory
    logs_dir = os.path.join(app_dir, 'logs')
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create data directory for sample files/temp files
    data_dir = os.path.join(app_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

def check_prerequisites():
    """Check that all required components are available."""
    # Check for ADOMD.NET DLL
    dll_path, success = load_adomd_dll()
    if not success:
        return False, f"ADOMD.NET DLL not found or could not be loaded.\nPlease install ADOMD.NET client libraries."
    
    # Try to load the DLL with pythonnet
    if not load_dll():
        return False, f"Failed to load ADOMD.NET DLL.\nThis may be due to missing dependencies or permissions."
    
    return True, "All prerequisites met."

def main():
    # Setup required directories
    setup_directories()
    
    # Setup logging
    logger = setup_logger()
    logger.info("Starting TMDL Live Editor")
    
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("TMDL Live Editor")
    app.setOrganizationName("TMDLLiveEditor")
    
    # Check prerequisites
    success, message = check_prerequisites()
    if not success:
        QMessageBox.critical(None, "Startup Error", message)
        logger.critical(f"Startup failed: {message}")
        return 1
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application event loop
    try:
        logger.info("Application running")
        return app.exec_()
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        return 1
    finally:
        logger.info("Application shutdown")

if __name__ == "__main__":
    sys.exit(main())
