"""PDF Viewer widget with redaction drawing capabilities."""

from PyQt6.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsPixmapItem
from PyQt6.QtCore import Qt, pyqtSignal, QPointF, QRectF, QTimer
from PyQt6.QtGui import QPixmap, QImage, QPen, QBrush, QColor, QCursor, QMouseEvent, QPainter, QWheelEvent


class PDFViewerScene(QGraphicsScene):
    """Custom scene to hold PDF page and redaction overlays."""

    def __init__(self):
        super().__init__()


class RedactionRectItem(QGraphicsRectItem):
    """Represents a final black redaction rectangle."""

    def __init__(self, rect: QRectF):
        super().__init__(rect)
        # Solid black rectangle
        self.setPen(QPen(Qt.GlobalColor.black, 2))
        self.setBrush(QBrush(Qt.GlobalColor.black))


class PDFViewer(QGraphicsView):
    """
    Custom PDF viewer with mouse-based rectangle drawing for redactions.

    Signals:
        redaction_added: Emitted when user completes drawing a redaction rectangle
                        Parameters: (QRectF rect, tuple page_size)
        next_page_requested: Emitted when user scrolls past the bottom
        previous_page_requested: Emitted when user scrolls past the top
    """

    redaction_added = pyqtSignal(QRectF, tuple)  # rect, page_size
    next_page_requested = pyqtSignal()
    previous_page_requested = pyqtSignal()

    def __init__(self):
        super().__init__()

        # Setup scene
        self.scene = PDFViewerScene()
        self.setScene(self.scene)

        # PDF display
        self.pixmap_item: QGraphicsPixmapItem | None = None
        self.page_size: tuple[float, float] = (0.0, 0.0)  # Original PDF page size

        # Drawing state
        self.drawing_rect: QGraphicsRectItem | None = None
        self.start_point: QPointF | None = None
        self.is_drawing: bool = False

        # Zoom
        self.zoom_factor: float = 1.0

        # View settings - enable high quality rendering
        self.setRenderHints(
            QPainter.RenderHint.Antialiasing |
            QPainter.RenderHint.SmoothPixmapTransform |
            QPainter.RenderHint.TextAntialiasing
        )
        self.setDragMode(QGraphicsView.DragMode.NoDrag)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        # Enable scrollbars for large documents
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Enable mouse tracking
        self.setMouseTracking(True)

    def set_page_image(self, qimage: QImage, page_size: tuple[float, float]) -> None:
        """
        Display a PDF page image in the viewer.

        Args:
            qimage: Rendered PDF page as QImage
            page_size: Original PDF page dimensions (width, height) in points
        """
        # Clear existing content
        self.clear_page()

        # Convert QImage to QPixmap and add to scene
        pixmap = QPixmap.fromImage(qimage)
        self.pixmap_item = self.scene.addPixmap(pixmap)

        # Store page size for coordinate conversion
        self.page_size = page_size

        # Set scene rect to pixmap bounds
        self.setSceneRect(self.pixmap_item.boundingRect())

        # Reset transform to show image at native resolution (no scaling)
        self.resetTransform()
        self.zoom_factor = 1.0

    def clear_page(self) -> None:
        """Clear all items from the scene."""
        self.scene.clear()
        self.pixmap_item = None
        self.drawing_rect = None
        self.start_point = None
        self.is_drawing = False
        self.page_size = (0.0, 0.0)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Handle mouse press to start drawing a redaction rectangle."""
        if event.button() == Qt.MouseButton.LeftButton and self.pixmap_item:
            # Convert view coordinates to scene coordinates
            self.start_point = self.mapToScene(event.pos())
            self.is_drawing = True

        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        """Handle mouse move to update the temporary redaction rectangle."""
        if self.is_drawing and self.start_point:
            # Get current point in scene coordinates
            current_point = self.mapToScene(event.pos())

            # Remove previous temporary rectangle
            if self.drawing_rect:
                self.scene.removeItem(self.drawing_rect)
                self.drawing_rect = None

            # Create new temporary rectangle (red with dashed border)
            rect = QRectF(self.start_point, current_point).normalized()
            self.drawing_rect = QGraphicsRectItem(rect)
            self.drawing_rect.setPen(QPen(Qt.GlobalColor.red, 2, Qt.PenStyle.DashLine))
            self.drawing_rect.setBrush(QBrush(QColor(255, 0, 0, 50)))  # Semi-transparent red
            self.scene.addItem(self.drawing_rect)

        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        """Handle mouse release to finalize the redaction rectangle."""
        if self.is_drawing and event.button() == Qt.MouseButton.LeftButton and self.start_point:
            # Get end point in scene coordinates
            end_point = self.mapToScene(event.pos())

            # Remove temporary rectangle
            if self.drawing_rect:
                self.scene.removeItem(self.drawing_rect)
                self.drawing_rect = None

            # Create final rectangle (normalized to handle any drag direction)
            rect = QRectF(self.start_point, end_point).normalized()

            # Only create redaction if rectangle has area
            if rect.width() > 5 and rect.height() > 5:  # Minimum size threshold
                # Create final black rectangle
                final_rect = RedactionRectItem(rect)
                self.scene.addItem(final_rect)

                # Emit signal with rectangle and page size
                self.redaction_added.emit(rect, self.page_size)

            # Reset drawing state
            self.is_drawing = False
            self.start_point = None

        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        """Handle mouse wheel events for page navigation."""
        # Get vertical scrollbar
        vbar = self.verticalScrollBar()

        # Check if scrolling down and at bottom
        if event.angleDelta().y() < 0:  # Scrolling down
            if vbar.value() >= vbar.maximum() - 10:  # Near bottom (with small threshold)
                # Request next page
                self.next_page_requested.emit()
                return  # Don't process scroll

        # Check if scrolling up and at top
        elif event.angleDelta().y() > 0:  # Scrolling up
            if vbar.value() <= vbar.minimum() + 10:  # Near top (with small threshold)
                # Request previous page
                self.previous_page_requested.emit()
                return  # Don't process scroll

        # Normal scroll behavior
        super().wheelEvent(event)

    def zoom_in(self) -> None:
        """Zoom in the view."""
        self.zoom_factor *= 1.25
        self.scale(1.25, 1.25)

    def zoom_out(self) -> None:
        """Zoom out the view."""
        self.zoom_factor /= 1.25
        self.scale(0.8, 0.8)

    def reset_zoom(self) -> None:
        """Reset zoom to fit the page."""
        if self.pixmap_item:
            self.resetTransform()
            self.zoom_factor = 1.0
            self.fitInView(self.pixmap_item, Qt.AspectRatioMode.KeepAspectRatio)

    def scroll_to_top(self) -> None:
        """Scroll to the top of the page."""
        self.verticalScrollBar().setValue(0)

    def scroll_to_bottom(self) -> None:
        """Scroll to the bottom of the page."""
        self.verticalScrollBar().setValue(self.verticalScrollBar().maximum())
