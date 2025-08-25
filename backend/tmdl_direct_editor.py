# backend/tmdl_direct_editor.py

import os
import sys
import json
import shutil
import logging
import pandas as pd
import tempfile
import zipfile
from pathlib import Path

# Add project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def extract_pbip_file(pbip_path):
    """
    Extract contents of a .pbip file (which is essentially a zip file)
    
    Args:
        pbip_path: Path to the .pbip file
        
    Returns:
        Path to the temporary directory containing extracted files
    """
    temp_dir = os.path.join(tempfile.gettempdir(), "pbip_extract")
    
    # Create clean temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    
    # Extract the PBIP file (it's a zip file)
    with zipfile.ZipFile(pbip_path, 'r') as zip_ref:
        zip_ref.extractall(temp_dir)
    
    logging.info(f"Extracted PBIP file to: {temp_dir}")
    return temp_dir

def find_tmdl_model_file(extract_dir):
    """
    Find the main TMDL model file in the extracted PBIP contents
    
    Args:
        extract_dir: Directory containing extracted PBIP contents
        
    Returns:
        Path to the model.tmdl file
    """
    # Look for model.tmdl or similar file
    for root, dirs, files in os.walk(extract_dir):
        for file in files:
            if file.endswith('.tmdl'):
                tmdl_path = os.path.join(root, file)
                logging.info(f"Found TMDL file: {tmdl_path}")
                return tmdl_path
    
    raise FileNotFoundError("No .tmdl file found in the extracted PBIP contents")

def parse_tmdl_file(tmdl_path):
    """
    Parse the TMDL file and return its content as a dictionary
    
    Args:
        tmdl_path: Path to the TMDL file
        
    Returns:
        Dictionary representing the TMDL model
    """
    with open(tmdl_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # TMDL files are JSON with comments, so we need to parse it carefully
    # For simplicity, we're using json.loads, but in a production environment,
    # you might want to use a more robust JSON with comments parser
    try:
        model_data = json.loads(content)
        return model_data
    except json.JSONDecodeError as e:
        logging.error(f"Failed to parse TMDL file: {e}")
        raise

def update_instrument_groupings(model_data, groupings_df):
    """
    Update the InstrumentGroupings table in the TMDL model
    
    Args:
        model_data: Dictionary representing the TMDL model
        groupings_df: DataFrame containing the groupings data
        
    Returns:
        Updated model_data dictionary
    """
    # Find the InstrumentGroupings table in the model
    target_table = None
    
    if 'model' not in model_data or 'tables' not in model_data['model']:
        raise ValueError("Invalid TMDL model structure: 'model' or 'tables' not found")
    
    for table in model_data['model']['tables']:
        if table.get('name') == 'InstrumentGroupings':
            target_table = table
            break
    
    if not target_table:
        logging.warning("InstrumentGroupings table not found in the model")
        # Create the table if it doesn't exist
        new_table = {
            "name": "InstrumentGroupings",
            "columns": [
                {"name": "Instrument ID", "dataType": "string"},
                {"name": "First Group", "dataType": "string"},
                {"name": "Second Group", "dataType": "string"},
                {"name": "Third Group", "dataType": "string"}
            ],
            "partitions": [
                {
                    "name": "InstrumentGroupings",
                    "source": {
                        "type": "m",
                        "expression": [
                            "let",
                            "    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText(\"\", BinaryEncoding.Base64), Compression.Deflate)), {\"Instrument ID\", \"First Group\", \"Second Group\", \"Third Group\"})",
                            "in",
                            "    Source"
                        ]
                    }
                }
            ]
        }
        model_data['model']['tables'].append(new_table)
        target_table = new_table
    
    # Convert DataFrame to rows for TMDL format
    rows_json = []
    for _, row in groupings_df.iterrows():
        rows_json.append([
            row.get('Instrument ID', ''),
            row.get('First Group', ''),
            row.get('Second Group', ''),
            row.get('Third Group', '')
        ])
    
    # Convert rows to TMDL partition expression format
    import zlib
    import base64
    
    # Convert rows to JSON string
    rows_json_str = json.dumps(rows_json)
    
    # Compress and encode
    compressed = zlib.compress(rows_json_str.encode('utf-8'))
    b64_encoded = base64.b64encode(compressed).decode('utf-8')
    
    # Update the partition expression
    for partition in target_table.get('partitions', []):
        if partition.get('name') == 'InstrumentGroupings':
            if 'source' in partition and 'expression' in partition['source']:
                # Replace the expression with our new encoded data
                partition['source']['expression'] = [
                    "let",
                    f"    Source = Table.FromRows(Json.Document(Binary.Decompress(Binary.FromText(\"{b64_encoded}\", BinaryEncoding.Base64), Compression.Deflate)), {{\"Instrument ID\", \"First Group\", \"Second Group\", \"Third Group\"}})",
                    "in",
                    "    Source"
                ]
    
    return model_data

def write_tmdl_file(model_data, tmdl_path):
    """
    Write the updated model data back to the TMDL file
    
    Args:
        model_data: Dictionary representing the TMDL model
        tmdl_path: Path to the TMDL file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a backup
        backup_path = f"{tmdl_path}.bak"
        shutil.copy2(tmdl_path, backup_path)
        logging.info(f"Created backup at: {backup_path}")
        
        # Write the updated model
        with open(tmdl_path, 'w', encoding='utf-8') as f:
            json.dump(model_data, f, indent=2)
        
        logging.info(f"Successfully wrote updated TMDL file: {tmdl_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to write TMDL file: {e}")
        return False

def repack_pbip_file(extract_dir, pbip_path):
    """
    Re-pack the updated TMDL files back into the PBIP file
    
    Args:
        extract_dir: Directory containing the extracted and modified files
        pbip_path: Path to the original PBIP file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Create a backup of the original PBIP file
        backup_path = f"{pbip_path}.bak"
        shutil.copy2(pbip_path, backup_path)
        logging.info(f"Created backup of PBIP file at: {backup_path}")
        
        # Create a new zip file with the updated contents
        with zipfile.ZipFile(pbip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(extract_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    # Get relative path for the zip file
                    rel_path = os.path.relpath(file_path, extract_dir)
                    zipf.write(file_path, rel_path)
        
        logging.info(f"Successfully repacked PBIP file: {pbip_path}")
        return True
    except Exception as e:
        logging.error(f"Failed to repack PBIP file: {e}")
        # Restore backup if something went wrong
        try:
            if os.path.exists(backup_path):
                shutil.copy2(backup_path, pbip_path)
                logging.info(f"Restored backup PBIP file after error")
        except:
            pass
        return False

def update_pbip_groupings(pbip_path, df: pd.DataFrame):
    """
    Main function to update groupings directly in a PBIP file
    
    Args:
        pbip_path: Path to the PBIP file
        df: DataFrame containing the groupings data
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Validate inputs
        if not os.path.exists(pbip_path):
            raise FileNotFoundError(f"PBIP file not found: {pbip_path}")
        
        if not pbip_path.lower().endswith('.pbip'):
            raise ValueError("File must be a .pbip file")
        
        if df.empty:
            raise ValueError("Groupings data is empty")
        
        # Required columns
        required_cols = ['Instrument ID', 'First Group', 'Second Group', 'Third Group']
        if not all(col in df.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Need: {required_cols}")
        
        # Extract PBIP file
        extract_dir = extract_pbip_file(pbip_path)
        
        # Find TMDL model file
        tmdl_path = find_tmdl_model_file(extract_dir)
        
        # Parse TMDL
        model_data = parse_tmdl_file(tmdl_path)
        
        # Update the model with new groupings
        updated_model = update_instrument_groupings(model_data, df)
        
        # Write back to TMDL file
        success = write_tmdl_file(updated_model, tmdl_path)
        if not success:
            raise Exception("Failed to write TMDL file")
        
        # Repack into PBIP
        success = repack_pbip_file(extract_dir, pbip_path)
        if not success:
            raise Exception("Failed to repack PBIP file")
        
        # Clean up temp directory
        try:
            shutil.rmtree(extract_dir)
        except:
            logging.warning(f"Failed to clean up temp directory: {extract_dir}")
        
        logging.info(f"Successfully updated groupings in PBIP file: {pbip_path}")
        return True
        
    except Exception as e:
        logging.error(f"Failed to update PBIP file: {e}")
        return False

def extract_groupings_from_pbip(pbip_path):
    """
    Extract the instrument groupings data from a PBIP file
    
    Args:
        pbip_path: Path to the PBIP file
        
    Returns:
        DataFrame containing the groupings data or None if extraction fails or no groupings found
    """
    try:
        # Validate inputs
        if not os.path.exists(pbip_path):
            raise FileNotFoundError(f"PBIP file not found: {pbip_path}")
        
        if not pbip_path.lower().endswith('.pbip'):
            raise ValueError("File must be a .pbip file")
        
        logging.info(f"Extracting groupings from PBIP file: {pbip_path}")
        
        # Extract PBIP file
        extract_dir = extract_pbip_file(pbip_path)
        
        # Find TMDL model file
        tmdl_path = find_tmdl_model_file(extract_dir)
        
        # Parse TMDL
        model_data = parse_tmdl_file(tmdl_path)
        
        # Find the InstrumentGroupings table in the model
        target_table = None
        
        if 'model' not in model_data or 'tables' not in model_data['model']:
            logging.warning("Invalid TMDL model structure: 'model' or 'tables' not found")
            return None
        
        for table in model_data['model']['tables']:
            if table.get('name') == 'InstrumentGroupings':
                target_table = table
                break
        
        if not target_table:
            logging.warning("InstrumentGroupings table not found in the model")
            return None
        
        # Extract data from the partition expression
        import zlib
        import base64
        import re
        
        # Find the partition with the data
        for partition in target_table.get('partitions', []):
            if partition.get('name') == 'InstrumentGroupings':
                if 'source' in partition and 'expression' in partition['source']:
                    expressions = partition['source']['expression']
                    
                    # Find the expression containing Binary.FromText
                    b64_data = None
                    for expr in expressions:
                        # Look for the encoded data
                        match = re.search(r'Binary\.FromText\("([^"]+)"', expr)
                        if match:
                            b64_data = match.group(1)
                            break
                    
                    if b64_data:
                        try:
                            # Decode and decompress
                            binary_data = base64.b64decode(b64_data)
                            decompressed = zlib.decompress(binary_data)
                            json_str = decompressed.decode('utf-8')
                            
                            # Parse JSON
                            rows = json.loads(json_str)
                            
                            # Create DataFrame from rows
                            columns = ["Instrument ID", "First Group", "Second Group", "Third Group"]
                            df = pd.DataFrame(rows, columns=columns)
                            
                            logging.info(f"Successfully extracted {len(df)} groupings from PBIP file")
                            
                            # Clean up temp directory
                            try:
                                shutil.rmtree(extract_dir)
                            except:
                                logging.warning(f"Failed to clean up temp directory: {extract_dir}")
                                
                            return df
                        except Exception as e:
                            logging.error(f"Failed to decode/decompress data: {e}")
                            return None
        
        # If we reach here, we didn't find the data
        logging.warning("No groupings data found in the model")
        
        # Clean up temp directory
        try:
            shutil.rmtree(extract_dir)
        except:
            logging.warning(f"Failed to clean up temp directory: {extract_dir}")
            
        return None
        
    except Exception as e:
        logging.error(f"Failed to extract groupings from PBIP file: {e}")
        return None

# Standalone test function
def test_update_pbip(pbip_path=None):
    """Test the PBIP update functionality with sample data"""
    if not pbip_path:
        print("Please provide a path to a .pbip file:")
        pbip_path = input("> ").strip()
    
    # Create sample groupings DataFrame
    data = [
        {'Instrument ID': 'BOND1001', 'First Group': 'Government', 'Second Group': 'Treasury', 'Third Group': 'US'},
        {'Instrument ID': 'BOND1002', 'First Group': 'Government', 'Second Group': 'Treasury', 'Third Group': 'UK'},
        {'Instrument ID': 'BOND1003', 'First Group': 'Government', 'Second Group': 'Agency', 'Third Group': 'US'},
        {'Instrument ID': 'BOND1004', 'First Group': 'Corporate', 'Second Group': 'Financial', 'Third Group': 'Banking'},
        {'Instrument ID': 'BOND1005', 'First Group': 'Corporate', 'Second Group': 'Financial', 'Third Group': 'Insurance'},
    ]
    
    df = pd.DataFrame(data)
    print(f"Updating PBIP file with {len(df)} groupings...")
    
    success = update_pbip_groupings(pbip_path, df)
    
    if success:
        print(f"✅ PBIP file updated successfully: {pbip_path}")
    else:
        print(f"❌ Failed to update PBIP file")
    
    return success

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Test with command line argument or prompt
    import sys
    pbip_path = sys.argv[1] if len(sys.argv) > 1 else None
    test_update_pbip(pbip_path) 