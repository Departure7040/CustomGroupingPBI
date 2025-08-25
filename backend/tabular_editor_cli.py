# backend/tabular_editor_cli.py

import subprocess
import os
import pandas as pd
import tempfile
import sys
import logging

# Add project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.model_connector import ModelConnector
from utils.config import get_tabular_editor_path

def write_tsv(df: pd.DataFrame, table_name: str):
    """
    Write DataFrame to a TSV file in a temporary directory
    Make sure path handling is done correctly with proper escaping
    """
    temp_dir = tempfile.gettempdir()
    file_path = os.path.join(temp_dir, f"{table_name}.tsv")
    
    # Write with tab delimiter and Windows line endings
    df.to_csv(file_path, sep="\t", index=False, lineterminator="\r\n")
    
    # Verify the file was created
    if not os.path.exists(file_path):
        logging.error(f"Failed to create TSV file at {file_path}")
        raise FileNotFoundError(f"Failed to create TSV file at {file_path}")
    
    # Log file size for debugging
    file_size = os.path.getsize(file_path)
    logging.info(f"Created TSV file at {file_path}, size: {file_size} bytes")
    
    return file_path

def build_script(table_name: str, tsv_path: str):
    """
    Returns a TMSL script to refresh the table and replace its contents.
    Handles path escaping for C# script.
    """
    # Normalize the path with backslashes for C# and escape them properly
    normalized_path = tsv_path.replace('\\', '\\\\')
    
    script = f"""
// Script to update table {table_name}
// Generated at {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}

// Get the table
var tbl = Model.Tables["{table_name}"];

// Clear existing rows
tbl.ClearRows();

// Import new data - using tab as delimiter since the file is TSV
tbl.ImportFile(@"{normalized_path}", "\\t");

// Save changes
Model.SaveChanges();

// Output success message for detection
Console.WriteLine("Table {0} updated successfully.", "{table_name}");
"""
    return script

def run_tabular_editor(table_name: str, df: pd.DataFrame, port=None):
    # Get Tabular Editor path from config
    tabular_editor_path = get_tabular_editor_path()
    
    if not tabular_editor_path or not os.path.isfile(tabular_editor_path):
        error_message = f"Tabular Editor not found at: {tabular_editor_path}"
        logging.error(error_message)
        raise FileNotFoundError(error_message)
    
    # If port wasn't provided, try to detect it
    if port is None:
        try:
            connector = ModelConnector()
            port = connector.detect_port()
        except Exception as e:
            error_message = f"Failed to detect Power BI port: {e}"
            logging.error(error_message)
            raise RuntimeError(error_message)
    
    # Verify port connection before proceeding
    try:
        connector = ModelConnector()
        connector.port = port
        connector.conn_str = f"Provider=MSOLAP;Data Source=localhost:{port}"
        
        if not connector.test_connection():
            error_message = f"Cannot connect to Power BI on port {port}. Please ensure Power BI is running and the model is open."
            logging.error(error_message)
            raise RuntimeError(error_message)
    except Exception as e:
        error_message = f"Connection test failed: {e}"
        logging.error(error_message)
        raise RuntimeError(error_message)

    # Export the data to TSV
    tsv_path = write_tsv(df, table_name)
    script = build_script(table_name, tsv_path)

    # Write the script to a temporary file
    script_path = os.path.join(tempfile.gettempdir(), f"{table_name}_script.cs")
    with open(script_path, "w") as f:
        f.write(script)
    
    # For demo purposes - create a help file with instructions
    help_file = os.path.join(tempfile.gettempdir(), "tabular_editor_instructions.txt")
    with open(help_file, "w") as f:
        f.write(f"TABULAR EDITOR MANUAL STEPS\n")
        f.write(f"==========================\n\n")
        f.write(f"Since automated approaches didn't work, please follow these steps:\n\n")
        f.write(f"1. In Tabular Editor, click 'File' > 'Open' > 'From Analysis Services...'\n\n")
        f.write(f"2. Enter this connection string: Provider=MSOLAP;Data Source=localhost:{port}\n\n")
        f.write(f"3. Once connected, click 'File' > 'Script' > 'Run C# Script...'\n\n")
        f.write(f"4. Navigate to and open this file:\n   {script_path}\n\n")
        f.write(f"5. Verify in the output window that the table was updated successfully\n\n")
        f.write(f"CONNECTION STRING TO COPY/PASTE:\n")
        f.write(f"Provider=MSOLAP;Data Source=localhost:{port}\n\n")
        f.write(f"SCRIPT PATH TO COPY/PASTE:\n")
        f.write(f"{script_path}\n")

    print("\n==== IMPORTANT: INTERACTIVE MODE REQUIRED ====")
    print("We need to use Tabular Editor interactively for this operation.\n")
    
    # Show clear instructions with important info highlighted
    print("📌 STEP 1: Opening Tabular Editor now...")
    os.startfile(tabular_editor_path)
    print("✅ Tabular Editor should now be open\n")
    
    print("📌 STEP 2: In Tabular Editor, connect to Power BI:")
    print("   → Click 'File' > 'Open' > 'From Analysis Services...'")
    print(f"   → Enter this connection string: Provider=MSOLAP;Data Source=localhost:{port}")
    print("   → Click 'OK'\n")
    
    print("📌 STEP 3: Run the script:")
    print("   → Click 'File' > 'Script' > 'Run C# Script...'")
    print(f"   → Navigate to this folder: {os.path.dirname(script_path)}")
    print(f"   → Open this file: {os.path.basename(script_path)}\n")
    
    print("📌 STEP 4: Verify results:")
    print("   → Check the output window for 'Table updated successfully' message\n")
    
    # Also open the instructions file
    os.startfile(help_file)
    print(f"✅ Instructions file opened: {help_file}")
    
    print("\n==== FOR QUICK COPY/PASTE ====")
    print(f"Connection string: Provider=MSOLAP;Data Source=localhost:{port}")
    print(f"Script path: {script_path}")
    print("===============================\n")
    
    # Ask for confirmation
    confirm = input("Did you successfully update the table in Tabular Editor? (y/n): ")
    return confirm.lower().startswith('y')
