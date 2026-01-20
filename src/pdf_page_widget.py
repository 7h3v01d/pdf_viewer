from PyQt6.QtWidgets import QLabel

class PDFPageWidget(QLabel):
    """
    A custom QLabel that automatically repositions its child form fields
    whenever it is resized.
    """
    def __init__(self, app_instance, page_num, parent=None):
        super().__init__(parent)
        self.app = app_instance
        self.page_num = page_num

    def resizeEvent(self, event):
        """Overrides the default resize event."""
        # First, let the parent QLabel handle its own resize logic.
        super().resizeEvent(event)
        
        # Now, if form fields exist for this page, tell the main app to reposition them.
        # This check prevents errors when no PDF is loaded.
        if self.page_num in self.app.field_widgets:
            self.app._reposition_form_fields(self.page_num, self)