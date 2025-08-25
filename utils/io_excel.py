# utils/io_excel.py

import pandas as pd
import os
import logging

logger = logging.getLogger(__name__)

def validate_grouping_data(df):
    """
    Validate that the dataframe has the required columns for grouping data.
    Returns a tuple (valid, message) where valid is a boolean and message explains any issues.
    """
    required_columns = {'Instrument ID', 'First Group', 'Second Group', 'Third Group'}
    
    # Check if all required columns exist
    missing_columns = required_columns - set(df.columns)
    if missing_columns:
        return False, f"Missing required columns: {', '.join(missing_columns)}"
    
    # Check if Instrument ID is unique
    if df['Instrument ID'].duplicated().any():
        return False, "Instrument ID column contains duplicate values"
    
    # Check for null Instrument IDs
    if df['Instrument ID'].isnull().any():
        return False, "Instrument ID column contains null values"
    
    return True, "Data is valid"

def read_groupings_excel(file_path, sheet_name=0):
    """
    Read groupings from an Excel file.
    Returns the data as a pandas DataFrame.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name or index of the sheet (default: 0 for first sheet)
        
    Returns:
        Tuple of (DataFrame, message)
    """
    try:
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
            
        # Read Excel file
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        
        # Validate the data
        valid, message = validate_grouping_data(df)
        if not valid:
            return None, message
            
        # Clean up column names (trim whitespace)
        df.columns = df.columns.str.strip()
        
        logger.info(f"Successfully read {len(df)} records from {file_path}")
        return df, f"Successfully read {len(df)} records"
        
    except Exception as e:
        logger.error(f"Error reading Excel file {file_path}: {str(e)}")
        return None, f"Error reading Excel file: {str(e)}"

def write_groupings_excel(df, file_path, sheet_name="Groupings"):
    """
    Write groupings to an Excel file.
    
    Args:
        df: DataFrame containing grouping data
        file_path: Path where the Excel file will be saved
        sheet_name: Name of the sheet (default: "Groupings")
        
    Returns:
        Tuple of (success, message)
    """
    try:
        # Validate the data
        valid, message = validate_grouping_data(df)
        if not valid:
            return False, message
            
        # Ensure the directory exists
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        
        # Write to Excel
        df.to_excel(file_path, sheet_name=sheet_name, index=False)
        
        logger.info(f"Successfully wrote {len(df)} records to {file_path}")
        return True, f"Successfully wrote {len(df)} records"
        
    except Exception as e:
        logger.error(f"Error writing Excel file {file_path}: {str(e)}")
        return False, f"Error writing Excel file: {str(e)}" 