# utils/io_json.py

import pandas as pd
import json
import os
import logging
from utils.io_excel import validate_grouping_data

logger = logging.getLogger(__name__)

def read_groupings_json(file_path):
    """
    Read groupings from a JSON file.
    Returns the data as a pandas DataFrame.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        Tuple of (DataFrame, message)
    """
    try:
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
            
        # Read JSON file
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        # Convert to DataFrame
        if isinstance(data, list):
            # Simple array of objects
            df = pd.DataFrame(data)
        elif isinstance(data, dict) and 'records' in data:
            # JSON with records key
            df = pd.DataFrame(data['records'])
        elif isinstance(data, dict) and 'data' in data:
            # JSON with data key
            df = pd.DataFrame(data['data'])
        else:
            return None, "Invalid JSON format - expected array of objects or object with 'records'/'data' key"
        
        # Validate the data
        valid, message = validate_grouping_data(df)
        if not valid:
            return None, message
            
        logger.info(f"Successfully read {len(df)} records from {file_path}")
        return df, f"Successfully read {len(df)} records"
        
    except json.JSONDecodeError as e:
        logger.error(f"JSON parsing error in {file_path}: {str(e)}")
        return None, f"Invalid JSON format: {str(e)}"
    except Exception as e:
        logger.error(f"Error reading JSON file {file_path}: {str(e)}")
        return None, f"Error reading JSON file: {str(e)}"

def write_groupings_json(df, file_path, orient='records', indent=2):
    """
    Write groupings to a JSON file.
    
    Args:
        df: DataFrame containing grouping data
        file_path: Path where the JSON file will be saved
        orient: JSON orientation (default: 'records')
        indent: JSON indentation (default: 2)
        
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
        
        # Convert to JSON
        json_data = df.to_json(orient=orient, indent=indent)
        
        # Write to file
        with open(file_path, 'w') as f:
            f.write(json_data)
        
        logger.info(f"Successfully wrote {len(df)} records to {file_path}")
        return True, f"Successfully wrote {len(df)} records"
        
    except Exception as e:
        logger.error(f"Error writing JSON file {file_path}: {str(e)}")
        return False, f"Error writing JSON file: {str(e)}" 