# Professional PDF Reader

Modern, feature-rich PDF viewer and lightweight editor built with **Python** + **PyQt6** + **PyMuPDF (fitz)**.

---

⚠️ **LICENSE & USAGE NOTICE — READ FIRST**

This repository is **source-available for private technical evaluation and testing only**.

- ❌ No commercial use  
- ❌ No production use  
- ❌ No academic, institutional, or government use  
- ❌ No research, benchmarking, or publication  
- ❌ No redistribution, sublicensing, or derivative works  
- ❌ No independent development based on this code  

All rights remain exclusively with the author.  
Use of this software constitutes acceptance of the terms defined in **LICENSE.txt**.

---

Clean interface · Continuous / Single page view · Form filling · Text search · Annotations · Page management · Dark mode · Zoom modes · Print support

<p align="center">
  <img src="https://placehold.co/800x500/2d3748/ffffff/png?text=PDF+Reader+Screenshot+(replace+with+real+one)" alt="Main window" width="70%"/>
  <br/>
  <em>Screenshot of the application (add real screenshot later)</em>
</p>

---

## ✨ Features

- **Viewing modes**
  - Single page
  - Continuous scrolling
- **Navigation**
  - Thumbnail sidebar
  - Table of Contents (TOC) sidebar
  - Go to page + mouse wheel page turning (single-page mode)
- **Viewing controls**
  - Zoom (50–400% + Fit Width / Fit Page)
  - Rotate page
  - Dark / Light mode for reading area
- **Search**
  - Text search with prev/next result navigation
  - Highlights matching regions
- **Interactive forms**
  - Fillable PDF form support (text fields)
- **Annotations**
  - Add red text notes (click to place)
  - Delete annotations (right-click)
  - Persistent annotations (saved to `.annotations.json`)
- **Page management**
  - Add blank page
  - Remove current page
  - Reorder pages (drag thumbnails or use buttons)
  - Move page up/down
- **Other**
  - Document properties / metadata viewer
  - Print selected pages or all
  - Save modified PDF (with annotations baked in)
  - Copy selected text (Ctrl+C)

## 📸 Screenshots

_(Add 3–5 screenshots here later – toolbar, continuous mode, form filling, annotations, dark mode, etc.)_

| Single Page Mode              | Continuous Mode               | Form Filling                  |
|-------------------------------|-------------------------------|-------------------------------|
| ![](screenshots/single.png)   | ![](screenshots/continuous.png) | ![](screenshots/form.png)     |

## 🚀 Quick Start

### 1. Prerequisites

- Python **3.9** – **3.12** recommended
- Operating System: Windows / macOS / Linux

### 2. Install dependencies

#### Recommended: use a virtual environment
```bash
python -m venv venv
```
```bash
source venv/bin/activate      # Linux/macOS
```
 or
```bash
venv\Scripts\activate         # Windows
```
```bash
pip install -r requirements.txt
```
requirements.txt example:
```text
PyQt6>=6.6.0
PyMuPDF>=1.23.0     # fitz
```
3. Run the application
```Bash
python pdf_reader.py
```
or (most common way)
```Bash
python -m pdf_reader
```
### 🛠️ Project Structure
```text
textpdf-reader/
├── pdf_reader.py           # Entry point
├── pdf_reader_app.py       # Main logic & window class
├── pdf_reader_ui.py        # UI layout & widgets
├── pdf_utils.py            # Search, annotations, page ops, thumbnails…
├── pdf_scroll_area.py      # Custom scroll area with wheel navigation
├── pdf_page_widget.py      # QLabel subclass that repositions form fields
└── requirements.txt
```

### ⌨️ Keyboard Shortcuts
```text
Action                  Shortcut
Zoom in                 Ctrl + + / Ctrl + =
Zoom out                Ctrl + -
Focus search bar        Ctrl + F
Copy selected text      Ctrl + C
(more to come…)
```
### ⚡ To-Do / Planned Features

-  Highlight & copy text (currently only basic selection rectangle)
- Better annotation types (highlight, underline, strikethrough, drawing)
- Undo/redo for annotations & page changes
- Save annotations inside the PDF (not only .json sidecar)
- Export pages as images
- Bookmark support
- Night mode with real color inversion (not just background)
- Command line mode / open file from argument
- PyInstaller / cx_Freeze one-file executable builds

## Contribution Policy

Feedback, bug reports, and suggestions are welcome.

You may submit:

- Issues
- Design feedback
- Pull requests for review

However:

- Contributions do not grant any license or ownership rights
- The author retains full discretion over acceptance and future use
- Contributors receive no rights to reuse, redistribute, or derive from this code

---

## License
This project is not open-source.

It is licensed under a private evaluation-only license.
See LICENSE.txt for full terms.
