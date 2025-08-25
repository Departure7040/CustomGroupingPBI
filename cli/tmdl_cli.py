# cli/tmdl_cli.py

import argparse
import sys
import os
import pandas as pd
import logging

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logger
from utils.io_excel import read_groupings_excel, write_groupings_excel
from utils.io_json import read_groupings_json, write_groupings_json
from backend.model_connector import ModelConnector
from backend.tabular_editor_cli import run_tabular_editor
from backend.dax_info_views import DaxMetadataExplorer

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="TMDL Editor CLI - Manage Power BI groupings")
    
    # Main command groups
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get information about the Power BI model")
    info_parser.add_argument("--tables", action="store_true", help="List all tables")
    info_parser.add_argument("--columns", action="store_true", help="List all columns")
    info_parser.add_argument("--relationships", action="store_true", help="List all relationships")
    info_parser.add_argument("--port", type=int, help="Power BI Desktop port (optional, auto-detected if not provided)")
    
    # Import command
    import_parser = subparsers.add_parser("import", help="Import groupings from a file and push to Power BI")
    import_parser.add_argument("file", help="Path to the Excel or JSON file containing groupings")
    import_parser.add_argument("--table", default="InstrumentGroupings", help="Target table name (default: InstrumentGroupings)")
    import_parser.add_argument("--port", type=int, help="Power BI Desktop port (optional)")
    import_parser.add_argument("--sheet", help="Excel sheet name or index (default: 0)")
    import_parser.add_argument("--dry-run", action="store_true", help="Preview changes without applying them")
    
    # Export command
    export_parser = subparsers.add_parser("export", help="Export groupings from Power BI")
    export_parser.add_argument("file", help="Path to save the Excel or JSON file")
    export_parser.add_argument("--table", default="InstrumentGroupings", help="Source table name (default: InstrumentGroupings)")
    export_parser.add_argument("--port", type=int, help="Power BI Desktop port (optional)")
    
    # Compare command
    compare_parser = subparsers.add_parser("compare", help="Compare groupings between file and Power BI")
    compare_parser.add_argument("file", help="Path to the Excel or JSON file containing groupings")
    compare_parser.add_argument("--table", default="InstrumentGroupings", help="Target table name in Power BI (default: InstrumentGroupings)")
    compare_parser.add_argument("--port", type=int, help="Power BI Desktop port (optional)")
    compare_parser.add_argument("--output", help="Path to save comparison results (optional)")
    
    # Format conversion
    convert_parser = subparsers.add_parser("convert", help="Convert between Excel and JSON formats")
    convert_parser.add_argument("input", help="Input file path (Excel or JSON)")
    convert_parser.add_argument("output", help="Output file path (Excel or JSON)")
    
    # Common options
    parser.add_argument("--verbose", "-v", action="store_true", help="Enable verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Suppress all output except errors")
    parser.add_argument("--log-file", help="Path to log file")
    
    return parser.parse_args()

def detect_file_type(file_path):
    """Detect file type (excel or json) from extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.xlsx', '.xls']:
        return 'excel'
    elif ext == '.json':
        return 'json'
    else:
        raise ValueError(f"Unsupported file type: {ext}")

def read_file(file_path, sheet_name=0):
    """Read data from Excel or JSON file."""
    file_type = detect_file_type(file_path)
    
    if file_type == 'excel':
        df, message = read_groupings_excel(file_path, sheet_name)
    elif file_type == 'json':
        df, message = read_groupings_json(file_path)
    else:
        return None, f"Unsupported file type: {file_type}"
        
    return df, message

def write_file(df, file_path):
    """Write data to Excel or JSON file."""
    file_type = detect_file_type(file_path)
    
    if file_type == 'excel':
        success, message = write_groupings_excel(df, file_path)
    elif file_type == 'json':
        success, message = write_groupings_json(df, file_path)
    else:
        return False, f"Unsupported file type: {file_type}"
        
    return success, message

def execute_info_command(args, logger):
    """Execute the info command."""
    try:
        # Connect to Power BI
        connector = ModelConnector()
        if args.port:
            port = args.port
            logger.info(f"Using specified port: {port}")
        else:
            port = connector.detect_port()
            logger.info(f"Detected Power BI port: {port}")
        
        # Initialize metadata explorer
        explorer = DaxMetadataExplorer()
        
        if args.tables:
            # Display tables
            tables = explorer.get_tables()
            print(f"\nTables in model ({len(tables)}):")
            print("="*80)
            for idx, row in tables.iterrows():
                hidden = " (Hidden)" if row['IsHidden'] else ""
                rows = f", Rows: {row['RowCount']}" if not pd.isna(row['RowCount']) else ""
                print(f"{idx+1}. {row['Table']}{hidden}{rows}")
                if not pd.isna(row['Description']) and row['Description']:
                    print(f"   Description: {row['Description']}")
        
        if args.columns:
            # Display columns
            columns = explorer.get_columns()
            print(f"\nColumns in model ({len(columns)}):")
            print("="*80)
            current_table = None
            for idx, row in columns.iterrows():
                if current_table != row['Table']:
                    current_table = row['Table']
                    print(f"\n[Table: {current_table}]")
                
                hidden = " (Hidden)" if row['IsHidden'] else ""
                data_type = f", Type: {row['DataType']}" if not pd.isna(row['DataType']) else ""
                print(f"  - {row['Column']}{hidden}{data_type}")
                
        if args.relationships:
            # Display relationships
            relationships = explorer.get_relationships()
            print(f"\nRelationships in model ({len(relationships)}):")
            print("="*80)
            for idx, row in relationships.iterrows():
                active = " (Inactive)" if not row['IsActive'] else ""
                print(f"{idx+1}. {row['FromTable']}[{row['FromColumn']}] → {row['ToTable']}[{row['ToColumn']}]{active}")
                print(f"   Cross Filter: {row['CrossFilteringBehavior']}")
        
        # If no specific info requested, show a summary
        if not (args.tables or args.columns or args.relationships):
            tables = explorer.get_tables()
            columns = explorer.get_columns()
            relationships = explorer.get_relationships()
            
            print("\nPower BI Model Summary:")
            print("="*80)
            print(f"Tables: {len(tables)}")
            print(f"Columns: {len(columns)}")
            print(f"Relationships: {len(relationships)}")
            print("\nUse --tables, --columns, or --relationships for detailed info.")
        
        logger.info("Info command completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error executing info command: {str(e)}")
        print(f"Error: {str(e)}")
        return False

def execute_import_command(args, logger):
    """Execute the import command."""
    try:
        # Read the data from file
        logger.info(f"Reading data from {args.file}")
        sheet = args.sheet if args.sheet else 0
        df, message = read_file(args.file, sheet)
        
        if df is None:
            logger.error(f"Failed to read data: {message}")
            print(f"Error: {message}")
            return False
        
        logger.info(f"Successfully read {len(df)} records from {args.file}")
        print(f"Read {len(df)} records from {args.file}")
        
        if args.dry_run:
            # Preview the import without pushing to Power BI
            logger.info("Dry run mode - not pushing to Power BI")
            print("\nPreview of data (first 5 rows):")
            print(df.head(5).to_string())
            print(f"\nTotal records to import: {len(df)}")
            print("DRY RUN - No changes made to Power BI model")
            return True
        
        # Push to Power BI
        logger.info(f"Pushing data to Power BI table: {args.table}")
        print(f"Pushing {len(df)} records to Power BI table: {args.table}")
        
        # Get port if specified
        port = args.port if args.port else None
        
        # Run the tabular editor CLI
        success = run_tabular_editor(args.table, df, port)
        
        if success:
            logger.info("Successfully pushed data to Power BI")
            print("Successfully pushed data to Power BI")
            return True
        else:
            logger.error("Failed to push data to Power BI")
            print("Error: Failed to push data to Power BI")
            return False
        
    except Exception as e:
        logger.error(f"Error executing import command: {str(e)}")
        print(f"Error: {str(e)}")
        return False

def execute_export_command(args, logger):
    """Execute the export command."""
    try:
        # Connect to Power BI
        connector = ModelConnector()
        if args.port:
            port = args.port
            logger.info(f"Using specified port: {port}")
        else:
            port = connector.detect_port()
            logger.info(f"Detected Power BI port: {port}")
        
        # Initialize metadata explorer
        explorer = DaxMetadataExplorer()
        
        # Query the table
        connection_string = f"Provider=MSOLAP;Data Source=localhost:{port}"
        explorer = DaxMetadataExplorer(connection_string)
        
        # Build DAX query to get table data
        query = f"EVALUATE '{args.table}'"
        
        # Execute query and get data
        logger.info(f"Querying table: {args.table}")
        print(f"Exporting data from table: {args.table}")
        
        try:
            conn = explorer.connect()
            cursor = conn.cursor()
            results = cursor.execute(query)
            df = pd.DataFrame(results.fetchall())
            
            if len(df) == 0:
                logger.warning(f"No data found in table: {args.table}")
                print(f"Warning: No data found in table: {args.table}")
                return False
                
            # Set column names from the results
            if hasattr(results, 'description'):
                df.columns = [col[0] for col in results.description]
            
            # Write to file
            logger.info(f"Writing {len(df)} records to {args.file}")
            print(f"Writing {len(df)} records to {args.file}")
            
            success, message = write_file(df, args.file)
            
            if success:
                logger.info(f"Successfully exported data: {message}")
                print(f"Successfully exported data: {message}")
                return True
            else:
                logger.error(f"Failed to export data: {message}")
                print(f"Error: {message}")
                return False
                
        except Exception as e:
            logger.error(f"Error querying Power BI: {str(e)}")
            print(f"Error querying Power BI: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Error executing export command: {str(e)}")
        print(f"Error: {str(e)}")
        return False

def execute_convert_command(args, logger):
    """Execute the convert command."""
    try:
        # Read input file
        logger.info(f"Reading data from {args.input}")
        df, message = read_file(args.input)
        
        if df is None:
            logger.error(f"Failed to read data: {message}")
            print(f"Error: {message}")
            return False
        
        logger.info(f"Successfully read {len(df)} records from {args.input}")
        print(f"Read {len(df)} records from {args.input}")
        
        # Write to output file
        logger.info(f"Writing {len(df)} records to {args.output}")
        print(f"Converting to {args.output}")
        
        success, message = write_file(df, args.output)
        
        if success:
            logger.info(f"Successfully converted data: {message}")
            print(f"Successfully converted data: {message}")
            return True
        else:
            logger.error(f"Failed to convert data: {message}")
            print(f"Error: {message}")
            return False
        
    except Exception as e:
        logger.error(f"Error executing convert command: {str(e)}")
        print(f"Error: {str(e)}")
        return False

def execute_compare_command(args, logger):
    """Execute the compare command."""
    try:
        # Read the data from file
        logger.info(f"Reading data from {args.file}")
        df_file, message = read_file(args.file)
        
        if df_file is None:
            logger.error(f"Failed to read data from file: {message}")
            print(f"Error: {message}")
            return False
        
        logger.info(f"Successfully read {len(df_file)} records from {args.file}")
        print(f"Read {len(df_file)} records from {args.file}")
        
        # Connect to Power BI
        connector = ModelConnector()
        if args.port:
            port = args.port
            logger.info(f"Using specified port: {port}")
        else:
            port = connector.detect_port()
            logger.info(f"Detected Power BI port: {port}")
        
        # Query the table
        connection_string = f"Provider=MSOLAP;Data Source=localhost:{port}"
        explorer = DaxMetadataExplorer(connection_string)
        
        # Build DAX query to get table data
        query = f"EVALUATE '{args.table}'"
        
        # Execute query and get data
        logger.info(f"Querying table: {args.table}")
        print(f"Comparing with data from table: {args.table}")
        
        try:
            conn = explorer.connect()
            cursor = conn.cursor()
            results = cursor.execute(query)
            df_model = pd.DataFrame(results.fetchall())
            
            if len(df_model) == 0:
                logger.warning(f"No data found in Power BI table: {args.table}")
                print(f"Warning: No data found in Power BI table: {args.table}")
                return False
                
            # Set column names from the results
            if hasattr(results, 'description'):
                df_model.columns = [col[0] for col in results.description]
            
            # Compare data
            logger.info("Comparing data...")
            print("\nComparison Summary:")
            print("="*80)
            
            # Check for differences in number of records
            print(f"Records in file: {len(df_file)}")
            print(f"Records in Power BI: {len(df_model)}")
            
            # Compare specific records if both have Instrument ID column
            if 'Instrument ID' in df_file.columns and 'Instrument ID' in df_model.columns:
                # Find IDs that exist in file but not in model
                file_ids = set(df_file['Instrument ID'])
                model_ids = set(df_model['Instrument ID'])
                
                only_in_file = file_ids - model_ids
                only_in_model = model_ids - file_ids
                
                print(f"Instruments only in file: {len(only_in_file)}")
                print(f"Instruments only in Power BI: {len(only_in_model)}")
                
                # Find records with different values
                common_ids = file_ids.intersection(model_ids)
                
                # Compare common IDs
                changes = []
                for id in common_ids:
                    file_row = df_file[df_file['Instrument ID'] == id].iloc[0]
                    model_row = df_model[df_model['Instrument ID'] == id].iloc[0]
                    
                    for col in df_file.columns:
                        if col in df_model.columns and col != 'Instrument ID':
                            file_val = str(file_row[col])
                            model_val = str(model_row[col])
                            
                            if file_val != model_val:
                                changes.append({
                                    'Instrument ID': id,
                                    'Column': col,
                                    'File Value': file_val,
                                    'Model Value': model_val
                                })
                
                print(f"Records with differences: {len(set(change['Instrument ID'] for change in changes))}")
                print(f"Total field differences: {len(changes)}")
                
                # Show some examples of differences
                if changes:
                    print("\nExample differences:")
                    for i, change in enumerate(changes[:5]):  # Show first 5 differences
                        print(f"{i+1}. Instrument {change['Instrument ID']} - {change['Column']}:")
                        print(f"   File: '{change['File Value']}'")
                        print(f"   Model: '{change['Model Value']}'")
                    
                    if len(changes) > 5:
                        print(f"... and {len(changes) - 5} more differences")
                
                # Save comparison results if requested
                if args.output:
                    # Create a comparison DataFrame
                    comparison_df = pd.DataFrame(changes)
                    
                    # Write to file
                    logger.info(f"Writing comparison to {args.output}")
                    print(f"\nWriting detailed comparison to {args.output}")
                    
                    success, message = write_file(comparison_df, args.output)
                    
                    if success:
                        logger.info(f"Successfully wrote comparison: {message}")
                        print(f"Successfully wrote comparison: {message}")
                    else:
                        logger.error(f"Failed to write comparison: {message}")
                        print(f"Error: {message}")
            
            return True
                
        except Exception as e:
            logger.error(f"Error comparing data: {str(e)}")
            print(f"Error comparing data: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Error executing compare command: {str(e)}")
        print(f"Error: {str(e)}")
        return False

def main():
    """Main entry point for the CLI."""
    args = parse_args()
    
    # Set up logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    if args.quiet:
        log_level = logging.ERROR
    
    logger = setup_logger(args.log_file, console_level=log_level)
    logger.info(f"Starting TMDL Editor CLI with command: {args.command}")
    
    # Execute the appropriate command
    success = False
    try:
        if args.command == "info":
            success = execute_info_command(args, logger)
        elif args.command == "import":
            success = execute_import_command(args, logger)
        elif args.command == "export":
            success = execute_export_command(args, logger)
        elif args.command == "convert":
            success = execute_convert_command(args, logger)
        elif args.command == "compare":
            success = execute_compare_command(args, logger)
        else:
            logger.error(f"Unknown command: {args.command}")
            print(f"Error: Unknown command '{args.command}'")
            print("Run with --help for usage information")
            success = False
    except Exception as e:
        logger.exception(f"Unhandled exception: {str(e)}")
        print(f"Error: {str(e)}")
        success = False
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 