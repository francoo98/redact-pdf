"""PDF Document Model - Wrapper around PyMuPDF for PDF operations."""

from typing import Optional
import fitz  # PyMuPDF
from PyQt6.QtGui import QImage


class PDFDocument:
    """Manages PDF document operations including rendering and redaction."""

    def __init__(self):
        """Initialize an empty PDF document."""
        self.doc: Optional[fitz.Document] = None
        self.current_page_num: int = 0
        self.redaction_rects: dict[int, list[fitz.Rect]] = {}  # {page_num: [rect1, rect2, ...]}
        self.file_path: Optional[str] = None

    def open_pdf(self, file_path: str) -> bool:
        """
        Open a PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            True if successful, False otherwise
        """
        try:
            self.close_pdf()  # Close any existing document
            self.doc = fitz.open(file_path)
            self.file_path = file_path
            self.current_page_num = 0
            self.redaction_rects = {}
            return True
        except Exception as e:
            print(f"Error opening PDF: {e}")
            return False

    def close_pdf(self) -> None:
        """Close the current PDF document."""
        if self.doc:
            self.doc.close()
            self.doc = None
            self.file_path = None
            self.current_page_num = 0
            self.redaction_rects = {}

    def get_page_count(self) -> int:
        """
        Get the total number of pages in the PDF.

        Returns:
            Number of pages, or 0 if no document is open
        """
        if self.doc:
            return len(self.doc)
        return 0

    def render_page(self, page_num: int, zoom: float = 1.0) -> tuple[Optional[QImage], tuple[float, float]]:
        """
        Render a PDF page to a QImage.

        Args:
            page_num: Page number (0-indexed)
            zoom: Zoom factor (1.0 = 100%, 2.0 = 200%, etc.)

        Returns:
            Tuple of (QImage, (page_width, page_height)) or (None, (0, 0)) if error
        """
        if not self.doc or page_num < 0 or page_num >= len(self.doc):
            return None, (0.0, 0.0)

        try:
            page = self.doc.load_page(page_num)

            # Get original page dimensions (in PDF points)
            page_rect = page.rect
            page_width = page_rect.width
            page_height = page_rect.height

            # Create transformation matrix for zoom
            mat = fitz.Matrix(zoom, zoom)

            # Render page to pixmap
            pix = page.get_pixmap(matrix=mat)

            # Convert PyMuPDF pixmap to QImage
            img = QImage(
                pix.samples,
                pix.width,
                pix.height,
                pix.stride,
                QImage.Format.Format_RGB888
            )

            # Make a copy to ensure the data persists
            img = img.copy()

            return img, (page_width, page_height)
        except Exception as e:
            print(f"Error rendering page {page_num}: {e}")
            return None, (0.0, 0.0)

    def add_redaction_rect(self, page_num: int, rect: fitz.Rect) -> None:
        """
        Add a redaction rectangle for a specific page.

        Args:
            page_num: Page number (0-indexed)
            rect: Rectangle to redact in PDF coordinates
        """
        if page_num not in self.redaction_rects:
            self.redaction_rects[page_num] = []
        self.redaction_rects[page_num].append(rect)

    def save_redacted_pdf(self, output_path: str) -> bool:
        """
        Save the PDF with redactions applied.

        Args:
            output_path: Path where to save the redacted PDF

        Returns:
            True if successful, False otherwise
        """
        if not self.doc:
            return False

        try:
            # Apply redactions to each page
            for page_num, rects in self.redaction_rects.items():
                if page_num < 0 or page_num >= len(self.doc):
                    continue

                page = self.doc.load_page(page_num)

                # Add redaction annotations (black rectangles)
                for rect in rects:
                    page.add_redact_annot(rect, fill=(0, 0, 0))

                # Apply redactions (this permanently removes content)
                page.apply_redactions()

            # Save to output file
            self.doc.save(output_path, garbage=4, deflate=True)
            return True
        except Exception as e:
            print(f"Error saving redacted PDF: {e}")
            return False

    def is_open(self) -> bool:
        """Check if a PDF document is currently open."""
        return self.doc is not None
