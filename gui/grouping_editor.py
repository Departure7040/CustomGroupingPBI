# gui/grouping_editor.py

import pandas as pd
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QFileDialog, QTableWidget, QTableWidgetItem, QLabel, QMessageBox,
    QSplitter, QTextEdit, QHeaderView, QAction, QToolBar, QApplication,
    QDialog, QLineEdit, QFormLayout, QDialogButtonBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QIcon, QFont, QColor
import os
import json
import copy
import logging

# Add import for connecting to Power BI if needed
import sys
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from tmdl_editor import connect_to_model

class UndoRedoStack:
    """Simple undo/redo stack implementation for DataFrame states."""
    
    def __init__(self, initial_state=None, max_stack_size=20):
        self.undo_stack = []
        self.redo_stack = []
        self.max_stack_size = max_stack_size
        if initial_state is not None:
            self.push(initial_state)
    
    def push(self, state):
        """Push a new state to the undo stack."""
        # Create a deep copy to ensure state is preserved
        state_copy = copy.deepcopy(state)
        self.undo_stack.append(state_copy)
        # Clear redo stack when new changes are made
        self.redo_stack.clear()
        
        # Limit stack size
        if len(self.undo_stack) > self.max_stack_size:
            self.undo_stack.pop(0)
    
    def undo(self):
        """Undo to the previous state."""
        if len(self.undo_stack) <= 1:
            # Nothing to undo or we're at the initial state
            return None
            
        current = self.undo_stack.pop()
        self.redo_stack.append(current)
        return self.undo_stack[-1]  # Return the new current state
    
    def redo(self):
        """Redo the last undone action."""
        if not self.redo_stack:
            return None
            
        next_state = self.redo_stack.pop()
        self.undo_stack.append(next_state)
        return next_state
    
    def can_undo(self):
        """Check if undo is available."""
        return len(self.undo_stack) > 1
    
    def can_redo(self):
        """Check if redo is available."""
        return len(self.redo_stack) > 0
    
    def clear(self):
        """Clear all stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()
    
    def current_state(self):
        """Get the current state."""
        if not self.undo_stack:
            return None
        return self.undo_stack[-1]

class GroupingEditor(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Grouping Editor")
        self.main_layout = QVBoxLayout()
        self.setLayout(self.main_layout)
        
        # Initialize the undo/redo stack
        self.history = UndoRedoStack()
        self._is_table_updating = False
        
        # Create toolbar with undo/redo actions
        self.toolbar = QToolBar("Editor Toolbar")
        
        # Undo action
        self.undo_action = QAction("Undo", self)
        self.undo_action.setShortcut("Ctrl+Z")
        self.undo_action.setStatusTip("Undo last change")
        self.undo_action.triggered.connect(self.undo)
        self.undo_action.setEnabled(False)
        self.toolbar.addAction(self.undo_action)
        
        # Redo action
        self.redo_action = QAction("Redo", self)
        self.redo_action.setShortcut("Ctrl+Y")
        self.redo_action.setStatusTip("Redo last undone change")
        self.redo_action.triggered.connect(self.redo)
        self.redo_action.setEnabled(False)
        self.toolbar.addAction(self.redo_action)
        
        self.toolbar.addSeparator()
        
        # Add action buttons to toolbar
        self.import_action = QAction("Import", self)
        self.import_action.triggered.connect(self.import_groupings)
        self.toolbar.addAction(self.import_action)
        
        self.export_action = QAction("Export", self)
        self.export_action.triggered.connect(self.export_groupings)
        self.toolbar.addAction(self.export_action)
        
        self.reload_action = QAction("Reload", self)
        self.reload_action.triggered.connect(self.reload_table)
        self.toolbar.addAction(self.reload_action)
        
        # Add filter action
        self.filter_action = QAction("Filter", self)
        self.filter_action.triggered.connect(self.filter_data)
        self.toolbar.addAction(self.filter_action)
        
        self.main_layout.addWidget(self.toolbar)
        
        # Create a splitter for the table and preview pane
        self.splitter = QSplitter(Qt.Vertical)
        
        # Setup table
        self.table = QTableWidget()
        self.table.itemChanged.connect(self.on_cell_changed)
        self.table.setToolTip("Double-click a cell to edit groupings")
        
        # Setup preview pane
        self.preview_pane = QTextEdit()
        self.preview_pane.setReadOnly(True)
        self.preview_pane.setMinimumHeight(100)
        self.preview_pane.setPlaceholderText("Change preview will appear here")
        
        # Add widgets to splitter
        self.splitter.addWidget(self.table)
        self.splitter.addWidget(self.preview_pane)
        self.splitter.setSizes([300, 100])  # Initial sizes
        
        # Add splitter to layout
        self.main_layout.addWidget(self.splitter)
        
        # Status label
        self.status_label = QLabel("Status: No data loaded")
        self.main_layout.addWidget(self.status_label)
        
        # Initialize data
        self.group_df = pd.DataFrame()
        self.original_df = pd.DataFrame()  # For comparison/preview
        
        # Timer for delayed updates (to avoid too many rapid changes)
        self.update_timer = QTimer()
        self.update_timer.setSingleShot(True)
        self.update_timer.timeout.connect(self.update_preview)
    
    def add_column_grouping(self, table_name, column_name):
        """
        Create a new grouping based on a column from a Power BI table.
        
        Args:
            table_name: The name of the table in Power BI
            column_name: The name of the column to use for grouping
        """
        try:
            # Ask for grouping settings
            settings_dialog = ColumnGroupingDialog(table_name, column_name, self)
            if settings_dialog.exec_() != QDialog.Accepted:
                return  # User canceled
                
            id_column = settings_dialog.id_column.text()
            first_group = settings_dialog.first_group.text()
            second_group = settings_dialog.second_group.text()
            third_group = settings_dialog.third_group.text()
            
            # Fetch data from Power BI
            self.status_label.setText(f"Fetching data for {column_name}...")
            
            # For now, create a sample dataframe as a demo
            # In a real implementation, you would fetch this from Power BI
            demo_df = pd.DataFrame({
                'Instrument ID': ['BOND1001', 'BOND1002', 'BOND1003', 'BOND1004'],
                'First Group': [first_group] * 4,
                'Second Group': [second_group] * 4,
                'Third Group': [third_group] * 4
            })
            
            # Store original and current data
            self.original_df = demo_df.copy()
            self.group_df = demo_df.copy()
            
            # Reset history with new initial state
            self.history = UndoRedoStack()
            self.history.push(self.group_df.copy())
            
            # Update UI
            self.reload_table()
            self.update_preview()
            self.status_label.setText(f"Created grouping based on {column_name}")
            
            # Update action states
            self.update_undo_redo_state()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create grouping: {str(e)}")
            logging.error(f"Error creating grouping: {e}")
            return False

    def import_groupings(self, file_path=None):
        """Import groupings from a file."""
        if not file_path:
            file_path, _ = QFileDialog.getOpenFileName(
                self, "Open Grouping File", "", 
                "All Files (*.xlsx *.json);;Excel Files (*.xlsx);;JSON Files (*.json)"
            )
            
        if not file_path:
            return

        try:
            if file_path.endswith(".xlsx"):
                df = pd.read_excel(file_path)
            elif file_path.endswith(".json"):
                df = pd.read_json(file_path)
            else:
                raise ValueError("Unsupported file type")

            if not {'Instrument ID', 'First Group', 'Second Group', 'Third Group'}.issubset(df.columns):
                raise ValueError("Missing required grouping columns")

            # Store original and current data
            self.original_df = df.copy()
            self.group_df = df.copy()
            
            # Reset history with new initial state
            self.history = UndoRedoStack()
            self.history.push(self.group_df.copy())
            
            # Update UI
            self.reload_table()
            self.update_preview()
            self.status_label.setText(f"Loaded {len(df)} groupings from {os.path.basename(file_path)}")
            
            # Update action states
            self.update_undo_redo_state()

        except Exception as e:
            QMessageBox.critical(self, "Import Error", str(e))

    def export_groupings(self):
        if self.group_df.empty:
            QMessageBox.warning(self, "Export Error", "No data to export")
            return

        file_path, _ = QFileDialog.getSaveFileName(self, "Save Grouping File", "", "Excel Files (*.xlsx);;JSON Files (*.json)")
        if not file_path:
            return

        try:
            if file_path.endswith(".xlsx"):
                self.group_df.to_excel(file_path, index=False)
            elif file_path.endswith(".json"):
                self.group_df.to_json(file_path, orient='records', indent=2)
            else:
                raise ValueError("Unsupported file extension")

            # Update original data after successful export
            self.original_df = self.group_df.copy()
            self.update_preview()  # Refresh preview pane
            self.status_label.setText(f"Exported groupings to {os.path.basename(file_path)}")

        except Exception as e:
            QMessageBox.critical(self, "Export Error", str(e))

    def reload_table(self):
        self._is_table_updating = True  # Prevent cell change events
        
        self.table.clear()
        if self.group_df.empty:
            self.status_label.setText("Status: No data loaded")
            self._is_table_updating = False
            return

        self.table.setColumnCount(len(self.group_df.columns))
        self.table.setRowCount(len(self.group_df))
        self.table.setHorizontalHeaderLabels(self.group_df.columns.tolist())
        
        # Auto-size columns to content
        header = self.table.horizontalHeader()       
        header.setSectionResizeMode(QHeaderView.ResizeToContents)

        for row_idx, row in self.group_df.iterrows():
            for col_idx, value in enumerate(row):
                item = QTableWidgetItem(str(value))
                # Make Instrument ID read-only
                if self.group_df.columns[col_idx] == 'Instrument ID':
                    item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                self.table.setItem(row_idx, col_idx, item)

        self.status_label.setText(f"Table reloaded with {len(self.group_df)} records")
        self._is_table_updating = False

    def get_groupings(self) -> pd.DataFrame:
        """Collect current table data back into a DataFrame."""
        if self.table.rowCount() == 0:
            return pd.DataFrame()

        data = []
        for row in range(self.table.rowCount()):
            row_data = []
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                row_data.append(item.text() if item else "")
            data.append(row_data)

        return pd.DataFrame(data, columns=self.group_df.columns)
    
    def on_cell_changed(self, item):
        """Handle cell edits and update history."""
        if self._is_table_updating:
            return  # Ignore changes during table updates
            
        # Update internal DataFrame from the table
        self.group_df = self.get_groupings()
        
        # Add to undo history
        self.history.push(self.group_df.copy())
        
        # Update undo/redo action states
        self.update_undo_redo_state()
        
        # Schedule preview update after a short delay (for performance)
        self.update_timer.start(500)  # 500ms delay
    
    def update_undo_redo_state(self):
        """Update the enabled state of undo/redo actions."""
        self.undo_action.setEnabled(self.history.can_undo())
        self.redo_action.setEnabled(self.history.can_redo())
    
    def undo(self):
        """Restore the previous state from history."""
        state = self.history.undo()
        if state is not None:
            self.group_df = state.copy()
            self.reload_table()
            self.update_preview()
        
        self.update_undo_redo_state()
    
    def redo(self):
        """Restore the previously undone state."""
        state = self.history.redo()
        if state is not None:
            self.group_df = state.copy()
            self.reload_table()
            self.update_preview()
        
        self.update_undo_redo_state()
    
    def update_preview(self):
        """Update the preview pane with changes."""
        if self.group_df.empty or self.original_df.empty:
            self.preview_pane.clear()
            return
        
        # Compare current data with original data
        merged = self.group_df.merge(
            self.original_df, 
            on='Instrument ID', 
            how='outer', 
            suffixes=('_current', '_original')
        )
        
        # Identify changed rows
        changes = []
        for idx, row in merged.iterrows():
            instrument_id = row['Instrument ID']
            
            # Check each grouping level for changes
            for level in ['First Group', 'Second Group', 'Third Group']:
                current = row.get(f'{level}_current', '')
                original = row.get(f'{level}_original', '')
                
                if current != original:
                    changes.append({
                        'Instrument ID': instrument_id,
                        'Level': level,
                        'Original': original,
                        'Current': current
                    })
        
        # Format the preview
        if changes:
            html = """
            <style>
                table { width: 100%; border-collapse: collapse; }
                th { background-color: #f0f0f0; }
                th, td { border: 1px solid #ccc; padding: 4px; text-align: left; }
                .changed { background-color: #ffff99; }
                .header { font-weight: bold; margin-bottom: 5px; }
            </style>
            <div class="header">Changes ({num_changes}):</div>
            <table>
                <tr>
                    <th>Instrument ID</th>
                    <th>Group Level</th>
                    <th>Original Value</th>
                    <th>New Value</th>
                </tr>
            """.format(num_changes=len(changes))
            
            for change in changes:
                html += f"""
                <tr class="changed">
                    <td>{change['Instrument ID']}</td>
                    <td>{change['Level']}</td>
                    <td>{change['Original']}</td>
                    <td>{change['Current']}</td>
                </tr>
                """
            
            html += "</table>"
            self.preview_pane.setHtml(html)
        else:
            self.preview_pane.setPlainText("No changes detected.")
    
    def filter_data(self):
        """Show a dialog to filter the data by instrument ID or group."""
        # This is a simple implementation - could be expanded with more filter options
        filter_text, ok = QFileDialog.getOpenFileName(
            self, "Enter filter text (case-sensitive)", "", 
            "Filter value contains:"
        )
        
        if not ok or not filter_text:
            return
            
        # Apply filter to all columns
        mask = False
        for col in self.group_df.columns:
            mask |= self.group_df[col].astype(str).str.contains(filter_text, na=False)
        
        filtered_df = self.group_df[mask]
        
        if len(filtered_df) == 0:
            QMessageBox.information(self, "Filter Results", "No matching records found.")
            return
            
        # Temporarily set the filtered view
        temp_df = self.group_df.copy()  # Save current state
        self._is_table_updating = True
        self.group_df = filtered_df
        self.reload_table()
        self._is_table_updating = False
        
        # Ask if user wants to keep the filter
        response = QMessageBox.question(
            self, 
            "Filter Applied", 
            f"Showing {len(filtered_df)} of {len(temp_df)} records. Keep filter?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if response == QMessageBox.No:
            self._is_table_updating = True
            self.group_df = temp_df
            self.reload_table()
            self._is_table_updating = False

    def import_file(self, file_path):
        """Legacy method for backwards compatibility"""
        return self.import_groupings(file_path)


class ColumnGroupingDialog(QDialog):
    """Dialog for configuring column grouping settings."""
    
    def __init__(self, table_name, column_name, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configure Grouping")
        self.resize(400, 200)
        
        layout = QVBoxLayout(self)
        
        # Description
        description = QLabel(
            f"Create a grouping based on column '{column_name}' from table '{table_name}'.\n"
            "Please provide the following information:"
        )
        description.setWordWrap(True)
        layout.addWidget(description)
        
        # Form for settings
        form_layout = QFormLayout()
        
        self.id_column = QLineEdit("Instrument ID")
        form_layout.addRow("ID Column:", self.id_column)
        
        self.first_group = QLineEdit(column_name)  # Default to column name
        form_layout.addRow("First Group Name:", self.first_group)
        
        self.second_group = QLineEdit("Category")
        form_layout.addRow("Second Group Name:", self.second_group)
        
        self.third_group = QLineEdit("SubCategory")
        form_layout.addRow("Third Group Name:", self.third_group)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
