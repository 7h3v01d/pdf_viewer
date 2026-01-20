from PyQt6.QtWidgets import QScrollArea
from PyQt6.QtCore import Qt

# Import constants from the main reader file
try:
    from pdf_reader import SINGLE_PAGE, CONTINUOUS
except ImportError:
    # Define fallback constants if running this file alone
    SINGLE_PAGE = 0
    CONTINUOUS = 1

class PDFScrollArea(QScrollArea):
    """Custom QScrollArea to handle mouse wheel for page navigation."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent  # Reference to PDFReader instance

    def wheelEvent(self, event):
        if not self.parent.pdf_document:
            super().wheelEvent(event)
            return
        
        # Only use custom page navigation in SINGLE_PAGE mode
        if self.parent.view_mode == SINGLE_PAGE:
            v_scroll = self.verticalScrollBar()
            at_top = v_scroll.value() == v_scroll.minimum()
            at_bottom = v_scroll.value() == v_scroll.maximum()
            delta = event.angleDelta().y()
            content_height = self.widget().height()
            viewport_height = self.viewport().height()
            content_fits = content_height <= viewport_height

            # If the content fits OR if we are at the edge
            if content_fits or (delta > 0 and at_top) or (delta < 0 and at_bottom):
                if delta > 0 and self.parent.current_page > 0:
                    self.parent.prev_page()
                    return 
                elif delta < 0 and self.parent.current_page < self.parent.total_pages - 1:
                    self.parent.next_page()
                    return 
        
        # For CONTINUOUS mode, or if single-page mode scroll logic didn't trigger a page turn
        super().wheelEvent(event)