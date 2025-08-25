# 🛠 TMDL Live Editor – Implementation Plan

This file outlines the phased development plan for the Python-based TMDL Live Editor application. The app enables real-time modification of a Power BI Desktop model using the local XMLA endpoint.

---

## 📌 Phase 1: Core Functionality (Back-End Foundation)

### Features
- [x] Connect to XMLA endpoint via `pyadomd`
- [x] Query `INFO.VIEW.TABLES()` and `INFO.VIEW.COLUMNS()`
- [ ] CLI-based import/export (JSON, Excel)
- [ ] Apply grouping edits to Power BI model via XMLA

### Milestone 1: **Backend Ready**
**ETA:** End of Week 1  
- Validate XMLA queries  
- Test basic export/import logic  
- Unit test JSON/Excel handling

---

## 📌 Phase 2: Metadata Navigation Engine

### Features
- [ ] Interactive table/column/relationship explorer
- [ ] Drilldown: tables → columns → relationships
- [ ] Caching metadata for reuse

### Milestone 2: **Schema Explorer Functional**
**ETA:** End of Week 2  
- Drilldown CLI utility  
- Filter and search in INFO.VIEW results  
- Integration tested with real Power BI models

---

## 📌 Phase 3: GUI Architecture Setup

### Features
- [ ] Choose and implement GUI framework (Tkinter / PyQt5)
- [ ] Main window with tabs: Model Explorer, Grouping Editor, Import/Export
- [ ] Log/status panel for user feedback

### Milestone 3: **GUI Bootstrapped**
**ETA:** Mid Week 3  
- Display tabs and placeholders  
- Show table list in UI  
- Responsive window layout

---

## 📌 Phase 4: Grouping Editor

### Features
- [ ] Load existing grouping structure into a table view
- [ ] Enable inline editing
- [ ] Add undo/redo logic
- [ ] Add change preview pane (diff)

### Milestone 4: **Editable Grouping UI**
**ETA:** End of Week 4  
- Validate local state reflects edits  
- Preview view comparison tested  
- Bulk edit tested with large datasets

---

## 📌 Phase 5: Model Update Integration

### Features
- [ ] Push updates to Power BI via XMLA
- [ ] Handle validation errors before commit
- [ ] Rollback logic on error
- [ ] Port discovery support

### Milestone 5: **Live Model Roundtrip**
**ETA:** Mid Week 5  
- Roundtrip flow complete (load → edit → push)  
- Test rollback scenarios  
- Validate changes appear in Power BI Desktop

---

## 📌 Phase 6: Import/Export & Automation

### Features
- [ ] Export/import grouping structures to/from JSON & Excel
- [ ] CLI mode for headless sync
- [ ] Logging and error codes for CLI mode

### Milestone 6: **Import/Export Ready**
**ETA:** End of Week 5  
- Roundtrip tests with Excel/JSON  
- CLI with flags for automation  
- Cron-based batch script testing

---

## 📌 Phase 7: UX Polish and Production Prep

### Features
- [ ] Save/load user project config
- [ ] Light/Dark theme switching
- [ ] Auto-discover Power BI XMLA port
- [ ] Add Help/About section

### Milestone 7: **Production Ready**
**ETA:** Week 6  
- End-to-end regression testing  
- Build final app using PyInstaller  
- Create documentation and onboarding flow

---

## 🧪 Testing Strategy

| Phase        | Tests                                                                 |
|--------------|-----------------------------------------------------------------------|
| Phase 1      | Unit tests for `pyadomd`, connection handling, JSON/Excel roundtrip   |
| Phase 2      | Integration tests for metadata graph traversal                        |
| Phase 3      | GUI smoke tests, tab rendering, responsiveness                        |
| Phase 4      | Table edits, undo/redo, preview rendering                             |
| Phase 5      | Full edit-push roundtrip and rollback                                 |
| Phase 6      | Format conversion validation, CLI test cases                          |
| Phase 7      | Final QA pass, multi-user testing                                     |

---

## 🗂 Suggested Folder Structure

tmdl_editor/
├── gui/
│ ├── main_window.py
│ ├── grouping_editor.py
├── backend/
│ ├── model_connector.py
│ ├── dax_info_views.py
│ ├── grouping_logic.py
├── utils/
│ ├── io_excel.py
│ ├── io_json.py
│ ├── logger.py
├── cli/
│ ├── tmdl_cli.py
├── assets/
│ ├── sample_configs/
├── tests/
│ ├── test_grouping_logic.py
├── tmdl_editor_gui.py
├── tmdl_editor.py
├── IMPLEMENTATION_PLAN.md
├── README.md


---

## ✅ Deliverable Summary

| Phase | Deliverable                      | Format         |
|-------|----------------------------------|----------------|
| 1     | `model_connector.py`             | Py module      |
| 2     | `dax_info_views.py`              | Py module      |
| 3     | `tmdl_editor_gui.py`             | Py file        |
| 4     | `grouping_editor.py`             | GUI + logic    |
| 5     | XMLA model updater               | Integrated     |
| 6     | `io_json.py`, `io_excel.py`      | Utils          |
| 7     | Theme/config/help in GUI         | UI polish      |

--- 