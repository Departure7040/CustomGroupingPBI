#!/usr/bin/env python
# tests/run_tests.py

"""
Run all tests for the TMDL Live Editor.
"""

import unittest
import os
import sys

def run_tests():
    """Run all tests in the tests directory."""
    # Get the current directory (tests)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Add parent directory to path for imports
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)
    
    # Discover and run tests
    test_suite = unittest.defaultTestLoader.discover(
        current_dir,
        pattern='test_*.py'
    )
    
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return 0 if successful, 1 if failures
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests()) 