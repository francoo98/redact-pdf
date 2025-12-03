"""Controller for managing PDF redaction operations."""

from PyQt6.QtCore import QRectF
from PyQt6.QtGui import QImage
import fitz

from models.pdf_document import PDFDocument


class RedactionController:
    """
    Coordinates between PDF model and viewer.

    Handles business logic for loading PDFs, converting coordinates,
    and managing redaction state.
    """

    def __init__(self):
        """Initialize the controller."""
        self.pdf_model = PDFDocument()
        self.current_zoom = 1.5
        self.current_page_num = 0

    def open_pdf(self, file_path: str) -> tuple[bool, str]:
        """
        Open a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (success: bool, message: str)
        """
        success = self.pdf_model.open_pdf(file_path)

        if success:
            self.current_page_num = 0
            return True, "PDF opened successfully"
        else:
            return False, "Failed to open PDF file"

    def get_current_page_image(self) -> tuple[QImage | None, tuple[float, float]]:
        """
        Get the rendered image of the current page.

        Returns:
            Tuple of (QImage, (page_width, page_height))
        """
        return self.pdf_model.render_page(self.current_page_num, self.current_zoom)

    def add_redaction(self, view_rect: QRectF, page_size: tuple[float, float]) -> None:
        """
        Add a redaction rectangle.

        Converts viewer coordinates to PDF coordinates and stores the redaction.

        Args:
            view_rect: Rectangle in viewer scene coordinates (pixels)
            page_size: Original PDF page size (width, height) in points
        """
        # Convert viewer coordinates to PDF coordinates
        pdf_rect = self.convert_view_to_pdf_coords(view_rect, page_size)

        # Add to PDF model
        self.pdf_model.add_redaction_rect(self.current_page_num, pdf_rect)

    def convert_view_to_pdf_coords(
        self, view_rect: QRectF, page_size: tuple[float, float]
    ) -> fitz.Rect:
        """
        Convert viewer scene coordinates to PDF coordinates.

        The viewer displays a rendered image of the PDF page. This image is
        created at a certain zoom level. The scene coordinates are in pixels
        of this rendered image. We need to convert back to PDF point coordinates.

        Args:
            view_rect: Rectangle in scene coordinates (pixels of rendered image)
            page_size: Original PDF page dimensions (width, height) in points

        Returns:
            Rectangle in PDF coordinate system (points)
        """
        page_width, page_height = page_size

        # The rendered image has dimensions: page_size * zoom
        # So to convert back: pdf_coord = view_coord / zoom
        x0 = view_rect.left() / self.current_zoom
        y0 = view_rect.top() / self.current_zoom
        x1 = view_rect.right() / self.current_zoom
        y1 = view_rect.bottom() / self.current_zoom

        # Create PDF rectangle
        # Note: PDF coordinates have origin at bottom-left, but for redactions
        # PyMuPDF handles this correctly with the rect as-is
        return fitz.Rect(x0, y0, x1, y1)

    def save_redacted_pdf(self, output_path: str) -> bool:
        """
        Save the PDF with redactions applied.

        Args:
            output_path: Path where to save the redacted PDF

        Returns:
            True if successful, False otherwise
        """
        return self.pdf_model.save_redacted_pdf(output_path)

    def is_pdf_open(self) -> bool:
        """Check if a PDF is currently open."""
        return self.pdf_model.is_open()

    def set_zoom(self, zoom: float) -> None:
        """
        Set the zoom level for rendering.

        Args:
            zoom: Zoom factor (1.0 = 100%, 2.0 = 200%, etc.)
        """
        self.current_zoom = zoom

    def get_page_count(self) -> int:
        """Get the total number of pages in the PDF."""
        return self.pdf_model.get_page_count()

    def get_current_page_number(self) -> int:
        """Get the current page number (0-indexed)."""
        return self.current_page_num

    def go_to_page(self, page_num: int) -> tuple[QImage | None, tuple[float, float]]:
        """
        Navigate to a specific page.

        Args:
            page_num: Page number to navigate to (0-indexed)

        Returns:
            Tuple of (QImage, (page_width, page_height))
        """
        page_count = self.get_page_count()
        if 0 <= page_num < page_count:
            self.current_page_num = page_num
            return self.get_current_page_image()
        return None, (0.0, 0.0)

    def next_page(self) -> tuple[QImage | None, tuple[float, float]]:
        """
        Navigate to the next page.

        Returns:
            Tuple of (QImage, (page_width, page_height))
        """
        if self.current_page_num < self.get_page_count() - 1:
            self.current_page_num += 1
            return self.get_current_page_image()
        return None, (0.0, 0.0)

    def previous_page(self) -> tuple[QImage | None, tuple[float, float]]:
        """
        Navigate to the previous page.

        Returns:
            Tuple of (QImage, (page_width, page_height))
        """
        if self.current_page_num > 0:
            self.current_page_num -= 1
            return self.get_current_page_image()
        return None, (0.0, 0.0)

    def has_next_page(self) -> bool:
        """Check if there is a next page."""
        return self.current_page_num < self.get_page_count() - 1

    def has_previous_page(self) -> bool:
        """Check if there is a previous page."""
        return self.current_page_num > 0
