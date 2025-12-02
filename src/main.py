"""PDF Redactor - Main entry point."""

import sys
from PyQt6.QtWidgets import QApplication
from views.main_window import MainWindow


def main():
    """Initialize and run the PDF Redactor application."""
    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("PDF Redactor")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("PDF Redactor")

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
