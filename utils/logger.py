# utils/logger.py

import logging
import os
from datetime import datetime

def setup_logger(log_file=None, console_level=logging.INFO, file_level=logging.DEBUG):
    """
    Set up logging for the application.
    
    Args:
        log_file: Path to the log file (default: None, auto-generated)
        console_level: Logging level for console output
        file_level: Logging level for file output
        
    Returns:
        Configured logger
    """
    # If no log file specified, create one with timestamp
    if log_file is None:
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'logs')
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"tmdl_editor_{timestamp}.log")
    
    # Create logger
    logger = logging.getLogger('tmdl_editor')
    logger.setLevel(logging.DEBUG)  # Capture all levels
    
    # Remove existing handlers if any
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(console_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler
    try:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(file_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        logger.info(f"Logging to file: {log_file}")
    except Exception as e:
        logger.warning(f"Could not create log file {log_file}: {e}")
    
    return logger

def get_logger():
    """Get the configured logger or create one if it doesn't exist."""
    logger = logging.getLogger('tmdl_editor')
    if not logger.handlers:
        logger = setup_logger()
    return logger 