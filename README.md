# TMDL Live Editor (Python Edition)

A **local Python desktop application** for modifying the TMDL (Tabular Model Definition Language) of a **live Power BI Desktop model** via the XMLA endpoint and `pyadomd`. Designed as a lightweight, fast, and fully integrated replacement for Armanta, it enables dynamic custom grouping and hierarchy editing directly within the Power BI ecosystem.

---

## Why Replace Armanta?

### Armanta Limitations:
- Refresh cycles take up to an hour
- High external system and maintenance overhead
- Separate from the Power BI platform
- Complex licensing and infrastructure

### Python-Based TMDL Live Editor Advantages:
- ✅ Direct, low-latency access to live Power BI Desktop models
- ✅ No external servers or services needed
- ✅ Uses Power BI's native XMLA endpoint for live edits
- ✅ Python-powered GUI and scripting flexibility
- ✅ No browser, no Node.js, no Electron

---

## Features

- 🔌 **Live Connection** to Power BI Desktop via XMLA (`localhost:<port>`)
- 🧱 **Dynamic Grouping Interface**: Update hierarchies and group rules in real time
- 🔎 **Filter & Search**: Explore instruments across multiple dimensions
- 🧪 **Preview Changes**: Safely simulate before applying
- 📦 **Batch Modifications**: Apply updates at scale
- 🔄 **Immediate Model Updates**: Changes take effect instantly
- 💻 **Local Python UI** using PyQt5

---

## Installation

### Prerequisites

- Python 3.8 or higher
- Power BI Desktop
- Tabular Editor (installed locally)
- ADOMD.NET client libraries (usually installed with Power BI)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/tmdl-editor-python.git
   cd tmdl-editor-python
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Ensure Tabular Editor is installed at the default path or update the path in `backend/tabular_editor_cli.py`.

---

## Usage

### Running the Application

1. Open Power BI Desktop with your model

2. Launch the TMDL Live Editor:
   ```
   python tmdl_editor_gui.py
   ```

3. The application will automatically detect the Power BI Desktop XMLA port

### Using the Grouping Editor

1. Import groupings from Excel or JSON (File -> Import Groupings)
2. Edit groupings in the table
3. Preview changes in the preview pane
4. Push changes to Power BI (Push Groupings button)

### Using the Model Explorer

1. Navigate your Power BI model structure
2. Explore tables, columns, relationships, and hierarchies
3. Double-click items to view details
4. Right-click for context menu options

### Command-Line Interface

For automation and scripting, use the CLI tool:

```
python -m cli.tmdl_cli --help
```

Example commands:

```
# Import groupings from a file and push to Power BI
python -m cli.tmdl_cli import data/groupings.xlsx --table InstrumentGroupings

# Export groupings from Power BI to a file
python -m cli.tmdl_cli export groupings_export.json --table InstrumentGroupings

# Get information about the Power BI model
python -m cli.tmdl_cli info --tables
```

---

## Development

### Running Tests

To run all tests:

```
python run_tests.py
```

### Project Structure

- `backend/`: Core functionality for connecting to and updating Power BI
- `gui/`: PyQt5 user interface components
- `utils/`: Utility functions for file I/O, logging, etc.
- `cli/`: Command-line interface for scripting and automation
- `tests/`: Unit and integration tests
- `data/`: Sample data files

---

## Schema Design

### Grouping Hierarchy Table:
- `Instrument ID` (PK)
- `First Group`
- `Second Group`
- `Third Group`

### Joined Metadata Table:
- `Rating`
- `LB1 Class Code Desc`
- `Bloomberg_Ticker`
- `Maturity Years`

---

## Technology Stack

- **Python 3.x**
- [`pyadomd`](https://pypi.org/project/pyadomd/)
- `Microsoft.AnalysisServices.AdomdClient.dll` via `pythonnet`
- GUI: PyQt5

---

## Troubleshooting

### Common Issues

- **Connection Failed**: Ensure Power BI Desktop is running and has a model open
- **Port Detection Failed**: The application may need to be run as Administrator
- **Tabular Editor Not Found**: Verify Tabular Editor is installed at the expected path

### Logs

Log files are stored in the `logs/` directory and can be helpful for diagnosing issues.

```python
from pyadomd import Pyadomd
import pandas as pd
import clr
clr.AddReference(r"C:\Program Files\Microsoft.NET\ADOMD.NET\160\Microsoft.AnalysisServices.AdomdClient.dll")
from Microsoft.AnalysisServices.AdomdClient import AdomdConnection

# Replace with your actual local port from Power BI Desktop
conn_str = 'Provider=MSOLAP;Data Source=localhost:56888'

conn = Pyadomd(conn_str)
conn.open()

# Get table list
tables_df = pd.DataFrame(conn.cursor().execute("""
EVALUATE SELECTCOLUMNS(INFO.VIEW.TABLES(), "Table", [Name])
""").fetchall(), columns=["Table"])

# Get column list
columns_df = pd.DataFrame(conn.cursor().execute("""
EVALUATE SELECTCOLUMNS(INFO.VIEW.COLUMNS(), "Column", [Name], "Table", [Table])
""").fetchall(), columns=["Column", "Table"])
