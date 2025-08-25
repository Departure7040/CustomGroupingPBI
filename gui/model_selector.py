# gui/model_selector.py

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QComboBox, QMessageBox, QProgressBar,
    QTextBrowser, QTabWidget, QWidget
)
from PyQt5.QtCore import Qt, QTimer

import os
import sys
import logging

# Add project root to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from tmdl_editor import get_available_ports, reset_port
from backend.model_connector import ModelConnector
from gui.port_checker import check_ports

class ModelSelectorDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Power BI Model")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        self.selected_port = None
        self.connector = None
        self.init_ui()
        
        # Refresh ports when dialog is shown
        self.refresh_ports()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Create tabs
        self.tabs = QTabWidget()
        
        # Connection tab
        connection_tab = QWidget()
        connection_layout = QVBoxLayout(connection_tab)
        
        # Explanation
        description = QLabel(
            "Select a Power BI Desktop model to connect to.\n"
            "Each port corresponds to a different open Power BI file."
        )
        description.setWordWrap(True)
        connection_layout.addWidget(description)
        
        # Port selection
        port_layout = QHBoxLayout()
        port_layout.addWidget(QLabel("Available ports:"))
        
        self.port_combo = QComboBox()
        self.port_combo.setMinimumWidth(200)
        port_layout.addWidget(self.port_combo)
        
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self.refresh_ports)
        port_layout.addWidget(self.refresh_button)
        
        connection_layout.addLayout(port_layout)
        
        # Port checker button
        port_checker_layout = QHBoxLayout()
        port_checker_layout.addWidget(QLabel("Can't find the right port?"))
        
        self.port_checker_button = QPushButton("Port Checker Tool")
        self.port_checker_button.clicked.connect(self.show_port_checker)
        port_checker_layout.addWidget(self.port_checker_button)
        
        connection_layout.addLayout(port_checker_layout)
        
        # Manual port entry option
        manual_layout = QHBoxLayout()
        manual_layout.addWidget(QLabel("Or enter port manually:"))
        
        self.manual_port_combo = QComboBox()
        self.manual_port_combo.setEditable(True)
        # Add both 49xxx and 56xxx port ranges as default options
        self.manual_port_combo.addItems(["56888", "56889", "56890", "49295", "49300", "49305", "49310", "49315"])
        manual_layout.addWidget(self.manual_port_combo)
        
        self.manual_connect_button = QPushButton("Try Connect")
        self.manual_connect_button.clicked.connect(self.connect_to_manual)
        manual_layout.addWidget(self.manual_connect_button)
        
        connection_layout.addLayout(manual_layout)
        
        # Progress indicator
        self.progress_layout = QHBoxLayout()
        self.status_label = QLabel("Ready")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        
        self.progress_layout.addWidget(self.status_label)
        self.progress_layout.addWidget(self.progress_bar)
        connection_layout.addLayout(self.progress_layout)
        
        # Add note about correct port
        note_label = QLabel(
            "<b>Note:</b> Finding the correct port can be challenging. "
            "Power BI typically uses ports in the 49xxx or 56xxx range. "
            "Try each port until you find one that works. "
            "Use the Port Checker Tool to find all listening ports."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #555;")
        connection_layout.addWidget(note_label)
        
        # Troubleshooting tab
        troubleshooting_tab = QWidget()
        troubleshooting_layout = QVBoxLayout(troubleshooting_tab)
        
        troubleshooting_text = QTextBrowser()
        troubleshooting_text.setOpenExternalLinks(True)
        troubleshooting_text.setHtml("""
        <h3>Troubleshooting Power BI Connections</h3>
        <p>If you're having trouble connecting to Power BI, here are some steps to try:</p>
        <ol>
            <li><b>Make sure Power BI Desktop is running</b> with at least one file open.</li>
            <li><b>Check if XMLA endpoint is enabled</b> in Power BI Desktop.</li>
            <li><b>Try different ports</b> - Power BI Desktop typically uses ports in the 49xxx or 56xxx range.</li>
            <li><b>Restart Power BI Desktop</b> after making changes.</li>
        </ol>
        
        <h3>Step-by-Step Guide:</h3>
        <ol>
            <li>Open Power BI Desktop with any model</li>
            <li>In Power BI Desktop, go to File > Options > Preview features</li>
            <li>Make sure "XMLA Endpoint" is enabled and restart Power BI Desktop</li>
            <li>Use the "Port Checker Tool" button to find active listening ports</li>
            <li>Try each port shown in the Port Checker results until one works</li>
            <li>If you connect but see no tables, your model might be empty or have issues</li>
        </ol>
        
        <h3>Common Issues:</h3>
        <ul>
            <li><b>No ports found</b>: Power BI may not be running, or XMLA endpoint is not enabled</li>
            <li><b>Connection refused</b>: The port may be used by another application</li>
            <li><b>Authentication failure</b>: Make sure you're using the correct login credentials</li>
            <li><b>XMLA Endpoint not enabled</b>: In Power BI Desktop, go to File > Options > Preview features, enable XMLA Endpoint and restart</li>
            <li><b>Connected but no tables</b>: The model might be empty, or the tables aren't visible via XMLA</li>
        </ul>
        
        <h3>For Demo Purposes:</h3>
        <p>If you're unable to connect to Power BI for your showcase, you can still demonstrate the UI functionality by:</p>
        <ul>
            <li>Using the "Help > Demo Mode" option from the main menu</li>
            <li>Importing sample data from the data/ directory</li>
            <li>Using the grouping editor to make changes</li>
            <li>Exporting the modified data</li>
        </ul>
        """)
        troubleshooting_layout.addWidget(troubleshooting_text)
        
        # Add tabs to the tab widget
        self.tabs.addTab(connection_tab, "Connect")
        self.tabs.addTab(troubleshooting_tab, "Troubleshooting")
        
        layout.addWidget(self.tabs)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.connect_button = QPushButton("Connect")
        self.connect_button.clicked.connect(self.connect_to_selected)
        self.connect_button.setDefault(True)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.connect_button)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def refresh_ports(self):
        """Refresh the list of available Power BI ports"""
        self.status_label.setText("Scanning for Power BI instances...")
        self.progress_bar.setVisible(True)
        self.connect_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
        # Use QTimer to allow the UI to update
        QTimer.singleShot(100, self._do_refresh_ports)

    def _do_refresh_ports(self):
        """Do the actual port refresh (called after UI updates)"""
        try:
            ports = get_available_ports()
            
            self.port_combo.clear()
            
            if not ports:
                self.status_label.setText("No Power BI instances found. Open Power BI and try again.")
                self.progress_bar.setVisible(False)
                self.connect_button.setEnabled(False)
                self.refresh_button.setEnabled(True)
                return
            
            for port in ports:
                self.port_combo.addItem(f"localhost:{port}", port)
            
            self.status_label.setText(f"Found {len(ports)} potential Power BI port(s)")
            self.connect_button.setEnabled(True)
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            logging.error(f"Error refreshing ports: {e}")
        
        self.progress_bar.setVisible(False)
        self.refresh_button.setEnabled(True)
    
    def show_port_checker(self):
        """Show the port checker tool dialog."""
        try:
            found_ports, selected_port = check_ports(self)
            
            if found_ports:
                # Add the found ports to the manual port combo box
                for port in found_ports:
                    # Check if it's already in the combo box
                    found = False
                    for i in range(self.manual_port_combo.count()):
                        if self.manual_port_combo.itemText(i) == port:
                            found = True
                            break
                    
                    if not found:
                        self.manual_port_combo.addItem(port)
                
                # If a specific port was selected, set it as the current one
                if selected_port:
                    index = self.manual_port_combo.findText(selected_port)
                    if index >= 0:
                        self.manual_port_combo.setCurrentIndex(index)
                    else:
                        self.manual_port_combo.setEditText(selected_port)
            
                self.status_label.setText(f"Found {len(found_ports)} listening ports")
        except Exception as e:
            logging.error(f"Error in port checker: {e}")
            QMessageBox.warning(self, "Port Checker Error", f"An error occurred: {str(e)}")

    def connect_to_manual(self):
        """Connect to a manually entered port"""
        port = self.manual_port_combo.currentText().strip()
        
        if not port or not port.isdigit():
            QMessageBox.warning(self, "Invalid Port", "Please enter a valid port number.")
            return
        
        self.status_label.setText(f"Testing connection to port {port}...")
        self.progress_bar.setVisible(True)
        self.manual_connect_button.setEnabled(False)
        
        # Use QTimer to allow the UI to update
        QTimer.singleShot(100, lambda: self._do_connect_to_selected(port))

    def connect_to_selected(self):
        """Test connection to the selected Power BI port"""
        if self.port_combo.count() == 0:
            QMessageBox.warning(self, "No Ports Found", 
                                "No ports detected automatically.\n"
                                "Please use the manual port entry option or see the troubleshooting tab.")
            self.tabs.setCurrentIndex(1)  # Switch to troubleshooting tab
            return
        
        port = self.port_combo.currentData()
        if not port:
            return
        
        self.status_label.setText(f"Testing connection to port {port}...")
        self.progress_bar.setVisible(True)
        self.connect_button.setEnabled(False)
        self.refresh_button.setEnabled(False)
        
        # Use QTimer to allow the UI to update
        QTimer.singleShot(100, lambda: self._do_connect_to_selected(port))

    def _do_connect_to_selected(self, port):
        """Do the actual connection test (called after UI updates)"""
        try:
            # Import tmdl_editor to reset the global port
            import sys
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            parent_dir = os.path.dirname(current_dir)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
                
            from tmdl_editor import reset_port
            
            # Reset any stored port to ensure we use the one the user selected
            reset_port()
            
            self.connector = ModelConnector()
            self.connector.port = port
            self.connector.conn_str = f"Provider=MSOLAP;Data Source=localhost:{port}"
            
            if self.connector.test_connection():
                # Success - we have a valid connection
                self.selected_port = port
                
                # Show success message with a note about loading tables
                QMessageBox.information(
                    self, 
                    "Connection Successful", 
                    f"Successfully connected to Power BI on port {port}.\n\n"
                    "If you don't see any tables after connecting, this could mean:\n"
                    "1. Your Power BI model is empty\n" 
                    "2. Tables aren't visible via the XMLA endpoint\n"
                    "3. Tables need to be refreshed in Power BI\n\n"
                    "You can still use the application in Demo Mode if needed."
                )
                
                self.accept()  # Close dialog with success
            else:
                error_msg = (
                    f"Could not connect to Power BI on port {port}.\n\n"
                    "Common reasons for connection failures:\n"
                    "1. Power BI Desktop is not running\n"
                    "2. No model is open in Power BI Desktop\n"
                    "3. This port is not actually a Power BI XMLA endpoint\n"
                    "4. XMLA Endpoint is not enabled in Power BI Desktop\n\n"
                    "Please check the Troubleshooting tab for more information."
                )
                QMessageBox.warning(self, "Connection Failed", error_msg)
                self.status_label.setText("Connection failed")
                self.tabs.setCurrentIndex(1)  # Switch to troubleshooting tab
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection error: {str(e)}")
            self.status_label.setText(f"Error: {str(e)}")
            logging.error(f"Connection error: {e}")
        
        self.progress_bar.setVisible(False)
        self.connect_button.setEnabled(True)
        self.refresh_button.setEnabled(True)
        self.manual_connect_button.setEnabled(True)

def get_model_connection(parent=None):
    """
    Show the model selector dialog and return the selected port and connector.
    Returns (port, connector) if successful, or (None, None) if canceled.
    """
    dialog = ModelSelectorDialog(parent)
    result = dialog.exec_()
    
    if result == QDialog.Accepted and dialog.selected_port:
        return dialog.selected_port, dialog.connector
    
    return None, None 