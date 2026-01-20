import sys
from PyQt6.QtWidgets import QApplication
from pdf_reader_app import PDFReader

if __name__ == '__main__':
    # Set up the application environment
    app = QApplication(sys.argv)
    QApplication.setQuitOnLastWindowClosed(True) 
    
    # Launch the main application class
    reader = PDFReader()
    reader.show()
    
    sys.exit(app.exec())