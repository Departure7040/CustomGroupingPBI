# tmdl_editor.py
import os
import sys
import logging
import pandas as pd

# Add project root to the path if needed
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Import from backend which handles DLL loading
from backend.model_connector import ModelConnector, load_dll

# Make sure DLL is loaded
if not load_dll():
    logging.error("Failed to load ADOMD.NET DLL. Cannot proceed.")
    print("ERROR: Failed to load ADOMD.NET DLL. Cannot proceed.")
    sys.exit(1)

# Now we can import pyadomd
try:
    from pyadomd import Pyadomd
except Exception as e:
    logging.error(f"Failed to import pyadomd: {e}")
    print(f"ERROR: Failed to import pyadomd: {e}")
    sys.exit(1)

# Global variable to store the currently connected port
_CURRENT_PORT = None

def reset_port():
    """Reset the global port variable to None"""
    global _CURRENT_PORT
    logging.info("Resetting global port variable")
    _CURRENT_PORT = None
    return True

def get_available_ports():
    """
    Get a list of ports available for connection by considering both 
    automatically detected ports and allowing for manual entry.
    """
    try:
        connector = ModelConnector()
        detected_ports = connector.get_available_ports()
        logging.info(f"Detected ports: {detected_ports}")
        return detected_ports
    except Exception as e:
        logging.error(f"Error detecting ports: {e}")
        return []

def connect_to_model(port=None):
    """
    Connect to the Power BI model using the specified port or trying to detect one.
    
    Args:
        port (str, optional): The port number to connect to. If None, will try to detect.
        
    Returns:
        ModelConnector: A connected model connector object or None if connection fails.
    """
    global _CURRENT_PORT
    
    # Use the provided port or the stored one if available
    if port is not None:
        _CURRENT_PORT = port
    
    connector = ModelConnector()
    
    # If we have a specific port to use
    if _CURRENT_PORT:
        connector.port = _CURRENT_PORT
        connector.conn_str = f"Provider=MSOLAP;Data Source=localhost:{_CURRENT_PORT}"
        logging.info(f"Attempting to connect using specified port: {_CURRENT_PORT}")
    else:
        # Try to auto-detect a port
        detected = connector.detect_port()
        if detected:
            _CURRENT_PORT = connector.port
            logging.info(f"Auto-detected port: {_CURRENT_PORT}")
        else:
            logging.warning("No ports detected")
            return None
    
    # Test the connection
    if not connector.test_connection():
        logging.error(f"Connection test failed on port {connector.port}")
        return None
        
    return connector

def fetch_tables(port=None):
    """
    Fetch all tables from the Power BI model.
    
    Args:
        port (str, optional): The port to connect to. If None, will use stored port.
        
    Returns:
        list: List of table names or empty list if connection fails
    """
    global _CURRENT_PORT
    
    # Connect to model
    connector = connect_to_model(port)
    if not connector:
        logging.error("Could not connect to model to fetch tables")
        return []
    
    # Log the port being used
    logging.info(f"Fetching tables using port: {_CURRENT_PORT}")
    
    # Get tables
    try:
        tables = connector.get_tables()
        logging.info(f"Found {len(tables)} tables")
        return tables
    except Exception as e:
        logging.error(f"Error fetching tables: {e}")
        return []

def fetch_columns_for_table(table_name, port=None):
    """
    Fetch all columns for a specific table.
    
    Args:
        table_name (str): The name of the table to fetch columns for
        port (str, optional): The port to connect to. If None, will use stored port.
        
    Returns:
        list: List of column names or empty list if connection fails
    """
    global _CURRENT_PORT
    
    # Connect to model
    connector = connect_to_model(port)
    if not connector:
        logging.error(f"Could not connect to model to fetch columns for {table_name}")
        return []
    
    # Log the port being used
    logging.info(f"Fetching columns for table {table_name} using port: {_CURRENT_PORT}")
    
    # Get columns
    try:
        columns = connector.get_columns_for_table(table_name)
        logging.info(f"Found {len(columns)} columns for table {table_name}")
        return columns
    except Exception as e:
        logging.error(f"Error fetching columns for table {table_name}: {e}")
        return []

if __name__ == "__main__":
    print("Available Power BI ports:", get_available_ports())
    
    user_port = input("Enter port number (or leave empty to autodetect): ")
    if not user_port:
        user_port = None
    
    # Connect to model and check connection
    connector = connect_to_model(user_port)
    if connector:
        print(f"Connected successfully to port {_CURRENT_PORT}")
        
        # Get tables
        tables = connector.get_tables()
        print("\nTables in model:")
        for table in tables:
            print(f" - {table}")
        
        # Get columns for first table if any tables exist
        if tables:
            sample_table = tables[0]
            columns = connector.get_columns_for_table(sample_table)
            print(f"\nColumns in {sample_table}:")
            for column in columns:
                print(f" - {column}")
    else:
        print("Failed to connect to Power BI Desktop.")
        print("Please ensure Power BI Desktop is running with a model open.")
