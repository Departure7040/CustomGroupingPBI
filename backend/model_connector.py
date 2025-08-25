# backend/model_connector.py

import subprocess
import re
import os
import sys
import logging
import pandas as pd
import time

# Add project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import configuration module to get the ADOMD.NET DLL path
from utils.config import load_adomd_dll

# Global variables for DLL and connection
ADOMD_DLL_PATH = None
ADOMD_LOADED = False
AdomdConnection = None

def load_dll():
    """Load the ADOMD.NET DLL and required components"""
    global ADOMD_DLL_PATH, ADOMD_LOADED, AdomdConnection
    
    # Skip if already loaded
    if ADOMD_LOADED:
        return True
    
    try:
        # Get the DLL path and ensure it's in the system path
        dll_path, success = load_adomd_dll()
        if not success:
            logging.error("Failed to load ADOMD.NET DLL")
            return False
        
        ADOMD_DLL_PATH = dll_path
        
        # First import clr after ensuring DLL path is set up
        import clr
        
        # Try to add reference to the DLL
        try:
            clr.AddReference(ADOMD_DLL_PATH)
            # Import the AdomdConnection class
            from Microsoft.AnalysisServices.AdomdClient import AdomdConnection as AC
            globals()['AdomdConnection'] = AC
            ADOMD_LOADED = True
            logging.info(f"Successfully loaded ADOMD.NET DLL: {ADOMD_DLL_PATH}")
            return True
        except Exception as e:
            logging.error(f"Failed to add reference to ADOMD.NET DLL: {e}")
            return False
    except Exception as e:
        logging.error(f"Error in load_dll: {e}")
        return False

# Try to load the DLL when module is imported
load_dll()

class ModelConnector:
    def __init__(self, dll_path=ADOMD_DLL_PATH):
        self.port = None
        self.conn_str = None
        self.adomd_path = dll_path
        
        # Make sure DLL is loaded
        if not ADOMD_LOADED:
            if not load_dll():
                raise ImportError("Failed to load ADOMD.NET DLL. Cannot continue.")

    def detect_port(self):
        """
        Detects the Power BI Desktop XMLA port using 'netstat'.
        Looks for connections on 127.0.0.1 to Analysis Services.
        """
        try:
            result = subprocess.check_output("netstat -ano", shell=True, text=True)
            # Look for both 49xxx and 56xxx port ranges commonly used by Power BI
            matches = re.findall(r"127\.0\.0\.1:(49\d{3}|56\d{3})", result)
            ports = list(set(matches))
            if not ports:
                raise Exception("No XMLA port found. Open a Power BI Desktop model.")
                
            # Prioritize the 56xxx ports if any are found
            port_56xxx = [p for p in ports if p.startswith('56')]
            if port_56xxx:
                # Use the first 56xxx port found
                logging.info(f"Prioritizing 56xxx port: {port_56xxx[0]}")
                self.port = port_56xxx[0]
            else:
                # Fall back to the first port found
                self.port = ports[0]
                
            self.conn_str = f"Provider=MSOLAP;Data Source=localhost:{self.port}"
            return self.port
        except Exception as e:
            raise RuntimeError(f"Port detection failed: {e}")

    def test_connection(self, max_retries=3, retry_delay=1.0):
        """Test connection to Power BI with retries"""
        if not self.conn_str and self.port:
            self.conn_str = f"Provider=MSOLAP;Data Source=localhost:{self.port}"
        
        if not self.conn_str:
            try:
                self.detect_port()
            except Exception as e:
                logging.error(f"Failed to detect port: {e}")
                return False
        
        for i in range(max_retries):
            try:
                # Ensure DLL is loaded before attempting connection
                if not ADOMD_LOADED:
                    if not load_dll():
                        return False
                
                from pyadomd import Pyadomd
                conn = Pyadomd(self.conn_str)
                conn.open()
                conn.close()
                return True
            except Exception as e:
                logging.warning(f"Connection attempt {i+1} failed: {e}")
                if i < max_retries - 1:
                    time.sleep(retry_delay)
        
        return False

    def get_tables(self):
        try:
            from pyadomd import Pyadomd
            conn = Pyadomd(self.conn_str)
            conn.open()
            cursor = conn.cursor()
            results = cursor.execute("EVALUATE SELECTCOLUMNS(INFO.VIEW.TABLES(), \"Table\", [Name])")
            df = pd.DataFrame(results.fetchall(), columns=["Table"])
            return df["Table"].tolist()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch tables: {e}")
        finally:
            try:
                conn.close()
            except:
                pass

    def get_columns(self):
        try:
            from pyadomd import Pyadomd
            conn = Pyadomd(self.conn_str)
            conn.open()
            cursor = conn.cursor()
            results = cursor.execute("""
                EVALUATE SELECTCOLUMNS(INFO.VIEW.COLUMNS(), "Column", [Name], "Table", [Table])
            """)
            return pd.DataFrame(results.fetchall(), columns=["Column", "Table"])
        except Exception as e:
            raise RuntimeError(f"Failed to fetch columns: {e}")
    
    def get_available_ports(self):
        """Returns a list of all potential Power BI XMLA ports."""
        try:
            result = subprocess.check_output("netstat -ano", shell=True, text=True)
            # Look for both 49xxx and 56xxx port ranges commonly used by Power BI
            matches = re.findall(r"127\.0\.0\.1:(49\d{3}|56\d{3})", result)
            # Remove duplicates and sort
            ports = sorted(set(matches))
            return ports
        except Exception as e:
            logging.error(f"Failed to get available ports: {e}")
            return []

    def get_model_info(self):
        """Get basic information about the connected Power BI model."""
        if not self.conn_str:
            return None
            
        try:
            # Ensure DLL is loaded before attempting connection
            if not ADOMD_LOADED:
                if not load_dll():
                    return None
                    
            from pyadomd import Pyadomd
            conn = Pyadomd(self.conn_str)
            conn.open()
            cursor = conn.cursor()
            
            # Try to get model name
            try:
                results = cursor.execute("EVALUATE {1}") # Just a dummy query to get session info
                model_name = conn.connection.Database
                
                # Alternative query to get more details if needed
                # results = cursor.execute("EVALUATE SELECTCOLUMNS(INFO.MODEL(), \"Name\", [Name], \"Description\", [Description])")
                # model_info = pd.DataFrame(results.fetchall(), columns=["Name", "Description"])
                # if not model_info.empty:
                #     model_name = model_info.iloc[0]["Name"]
                
                conn.close()
                return model_name
            except:
                # If the specific query fails, try something simpler
                try:
                    conn.close()
                    conn = Pyadomd(self.conn_str)
                    conn.open()
                    model_name = conn.connection.Database
                    conn.close()
                    return model_name
                except:
                    conn.close()
                    return "Connected to Power BI (model name unavailable)"
        except Exception as e:
            logging.warning(f"Failed to get model info: {e}")
            return None

    def get_columns_for_table(self, table_name):
        """Get all columns for a specific table"""
        try:
            from pyadomd import Pyadomd
            conn = Pyadomd(self.conn_str)
            conn.open()
            cursor = conn.cursor()
            
            # Use a simpler and more direct approach to get columns for a table
            query = f"""
                EVALUATE
                FILTER(
                    SELECTCOLUMNS(INFO.VIEW.COLUMNS(), "Column", [Name], "TableName", [Table]),
                    [TableName] = "{table_name}"
                )
            """
            
            logging.info(f"Executing DAX query to get columns for table {table_name}: {query}")
            results = cursor.execute(query)
            df = pd.DataFrame(results.fetchall(), columns=["Column", "TableName"])
            
            # Only return the Column names
            return df["Column"].tolist()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch columns for table {table_name}: {e}")
        finally:
            try:
                conn.close()
            except:
                pass
