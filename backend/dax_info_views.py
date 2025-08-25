import pandas as pd
from pyadomd import Pyadomd
from backend.model_connector import ModelConnector

class DaxMetadataExplorer:
    """
    Class for exploring Power BI model metadata using DAX INFO.VIEW queries.
    Provides access to tables, columns, measures, relationships, and hierarchies.
    """
    
    def __init__(self, connection_string=None):
        """Initialize with an optional connection string or use the ModelConnector."""
        self.connector = ModelConnector()
        self.connection_string = connection_string
        self._conn = None
        self._metadata_cache = {}
    
    def connect(self):
        """Establish connection to the Power BI model."""
        if self._conn is not None:
            return self._conn
            
        if self.connection_string is None:
            port = self.connector.detect_port()
            self.connection_string = f"Provider=MSOLAP;Data Source=localhost:{port}"
        
        try:
            self._conn = Pyadomd(self.connection_string)
            self._conn.open()
            return self._conn
        except Exception as e:
            raise ConnectionError(f"Failed to connect to Power BI model: {e}")
    
    def disconnect(self):
        """Close the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
    
    def _execute_query(self, query):
        """Execute a DAX query and return results as a DataFrame."""
        conn = self.connect()
        cursor = conn.cursor()
        results = cursor.execute(query)
        return pd.DataFrame(results.fetchall())
    
    def get_tables(self, force_refresh=False):
        """Get all tables in the model."""
        if "tables" in self._metadata_cache and not force_refresh:
            return self._metadata_cache["tables"]
            
        query = """
        EVALUATE
        SELECTCOLUMNS(
            INFO.VIEW.TABLES(),
            "Table", [Name],
            "Description", [Description],
            "IsHidden", [IsHidden],
            "RowCount", [RowCount]
        )
        ORDER BY [Name]
        """
        
        df = self._execute_query(query)
        if len(df.columns) > 0:
            df.columns = ["Table", "Description", "IsHidden", "RowCount"]
        else:
            df = pd.DataFrame(columns=["Table", "Description", "IsHidden", "RowCount"])
        
        self._metadata_cache["tables"] = df
        return df
    
    def get_columns(self, table_name=None, force_refresh=False):
        """Get columns, optionally filtering by table."""
        cache_key = f"columns_{table_name}" if table_name else "columns"
        
        if cache_key in self._metadata_cache and not force_refresh:
            return self._metadata_cache[cache_key]
        
        query = """
        EVALUATE
        SELECTCOLUMNS(
            INFO.VIEW.COLUMNS(),
            "Column", [Name],
            "Table", [Table],
            "DataType", [DataType],
            "IsHidden", [IsHidden],
            "Description", [Description]
        )
        """
        
        if table_name:
            query += f"\nWHERE [Table] = \"{table_name}\"\n"
            
        query += "ORDER BY [Table], [Name]"
        
        df = self._execute_query(query)
        if len(df.columns) > 0:
            df.columns = ["Column", "Table", "DataType", "IsHidden", "Description"]
        else:
            df = pd.DataFrame(columns=["Column", "Table", "DataType", "IsHidden", "Description"])
        
        self._metadata_cache[cache_key] = df
        return df
    
    def get_relationships(self, force_refresh=False):
        """Get all relationships in the model."""
        if "relationships" in self._metadata_cache and not force_refresh:
            return self._metadata_cache["relationships"]
            
        query = """
        EVALUATE
        SELECTCOLUMNS(
            INFO.VIEW.RELATIONSHIPS(),
            "FromTable", [FromTable],
            "FromColumn", [FromColumn],
            "ToTable", [ToTable],
            "ToColumn", [ToColumn],
            "IsActive", [IsActive],
            "CrossFilteringBehavior", [CrossFilteringBehavior]
        )
        ORDER BY [FromTable], [ToTable]
        """
        
        df = self._execute_query(query)
        if len(df.columns) > 0:
            df.columns = ["FromTable", "FromColumn", "ToTable", "ToColumn", "IsActive", "CrossFilteringBehavior"]
        else:
            df = pd.DataFrame(columns=["FromTable", "FromColumn", "ToTable", "ToColumn", "IsActive", "CrossFilteringBehavior"])
        
        self._metadata_cache["relationships"] = df
        return df
    
    def get_hierarchies(self, force_refresh=False):
        """Get all hierarchies in the model."""
        if "hierarchies" in self._metadata_cache and not force_refresh:
            return self._metadata_cache["hierarchies"]
            
        query = """
        EVALUATE
        SELECTCOLUMNS(
            INFO.VIEW.HIERARCHIES(),
            "Hierarchy", [Name],
            "Table", [Table],
            "Description", [Description]
        )
        ORDER BY [Table], [Name]
        """
        
        df = self._execute_query(query)
        if len(df.columns) > 0:
            df.columns = ["Hierarchy", "Table", "Description"]
        else:
            df = pd.DataFrame(columns=["Hierarchy", "Table", "Description"])
        
        self._metadata_cache["hierarchies"] = df
        return df
    
    def search_metadata(self, search_term, case_sensitive=False):
        """
        Search across tables, columns, and hierarchies for matching names.
        Returns a dictionary with dataframes for each category.
        """
        results = {}
        
        # Get all metadata
        tables = self.get_tables()
        columns = self.get_columns()
        hierarchies = self.get_hierarchies()
        
        # Case-insensitive search if requested
        if not case_sensitive:
            search_term = search_term.lower()
            
            # Filter tables
            results["tables"] = tables[
                tables["Table"].str.lower().str.contains(search_term) | 
                tables["Description"].fillna("").str.lower().str.contains(search_term)
            ]
            
            # Filter columns
            results["columns"] = columns[
                columns["Column"].str.lower().str.contains(search_term) | 
                columns["Table"].str.lower().str.contains(search_term) |
                columns["Description"].fillna("").str.lower().str.contains(search_term)
            ]
            
            # Filter hierarchies
            results["hierarchies"] = hierarchies[
                hierarchies["Hierarchy"].str.lower().str.contains(search_term) | 
                hierarchies["Table"].str.lower().str.contains(search_term) |
                hierarchies["Description"].fillna("").str.lower().str.contains(search_term)
            ]
        else:
            # Case-sensitive search
            results["tables"] = tables[
                tables["Table"].str.contains(search_term) | 
                tables["Description"].fillna("").str.contains(search_term)
            ]
            
            results["columns"] = columns[
                columns["Column"].str.contains(search_term) | 
                columns["Table"].str.contains(search_term) |
                columns["Description"].fillna("").str.contains(search_term)
            ]
            
            results["hierarchies"] = hierarchies[
                hierarchies["Hierarchy"].str.contains(search_term) | 
                hierarchies["Table"].str.contains(search_term) |
                hierarchies["Description"].fillna("").str.contains(search_term)
            ]
            
        return results
    
    def clear_cache(self):
        """Clear the metadata cache."""
        self._metadata_cache = {}
        
    def __del__(self):
        """Ensure connection is closed when object is destroyed."""
        self.disconnect() 