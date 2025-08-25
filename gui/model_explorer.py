# gui/model_explorer.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTreeWidget, QTreeWidgetItem,
    QLabel, QLineEdit, QComboBox, QMessageBox, QApplication, QMenu, QAction,
    QTabWidget, QTextEdit, QSplitter, QStatusBar, QHeaderView
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QIcon, QCursor
import pandas as pd
from backend.dax_info_views import DaxMetadataExplorer

class ModelExplorer(QWidget):
    """
    A tree-based explorer for navigating Power BI model metadata.
    Shows tables, columns, relationships, and hierarchies.
    """
    
    # Signal emitted when an item is double-clicked
    item_selected = pyqtSignal(str, str, str)  # type, name, parent
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Model Explorer")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)
        
        # Initialize the metadata explorer
        self.explorer = DaxMetadataExplorer()
        
        # Create search and filter controls
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search...")
        self.search_input.textChanged.connect(self.on_search_changed)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Tables", "Columns", "Relationships", "Hierarchies"])
        self.filter_combo.currentTextChanged.connect(self.refresh_tree)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.refresh_metadata)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.filter_combo)
        search_layout.addWidget(self.refresh_btn)
        
        self.layout.addLayout(search_layout)
        
        # Create tree for metadata navigation
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Name", "Type", "Properties"])
        self.tree.setColumnCount(3)
        self.tree.setAlternatingRowColors(True)
        self.tree.itemDoubleClicked.connect(self.on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        
        # Auto-size columns
        header = self.tree.header()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        
        # Create splitter with tree and details pane
        self.splitter = QSplitter(Qt.Vertical)
        
        self.details_pane = QTextEdit()
        self.details_pane.setReadOnly(True)
        self.details_pane.setPlaceholderText("Select an item to view details")
        
        self.splitter.addWidget(self.tree)
        self.splitter.addWidget(self.details_pane)
        self.splitter.setSizes([300, 100])
        
        self.layout.addWidget(self.splitter)
        
        # Status bar
        self.status_label = QLabel("Ready")
        self.layout.addWidget(self.status_label)
        
        # Initialize metadata cache
        self._metadata = {
            "tables": None,
            "columns": None,
            "relationships": None,
            "hierarchies": None
        }
        
        # Delayed search timer
        self.search_timer = QTimer()
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(self.perform_search)
        
        # Load metadata on startup
        QTimer.singleShot(100, self.refresh_metadata)
    
    def refresh_metadata(self):
        """Refresh all metadata from the Power BI model."""
        try:
            self.status_label.setText("Connecting to Power BI model...")
            QApplication.processEvents()
            
            # Clear cache
            for key in self._metadata:
                self._metadata[key] = None
            
            # Load tables
            self.status_label.setText("Loading tables...")
            QApplication.processEvents()
            self._metadata["tables"] = self.explorer.get_tables(force_refresh=True)
            
            # Load columns
            self.status_label.setText("Loading columns...")
            QApplication.processEvents()
            self._metadata["columns"] = self.explorer.get_columns(force_refresh=True)
            
            # Load relationships
            self.status_label.setText("Loading relationships...")
            QApplication.processEvents()
            self._metadata["relationships"] = self.explorer.get_relationships(force_refresh=True)
            
            # Load hierarchies
            self.status_label.setText("Loading hierarchies...")
            QApplication.processEvents()
            self._metadata["hierarchies"] = self.explorer.get_hierarchies(force_refresh=True)
            
            # Update the tree
            self.refresh_tree()
            
            self.status_label.setText(f"Loaded {len(self._metadata['tables'])} tables, " +
                                     f"{len(self._metadata['columns'])} columns, " +
                                     f"{len(self._metadata['relationships'])} relationships")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            QMessageBox.critical(self, "Connection Error", 
                                f"Failed to connect to Power BI model:\n{str(e)}")
    
    def refresh_tree(self):
        """Refresh the tree view with current metadata."""
        self.tree.clear()
        filter_text = self.filter_combo.currentText()
        
        # Create root nodes
        if filter_text in ["All", "Tables"]:
            tables_node = QTreeWidgetItem(self.tree, ["Tables", "", f"{len(self._metadata['tables'])} items"])
            tables_node.setExpanded(True)
            self.populate_tables(tables_node)
        
        if filter_text in ["All", "Relationships"]:
            rels_node = QTreeWidgetItem(self.tree, ["Relationships", "", f"{len(self._metadata['relationships'])} items"])
            self.populate_relationships(rels_node)
        
        if filter_text in ["All", "Hierarchies"]:
            hier_node = QTreeWidgetItem(self.tree, ["Hierarchies", "", f"{len(self._metadata['hierarchies'])} items"])
            self.populate_hierarchies(hier_node)
    
    def populate_tables(self, parent_node):
        """Populate the tree with tables and their columns."""
        if self._metadata["tables"] is None or self._metadata["columns"] is None:
            return
            
        for idx, row in self._metadata["tables"].iterrows():
            table_name = row["Table"]
            is_hidden = row["IsHidden"] if not pd.isna(row["IsHidden"]) else False
            
            # Create table node
            display_name = f"{table_name}"
            if is_hidden:
                display_name += " (Hidden)"
                
            table_node = QTreeWidgetItem(parent_node, [display_name, "Table", ""])
            table_node.setData(0, Qt.UserRole, {"type": "table", "name": table_name})
            
            # Get columns for this table
            columns = self._metadata["columns"]
            table_columns = columns[columns["Table"] == table_name]
            
            for _, col_row in table_columns.iterrows():
                col_name = col_row["Column"]
                col_type = col_row["DataType"] if not pd.isna(col_row["DataType"]) else ""
                col_hidden = col_row["IsHidden"] if not pd.isna(col_row["IsHidden"]) else False
                
                # Create column node
                col_display = f"{col_name}"
                if col_hidden:
                    col_display += " (Hidden)"
                    
                col_node = QTreeWidgetItem(table_node, [col_display, "Column", col_type])
                col_node.setData(0, Qt.UserRole, {"type": "column", "name": col_name, "parent": table_name})
    
    def populate_relationships(self, parent_node):
        """Populate the tree with relationships."""
        if self._metadata["relationships"] is None:
            return
            
        for idx, row in self._metadata["relationships"].iterrows():
            from_table = row["FromTable"]
            from_col = row["FromColumn"]
            to_table = row["ToTable"]
            to_col = row["ToColumn"]
            is_active = row["IsActive"] if not pd.isna(row["IsActive"]) else True
            
            # Create relationship node
            display_name = f"{from_table} → {to_table}"
            if not is_active:
                display_name += " (Inactive)"
                
            details = f"{from_table}[{from_col}] to {to_table}[{to_col}]"
            rel_node = QTreeWidgetItem(parent_node, [display_name, "Relationship", details])
            rel_node.setData(0, Qt.UserRole, {
                "type": "relationship", 
                "name": f"{from_table}_{to_table}",
                "from_table": from_table,
                "from_column": from_col,
                "to_table": to_table,
                "to_column": to_col
            })
    
    def populate_hierarchies(self, parent_node):
        """Populate the tree with hierarchies."""
        if self._metadata["hierarchies"] is None:
            return
            
        for idx, row in self._metadata["hierarchies"].iterrows():
            hier_name = row["Hierarchy"]
            table_name = row["Table"]
            
            # Create hierarchy node
            display_name = f"{hier_name}"
            hier_node = QTreeWidgetItem(parent_node, [display_name, "Hierarchy", f"Table: {table_name}"])
            hier_node.setData(0, Qt.UserRole, {"type": "hierarchy", "name": hier_name, "parent": table_name})
    
    def on_item_double_clicked(self, item, column):
        """Handle double-click on tree item."""
        data = item.data(0, Qt.UserRole)
        if data:
            item_type = data.get("type")
            item_name = data.get("name")
            parent = data.get("parent", "")
            
            # Show details in the details pane
            self.show_item_details(data)
            
            # Emit signal for other components to use
            self.item_selected.emit(item_type, item_name, parent)
    
    def show_item_details(self, data):
        """Show detailed information about the selected item."""
        item_type = data.get("type")
        item_name = data.get("name")
        
        if item_type == "table":
            self.show_table_details(item_name)
        elif item_type == "column":
            parent = data.get("parent", "")
            self.show_column_details(parent, item_name)
        elif item_type == "relationship":
            self.show_relationship_details(data)
        elif item_type == "hierarchy":
            parent = data.get("parent", "")
            self.show_hierarchy_details(parent, item_name)
    
    def show_table_details(self, table_name):
        """Show details for a table."""
        try:
            # Get table metadata
            table_row = self._metadata["tables"][self._metadata["tables"]["Table"] == table_name].iloc[0]
            
            # Count columns
            columns = self._metadata["columns"]
            table_columns = columns[columns["Table"] == table_name]
            
            # Build HTML details
            html = f"""
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #0066cc; }}
                .metadata {{ margin-bottom: 15px; }}
                .property {{ font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
            <h2>Table: {table_name}</h2>
            <div class="metadata">
                <p><span class="property">Description:</span> {table_row.get('Description', '')}</p>
                <p><span class="property">Hidden:</span> {table_row.get('IsHidden', False)}</p>
                <p><span class="property">Row Count:</span> {table_row.get('RowCount', 'Unknown')}</p>
                <p><span class="property">Column Count:</span> {len(table_columns)}</p>
            </div>
            <h3>Columns:</h3>
            <table>
                <tr>
                    <th>Name</th>
                    <th>Data Type</th>
                    <th>Hidden</th>
                </tr>
            """
            
            for _, col in table_columns.iterrows():
                html += f"""
                <tr>
                    <td>{col.get('Column', '')}</td>
                    <td>{col.get('DataType', '')}</td>
                    <td>{'Yes' if col.get('IsHidden', False) else 'No'}</td>
                </tr>
                """
            
            html += "</table>"
            
            self.details_pane.setHtml(html)
            
        except Exception as e:
            self.details_pane.setPlainText(f"Error loading table details: {str(e)}")
    
    def show_column_details(self, table_name, column_name):
        """Show details for a column."""
        try:
            # Get column metadata
            columns = self._metadata["columns"]
            column_row = columns[(columns["Table"] == table_name) & 
                               (columns["Column"] == column_name)].iloc[0]
            
            # Find relationships involving this column
            relationships = self._metadata["relationships"]
            from_rels = relationships[(relationships["FromTable"] == table_name) & 
                                   (relationships["FromColumn"] == column_name)]
            to_rels = relationships[(relationships["ToTable"] == table_name) & 
                                 (relationships["ToColumn"] == column_name)]
            
            # Build HTML details
            html = f"""
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #0066cc; }}
                h3 {{ color: #0099cc; }}
                .metadata {{ margin-bottom: 15px; }}
                .property {{ font-weight: bold; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
            <h2>Column: {table_name}[{column_name}]</h2>
            <div class="metadata">
                <p><span class="property">Data Type:</span> {column_row.get('DataType', '')}</p>
                <p><span class="property">Hidden:</span> {column_row.get('IsHidden', False)}</p>
                <p><span class="property">Description:</span> {column_row.get('Description', '')}</p>
            </div>
            """
            
            if not from_rels.empty or not to_rels.empty:
                html += "<h3>Relationships:</h3><ul>"
                
                for _, rel in from_rels.iterrows():
                    html += f"""<li>{table_name}[{column_name}] → {rel['ToTable']}[{rel['ToColumn']}]
                             {"(Inactive)" if not rel['IsActive'] else ""}</li>"""
                
                for _, rel in to_rels.iterrows():
                    html += f"""<li>{rel['FromTable']}[{rel['FromColumn']}] → {table_name}[{column_name}]
                             {"(Inactive)" if not rel['IsActive'] else ""}</li>"""
                
                html += "</ul>"
            
            self.details_pane.setHtml(html)
            
        except Exception as e:
            self.details_pane.setPlainText(f"Error loading column details: {str(e)}")
    
    def show_relationship_details(self, data):
        """Show details for a relationship."""
        try:
            from_table = data.get("from_table", "")
            from_column = data.get("from_column", "")
            to_table = data.get("to_table", "")
            to_column = data.get("to_column", "")
            
            # Get relationship metadata
            relationships = self._metadata["relationships"]
            rel_row = relationships[(relationships["FromTable"] == from_table) & 
                                 (relationships["FromColumn"] == from_column) &
                                 (relationships["ToTable"] == to_table) & 
                                 (relationships["ToColumn"] == to_column)].iloc[0]
            
            # Build HTML details
            html = f"""
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #0066cc; }}
                .metadata {{ margin-bottom: 15px; }}
                .property {{ font-weight: bold; }}
                .diagram {{ margin: 20px 0; padding: 15px; background-color: #f8f8f8; border-radius: 5px; }}
                .arrow {{ font-size: 24px; margin: 0 10px; }}
            </style>
            <h2>Relationship</h2>
            <div class="metadata">
                <p><span class="property">From:</span> {from_table}[{from_column}]</p>
                <p><span class="property">To:</span> {to_table}[{to_column}]</p>
                <p><span class="property">Active:</span> {rel_row.get('IsActive', True)}</p>
                <p><span class="property">Cross Filter:</span> {rel_row.get('CrossFilteringBehavior', '')}</p>
            </div>
            <div class="diagram">
                <strong>{from_table}</strong>
                <span class="arrow">→</span>
                <strong>{to_table}</strong>
            </div>
            """
            
            self.details_pane.setHtml(html)
            
        except Exception as e:
            self.details_pane.setPlainText(f"Error loading relationship details: {str(e)}")
    
    def show_hierarchy_details(self, table_name, hierarchy_name):
        """Show details for a hierarchy."""
        try:
            # Get hierarchy metadata
            hierarchies = self._metadata["hierarchies"]
            hier_row = hierarchies[(hierarchies["Table"] == table_name) & 
                                (hierarchies["Hierarchy"] == hierarchy_name)].iloc[0]
            
            # Build HTML details
            html = f"""
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #0066cc; }}
                .metadata {{ margin-bottom: 15px; }}
                .property {{ font-weight: bold; }}
            </style>
            <h2>Hierarchy: {hierarchy_name}</h2>
            <div class="metadata">
                <p><span class="property">Table:</span> {table_name}</p>
                <p><span class="property">Description:</span> {hier_row.get('Description', '')}</p>
            </div>
            """
            
            self.details_pane.setHtml(html)
            
        except Exception as e:
            self.details_pane.setPlainText(f"Error loading hierarchy details: {str(e)}")
    
    def on_search_changed(self):
        """Handle search text changes with debouncing."""
        # Restart the timer to avoid searching on every keystroke
        self.search_timer.start(300)  # 300ms delay
    
    def perform_search(self):
        """Perform the actual search."""
        search_text = self.search_input.text().strip().lower()
        if not search_text:
            self.refresh_tree()
            return
            
        self.tree.clear()
        results_node = QTreeWidgetItem(self.tree, [f"Search Results: '{search_text}'", "", ""])
        results_node.setExpanded(True)
        
        # Search tables
        if self._metadata["tables"] is not None:
            tables = self._metadata["tables"]
            matching_tables = tables[tables["Table"].str.lower().str.contains(search_text)]
            
            if not matching_tables.empty:
                tables_node = QTreeWidgetItem(results_node, [f"Tables ({len(matching_tables)})", "", ""])
                tables_node.setExpanded(True)
                
                for _, row in matching_tables.iterrows():
                    table_name = row["Table"]
                    table_node = QTreeWidgetItem(tables_node, [table_name, "Table", ""])
                    table_node.setData(0, Qt.UserRole, {"type": "table", "name": table_name})
        
        # Search columns
        if self._metadata["columns"] is not None:
            columns = self._metadata["columns"]
            matching_columns = columns[columns["Column"].str.lower().str.contains(search_text)]
            
            if not matching_columns.empty:
                columns_node = QTreeWidgetItem(results_node, [f"Columns ({len(matching_columns)})", "", ""])
                columns_node.setExpanded(True)
                
                for _, row in matching_columns.iterrows():
                    col_name = row["Column"]
                    table_name = row["Table"]
                    col_node = QTreeWidgetItem(columns_node, [col_name, "Column", f"Table: {table_name}"])
                    col_node.setData(0, Qt.UserRole, {"type": "column", "name": col_name, "parent": table_name})
    
    def show_context_menu(self, position):
        """Show context menu for tree items."""
        item = self.tree.itemAt(position)
        if not item:
            return
            
        data = item.data(0, Qt.UserRole)
        if not data:
            return
            
        menu = QMenu()
        item_type = data.get("type")
        
        if item_type == "table":
            action = QAction("Copy Table Name", self)
            action.triggered.connect(lambda: QApplication.clipboard().setText(data.get("name", "")))
            menu.addAction(action)
            
            action = QAction("View Data Preview", self)
            action.triggered.connect(lambda: self.preview_table_data(data.get("name", "")))
            menu.addAction(action)
            
        elif item_type == "column":
            action = QAction("Copy Column Name", self)
            action.triggered.connect(lambda: QApplication.clipboard().setText(data.get("name", "")))
            menu.addAction(action)
            
            action = QAction("Copy Table.Column", self)
            action.triggered.connect(lambda: QApplication.clipboard().setText(
                f"{data.get('parent', '')}[{data.get('name', '')}]"))
            menu.addAction(action)
            
        menu.exec_(QCursor.pos())
    
    def preview_table_data(self, table_name):
        """Show a preview of table data."""
        try:
            # Build DAX query to get table data
            query = f"EVALUATE TOP(100, '{table_name}')"
            
            # Execute query and get data
            conn = self.explorer.connect()
            cursor = conn.cursor()
            results = cursor.execute(query)
            df = pd.DataFrame(results.fetchall())
            
            if len(df) == 0:
                self.status_label.setText(f"No data in table: {table_name}")
                self.details_pane.setPlainText("Table contains no data.")
                return
                
            # Set column names from the results
            if hasattr(results, 'description'):
                df.columns = [col[0] for col in results.description]
            
            # Convert to HTML table
            html = f"""
            <style>
                body {{ font-family: Arial, sans-serif; }}
                h2 {{ color: #0066cc; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
            </style>
            <h2>Data Preview: {table_name}</h2>
            <p>Showing first {len(df)} rows (max 100)</p>
            {df.to_html(index=False)}
            """
            
            self.details_pane.setHtml(html)
            self.status_label.setText(f"Loaded data preview for {table_name}")
            
        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.details_pane.setPlainText(f"Error loading data preview: {str(e)}")
            QMessageBox.warning(self, "Preview Error", f"Failed to load data preview:\n{str(e)}") 