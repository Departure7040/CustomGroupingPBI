# gui/main_window.py
import os
import sys
import logging
import pandas as pd
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QPushButton, QListWidget, QLabel, QMessageBox, QTabWidget,
    QToolBar, QAction, QStatusBar, QHBoxLayout, QMenu, QSplitter,
    QTreeWidget, QTreeWidgetItem, QHeaderView, QFileDialog, QCheckBox
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QTimer

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from tmdl_editor import fetch_tables, fetch_columns_for_table, reset_port
from gui.grouping_editor import GroupingEditor
from gui.model_selector import get_model_connection, ModelSelectorDialog
from backend.tabular_editor_cli import run_tabular_editor
from backend.model_connector import ModelConnector

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TMDL Live Editor (Python)")
        self.resize(1000, 700)
        
        # Initialize model connection variables
        self.port = None
        self.connector = None
        self.current_table = None
        self.columns_df = None
        
        # Create UI components
        self.create_ui()
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready - No model connected")
        
        # Try automatic port detection (but don't show error if it fails)
        try:
            self.connector = ModelConnector()
            self.port = self.connector.detect_port()
            if self.port:
                self.status_bar.showMessage(f"Auto-detected Power BI port: {self.port}")
        except Exception:
            # Silent failure for auto-detection
            pass

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
        
        # Connect button
        self.connect_button = QPushButton("Connect to Power BI")
        self.connect_button.clicked.connect(self.connect_to_model)
        button_layout.addWidget(self.connect_button)
        
        # Load tables button
        self.load_button = QPushButton("Load Tables")
        self.load_button.clicked.connect(self.load_tables)
        button_layout.addWidget(self.load_button)
        
        # Add a prominent Demo Mode button
        self.demo_button = QPushButton("Demo Mode")
        self.demo_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.demo_button.setToolTip("Load sample data for demonstration purposes")
        self.demo_button.clicked.connect(self.load_demo_data)
        button_layout.addWidget(self.demo_button)
        
        # Push button 
        self.push_button = QPushButton("Push Groupings to Power BI")
        self.push_button.clicked.connect(self.push_groupings)
        button_layout.addWidget(self.push_button)
        
        # Add button layout to main layout
        self.main_layout.addLayout(button_layout)
        
        # Demo notice - only shown when in demo mode
        self.demo_notice = QLabel("DEMO MODE: Using sample data - changes will not affect Power BI")
        self.demo_notice.setStyleSheet("background-color: #FFF3CD; color: #856404; padding: 5px; border-radius: 3px;")
        self.demo_notice.setAlignment(Qt.AlignCenter)
        self.demo_notice.setVisible(False)
        self.main_layout.addWidget(self.demo_notice)
        
        # Create a splitter for the main area
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left panel for tables and details
        self.left_panel = QWidget()
        self.left_layout = QVBoxLayout(self.left_panel)
        
        # Create the table list
        self.left_layout.addWidget(QLabel("Available Tables:"))
        self.tables_list = QListWidget()
        self.tables_list.setMaximumHeight(150)
        self.tables_list.itemClicked.connect(self.on_table_selected)
        self.left_layout.addWidget(self.tables_list)
        
        # Create the details tabs
        self.details_tabs = QTabWidget()
        
        # Columns tab
        self.columns_widget = QTreeWidget()
        self.columns_widget.setHeaderLabels(["Column", "Data Type"])
        self.columns_widget.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.details_tabs.addTab(self.columns_widget, "Columns")
        
        # Create Grouping button
        self.create_grouping_button = QPushButton("Create Grouping from Selected Column")
        self.create_grouping_button.clicked.connect(self.create_grouping_from_column)
        self.create_grouping_button.setEnabled(False)
        
        # Add details and button to the left panel
        self.left_layout.addWidget(self.details_tabs)
        self.left_layout.addWidget(self.create_grouping_button)
        
        # Right panel for grouping editor
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.grouping_editor = GroupingEditor()
        self.right_layout.addWidget(QLabel("Grouping Editor:"))
        self.right_layout.addWidget(self.grouping_editor)
        
        # Add panels to splitter
        self.splitter.addWidget(self.left_panel)
        self.splitter.addWidget(self.right_panel)
        self.splitter.setSizes([300, 700])  # Set initial sizes
        
        # Add splitter to main layout
        self.main_layout.addWidget(self.splitter)
        
        # Set the central widget layout
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
        
        # Update UI state
        self.update_ui_state()
        
        # Connect selection events
        self.columns_widget.itemClicked.connect(self.on_column_selected)

    def on_table_selected(self, item):
        """Handle table selection"""
        self.current_table = item.text()
        self.load_columns_for_table(self.current_table)
        
    def on_column_selected(self, item, column):
        """Handle selection of a column from the tree"""
        # Enable the create grouping button when a column is selected
        self.create_grouping_button.setEnabled(True)
    
    def create_grouping_from_column(self):
        """Create a grouping based on the selected column"""
        selected_items = self.columns_widget.selectedItems()
        if not selected_items:
            return
            
        column_name = selected_items[0].text(0)
        
        # Confirm with the user
        confirm = QMessageBox.question(
            self,
            "Create Grouping",
            f"Create a new grouping based on column '{column_name}' from table '{self.current_table}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm != QMessageBox.Yes:
            return
            
        # If the grouping editor has an add_column_grouping method, use it
        if hasattr(self.grouping_editor, 'add_column_grouping'):
            try:
                self.grouping_editor.add_column_grouping(self.current_table, column_name)
                self.status_bar.showMessage(f"Created grouping based on {column_name}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to create grouping: {str(e)}")
        else:
            # Otherwise load demo data as a fallback
            QMessageBox.information(
                self,
                "Demo Mode",
                f"In a real implementation, this would create a grouping based on '{column_name}'.\n"
                "For now, loading demo data instead."
            )
            self.load_demo_data()

    def load_columns_for_table(self, table_name):
        """Load columns for selected table and display them"""
        if not table_name:
            return
            
        self.status_bar.showMessage(f"Loading columns for {table_name}...", 3000)
        
        try:
            # Import for loading columns
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                
            # Import the updated function
            from tmdl_editor import fetch_columns_for_table
            
            # Check if we have a port
            if not self.port and not self.demo_notice.isVisible():
                QMessageBox.warning(
                    self,
                    "No Connection",
                    "No Power BI connection is active. Please connect to a Power BI model first."
                )
                return
            
            # Clear existing items
            self.columns_widget.clear()
            
            # Set headers
            self.columns_widget.setHeaderLabels(["Column", "Data Type"])
            
            # In demo mode, load sample columns
            if self.demo_notice.isVisible():
                # Filter columns from the sample data
                if hasattr(self, 'columns_df') and self.columns_df is not None:
                    table_columns = self.columns_df[self.columns_df["Table"] == table_name]
                    for _, row in table_columns.iterrows():
                        item = QTreeWidgetItem(self.columns_widget)
                        item.setText(0, row["Column"])
                        item.setText(1, "Text")  # Default data type
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(0, Qt.Unchecked)
                    
                    self.status_bar.showMessage(f"Loaded {len(table_columns)} columns for {table_name} (demo mode)", 3000)
                    return
            
            # If we get here, we're in real mode with a valid port
            # Fetch columns for the table using the selected port
            logging.info(f"MainWindow: Fetching columns for table {table_name} using port {self.port}")
            columns = fetch_columns_for_table(table_name, port=self.port)
            
            # Add columns to tree widget
            for column in columns:
                item = QTreeWidgetItem(self.columns_widget)
                item.setText(0, column)
                item.setText(1, "Unknown")  # We could fetch data types if needed
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(0, Qt.Unchecked)
            
            # Update status with port info
            self.status_bar.showMessage(f"Loaded {len(columns)} columns for {table_name} from port {self.port}", 3000)
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Error loading columns: {str(e)}")
            logging.error(f"Error loading columns for table {table_name}: {e}")
            self.status_bar.showMessage(f"Error loading columns for {table_name}", 3000)
            
            # Offer to switch to demo mode
            if not self.demo_notice.isVisible():
                reply = QMessageBox.question(
                    self,
                    "Use Demo Mode?",
                    f"Error loading columns: {str(e)}\n\nWould you like to use Demo Mode instead?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.load_demo_data()

    def create_toolbar(self):
        """Create the main toolbar"""
        self.toolbar = QToolBar("Main Toolbar")
        self.toolbar.setMovable(False)
        self.addToolBar(self.toolbar)
        
        # Add toolbar actions
        self.connect_action = QAction("Connect", self)
        self.connect_action.setStatusTip("Connect to a Power BI model")
        self.connect_action.triggered.connect(self.connect_to_model)
        self.toolbar.addAction(self.connect_action)
        
        self.refresh_action = QAction("Refresh Tables", self)
        self.refresh_action.setStatusTip("Refresh tables from Power BI model")
        self.refresh_action.triggered.connect(self.load_tables)
        self.toolbar.addAction(self.refresh_action)
        
        # Add demo mode action
        self.demo_action = QAction("Demo Mode", self)
        self.demo_action.setStatusTip("Load sample data for demonstration")
        self.demo_action.triggered.connect(self.load_demo_data)
        self.toolbar.addAction(self.demo_action)
        
        self.toolbar.addSeparator()
        
        self.push_action = QAction("Push Changes", self)
        self.push_action.setStatusTip("Push groupings to Power BI model")
        self.push_action.triggered.connect(self.push_groupings)
        self.toolbar.addAction(self.push_action)

    def create_menu(self):
        """Create the application menus"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('&File')
        
        # Connect action
        connect_action = QAction('&Connect to Power BI...', self)
        connect_action.setStatusTip('Connect to Power BI model')
        connect_action.triggered.connect(self.connect_to_model)
        file_menu.addAction(connect_action)
        
        # Refresh tables action
        refresh_action = QAction('&Refresh Tables', self)
        refresh_action.setStatusTip('Refresh tables from Power BI model')
        refresh_action.triggered.connect(self.load_tables)
        file_menu.addAction(refresh_action)
        
        # Demo mode action
        demo_action = QAction('&Demo Mode', self)
        demo_action.setStatusTip('Load sample data for demonstration')
        demo_action.triggered.connect(self.load_demo_data)
        file_menu.addAction(demo_action)
        
        file_menu.addSeparator()
        
        # Import action
        import_action = QAction('&Import Groupings...', self)
        import_action.setStatusTip('Import groupings from file')
        import_action.triggered.connect(self.import_groupings)
        file_menu.addAction(import_action)
        
        # Export action
        export_action = QAction('&Export Groupings...', self)
        export_action.setStatusTip('Export groupings to file')
        export_action.triggered.connect(self.export_groupings)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction('E&xit', self)
        exit_action.setStatusTip('Exit application')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('&Tools')
        
        # Push action
        push_action = QAction('&Push Groupings to Power BI', self)
        push_action.setStatusTip('Push groupings to Power BI model')
        push_action.triggered.connect(self.push_groupings)
        tools_menu.addAction(push_action)
        
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

    def load_demo_data(self):
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
            project_dir = os.path.dirname(base_dir)
            
            # List of possible locations
            possible_locations = [
                os.path.join(project_dir, 'data', 'sample_groupings.xlsx'),
                os.path.join(project_dir, 'data', 'sample_groupings_fixed.json'),
                os.path.join(project_dir, 'data', 'sample_groupings.json')
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
            
            # Also load demo table data
            self.load_demo_table_data()
            
            # Show the demo notice
            self.demo_notice.setVisible(True)
            self.status_bar.showMessage("Demo mode active - sample data loaded")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load demo data: {str(e)}")
            self.status_bar.showMessage(f"Error loading demo data: {str(e)}")

    def show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About TMDL Live Editor",
            """<h3>TMDL Live Editor (Python Edition)</h3>
            <p>A local Python desktop application for modifying Power BI models via the XMLA endpoint.</p>
            <p>Developed for demonstration purposes.</p>
            <p>Version: 1.0.0</p>"""
        )

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

    def connect_to_model(self):
        """Show dialog to connect to a Power BI model"""
        try:
            # Import the reset_port function to ensure we start fresh
            from tmdl_editor import reset_port
            reset_port()  # Clear any previously stored port
            
            port, connector = get_model_connection(self)
            
            if port and connector:
                self.port = port
                self.connector = connector
                self.status_bar.showMessage(f"Connected to Power BI on port {port}")
                
                # Reset demo mode if we successfully connect
                self.demo_notice.setVisible(False)
                
                # Reset any cached data to ensure we're getting fresh data from the correct port
                self.columns_df = None
                
                # Load tables automatically after successful connection
                self.load_tables()
            
            # Update UI based on connection state
            self.update_ui_state()
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", str(e))
            self.status_bar.showMessage(f"Connection error: {str(e)}")
            
            # Offer to use demo mode
            demo_msg = (
                f"Connection error: {str(e)}\n\n"
                "Would you like to use Demo Mode instead to showcase the application functionality?"
            )
            demo_confirm = QMessageBox.question(
                self, "Use Demo Mode?", demo_msg, QMessageBox.Yes | QMessageBox.No
            )
            if demo_confirm == QMessageBox.Yes:
                self.load_demo_data()

    def update_ui_state(self):
        """Update the UI state based on the connection status"""
        connected = self.port is not None and self.connector is not None
        
        # Update button states
        self.load_button.setEnabled(connected)
        self.push_button.setEnabled(connected or self.demo_notice.isVisible())
        
        # Update toolbar actions
        self.refresh_action.setEnabled(connected)
        self.push_action.setEnabled(connected or self.demo_notice.isVisible())
        
        # Update connection button text
        if connected:
            self.connect_button.setText(f"Connected ({self.port})")
        else:
            self.connect_button.setText("Connect to Power BI")

    def load_tables(self):
        """Load tables from connected Power BI model"""
        
        # Update status bar
        self.status_bar.showMessage("Loading tables from Power BI...", 3000)
        
        try:
            # Import for loading tables
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                
            # Import the updated functions
            from tmdl_editor import fetch_tables
            
            # Check if we have a port selected
            if not self.port:
                QMessageBox.warning(
                    self,
                    "No Connection",
                    "No Power BI connection is active. Please connect to a Power BI model first."
                )
                # Offer to use demo mode
                reply = QMessageBox.question(
                    self,
                    "Use Demo Mode?",
                    "Would you like to use Demo Mode instead?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                if reply == QMessageBox.Yes:
                    self.load_demo_data()
                return
            
            # Fetch tables explicitly using the port set during connection
            logging.info(f"MainWindow: Fetching tables using port {self.port}")
            tables = fetch_tables(port=self.port)
            
            # Check if we have tables
            if not tables or len(tables) == 0:
                msg = (f"No tables found in Power BI model (port {self.port}).\n\n"
                       "This could be because:\n"
                       "1. Your Power BI model is empty\n"
                       "2. Tables aren't visible via the XMLA endpoint\n"
                       "3. Tables need to be refreshed in Power BI\n\n"
                       "Would you like to switch to Demo Mode?")
                
                reply = QMessageBox.question(
                    self, 
                    "No Tables Found", 
                    msg,
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes
                )
                
                if reply == QMessageBox.Yes:
                    self.load_demo_data()
                    return
                else:
                    self.status_bar.showMessage("No tables loaded", 3000)
                    return
            
            # Clear existing items
            self.tables_list.clear()
            
            # Add tables to the list widget
            for table in tables:
                self.tables_list.addItem(table)
                
            # Update status - make sure to show which port we're using
            self.status_bar.showMessage(f"Loaded {len(tables)} tables from port {self.port}", 3000)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error loading tables: {str(e)}")
            logging.error(f"Error loading tables: {e}")
            self.status_bar.showMessage("Error loading tables", 3000)
            
            # Offer to switch to demo mode
            reply = QMessageBox.question(
                self, 
                "Connection Error", 
                f"Error loading tables: {str(e)}\n\nWould you like to switch to Demo Mode?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.load_demo_data()

    def push_groupings(self):
        """Push groupings to the Power BI model"""
        # If in demo mode, just show a message
        if self.demo_notice.isVisible():
            QMessageBox.information(
                self, 
                "Demo Mode", 
                "In Demo Mode, changes are not pushed to Power BI.\n\n"
                "This would normally update the connected Power BI model with your grouping changes."
            )
            self.status_bar.showMessage("Demo mode - changes not pushed to Power BI")
            return
            
        if not self.port:
            self.connect_to_model()
            if not self.port:  # If still no port after dialog
                return
        
        df = self.grouping_editor.get_groupings()
        if df.empty:
            QMessageBox.warning(self, "No Data", "No groupings to push.")
            return

        confirm = QMessageBox.question(
            self,
            "Confirm Push",
            f"This will update {len(df)} records in the Power BI model.\nProceed?",
            QMessageBox.Yes | QMessageBox.No,
        )

        if confirm != QMessageBox.Yes:
            return

        try:
            self.status_bar.showMessage("Pushing groupings to Power BI...")
            success = run_tabular_editor("InstrumentGroupings", df, port=self.port)
            
            if success:
                QMessageBox.information(self, "Success", "Groupings pushed successfully.")
                self.status_bar.showMessage("Groupings pushed successfully.")
            else:
                QMessageBox.critical(self, "Failed", "Push failed. See console output.")
                self.status_bar.showMessage("Push failed.")
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            self.status_bar.showMessage(f"Error: {str(e)}")

    def load_demo_table_data(self):
        """Load sample table data for demo mode"""
        # Clear existing data
        self.tables_list.clear()
        self.columns_widget.clear()
        
        # Add sample tables
        sample_tables = ["InstrumentGroupings", "FinancialData", "CustomerAccounts", "Products"]
        for table in sample_tables:
            self.tables_list.addItem(table)
        
        # Create sample column data
        import pandas as pd
        self.columns_df = pd.DataFrame({
            "Column": [
                "Instrument ID", "First Group", "Second Group", "Third Group",
                "AccountID", "CustomerName", "AccountType", "Balance",
                "ProductID", "ProductName", "Category", "Price"
            ],
            "Table": [
                "InstrumentGroupings", "InstrumentGroupings", "InstrumentGroupings", "InstrumentGroupings",
                "CustomerAccounts", "CustomerAccounts", "CustomerAccounts", "CustomerAccounts",
                "Products", "Products", "Products", "Products"
            ]
        })
        
        # Select the first table automatically
        self.tables_list.setCurrentRow(0)
        self.current_table = "InstrumentGroupings"
        self.load_columns_for_table(self.current_table)
        
        # Show the demo notice
        self.demo_notice.setVisible(True)
        self.status_bar.showMessage("Demo mode active - sample data loaded")

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
