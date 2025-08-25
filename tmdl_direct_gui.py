#!/usr/bin/env python
# tmdl_direct_gui.py

"""
TMDL Direct Editor
A local Python desktop application for directly modifying the TMDL files inside PBIP format Power BI files.
This bypasses the XMLA endpoint and directly modifies the files.
"""

import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QFileDialog, QStatusBar,
    QSplitter, QAction, QMenu, QToolBar
)
from PyQt5.QtCore import Qt

# Add the project root to the path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Import application components
from utils.logger import setup_logger
from gui.grouping_editor import GroupingEditor
from backend.tmdl_direct_editor import update_pbip_groupings, extract_groupings_from_pbip

class TMDLDirectEditorWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMDL Direct Editor (PBIP Edition)")
        self.resize(1000, 700)
        
        # File path for the current PBIP file
        self.pbip_file_path = None
        
        # Create UI components
        self.create_ui()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - No PBIP file loaded")

    def create_ui(self):
        """Create the main UI components"""
        # Create central widget and layout
        self.central_widget = QWidget()
        self.main_layout = QVBoxLayout()
        
        # Create toolbar
        self.create_toolbar()
        
        # Create menu bar
        self.create_menu()
        
        # Button layout at top
        button_layout = QHBoxLayout()
        
        # Open PBIP button
        self.open_button = QPushButton("Open PBIP File")
        self.open_button.clicked.connect(self.open_pbip_file)
        button_layout.addWidget(self.open_button)
        
        # Add a prominent Demo Mode button
        self.demo_button = QPushButton("Demo Mode")
        self.demo_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.demo_button.setToolTip("Load sample data for demonstration purposes")
        self.demo_button.clicked.connect(self.load_demo_data)
        button_layout.addWidget(self.demo_button)
        
        # Save changes button
        self.save_button = QPushButton("Save Changes to PBIP")
        self.save_button.clicked.connect(self.save_to_pbip)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)
        
        # Add button layout to main layout
        self.main_layout.addLayout(button_layout)
        
        # File info label
        self.file_info = QLabel("No PBIP file loaded")
        self.file_info.setStyleSheet("font-weight: bold; color: #555;")
        self.file_info.setAlignment(Qt.AlignCenter)
        self.main_layout.addWidget(self.file_info)
        
        # Demo notice - only shown when in demo mode
        self.demo_notice = QLabel("DEMO MODE: Using sample data - changes will not affect any PBIP file")
        self.demo_notice.setStyleSheet("background-color: #FFF3CD; color: #856404; padding: 5px; border-radius: 3px;")
        self.demo_notice.setAlignment(Qt.AlignCenter)
        self.demo_notice.setVisible(False)
        self.main_layout.addWidget(self.demo_notice)
        
        # Main editing area
        self.grouping_editor = GroupingEditor()
        self.main_layout.addWidget(self.grouping_editor)
        
        # Set the central widget layout
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
        
        # Update UI state
        self.update_ui_state()

    def create_toolbar(self):
        """Create the main toolbar"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # Add toolbar actions
        self.open_action = QAction("Open PBIP", self)
        self.open_action.setStatusTip("Open a PBIP file")
        self.open_action.triggered.connect(self.open_pbip_file)
        self.toolbar.addAction(self.open_action)
        
        # Add demo mode action
        self.demo_action = QAction("Demo Mode", self)
        self.demo_action.setStatusTip("Load sample data for demonstration")
        self.demo_action.triggered.connect(self.load_demo_data)
        self.toolbar.addAction(self.demo_action)
        
        self.toolbar.addSeparator()
        
        self.save_action = QAction("Save", self)
        self.save_action.setStatusTip("Save changes to PBIP file")
        self.save_action.triggered.connect(self.save_to_pbip)
        self.save_action.setEnabled(False)
        self.toolbar.addAction(self.save_action)

    def create_menu(self):
        """Create the application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Open action
        open_action = QAction('&Open PBIP File...', self)
        open_action.setStatusTip('Open a PBIP file for editing')
        open_action.triggered.connect(self.open_pbip_file)
        file_menu.addAction(open_action)
        
        # Demo mode action
        demo_action = QAction('&Demo Mode', self)
        demo_action.setStatusTip('Load sample data for demonstration')
        demo_action.triggered.connect(self.load_demo_data)
        file_menu.addAction(demo_action)
        
        file_menu.addSeparator()
        
        # Save action
        save_action = QAction('&Save Changes to PBIP', self)
        save_action.setStatusTip('Save changes to the PBIP file')
        save_action.triggered.connect(self.save_to_pbip)
        save_action.setEnabled(False)
        file_menu.addAction(save_action)
        
        # Save As action
        save_as_action = QAction('Save &As...', self)
        save_as_action.setStatusTip('Save changes to a new PBIP file')
        save_as_action.triggered.connect(self.save_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        # Import action for groupings
        import_action = QAction('&Import Groupings...', self)
        import_action.setStatusTip('Import groupings from Excel or JSON file')
        import_action.triggered.connect(self.import_groupings)
        file_menu.addAction(import_action)
        
        # Export action for groupings
        export_action = QAction('&Export Groupings...', self)
        export_action.setStatusTip('Export groupings to Excel or JSON file')
        export_action.triggered.connect(self.export_groupings)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu('&Help')
        
        # About action
        about_action = QAction('&About', self)
        about_action.setStatusTip('About the application')
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)
        
        # Demo action (also in help menu for visibility)
        demo_action_help = QAction('&Demo Mode', self)
        demo_action_help.setStatusTip('Load sample data for demo')
        demo_action_help.triggered.connect(self.load_demo_data)
        help_menu.addAction(demo_action_help)

    def update_ui_state(self):
        """Update the UI state based on whether a file is loaded"""
        has_file = self.pbip_file_path is not None or self.demo_notice.isVisible()
        self.save_button.setEnabled(has_file and not self.demo_notice.isVisible())
        self.save_action.setEnabled(has_file and not self.demo_notice.isVisible())

    def open_pbip_file(self):
        """Open a PBIP file for editing"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open PBIP File", "", "Power BI Files (*.pbip);;All Files (*)"
        )
        
        if not file_path:
            return
            
        # Reset demo mode
        self.demo_notice.setVisible(False)
            
        try:
            # Update UI with file info
            self.pbip_file_path = file_path
            self.file_info.setText(f"Loaded: {os.path.basename(file_path)}")
            self.status_bar.showMessage(f"Opening PBIP file: {file_path}")
            
            # Extract groupings from the PBIP file
            groupings_df = extract_groupings_from_pbip(file_path)
            
            if groupings_df is not None and not groupings_df.empty:
                # Load the extracted groupings into the editor
                if hasattr(self.grouping_editor, 'set_data'):
                    self.grouping_editor.set_data(groupings_df)
                else:
                    # Manually set the data and reload
                    self.grouping_editor.original_df = groupings_df.copy()
                    self.grouping_editor.group_df = groupings_df.copy()
                    self.grouping_editor.reload_table()
                
                self.status_bar.showMessage(f"Loaded {len(groupings_df)} groupings from {os.path.basename(file_path)}")
                
                # Show success message
                QMessageBox.information(
                    self,
                    "PBIP File Loaded",
                    f"Successfully loaded {len(groupings_df)} groupings from {os.path.basename(file_path)}."
                )
            else:
                # No groupings found in the file, load demo data instead
                self.load_demo_data(show_demo_notice=False)
                
                # Show info
                QMessageBox.information(
                    self,
                    "No Groupings Found",
                    f"No InstrumentGroupings table found in {os.path.basename(file_path)}.\n\n"
                    "Sample data has been loaded as a starting point.\n"
                    "When you save, a new InstrumentGroupings table will be created in the PBIP file."
                )
            
            # Update UI state
            self.update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error opening PBIP file: {str(e)}")
            self.status_bar.showMessage(f"Error opening PBIP file: {str(e)}")
            self.pbip_file_path = None
            self.update_ui_state()

    def load_demo_data(self, show_demo_notice=True):
        """Load sample data for demo purposes."""
        try:
            # Check if the grouping editor is already loaded with data
            if hasattr(self.grouping_editor, 'group_df') and not self.grouping_editor.group_df.empty:
                confirm = QMessageBox.question(
                    self,
                    "Load Demo Data",
                    "This will replace your current grouping data. Continue?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if confirm != QMessageBox.Yes:
                    return
            
            # Try to find sample files in various locations
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
            # List of possible locations
            possible_locations = [
                os.path.join(base_dir, 'data', 'sample_groupings_fixed.json'),
                os.path.join(base_dir, 'data', 'sample_groupings.json'),
                os.path.join(base_dir, 'data', 'sample_groupings.xlsx')
            ]
            
            loaded = False
            # Try loading from each location
            for file_path in possible_locations:
                if os.path.exists(file_path):
                    self.status_bar.showMessage(f"Loading demo data from {os.path.basename(file_path)}...")
                    
                    # Call the appropriate import method based on the file extension
                    if hasattr(self.grouping_editor, 'import_groupings'):
                        # Use the import_groupings method if available
                        self.grouping_editor.import_groupings(file_path)
                        loaded = True
                        break
                    elif hasattr(self.grouping_editor, 'import_file'):
                        # Use the import_file method as a fallback
                        self.grouping_editor.import_file(file_path)
                        loaded = True
                        break
            
            if not loaded:
                # If we couldn't find any sample files, create a basic sample DataFrame
                QMessageBox.information(
                    self,
                    "Creating Demo Data",
                    "No sample files found. Creating basic demo data."
                )
                # Create a basic demo DataFrame
                import pandas as pd
                demo_df = pd.DataFrame({
                    'Instrument ID': ['BOND1001', 'BOND1002', 'BOND1003', 'BOND1004'],
                    'First Group': ['Government', 'Government', 'Corporate', 'Corporate'],
                    'Second Group': ['Treasury', 'Agency', 'Financial', 'Technology'],
                    'Third Group': ['US', 'US', 'Banking', 'Software']
                })
                
                # Use the setter method or create a new method to load this data
                if hasattr(self.grouping_editor, 'set_data'):
                    self.grouping_editor.set_data(demo_df)
                else:
                    # Manually set the data and reload
                    self.grouping_editor.original_df = demo_df.copy()
                    self.grouping_editor.group_df = demo_df.copy()
                    self.grouping_editor.reload_table()
            
            # Show the demo notice if requested
            if show_demo_notice:
                self.demo_notice.setVisible(True)
                self.file_info.setText("Demo Mode - No PBIP file loaded")
                self.status_bar.showMessage("Demo mode active - sample data loaded")
            
            # Update UI state
            self.update_ui_state()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load demo data: {str(e)}")
            self.status_bar.showMessage(f"Error loading demo data: {str(e)}")

    def save_to_pbip(self):
        """Save changes directly to the loaded PBIP file"""
        if not self.pbip_file_path:
            QMessageBox.warning(self, "No File", "No PBIP file is loaded. Use 'Save As' instead.")
            return
        
        # Get the groupings data
        df = self.grouping_editor.get_groupings()
        if df.empty:
            QMessageBox.warning(self, "No Data", "No groupings to save.")
            return
        
        # Confirm the save
        confirm = QMessageBox.question(
            self,
            "Confirm Save",
            f"Save {len(df)} groupings to {os.path.basename(self.pbip_file_path)}?\n\n"
            "This will modify the PBIP file directly.",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm != QMessageBox.Yes:
            return
        
        try:
            self.status_bar.showMessage(f"Saving to {self.pbip_file_path}...")
            
            # Call the update_pbip_groupings function
            success = update_pbip_groupings(self.pbip_file_path, df)
            
            if success:
                QMessageBox.information(
                    self, 
                    "Save Successful", 
                    f"Groupings saved to {os.path.basename(self.pbip_file_path)}.\n\n"
                    "Open the file in Power BI Desktop to see the changes."
                )
                self.status_bar.showMessage(f"Saved to {self.pbip_file_path}")
            else:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    "Failed to save groupings to the PBIP file.\n"
                    "Check the logs for more information."
                )
                self.status_bar.showMessage("Save failed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving to PBIP file: {str(e)}")
            self.status_bar.showMessage(f"Error: {str(e)}")

    def save_as(self):
        """Save changes to a new PBIP file"""
        # Get the groupings data
        df = self.grouping_editor.get_groupings()
        if df.empty:
            QMessageBox.warning(self, "No Data", "No groupings to save.")
            return
        
        # Get the destination file
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Save As", "", "Power BI Files (*.pbip);;All Files (*)"
        )
        
        if not file_path:
            return
            
        # Add .pbip extension if not present
        if not file_path.lower().endswith('.pbip'):
            file_path += '.pbip'
        
        # Check if the file exists
        if os.path.exists(file_path):
            confirm = QMessageBox.question(
                self,
                "File Exists",
                f"The file {os.path.basename(file_path)} already exists.\n"
                "Do you want to overwrite it?",
                QMessageBox.Yes | QMessageBox.No
            )
            if confirm != QMessageBox.Yes:
                return
        
        # If we don't have a source PBIP file, we can't create a new one
        if not self.pbip_file_path and not self.demo_notice.isVisible():
            QMessageBox.critical(
                self,
                "No Source File",
                "No source PBIP file is loaded.\n"
                "Please open a PBIP file first or use Export to save the data to Excel/JSON."
            )
            return
        
        try:
            self.status_bar.showMessage(f"Saving to {file_path}...")
            
            # If we have a source file, copy it first
            if self.pbip_file_path and os.path.exists(self.pbip_file_path):
                import shutil
                shutil.copy2(self.pbip_file_path, file_path)
                
                # Call the update_pbip_groupings function on the new file
                success = update_pbip_groupings(file_path, df)
            else:
                # In demo mode, we don't actually create a new PBIP file since we need a template
                QMessageBox.information(
                    self,
                    "Demo Mode Limitation",
                    "In demo mode, we can't create a new PBIP file from scratch.\n"
                    "Please use Export to save the data to Excel/JSON instead."
                )
                return
            
            if success:
                QMessageBox.information(
                    self, 
                    "Save Successful", 
                    f"Groupings saved to {os.path.basename(file_path)}.\n\n"
                    "Open the file in Power BI Desktop to see the changes."
                )
                
                # Update the current file to the new one
                self.pbip_file_path = file_path
                self.file_info.setText(f"Loaded: {os.path.basename(file_path)}")
                self.demo_notice.setVisible(False)
                self.update_ui_state()
                
                self.status_bar.showMessage(f"Saved to {file_path}")
            else:
                QMessageBox.critical(
                    self,
                    "Save Failed",
                    "Failed to save groupings to the PBIP file.\n"
                    "Check the logs for more information."
                )
                self.status_bar.showMessage("Save failed")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error saving to PBIP file: {str(e)}")
            self.status_bar.showMessage(f"Error: {str(e)}")

    def import_groupings(self):
        """Proxy to the grouping editor's import function."""
        if hasattr(self.grouping_editor, 'import_groupings'):
            self.grouping_editor.import_groupings()
            self.status_bar.showMessage("Imported groupings")
        else:
            self.status_bar.showMessage("Import function not available")

    def export_groupings(self):
        """Proxy to the grouping editor's export function."""
        if hasattr(self.grouping_editor, 'export_groupings'):
            self.grouping_editor.export_groupings()
            self.status_bar.showMessage("Exported groupings")
        else:
            self.status_bar.showMessage("Export function not available")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About TMDL Direct Editor",
            """<h3>TMDL Direct Editor (PBIP Edition)</h3>
            <p>A local Python desktop application for directly modifying TMDL files inside PBIP format Power BI files.</p>
            <p>This bypasses the XMLA endpoint and directly modifies the files, suitable for the newer PBIP file format.</p>
            <p>Developed for demonstration purposes.</p>
            <p>Version: 1.0.0</p>"""
        )

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TMDL Direct Editor")
    app.setOrganizationName("TMDLDirectEditor")
    
    # Setup logging
    logger = setup_logger()
    logger.info("Starting TMDL Direct Editor")
    
    # Create and show main window
    window = TMDLDirectEditorWindow()
    window.show()
    
    # Run application event loop
    try:
        logger.info("Application running")
        return app.exec_()
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}", exc_info=True)
        return 1
    finally:
        logger.info("Application shutdown")

if __name__ == "__main__":
    sys.exit(main()) 