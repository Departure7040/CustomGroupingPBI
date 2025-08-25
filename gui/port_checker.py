# gui/port_checker.py

import os
import subprocess
import re
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QTextEdit, QProgressBar, QComboBox
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

class PortCheckerDialog(QDialog):
    """Tool for checking available ports on the system."""
    
    portsFound = pyqtSignal(list)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Port Checker Tool")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        
        self.found_ports = []
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Description
        description = QLabel(
            "This tool helps you identify which ports are available for Power BI connection.\n"
            "Power BI typically listens on ports in the 49xxx or 56xxx range on localhost (127.0.0.1)."
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Filter options
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Filter ports by:"))
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems([
            "Power BI Ports (49xxx, 56xxx)",
            "All Listening Ports",
            "Custom..."
        ])
        filter_layout.addWidget(self.filter_combo)
        
        # Run button
        self.run_button = QPushButton("Check Ports")
        self.run_button.clicked.connect(self.run_port_check)
        filter_layout.addWidget(self.run_button)
        
        layout.addLayout(filter_layout)
        
        # Results area
        layout.addWidget(QLabel("Results:"))
        
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setStyleSheet("font-family: Consolas, Courier New, monospace;")
        layout.addWidget(self.results_text)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons at bottom
        button_layout = QHBoxLayout()
        
        self.use_port_button = QPushButton("Use Selected Port")
        self.use_port_button.setEnabled(False)
        self.use_port_button.clicked.connect(self.use_selected_port)
        
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.use_port_button)
        button_layout.addWidget(self.close_button)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def run_port_check(self):
        """Run the port check based on the selected filter."""
        self.results_text.clear()
        self.found_ports = []
        self.use_port_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.run_button.setEnabled(False)
        
        filter_option = self.filter_combo.currentText()
        
        self.results_text.append("Running port check...\n")
        QTimer.singleShot(100, lambda: self._do_port_check(filter_option))
    
    def _do_port_check(self, filter_option):
        """Execute the port check command and process results."""
        try:
            if "Power BI Ports" in filter_option:
                # Check for both 49xxx and 56xxx Power BI ports
                command = 'netstat -an | findstr "LISTENING" | findstr /C:"49" /C:"56"'
                filter_regex = r".*:(49\d{3}|56\d{3}).*LISTENING"
            elif "All Listening" in filter_option:
                # Check all listening ports
                command = 'netstat -an | findstr "LISTENING"'
                filter_regex = r".*:(\d+).*LISTENING"
            else:
                # Custom filter - default to both Power BI port ranges
                command = 'netstat -an | findstr "LISTENING" | findstr /C:"49" /C:"56"'
                filter_regex = r".*:(49\d{3}|56\d{3}).*LISTENING"
            
            # Run the command
            process = subprocess.Popen(
                command, 
                shell=True, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            
            if stderr:
                self.results_text.append(f"Error: {stderr}\n")
            
            if not stdout:
                self.results_text.append("No matching ports found.\n")
                self.results_text.append("\nTroubleshooting tips:")
                self.results_text.append("1. Make sure Power BI Desktop is running with a model open")
                self.results_text.append("2. Check if the XMLA endpoint is enabled in Power BI Desktop")
                self.results_text.append("3. Try restarting Power BI Desktop")
                self.results_text.append("4. Try the 'All Listening Ports' option to see all ports")
            else:
                # Process and display the results
                self.results_text.append("Found the following ports:\n")
                
                # Format table header
                self.results_text.append(f"{'Protocol':<10} {'Local Address':<25} {'Foreign Address':<25} {'State':<15}")
                self.results_text.append("-" * 75)
                
                # Process each line
                for line in stdout.splitlines():
                    line = line.strip()
                    if re.match(filter_regex, line):
                        self.results_text.append(line)
                        
                        # Extract the port number
                        match = re.search(r":(\d+)", line)
                        if match:
                            port = match.group(1)
                            if port not in self.found_ports:
                                self.found_ports.append(port)
                
                # Show summary
                self.results_text.append("\nPotential Power BI ports: " + ", ".join(self.found_ports))
                self.results_text.append("\nPower BI XMLA endpoints typically listen on ports in the 49xxx or 56xxx range.")
                self.results_text.append("Try connecting to each port to find the correct one for your Power BI instance.")
                
                # Enable the use port button if ports were found
                if self.found_ports:
                    self.use_port_button.setEnabled(True)
                    
                    # Emit the signal with the found ports
                    self.portsFound.emit(self.found_ports)
        
        except Exception as e:
            self.results_text.append(f"Error running port check: {str(e)}")
        
        finally:
            self.progress_bar.setVisible(False)
            self.run_button.setEnabled(True)
    
    def use_selected_port(self):
        """Return the first found port as selected port."""
        if self.found_ports:
            self.selected_port = self.found_ports[0]
            self.accept()
        else:
            self.reject()

def check_ports(parent=None):
    """Show the port checker dialog and return the selected port."""
    dialog = PortCheckerDialog(parent)
    result = dialog.exec_()
    
    if result == QDialog.Accepted and hasattr(dialog, 'selected_port'):
        return dialog.found_ports, dialog.selected_port
    
    return dialog.found_ports, None 