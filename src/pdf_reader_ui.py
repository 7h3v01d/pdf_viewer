import sys
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QPushButton, 
                            QLabel, QToolBar, QLineEdit, QStatusBar, QComboBox, 
                            QDockWidget, QListWidget) # <-- QAction REMOVED from here
from PyQt6.QtGui import QIcon, QShortcut, QKeySequence, QAction # <-- QAction ADDED here
from PyQt6.QtCore import Qt, QSize
from pdf_scroll_area import PDFScrollArea

class PDFReaderUI(QMainWindow):
    """
    Sets up all the UI elements, toolbars, layouts, and signal connections.
    It relies on methods implemented in the derived PDFReader class (in pdf_reader_app.py).
    """
    
    # Constants for View Mode (Redefined here for self-contained UI context)
    SINGLE_PAGE = 0
    CONTINUOUS = 1

    def __init__(self):
        super().__init__()
        # Initial window setup
        self.setWindowTitle("Professional PDF Reader")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize UI Components (State for UI class)
        self.toolbar = QToolBar()
        self.open_button = QPushButton()
        self.prev_button = QPushButton()
        self.next_button = QPushButton()
        self.rotate_button = QPushButton()
        self.fullscreen_button = QPushButton()
        self.annotate_button = QPushButton()
        self.search_button = QPushButton()
        self.next_search_button = QPushButton()
        self.prev_search_button = QPushButton()
        self.print_button = QPushButton()
        self.add_page_button = QPushButton()
        self.remove_page_button = QPushButton()
        self.move_up_button = QPushButton()
        self.move_down_button = QPushButton()
        self.save_button = QPushButton()
        self.properties_button = QPushButton("Properties")
        self.page_input = QLineEdit()
        self.page_label = QLabel(" / 0")
        self.search_input = QLineEdit()
        self.zoom_combo = QComboBox()
        self.view_mode_button = QPushButton("Continuous")
        self.dark_mode_button = QPushButton("Dark Mode")
        self.zoom_fit_width_button = QPushButton("Fit Width")
        self.zoom_fit_page_button = QPushButton("Fit Page")
        self.thumbnail_list = QListWidget()
        self.toc_list = QListWidget()
        self.status_bar = QStatusBar()
        
        # Call setup methods
        self._setup_ui_elements()
        self._setup_shortcuts()
        self._apply_styles()
        self._set_initial_state()

    def _setup_ui_elements(self):
        # 1. Main Layout
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QVBoxLayout(self.main_widget)
        self.setStatusBar(self.status_bar)
        
        # 2. Toolbar Setup
        self.addToolBar(Qt.ToolBarArea.TopToolBarArea, self.toolbar)
        self.open_button.setIcon(QIcon.fromTheme("document-open"))
        self.prev_button.setIcon(QIcon.fromTheme("go-previous"))
        self.next_button.setIcon(QIcon.fromTheme("go-next"))
        self.rotate_button.setIcon(QIcon.fromTheme("image-rotate"))
        self.fullscreen_button.setIcon(QIcon.fromTheme("view-fullscreen"))
        self.annotate_button.setIcon(QIcon.fromTheme("document-edit"))
        self.search_button.setIcon(QIcon.fromTheme("edit-find"))
        self.next_search_button.setIcon(QIcon.fromTheme("go-next"))
        self.prev_search_button.setIcon(QIcon.fromTheme("go-previous"))
        self.print_button.setIcon(QIcon.fromTheme("document-print"))
        self.add_page_button.setIcon(QIcon.fromTheme("list-add"))
        self.remove_page_button.setIcon(QIcon.fromTheme("list-remove"))
        self.move_up_button.setIcon(QIcon.fromTheme("go-up"))
        self.move_down_button.setIcon(QIcon.fromTheme("go-down"))
        self.save_button.setIcon(QIcon.fromTheme("document-save"))
        self.properties_button.setIcon(QIcon.fromTheme("document-properties"))

        self.page_input.setFixedWidth(50)
        self.page_input.setPlaceholderText("Page")
        self.search_input.setFixedWidth(150)
        self.search_input.setPlaceholderText("Search text...")
        self.zoom_combo.addItems(["50%", "75%", "100%", "125%", "150%", "200%", "300%", "400%"])
        self.zoom_combo.setCurrentText("100%")
        self.zoom_combo.setFixedWidth(100)
        self.view_mode_button.setToolTip("Toggle Continuous/Single Page View")
        self.dark_mode_button.setToolTip("Toggle Scroll Area Background Color")
        self.zoom_fit_width_button.setToolTip("Zoom to fit page width")
        self.zoom_fit_page_button.setToolTip("Zoom to fit entire page in view")
        
        # Toolbar Layout (The structure)
        self.toolbar.addWidget(self.open_button)
        self.toolbar.addWidget(self.prev_button)
        self.toolbar.addWidget(self.next_button)
        self.toolbar.addWidget(self.page_input)
        self.toolbar.addWidget(self.page_label)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.zoom_combo)
        self.toolbar.addWidget(self.zoom_fit_width_button) 
        self.toolbar.addWidget(self.zoom_fit_page_button)  
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.rotate_button)
        self.toolbar.addWidget(self.fullscreen_button)
        self.toolbar.addWidget(self.print_button)
        self.toolbar.addWidget(self.properties_button) 
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.search_button)
        self.toolbar.addWidget(self.search_input)
        self.toolbar.addWidget(self.prev_search_button)
        self.toolbar.addWidget(self.next_search_button)
        self.toolbar.addWidget(self.annotate_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.view_mode_button) 
        self.toolbar.addWidget(self.dark_mode_button)
        self.toolbar.addSeparator()
        self.toolbar.addWidget(self.add_page_button)
        self.toolbar.addWidget(self.remove_page_button)
        self.toolbar.addWidget(self.move_up_button)
        self.toolbar.addWidget(self.move_down_button)
        self.toolbar.addWidget(self.save_button)

        # 3. Sidebar (Dock Widget)
        self.sidebar = QDockWidget("Navigation", self)
        self.sidebar_widget = QWidget()
        self.sidebar_layout = QVBoxLayout(self.sidebar_widget)
        self.thumbnail_list.setIconSize(QSize(100, 140))
        self.thumbnail_list.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.thumbnail_list.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.thumbnail_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.sidebar_layout.addWidget(QLabel("Table of Contents"))
        self.sidebar_layout.addWidget(self.toc_list)
        self.sidebar_layout.addWidget(QLabel("Thumbnails"))
        self.sidebar_layout.addWidget(self.thumbnail_list)
        self.sidebar.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.sidebar)

        # 4. Core Viewport
        self.pdf_container = QWidget()
        self.pdf_layout = QVBoxLayout(self.pdf_container)
        self.pdf_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.pdf_layout.setContentsMargins(0, 0, 0, 0)
        self.pdf_layout.setSpacing(10)
        
        # PDFScrollArea requires a reference to the main app object (self), which will be the derived class
        self.scroll_area = PDFScrollArea(self) 
        self.scroll_area.setWidget(self.pdf_container) 
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("background-color: #f5f5f5;")
        
        self.layout.addWidget(self.scroll_area)
        
        # 5. Connect Signals to methods that exist in the derived class (PDFReader)
        self.open_button.clicked.connect(self.open_pdf)
        self.prev_button.clicked.connect(self.prev_page)
        self.next_button.clicked.connect(self.next_page)
        self.rotate_button.clicked.connect(self.rotate_page)
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen)
        self.page_input.returnPressed.connect(self.goto_page)
        self.zoom_combo.currentTextChanged.connect(self.change_zoom)
        self.annotate_button.clicked.connect(self.toggle_annotation_mode)
        self.search_button.clicked.connect(self.start_search) # Renamed lambda to method in app
        self.search_input.returnPressed.connect(self.start_search) # Renamed lambda to method in app
        self.next_search_button.clicked.connect(self.next_search_result) # Renamed lambda to method in app
        self.prev_search_button.clicked.connect(self.prev_search_result) # Renamed lambda to method in app
        self.print_button.clicked.connect(self.print_pdf) 
        self.add_page_button.clicked.connect(self.add_page_action) # Renamed lambda to method in app
        self.remove_page_button.clicked.connect(self.remove_page_action) # Renamed lambda to method in app
        self.move_up_button.clicked.connect(self.move_page_up_action) # Renamed lambda to method in app
        self.move_down_button.clicked.connect(self.move_page_down_action) # Renamed lambda to method in app
        self.save_button.clicked.connect(self.save_pdf)
        self.thumbnail_list.itemClicked.connect(self.thumbnail_clicked)
        # Note: rowsMoved is a complex signal handled by logic class
        self.toc_list.itemClicked.connect(self.toc_clicked) 
        self.view_mode_button.clicked.connect(self.toggle_view_mode)
        self.dark_mode_button.clicked.connect(self.toggle_dark_mode)
        self.zoom_fit_width_button.clicked.connect(self.set_zoom_fit_width) # Renamed lambda to method in app
        self.zoom_fit_page_button.clicked.connect(self.set_zoom_fit_page) # Renamed lambda to method in app
        self.properties_button.clicked.connect(self.show_metadata)

    def _setup_shortcuts(self):
        QShortcut(QKeySequence("Ctrl++"), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+="), self, self.zoom_in)
        QShortcut(QKeySequence("Ctrl+-"), self, self.zoom_out)
        QShortcut(QKeySequence("Ctrl+F"), self, self.focus_search)
        QShortcut(QKeySequence("Ctrl+C"), self, self.copy_selected_text)
        
    def _apply_styles(self):
        self.setStyleSheet("""
            QMainWindow { background-color: #f5f5f5; }
            QToolBar { background-color: #e0e0e0; border: none; padding: 5px; }
            QPushButton { background-color: #ffffff; border: 1px solid #cccccc; padding: 5px; border-radius: 3px; }
            QPushButton:hover { background-color: #e6e6e6; }
            QLineEdit { border: 1px solid #cccccc; border-radius: 3px; padding: 2px; }
            QComboBox { border: 1px solid #cccccc; border-radius: 3px; padding: 2px; }
            QDockWidget { background-color: #ffffff; border: 1px solid #cccccc; }
            QListWidget { border: 1px solid #cccccc; background-color: #ffffff; }
            QLabel[annotationMode="true"] { cursor: crosshair; }
        """)

    def _set_initial_state(self):
        # Disable all controls until a PDF is loaded
        for widget in [self.prev_button, self.next_button, self.rotate_button, self.page_input, 
                       self.annotate_button, self.search_button, self.search_input, 
                       self.next_search_button, self.prev_search_button, self.print_button, 
                       self.add_page_button, self.remove_page_button, self.move_up_button, 
                       self.move_down_button, self.save_button, self.view_mode_button, 
                       self.dark_mode_button, self.zoom_fit_width_button, 
                       self.zoom_fit_page_button, self.properties_button]:
            widget.setEnabled(False)
        self.status_bar.showMessage("Ready")