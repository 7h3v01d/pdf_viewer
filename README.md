# Professional PDF Reader

Modern, feature-rich PDF viewer and lightweight editor built with **Python** + **PyQt6** + **PyMuPDF (fitz)**.

Clean interface · Continuous / Single page view · Form filling · Text search · Annotations · Page management · Dark mode · Zoom modes · Print support

<p align="center">
  <img src="https://placehold.co/800x500/2d3748/ffffff/png?text=PDF+Reader+Screenshot+(replace+with+real+one)" alt="Main window" width="70%"/>
  <br/>
  <em>Screenshot of the application (add real screenshot later)</em>
</p>

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
txtPyQt6>=6.6.0
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

### Contributing
Pull requests welcome!</br>
Especially interested in:

- Text selection + copy improvement
- Better form rendering & more field types
- Annotation UX polish
- Cross-platform testing & bug fixes
- Packaging scripts (PyInstaller, briefcase, etc.)


1. Fork the repository
2. Create a feature branch (git checkout -b feature/amazing-thing)
3. Commit your changes (git commit -m 'Add amazing thing')
4. Push to the branch (git push origin feature/amazing-thing)
5. Open a Pull Request

### 📄 License
MIT License</br>
Feel free to use, modify, distribute — just keep the copyright notice.

⭐ If you find this useful, please give the repo a star!
🐛 Bug reports → Issues
