# gui/theme_manager.py

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtCore import Qt

class ThemeManager:
    """
    Manager for application themes (light/dark).
    """
    
    @staticmethod
    def apply_light_theme(app):
        """Apply the light theme to the application."""
        app.setStyle("Fusion")
        palette = QPalette()
        app.setPalette(palette)
        
        # Set default stylesheet
        app.setStyleSheet("""
            QToolTip { 
                color: #000000; 
                background-color: #fafafa; 
                border: 1px solid #aaaaaa;
                border-radius: 3px;
                padding: 3px;
            }
            
            QSplitter::handle:horizontal {
                width: 1px;
                background-color: #cccccc;
            }
            
            QSplitter::handle:vertical {
                height: 1px;
                background-color: #cccccc;
            }
        """)
        
        return "Light"
    
    @staticmethod
    def apply_dark_theme(app):
        """Apply the dark theme to the application."""
        app.setStyle("Fusion")
        
        # Set dark color palette
        dark_palette = QPalette()
        dark_palette.setColor(QPalette.Window, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.WindowText, Qt.white)
        dark_palette.setColor(QPalette.Base, QColor(35, 35, 35))
        dark_palette.setColor(QPalette.AlternateBase, QColor(43, 43, 43))
        dark_palette.setColor(QPalette.ToolTipBase, QColor(25, 25, 25))
        dark_palette.setColor(QPalette.ToolTipText, Qt.white)
        dark_palette.setColor(QPalette.Text, Qt.white)
        dark_palette.setColor(QPalette.Button, QColor(53, 53, 53))
        dark_palette.setColor(QPalette.ButtonText, Qt.white)
        dark_palette.setColor(QPalette.BrightText, Qt.red)
        dark_palette.setColor(QPalette.Link, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.Highlight, QColor(42, 130, 218))
        dark_palette.setColor(QPalette.HighlightedText, Qt.black)
        
        app.setPalette(dark_palette)
        
        # Set stylesheet for additional customization
        app.setStyleSheet("""
            QToolTip { 
                color: #ffffff; 
                background-color: #2a2a2a; 
                border: 1px solid #666666;
                border-radius: 3px;
                padding: 3px;
            }
            
            QTableWidget {
                gridline-color: #555555;
            }
            
            QHeaderView::section {
                background-color: #404040;
                color: white;
                padding: 4px;
                border: 1px solid #606060;
            }
            
            QSplitter::handle:horizontal {
                width: 1px;
                background-color: #666666;
            }
            
            QSplitter::handle:vertical {
                height: 1px;
                background-color: #666666;
            }
            
            QTabBar::tab {
                background-color: #404040;
                color: white;
                padding: 8px 16px;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                margin-right: 2px;
            }
            
            QTabBar::tab:selected {
                background-color: #2a82da;
            }
            
            QTreeView {
                alternate-background-color: #404040;
            }
        """)
        
        return "Dark"
    
    @staticmethod
    def apply_theme(app, theme_name):
        """Apply the specified theme to the application."""
        if theme_name.lower() == "dark":
            return ThemeManager.apply_dark_theme(app)
        else:
            return ThemeManager.apply_light_theme(app)
            
    @staticmethod
    def toggle_theme(app, current_theme):
        """Toggle between light and dark themes."""
        if current_theme.lower() == "dark":
            return ThemeManager.apply_light_theme(app)
        else:
            return ThemeManager.apply_dark_theme(app) 