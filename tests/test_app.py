#!/usr/bin/env python
# tests/test_app.py

"""
Test script for TMDL Live Editor.

This tests basic functionality of the TMDL Editor without requiring a running Power BI instance.
For testing the full application with live connection, run tmdl_editor_gui.py.
"""

import sys
import os
import unittest
import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import required modules
from utils.io_excel import validate_grouping_data, read_groupings_excel, write_groupings_excel
from utils.io_json import read_groupings_json, write_groupings_json

class TestTMDLEditor(unittest.TestCase):
    """Test cases for TMDL Editor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_data = pd.DataFrame({
            'Instrument ID': ['BOND1001', 'BOND1002', 'BOND1003'],
            'First Group': ['Government', 'Government', 'Corporate'],
            'Second Group': ['Treasury', 'Agency', 'Financial'],
            'Third Group': ['US', 'US', 'Banking']
        })
        
        # Create temp directory if it doesn't exist
        self.test_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'tests', 'temp')
        os.makedirs(self.test_dir, exist_ok=True)
        
        # Define test file paths
        self.json_path = os.path.join(self.test_dir, 'test_groupings.json')
        self.excel_path = os.path.join(self.test_dir, 'test_groupings.xlsx')
    
    def tearDown(self):
        """Clean up temporary files."""
        for path in [self.json_path, self.excel_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass
    
    def test_validate_grouping_data(self):
        """Test validation of grouping data."""
        # Valid data
        valid, message = validate_grouping_data(self.sample_data)
        self.assertTrue(valid, f"Valid data failed validation: {message}")
        
        # Missing column
        df_missing_column = self.sample_data.drop(columns=['Third Group'])
        valid, message = validate_grouping_data(df_missing_column)
        self.assertFalse(valid, "Missing column should fail validation")
        
        # Duplicate Instrument ID
        df_duplicate_id = self.sample_data.copy()
        df_duplicate_id.loc[len(df_duplicate_id)] = df_duplicate_id.loc[0]
        valid, message = validate_grouping_data(df_duplicate_id)
        self.assertFalse(valid, "Duplicate Instrument ID should fail validation")
    
    def test_json_roundtrip(self):
        """Test writing and reading JSON."""
        # Write to JSON
        success, message = write_groupings_json(self.sample_data, self.json_path)
        self.assertTrue(success, f"Failed to write JSON: {message}")
        self.assertTrue(os.path.exists(self.json_path), "JSON file not created")
        
        # Read from JSON
        df, message = read_groupings_json(self.json_path)
        self.assertIsNotNone(df, f"Failed to read JSON: {message}")
        
        # Verify data
        self.assertEqual(len(df), len(self.sample_data), "Row count mismatch after JSON roundtrip")
        pd.testing.assert_frame_equal(
            df.sort_values('Instrument ID').reset_index(drop=True),
            self.sample_data.sort_values('Instrument ID').reset_index(drop=True),
            "Data mismatch after JSON roundtrip"
        )
    
    def test_excel_roundtrip(self):
        """Test writing and reading Excel."""
        # Write to Excel
        success, message = write_groupings_excel(self.sample_data, self.excel_path)
        self.assertTrue(success, f"Failed to write Excel: {message}")
        self.assertTrue(os.path.exists(self.excel_path), "Excel file not created")
        
        # Read from Excel
        df, message = read_groupings_excel(self.excel_path)
        self.assertIsNotNone(df, f"Failed to read Excel: {message}")
        
        # Verify data
        self.assertEqual(len(df), len(self.sample_data), "Row count mismatch after Excel roundtrip")
        pd.testing.assert_frame_equal(
            df.sort_values('Instrument ID').reset_index(drop=True),
            self.sample_data.sort_values('Instrument ID').reset_index(drop=True),
            "Data mismatch after Excel roundtrip"
        )

if __name__ == '__main__':
    unittest.main() 