# backend/model_updater.py

from pyadomd import Pyadomd
import pandas as pd
import clr
import os
import sys
from backend.model_connector import ModelConnector

ADOMD_DLL_PATH = r"C:\Program Files\Microsoft.NET\ADOMD.NET\160\Microsoft.AnalysisServices.AdomdClient.dll"

if not os.path.exists(ADOMD_DLL_PATH):
    print("AdomdClient DLL missing. Cannot continue.")
    sys.exit(1)

clr.AddReference(ADOMD_DLL_PATH)
from Microsoft.AnalysisServices.AdomdClient import AdomdConnection

# Use dynamic port detection
def get_connection_string():
    try:
        connector = ModelConnector()
        port = connector.detect_port()
        return f"Provider=MSOLAP;Data Source=localhost:{port}"
    except Exception as e:
        print(f"Warning: Failed to detect Power BI port: {e}")
        # Fallback to a default port if detection fails
        return "Provider=MSOLAP;Data Source=localhost:49999"

def connect(conn_str=None):
    if conn_str is None:
        conn_str = get_connection_string()
    
    try:
        conn = Pyadomd(conn_str)
        conn.open()
        return conn
    except Exception as e:
        print(f"Connection failed: {e}")
        return None

def preview_changes(df: pd.DataFrame):
    print("\n=== Previewing Grouping Changes ===")
    print(df.head(10))
    print(f"\nTotal records: {len(df)}\n")

def build_update_script(df: pd.DataFrame, table_name="InstrumentGroupings"):
    """
    Build Tabular Model scripting logic to replace or update table data.
    Note: This will later be upgraded to full TMDL JSON output or integrated with Tabular Editor CLI.
    """
    script = "EVALUATE\nUNION(\n"

    rows = []
    for _, row in df.iterrows():
        row_expr = f"ROW(\"Instrument ID\", \"{row['Instrument ID']}\", " \
                   f"\"First Group\", \"{row['First Group']}\", " \
                   f"\"Second Group\", \"{row['Second Group']}\", " \
                   f"\"Third Group\", \"{row['Third Group']}\")"
        rows.append(row_expr)

    script += ",\n".join(rows)
    script += "\n)"

    return script

def push_groupings(df: pd.DataFrame, table_name="InstrumentGroupings", conn_str=None):
    """
    This simulates pushing data into a model by previewing the table and preparing the TMSL-style logic.
    Full push will require Tabular Editor CLI or TOM.
    """
    conn = connect(conn_str)
    if not conn:
        return False

    try:
        preview_changes(df)
        dax_script = build_update_script(df, table_name)

        print("\n=== DAX Query to Inject into Power BI Model ===")
        print(dax_script[:1000] + ("..." if len(dax_script) > 1000 else ""))  # Preview only

        # Actual push requires either:
        # - Tabular Editor CLI scripting
        # - Analysis Services TMSL API (which requires .NET or COM interop)
        # This is a placeholder for eventual integration

        print("\n[NOTE] Push not executed: Use Tabular Editor CLI for model mutation.\n")
        return True

    except Exception as e:
        print(f"Failed to prepare update: {e}")
        return False
