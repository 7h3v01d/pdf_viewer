import sys
import fitz  # PyMuPDF
from PyQt6.QtWidgets import (QInputDialog, QMessageBox, QLabel, QMenu, QWidgetAction, 
                            QFileDialog, QApplication, QListWidgetItem, QLineEdit, 
                            QCheckBox) # <-- QCheckBox added here!
from PyQt6.QtGui import QPixmap, QImage, QPainter, QPen, QColor, QAction, QIcon
from PyQt6.QtCore import Qt, QRectF, QPoint 

# Import UI elements and utilities
from pdf_reader_ui import PDFReaderUI # Import the base UI class
from pdf_utils import (load_annotations, save_annotations, search_text, 
                      next_search_result, prev_search_result, add_page, 
                      remove_page, move_page_up, move_page_down, 
                      handle_thumbnail_reorder)


class PDFReader(PDFReaderUI):
    def __init__(self):
        # 1. Initialize UI (which calls PDFReaderUI.__init__)
        super().__init__()
        
        # 2. Application State Variables (Logic/Model state)
        self.pdf_document = None
        self.current_page = 0
        self.total_pages = 0
        self.zoom_level = 1.0
        self.rotation = 0
        self.annotations = {}
        self.search_results = []
        self.current_search_index = -1
        self.pdf_file_path = ""
        self.annotation_mode = False
        
        self.view_mode = self.SINGLE_PAGE # Set default to SINGLE_PAGE
        self.dark_mode = False           # Default to Light Mode

        # --- NEW FIELD STATE ---
        self.form_fields = {} # Stores fields per page: {page_num: [fitz.Widget]}
        self.field_widgets = {} # Stores temporary QLineEdit widgets for filling
        # -----------------------
        
        # Text Selection State
        self.is_selecting_text = False
        self.selection_start_point = None
        self.selection_end_point = None   
        self.current_selection_page = -1  
        self.context_menu_page_widget = None 
        self.page_widgets = [] # List to hold QLabel widgets for each page
        
        # Ensure model logic is connected to UI events
        self.thumbnail_list.model().rowsMoved.connect(
            lambda p, s, e, d, r: handle_thumbnail_reorder(self, p, s, e, d, r)
        )
        
        # Call initial status update now that self.pdf_document is None
        self.update_status_bar() 
        
    # --- LOGIC METHODS (Implements all connected signals from PDFReaderUI) ---

    def open_pdf(self):
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Open PDF File", "", "PDF Files (*.pdf)"
        )
        if file_name:
            try:
                self.pdf_document = fitz.open(file_name)
                self.pdf_file_path = file_name
                self.total_pages = self.pdf_document.page_count
                self.current_page = 0
                self.rotation = 0
                self.search_results = []
                self.current_search_index = -1
                self.annotation_mode = False
                self.annotations = load_annotations(self.pdf_document, file_name)
                self.form_fields = {}
                for page_num in range(self.total_pages):
                    page = self.pdf_document.load_page(page_num)
                    self.form_fields[page_num] = list(page.widgets())


                # Reset selection state
                self.selection_start_point = None
                self.selection_end_point = None
                self.current_selection_page = -1

                self.load_pages() 
                self.update_view() 
                self.load_thumbnails()
                self.load_toc()
                
                # Enable buttons
                for widget in [self.rotate_button, self.page_input, self.annotate_button, 
                               self.search_button, self.search_input, self.print_button, 
                               self.add_page_button, self.remove_page_button, self.save_button, 
                               self.view_mode_button, self.dark_mode_button, self.zoom_fit_width_button, 
                               self.zoom_fit_page_button, self.properties_button]:
                    widget.setEnabled(True)

                self.update_ui_on_page_change()
                self.page_label.setText(f" / {self.total_pages}")
                self.status_bar.showMessage(f"Opened: {file_name}")
            except Exception as e:
                self.status_bar.showMessage(f"Error loading PDF: {str(e)}")

    def _update_pdf_field(self, field, value):
        field.field_value = value
        field.update()
        self.status_bar.showMessage("Form field updated")
        # Optional: self.save_pdf() or re-render the page if needed

    def load_pages(self):
        # 1. Clear existing widgets
        for widget in self.page_widgets:
            self.pdf_layout.removeWidget(widget)
            widget.deleteLater()
        self.page_widgets = []
        
        if not self.pdf_document:
            return

        # 2. Create a new QLabel for every page
        for page_num in range(self.total_pages):
            page_widget = QLabel()
            page_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            page_widget.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu) 
            page_widget.customContextMenuRequested.connect(self._show_context_menu)
            page_widget.setProperty("page_num", page_num)
            
            # Connect custom mouse handlers (using lambdas to pass the widget reference)
            page_widget.mousePressEvent = lambda event, w=page_widget: self._handle_page_mouse_press(event, w)
            page_widget.mouseMoveEvent = lambda event, w=page_widget: self._handle_page_mouse_move(event, w) 
            page_widget.mouseReleaseEvent = lambda event, w=page_widget: self._handle_page_mouse_release(event, w) 
            page_widget.setMouseTracking(True)
            
            self.pdf_layout.addWidget(page_widget)
            self.page_widgets.append(page_widget)
            
    # --- RENDERING AND COORDINATE LOGIC ---
    
    def _widget_coords_to_pdf_rect(self, page_widget, start_point, end_point):
        """Converts widget QPoints to a fitz.Rect on the PDF page."""
        page_num = page_widget.property("page_num")
        if page_num is None or self.pdf_document is None: return None

        pixmap = page_widget.pixmap()
        if not pixmap: return None
        
        label_size = page_widget.size()
        pixmap_size = pixmap.size()
        x_offset_alignment = (label_size.width() - pixmap_size.width()) // 2
        y_offset_alignment = (label_size.height() - pixmap_size.height()) // 2

        start_x = start_point.x() - x_offset_alignment
        start_y = start_point.y() - y_offset_alignment
        end_x = end_point.x() - x_offset_alignment
        end_y = end_point.y() - y_offset_alignment

        rect_x0 = max(0, min(start_x, end_x, pixmap_size.width()))
        rect_y0 = max(0, min(start_y, end_y, pixmap_size.height()))
        rect_x1 = min(pixmap_size.width(), max(start_x, end_x))
        rect_y1 = min(pixmap_size.height(), max(start_y, end_y))
        
        pdf_rect = fitz.Rect(rect_x0, rect_y0, rect_x1, rect_y1)
        
        matrix = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
        try:
            inverse_matrix = matrix.invert()
        except ValueError:
            self.status_bar.showMessage("Error: Cannot invert transformation matrix for selection.")
            return None
            
        return pdf_rect * inverse_matrix

    def render_page_content(self, page_num, widget):
        """Renders a single page's content, annotations, and search highlights."""
        if not self.pdf_document: return
        try:
            page = self.pdf_document.load_page(page_num)
            matrix = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
            pix = page.get_pixmap(matrix=matrix, alpha=False)
        
            img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
            pixmap = QPixmap.fromImage(img)
        
            painter = QPainter(pixmap)
            try:
                # Text Selection Highlight (Redrawing logic uses self.selection_points)
                if self.selection_start_point and self.selection_end_point and page_num == self.current_selection_page:
                    start_x = self.selection_start_point.x()
                    start_y = self.selection_start_point.y()
                    end_x = self.selection_end_point.x()
                    end_y = self.selection_end_point.y()
                
                    label_size = widget.size()
                    pixmap_size = pixmap.size()
                    x_offset_alignment = (label_size.width() - pixmap_size.width()) // 2
                    y_offset_alignment = (label_size.height() - pixmap_size.height()) // 2
                
                    selection_rect = QRectF(
                        min(start_x, end_x) - x_offset_alignment,
                        min(start_y, end_y) - y_offset_alignment,
                        abs(start_x - end_x),
                        abs(start_y - end_y)
                    )
                
                    painter.setPen(QPen(QColor(0, 0, 255, 100), 1, Qt.PenStyle.SolidLine))
                    painter.setBrush(QColor(0, 0, 255, 50)) 
                    painter.drawRect(selection_rect)

                # Annotations (Red Text)
                if page_num in self.annotations:
                    pen = QPen(QColor(255, 0, 0), 2)
                    painter.setPen(pen)
                    font = painter.font()
                    font.setPointSize(12)
                    painter.setFont(font)
                    for x, y, text in self.annotations[page_num]:
                        scaled_x = x * self.zoom_level
                        scaled_y = y * self.zoom_level
                        painter.drawText(QRectF(scaled_x, scaled_y, 200, 50), Qt.TextFlag.TextWordWrap, text)
            
                # Search Highlights (Yellow Rectangle)
                if self.search_results:
                    page_highlights = []
                    for i, result in enumerate(self.search_results):
                        if result["page"] == page_num:
                            is_current = (i == self.current_search_index)
                            page_highlights.append({"rects": result["rects"], "is_current": is_current})

                    if page_highlights:
                        painter.setPen(Qt.PenStyle.NoPen)
                        # Non-current
                        painter.setBrush(QColor(255, 255, 0, 50)) 
                        for hl in [h for h in page_highlights if not h["is_current"]]:
                            for rect in hl["rects"]:
                                scaled_rect = QRectF(
                                    rect.x0 * self.zoom_level, rect.y0 * self.zoom_level,
                                    (rect.x1 - rect.x0) * self.zoom_level, (rect.y1 - rect.y0) * self.zoom_level
                                )
                                painter.drawRect(scaled_rect)

                        # Current
                        painter.setBrush(QColor(255, 255, 0, 150))
                        for hl in [h for h in page_highlights if h["is_current"]]:
                            for rect in hl["rects"]:
                                scaled_rect = QRectF(
                                    rect.x0 * self.zoom_level, rect.y0 * self.zoom_level,
                                    (rect.x1 - rect.x0) * self.zoom_level, (rect.y1 - rect.y0) * self.zoom_level
                                )
                                painter.drawRect(scaled_rect)
            finally:
                painter.end()
        
            widget.setPixmap(pixmap)
        
            # NOW render form fields (after setPixmap, so offsets are accurate)
            self._render_form_fields(page_num, widget)
        
        except Exception as e:
            widget.setText(f"Error rendering page {page_num + 1}: {str(e)}")

    def render_single_page(self):
        if not self.page_widgets: return
        for i, widget in enumerate(self.page_widgets):
            if i == self.current_page:
                self.render_page_content(self.current_page, widget)
                widget.setVisible(True)
            else:
                widget.setVisible(False)
        self.scroll_area.verticalScrollBar().setValue(0)
        self.update_status_bar()

    def render_continuous_pages(self):
        if not self.page_widgets: return
    
        # 1. Ensure all page widgets are visible and update the rotation once
        for widget in self.page_widgets:
            widget.setVisible(True)
    
        # 2. Identify visible area in the scroll viewport
        viewport_rect = self.scroll_area.viewport().rect()
        scroll_offset = self.scroll_area.verticalScrollBar().value()
    
        # 3. Only render pages that intersect the visible area
        for i, widget in enumerate(self.page_widgets):
            # Map the widget's geometry to the scroll area's coordinate system
            widget_rect = widget.geometry()
        
            # Adjust for scroll position
            widget_top_y = self.scroll_area.widget().mapFromParent(widget_rect.topLeft()).y() - scroll_offset
            widget_bottom_y = self.scroll_area.widget().mapFromParent(widget_rect.bottomLeft()).y() - scroll_offset
        
            # Check for intersection with viewport (allowing a little buffer)
            is_visible = (widget_top_y < viewport_rect.bottom() + 100) and \
                         (widget_bottom_y > viewport_rect.top() - 100)
                     
            if is_visible:
                # Render visible pages fully
                self.render_page_content(i, widget)
            else:
                # OPTIMIZATION: Clear non-visible pages to reduce memory usage
                widget.clear()
            
        self.scroll_to_page(self.current_page)
        self.update_status_bar()

    def _render_form_fields(self, page_num, widget):
        # Clear any existing field widgets for this page
        if page_num in self.field_widgets:
            for field_widget in self.field_widgets[page_num]:
                field_widget.deleteLater()
            del self.field_widgets[page_num]
    
        if page_num not in self.form_fields or not self.form_fields[page_num]:
            return
    
        # Get current rendered sizes for alignment offsets
        label_size = widget.size()
        pixmap_size = widget.pixmap().size() if widget.pixmap() else QSize(0, 0)
        x_offset = (label_size.width() - pixmap_size.width()) // 2
        y_offset = (label_size.height() - pixmap_size.height()) // 2
    
        # Transformation matrix (must match the one used for pixmap rendering)
        matrix = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
    
        self.field_widgets[page_num] = []
    
        for field in self.form_fields[page_num]:
            # Transform the field's PDF rect to rendered coordinates
            transformed_rect = field.rect * matrix
        
            if field.field_type == fitz.PDF_WIDGET_TYPE_TEXT:
                line_edit = QLineEdit(widget)  # Parent to the page QLabel
                line_edit.setText(field.field_value or "")  # Load existing value if any
                line_edit.setGeometry(
                    int(transformed_rect.x0 + x_offset),
                    int(transformed_rect.y0 + y_offset),
                    int(transformed_rect.width),
                    int(transformed_rect.height)
                )
                # Optional: Style to blend in (adjust as needed)
                line_edit.setStyleSheet("border: 1px solid blue; background: transparent;")
                # Connect editing finished to update PDF field value
                line_edit.editingFinished.connect(lambda f=field, le=line_edit: self._update_pdf_field(f, le.text()))
                self.field_widgets[page_num].append(line_edit)
                line_edit.show()
        
            elif field.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
                check_box = QCheckBox(widget)  # Parent to the page QLabel
                check_box.setChecked(field.field_value == "Yes")  # Assuming "Yes"/"Off" for PDF checkboxes
                # Checkboxes often have fixed size; scale if needed
                cb_size = min(int(transformed_rect.width), int(transformed_rect.height))
                check_box.setGeometry(
                    int(transformed_rect.x0 + x_offset),
                    int(transformed_rect.y0 + y_offset),
                    cb_size,
                    cb_size
                )
                # Connect state change to update PDF field value
                check_box.stateChanged.connect(lambda state, f=field: self._update_pdf_field(f, "Yes" if state == Qt.CheckState.Checked else "Off"))
                self.field_widgets[page_num].append(check_box)
                check_box.show()
        
            # Add handling for other field types (e.g., radio, combo) as needed
    
        widget.update()  # Force repaint if necessary

    def _save_form_field(self, fitz_widget, qlineedit_widget):
        """
        Saves the user input from QLineEdit back to the fitz PDF field.
        This handles Text fields (field_type=1).
        """
        if not self.pdf_document: return

        # 1. Get the new value from the QLineEdit
        new_value = qlineedit_widget.text()
    
        # 2. Update the PyMuPDF field object
        try:
            # Use the field_value property to set the new content
            fitz_widget.field_value = new_value 
        
            # This is CRITICAL: it applies the value and updates the visual appearance in the PDF structure
            fitz_widget.update() 
        
            self.status_bar.showMessage(f"Text Field '{fitz_widget.field_name}' updated.")
        except Exception as e:
            self.status_bar.showMessage(f"Error saving text field: {e}")

        # Note: We don't call save_pdf() here, the user must explicitly save the document.

    def _save_checkbox_field(self, fitz_widget, state):
        """Saves the user input from QCheckBox back to the fitz PDF field, with error handling."""
        if not self.pdf_document: return
    
        # Initialize defaults
        new_value = "" 
    
        try:
            # Checkbox 'on' value is the second value in field_values(), 'off' is the first.
            # This is the PyMuPDF-recommended way, but it throws the AttributeError for some fields.
            field_values = fitz_widget.field_values()
            off_value = field_values[0] if len(field_values) > 0 else ""
            on_value = field_values[1] if len(field_values) > 1 else "Yes" 

            if state == Qt.CheckState.Checked.value:
                new_value = on_value
            else:
                new_value = off_value

        except AttributeError:
            # Fallback for fields (like some buttons) that lack field_values()
            if state == Qt.CheckState.Checked.value:
                new_value = "Yes" # Common 'on' value default
            else:
                new_value = "" # Common 'off' value default
    
        try:
            # Apply the determined new value
            fitz_widget.field_value = new_value
            fitz_widget.update() 
            self.status_bar.showMessage(f"Checkbox '{fitz_widget.field_name}' updated to {new_value}.")
        except Exception as e:
            self.status_bar.showMessage(f"Error saving checkbox field value: {e}")

    def update_view(self):
        if not self.pdf_document: return
        if self.view_mode == self.SINGLE_PAGE:
            self.render_single_page()
        elif self.view_mode == self.CONTINUOUS:
            self.render_continuous_pages()
            
    # --- PAGE NAVIGATION AND STATE MANAGEMENT ---

    def update_status_bar(self):
        if not self.pdf_document:
            self.status_bar.showMessage("Ready")
            return
            
        search_status = f"Result {self.current_search_index + 1} of {len(self.search_results)}" if self.search_results and self.current_search_index >= 0 else f"Search results: {len(self.search_results)}"
        view_status = "Continuous" if self.view_mode == self.CONTINUOUS else "Single"
        self.status_bar.showMessage(
            f"Page: {self.current_page + 1} / {self.total_pages} | "
            f"Zoom: {int(self.zoom_level * 100)}% | Rotation: {self.rotation}° | "
            f"Mode: {view_status} | {search_status}"
        )
        self.page_input.setText(str(self.current_page + 1))

    def update_ui_on_page_change(self):
        """Common logic executed after changing self.current_page."""
        self.annotation_mode = False
        self.toggle_annotation_mode(force_off=True) 
        
        self.selection_start_point = None
        self.selection_end_point = None
        self.current_selection_page = -1

        self.update_view()
        self.prev_button.setEnabled(self.current_page > 0 and self.view_mode == self.SINGLE_PAGE)
        self.next_button.setEnabled(self.current_page < self.total_pages - 1 and self.view_mode == self.SINGLE_PAGE)
        self.move_up_button.setEnabled(self.current_page > 0)
        self.move_down_button.setEnabled(self.current_page < self.total_pages - 1)
        self.thumbnail_list.setCurrentRow(self.current_page)
        self.page_input.setText(str(self.current_page + 1))
        
    def scroll_to_page(self, page_num):
        if self.view_mode == self.CONTINUOUS and 0 <= page_num < len(self.page_widgets):
            target_widget = self.page_widgets[page_num]
            target_pos = self.scroll_area.widget().mapFromParent(target_widget.pos())
            self.scroll_area.verticalScrollBar().setValue(target_pos.y())

    def prev_page(self):
        if self.view_mode == self.SINGLE_PAGE and self.current_page > 0:
            self.current_page -= 1
            self.update_ui_on_page_change()
            
    def next_page(self):
        if self.view_mode == self.SINGLE_PAGE and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.update_ui_on_page_change()

    def goto_page(self):
        try:
            page_num = int(self.page_input.text()) - 1
            if 0 <= page_num < self.total_pages:
                self.current_page = page_num
                self.update_ui_on_page_change()
            else:
                self.status_bar.showMessage("Invalid page number")
        except ValueError:
            self.status_bar.showMessage("Enter a valid page number")
            
    # --- ZOOM AND ROTATION ---

    def zoom_in(self):
        current_index = self.zoom_combo.currentIndex()
        if current_index < self.zoom_combo.count() - 1:
            self.zoom_combo.setCurrentIndex(current_index + 1)
            self.change_zoom(self.zoom_combo.currentText())
            
    def zoom_out(self):
        current_index = self.zoom_combo.currentIndex()
        if current_index > 0:
            self.zoom_combo.setCurrentIndex(current_index - 1)
            self.change_zoom(self.zoom_combo.currentText())
            
    def change_zoom(self, zoom_text):
        if zoom_text in ["Fit Width", "Fit Page"]: return 
            
        zoom_percentage = int(zoom_text.strip("%"))
        self.zoom_level = zoom_percentage / 100.0
        self.update_view()
        
    def set_zoom_fit_width(self): self.set_zoom_fit('width')
    def set_zoom_fit_page(self): self.set_zoom_fit('page')
        
    def set_zoom_fit(self, mode):
        if not self.pdf_document: return

        page = self.pdf_document.load_page(self.current_page)
        rect = page.rect
        page_width = rect.width
        page_height = rect.height
        
        viewport_size = self.scroll_area.viewport().size()
        viewport_width = viewport_size.width()
        viewport_height = viewport_size.height()
        
        # Account for spacing/margins 
        horizontal_padding = self.pdf_layout.spacing() 
        vertical_padding = self.pdf_layout.spacing()
        available_width = viewport_width - horizontal_padding
        available_height = viewport_height - vertical_padding
        
        if mode == 'width':
            new_zoom = available_width / page_width
        elif mode == 'page':
            zoom_w = available_width / page_width
            zoom_h = available_height / page_height
            new_zoom = min(zoom_w, zoom_h)
        else:
            return

        self.zoom_level = max(0.1, min(10.0, new_zoom))

        zoom_text = f"{int(self.zoom_level * 100)}%"
        zoom_items = [self.zoom_combo.itemText(i) for i in range(self.zoom_combo.count())]
        if zoom_text not in zoom_items:
            self.zoom_combo.blockSignals(True)
            self.zoom_combo.addItem(zoom_text)
            self.zoom_combo.blockSignals(False)
            
        self.zoom_combo.setCurrentText(zoom_text)
        self.update_view()
        
    def rotate_page(self):
        self.rotation = (self.rotation + 90) % 360
        self.update_view()
        
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.fullscreen_button.setIcon(QIcon.fromTheme("view-restore"))
        else:
            self.showFullScreen()
            self.fullscreen_button.setIcon(QIcon.fromTheme("view-fullscreen"))
            
    # --- ANNOTATION AND SELECTION ---

    def toggle_annotation_mode(self, force_off=False):
        if force_off:
            self.annotation_mode = False
        else:
            self.annotation_mode = not self.annotation_mode
            
        for widget in self.page_widgets:
            widget.setProperty("annotationMode", self.annotation_mode)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        if not force_off:
            self.status_bar.showMessage("Annotation mode enabled. Click to place.") if self.annotation_mode else self.status_bar.showMessage("Annotation mode disabled")
            
    def _handle_page_mouse_press(self, event, page_widget):
        page_num = page_widget.property("page_num")
        self.current_page = page_num 
        if not self.pdf_document: return
            
        # 1. Annotation Mode Logic
        if event.button() == Qt.MouseButton.LeftButton and self.annotation_mode:
            pixmap = page_widget.pixmap()
            if not pixmap: return
            click_point = event.position()
            label_size = page_widget.size()
            pixmap_size = pixmap.size()
            x_offset_alignment = (label_size.width() - pixmap_size.width()) // 2
            y_offset_alignment = (label_size.height() - pixmap_size.height()) // 2
            click_x = click_point.x() - x_offset_alignment
            click_y = click_point.y() - y_offset_alignment
            if not (0 <= click_x < pixmap_size.width() and 0 <= click_y < pixmap_size.height()): return

            page = self.pdf_document.load_page(page_num)
            matrix = fitz.Matrix(self.zoom_level, self.zoom_level).prerotate(self.rotation)
            try: inverse_matrix = matrix.invert()
            except ValueError:
                self.status_bar.showMessage("Error: Cannot invert transformation matrix."); return

            pdf_point = fitz.Point(click_x, click_y) * inverse_matrix
            text, ok = QInputDialog.getText(self, "Add Annotation", "Enter annotation text:")
            if ok and text:
                if page_num not in self.annotations: self.annotations[page_num] = []
                self.annotations[page_num].append((pdf_point.x, pdf_point.y, text))
                annot = page.add_text_annot(pdf_point, text); annot.set_colors(stroke=(1, 0, 0)); annot.update()
                save_annotations(self)
                self.render_page_content(page_num, page_widget) 
                self.toggle_annotation_mode(force_off=True) 
        
        # 2. Start text selection
        elif event.button() == Qt.MouseButton.LeftButton and not self.annotation_mode:
            self.is_selecting_text = True
            self.selection_start_point = event.position().toPoint()
            self.selection_end_point = event.position().toPoint()
            self.current_selection_page = page_num
            self.update_view() 

    def _handle_page_mouse_move(self, event, page_widget):
        page_num = page_widget.property("page_num")
        if self.is_selecting_text and page_num == self.current_selection_page and event.buttons() & Qt.MouseButton.LeftButton:
            self.selection_end_point = event.position().toPoint()
            self.update_view() 

    def _handle_page_mouse_release(self, event, page_widget):
        if self.is_selecting_text and event.button() == Qt.MouseButton.LeftButton:
            self.is_selecting_text = False
            self.selection_end_point = event.position().toPoint()
            
            # Clear if selection is just a tiny click
            if self.selection_start_point and self.selection_end_point and \
               abs(self.selection_start_point.x() - self.selection_end_point.x()) < 5 and \
               abs(self.selection_start_point.y() - self.selection_end_point.y()) < 5:
                self.selection_start_point = None
                self.selection_end_point = None
                self.current_selection_page = -1
                
            self.update_view()
            
    def _show_context_menu(self, pos):
        page_widget = self.sender()
        if not page_widget: return
        page_num = page_widget.property("page_num")
        self.context_menu_page_widget = page_widget

        context_menu = QMenu(self)
        copy_action = QAction("Copy Selected Text (Ctrl+C)", self)
        copy_action.triggered.connect(self.copy_selected_text)
        delete_action = QAction("Delete Nearest Annotation", self)
        delete_action.triggered.connect(lambda: self.delete_nearest_annotation(pos, page_widget))
        
        if self.selection_start_point and self.selection_end_point and self.current_selection_page == page_num:
            context_menu.addAction(copy_action)
        else:
            copy_action.setEnabled(False); context_menu.addAction(copy_action)
            
        context_menu.addSeparator()
        
        if page_num in self.annotations and self.annotations[page_num]:
            context_menu.addAction(delete_action)
        else:
            delete_action.setEnabled(False); context_menu.addAction(delete_action)

        context_menu.exec(self.context_menu_page_widget.mapToGlobal(pos))
        
    def copy_selected_text(self):
        if not self.selection_start_point or not self.selection_end_point or self.current_selection_page == -1:
            self.status_bar.showMessage("No text selected."); return

        page_widget = self.page_widgets[self.current_selection_page]
        pdf_rect = self._widget_coords_to_pdf_rect(page_widget, self.selection_start_point, self.selection_end_point)
        
        if pdf_rect:
            try:
                page = self.pdf_document.load_page(self.current_selection_page)
                selected_text = page.get_textbox(pdf_rect).strip()
                
                if selected_text:
                    clipboard = QApplication.clipboard()
                    clipboard.setText(selected_text)
                    self.status_bar.showMessage("Selected text copied to clipboard.")
                else:
                    self.status_bar.showMessage("No text found in selected area.")
            except Exception as e:
                self.status_bar.showMessage(f"Error extracting text: {e}")
        
        self.selection_start_point = None; self.selection_end_point = None; self.current_selection_page = -1
        self.update_view()
        
    def delete_nearest_annotation(self, pos, page_widget):
        page_num = page_widget.property("page_num")
        if page_num not in self.annotations: return

        click_point = pos
        pixmap = page_widget.pixmap(); 
        if not pixmap: return

        label_size = page_widget.size(); pixmap_size = pixmap.size()
        x_offset_alignment = (label_size.width() - pixmap_size.width()) // 2
        y_offset_alignment = (label_size.height() - pixmap_size.height()) // 2
        click_x_check = click_point.x(); click_y_check = click_point.y()
        
        min_distance = float('inf'); nearest_index = -1

        for i, (x, y, text) in enumerate(self.annotations[page_num]):
            scaled_x = x * self.zoom_level + x_offset_alignment
            scaled_y = y * self.zoom_level + y_offset_alignment
            distance = ((scaled_x - click_x_check)**2 + (scaled_y - click_y_check)**2)**0.5
            
            if distance < min_distance and distance < 30: 
                min_distance = distance
                nearest_index = i

        if nearest_index != -1:
            x, y, text = self.annotations[page_num][nearest_index]
            reply = QMessageBox.question(self, "Delete Annotation", f"Delete annotation: '{text}'?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.annotations[page_num].pop(nearest_index)
                if not self.annotations[page_num]: del self.annotations[page_num]
                
                page = self.pdf_document.load_page(page_num)
                for annot in page.annots():
                    if annot.type[0] == 8: 
                        pos = annot.rect.top_left
                        if abs(pos.x - x) < 1 and abs(pos.y - y) < 1 and annot.info.get("content") == text:
                            page.delete_annot(annot); break
                            
                save_annotations(self)
                self.render_page_content(page_num, page_widget) 
                self.status_bar.showMessage("Annotation deleted")
        else:
            self.status_bar.showMessage("No nearby annotation found to delete.")

    # --- DOCUMENT FUNCTIONS ---
    
    def show_metadata(self):
        if not self.pdf_document:
            self.status_bar.showMessage("No PDF loaded to show properties."); return

        metadata = self.pdf_document.metadata
        info_text = (
            f"Title: {metadata.get('title', 'N/A')}\n"
            f"Author: {metadata.get('author', 'N/A')}\n"
            f"Producer: {metadata.get('producer', 'N/A')}\n"
            f"Creator: {metadata.get('creator', 'N/A')}\n"
            f"Creation Date: {metadata.get('creationDate', 'N/A')}\n"
            f"Modification Date: {metadata.get('modDate', 'N/A')}\n"
            f"Format: {metadata.get('format', 'N/A')}\n"
            f"Page Count: {self.total_pages}\n"
        )
        QMessageBox.information(self, "PDF Document Properties", info_text)

    def print_pdf(self):
        if not self.pdf_document:
            self.status_bar.showMessage("No PDF loaded")
            return
        page_range, ok = QInputDialog.getText(
            self, "Print Pages", 
            f"Enter page range (e.g., '1-5' or 'all') (1-{self.total_pages}):",
            text=f"1-{self.total_pages}"
        )
        if not ok:
            return
        
        if page_range.lower() == "all":
            start_page = 0
            end_page = self.total_pages - 1
        else:
            try:
                if "-" in page_range:
                    start, end = map(int, page_range.split("-"))
                    start_page = max(0, start - 1)
                    end_page = min(self.total_pages - 1, end - 1)
                else:
                    start_page = end_page = int(page_range) - 1
                    if not (0 <= start_page < self.total_pages):
                        raise ValueError("Invalid page number")
            except ValueError:
                self.status_bar.showMessage("Invalid page range")
                return
        
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QPrintDialog.DialogCode.Accepted:
            try:
                painter = QPainter()
                if not painter.begin(printer):
                    self.status_bar.showMessage("Failed to initialize printer")
                    return
                
                for page_num in range(start_page, end_page + 1):
                    if page_num > start_page:
                        if not printer.newPage():
                            painter.end()
                            self.status_bar.showMessage("Failed to advance to next page")
                            return
                            
                    page = self.pdf_document.load_page(page_num)
                    matrix = fitz.Matrix(1, 1).prerotate(self.rotation)
                    pix = page.get_pixmap(matrix=matrix)
                    img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                    pixmap = QPixmap.fromImage(img)
                    
                    printer_rect = printer.pageRect(QPrinter.Unit.Pixel)
                    scaled_pixmap = pixmap.scaled(
                        printer_rect.width(), printer_rect.height(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    
                    x_offset = (printer_rect.width() - scaled_pixmap.width()) // 2
                    y_offset = (printer_rect.height() - scaled_pixmap.height()) // 2
                    painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
                
                painter.end()
                self.status_bar.showMessage(f"Printed pages {start_page + 1}-{end_page + 1}")
            except Exception as e:
                painter.end()
                self.status_bar.showMessage(f"Print error: {str(e)}")
                
    def save_pdf(self):
        if not self.pdf_document:
            self.status_bar.showMessage("No PDF loaded")
            return
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save PDF File", "", "PDF Files (*.pdf)"
        )
        if file_name:
            try:
                # Re-add all saved annotations to the document before saving
                for page_num in self.annotations:
                    page = self.pdf_document.load_page(page_num)
                    for x, y, text in self.annotations[page_num]:
                        existing = False
                        # Check if annotation already exists to prevent duplicates
                        for annot in page.annots():
                            if annot.type[0] == 8:
                                pos = annot.rect.top_left
                                if abs(pos.x - x) < 1 and abs(pos.y - y) < 1 and annot.info.get("content") == text:
                                    existing = True
                                    break
                        if not existing:
                            annot = page.add_text_annot(fitz.Point(x, y), text)
                            annot.set_colors(stroke=(1, 0, 0))
                            annot.update()
                            
                self.pdf_document.save(file_name)
                save_annotations(self)
                self.status_bar.showMessage(f"PDF saved as: {file_name}")
            except Exception as e:
                self.status_bar.showMessage(f"Error saving PDF: {str(e)}")
        
    # --- UTILITY HOOKS (Calls functions from pdf_utils.py) ---
    
    def focus_search(self): self.search_input.setFocus(); self.search_input.selectAll()
    def start_search(self): search_text(self)
    def next_search_result(self): next_search_result(self)
    def prev_search_result(self): prev_search_result(self)
    def add_page_action(self): add_page(self)
    def remove_page_action(self): remove_page(self)
    def move_page_up_action(self): move_page_up(self)
    def move_page_down_action(self): move_page_down(self)
        
    def load_thumbnails(self):
        self.thumbnail_list.clear()
        if self.pdf_document:
            for page_num in range(self.total_pages):
                page = self.pdf_document.load_page(page_num)
                pix = page.get_pixmap(matrix=fitz.Matrix(0.2, 0.2))
                img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format.Format_RGB888)
                pixmap = QPixmap.fromImage(img)
                item = QListWidgetItem(f"Page {page_num + 1}")
                item.setIcon(QIcon(pixmap))
                self.thumbnail_list.addItem(item)
                
    def thumbnail_clicked(self, item):
        self.current_page = self.thumbnail_list.row(item)
        self.update_ui_on_page_change()
        if self.view_mode == self.CONTINUOUS: self.scroll_to_page(self.current_page)
        
    def load_toc(self):
        self.toc_list.clear()
        if self.pdf_document:
            toc = self.pdf_document.get_toc()
            for level, title, page_num in toc:
                if page_num <= self.total_pages:
                    item = QListWidgetItem("  " * (level - 1) + title)
                    item.setData(Qt.ItemDataRole.UserRole, page_num - 1)
                    self.toc_list.addItem(item)
                
    def toc_clicked(self, item):
        self.current_page = item.data(Qt.ItemDataRole.UserRole)
        self.update_ui_on_page_change()
        if self.view_mode == self.CONTINUOUS: self.scroll_to_page(self.current_page)
        
    def resizeEvent(self, event):
        super().resizeEvent(event)
    
        if not self.pdf_document:
            return

        # Check if a fit-to-page/width zoom mode is active (by checking zoom_combo text)
        current_zoom_text = self.zoom_combo.currentText()
    
        if current_zoom_text == "Fit Width":
            self.set_zoom_fit_width()
        elif current_zoom_text == "Fit Page":
            self.set_zoom_fit_page()
        else:
            # If zoom is set to a fixed percentage (e.g., 100%), only re-render visible pages
            self.update_view() # This will now use the optimized view functions

    def toggle_view_mode(self):
        self.view_mode = self.CONTINUOUS if self.view_mode == self.SINGLE_PAGE else self.SINGLE_PAGE
        
        if self.view_mode == self.CONTINUOUS:
            self.view_mode_button.setText("Single Page")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            self.status_bar.showMessage("Continuous View Mode")
        else:
            self.view_mode_button.setText("Continuous")
            self.prev_button.setEnabled(self.current_page > 0)
            self.next_button.setEnabled(self.current_page < self.total_pages - 1)
            self.status_bar.showMessage("Single Page View Mode")
            
        self.update_view()
        
    def toggle_dark_mode(self):
        self.dark_mode = not self.dark_mode
        
        if self.dark_mode:
            self.scroll_area.setStyleSheet("background-color: #1e1e1e;") 
            self.dark_mode_button.setText("Light Mode")
            self.status_bar.showMessage("Dark Mode enabled")
        else:
            self.scroll_area.setStyleSheet("background-color: #f5f5f5;")
            self.dark_mode_button.setText("Dark Mode")
            self.status_bar.showMessage("Light Mode enabled")