"""Main application window."""

from PyQt6.QtWidgets import (
    QMainWindow, QFileDialog, QToolBar, QStatusBar, QMessageBox
)
from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QAction, QKeySequence

from views.pdf_viewer import PDFViewer
from controllers.redaction_controller import RedactionController


class MainWindow(QMainWindow):
    """Main application window with menu, toolbar, and PDF viewer."""

    def __init__(self):
        super().__init__()

        # Initialize components
        self.pdf_viewer = PDFViewer()
        self.controller = RedactionController()

        # Setup UI
        self.setup_ui()
        self.create_menu_bar()
        self.create_toolbar()
        self.create_status_bar()
        self.connect_signals()

        # Initial state
        self.current_file_path: str | None = None
        self.update_window_state()

    def setup_ui(self) -> None:
        """Setup the main window UI."""
        self.setWindowTitle("PDF Redactor")
        self.resize(1024, 768)

        # Set PDF viewer as central widget
        self.setCentralWidget(self.pdf_viewer)

    def create_menu_bar(self) -> None:
        """Create the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        # Open PDF action
        self.open_action = QAction("&Open PDF...", self)
        self.open_action.setShortcut(QKeySequence.StandardKey.Open)
        self.open_action.setStatusTip("Open a PDF file")
        self.open_action.triggered.connect(self.open_pdf_dialog)
        file_menu.addAction(self.open_action)

        # Save As action
        self.save_action = QAction("&Save As...", self)
        self.save_action.setShortcut(QKeySequence.StandardKey.Save)
        self.save_action.setStatusTip("Save redacted PDF")
        self.save_action.triggered.connect(self.save_pdf_dialog)
        file_menu.addAction(self.save_action)

        file_menu.addSeparator()

        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        # Zoom In action
        self.zoom_in_action = QAction("Zoom &In", self)
        self.zoom_in_action.setShortcut(QKeySequence.StandardKey.ZoomIn)
        self.zoom_in_action.setStatusTip("Zoom in")
        self.zoom_in_action.triggered.connect(self.pdf_viewer.zoom_in)
        view_menu.addAction(self.zoom_in_action)

        # Zoom Out action
        self.zoom_out_action = QAction("Zoom &Out", self)
        self.zoom_out_action.setShortcut(QKeySequence.StandardKey.ZoomOut)
        self.zoom_out_action.setStatusTip("Zoom out")
        self.zoom_out_action.triggered.connect(self.pdf_viewer.zoom_out)
        view_menu.addAction(self.zoom_out_action)

        # Reset Zoom action
        self.reset_zoom_action = QAction("&Fit to Window", self)
        self.reset_zoom_action.setShortcut("Ctrl+0")
        self.reset_zoom_action.setStatusTip("Fit page to window")
        self.reset_zoom_action.triggered.connect(self.pdf_viewer.reset_zoom)
        view_menu.addAction(self.reset_zoom_action)

    def create_toolbar(self) -> None:
        """Create the application toolbar."""
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        # Add actions to toolbar
        toolbar.addAction(self.open_action)
        toolbar.addAction(self.save_action)
        toolbar.addSeparator()
        toolbar.addAction(self.zoom_in_action)
        toolbar.addAction(self.zoom_out_action)
        toolbar.addAction(self.reset_zoom_action)

    def create_status_bar(self) -> None:
        """Create the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def connect_signals(self) -> None:
        """Connect signals and slots between components."""
        # Connect PDF viewer redaction signal to controller
        self.pdf_viewer.redaction_added.connect(self.on_redaction_added)

    def open_pdf_dialog(self) -> None:
        """Open file dialog to select a PDF file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Open PDF File",
            "",
            "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            self.open_pdf(file_path)

    def open_pdf(self, file_path: str) -> None:
        """
        Open and display a PDF file.

        Args:
            file_path: Path to the PDF file
        """
        success, message = self.controller.open_pdf(file_path)

        if success:
            self.current_file_path = file_path

            # Get rendered page from controller
            qimage, page_size = self.controller.get_current_page_image()

            if qimage:
                # Display in viewer
                self.pdf_viewer.set_page_image(qimage, page_size)

                # Update UI state
                self.update_window_state()
                self.status_bar.showMessage(f"Loaded: {file_path}")
            else:
                self.show_error("Failed to render PDF page")
        else:
            self.show_error(f"Failed to open PDF: {message}")

    def save_pdf_dialog(self) -> None:
        """Open file dialog to save the redacted PDF."""
        if not self.controller.is_pdf_open():
            self.show_error("No PDF is currently open")
            return

        # Suggest output filename
        default_name = ""
        if self.current_file_path:
            import os
            base = os.path.splitext(self.current_file_path)[0]
            default_name = f"{base}_redacted.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Redacted PDF",
            default_name,
            "PDF Files (*.pdf);;All Files (*)"
        )

        if file_path:
            # Ensure .pdf extension
            if not file_path.lower().endswith('.pdf'):
                file_path += '.pdf'

            self.save_pdf(file_path)

    def save_pdf(self, output_path: str) -> None:
        """
        Save the redacted PDF.

        Args:
            output_path: Path where to save the file
        """
        success = self.controller.save_redacted_pdf(output_path)

        if success:
            self.status_bar.showMessage(f"Saved: {output_path}")
            QMessageBox.information(
                self,
                "Success",
                f"Redacted PDF saved successfully to:\n{output_path}"
            )
        else:
            self.show_error("Failed to save redacted PDF")

    def on_redaction_added(self, rect: QRectF, page_size: tuple) -> None:
        """
        Handle when a redaction rectangle is added in the viewer.

        Args:
            rect: Rectangle in scene coordinates
            page_size: Original PDF page size
        """
        # Forward to controller to convert and store
        self.controller.add_redaction(rect, page_size)
        self.status_bar.showMessage("Redaction added")

    def update_window_state(self) -> None:
        """Update UI state based on whether a PDF is open."""
        pdf_is_open = self.controller.is_pdf_open()

        # Enable/disable actions based on state
        self.save_action.setEnabled(pdf_is_open)
        self.zoom_in_action.setEnabled(pdf_is_open)
        self.zoom_out_action.setEnabled(pdf_is_open)
        self.reset_zoom_action.setEnabled(pdf_is_open)

    def show_error(self, message: str) -> None:
        """
        Show an error message dialog.

        Args:
            message: Error message to display
        """
        QMessageBox.critical(self, "Error", message)
        self.status_bar.showMessage(f"Error: {message}")
