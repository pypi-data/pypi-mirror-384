import os
from PySide6.QtWidgets import QMainWindow, QVBoxLayout, QWidget
from PySide6.QtGui import QIcon, QPixmap, QPalette, QBrush, QPainter
from PySide6.QtCore import Qt


class PvWindow(QMainWindow):
    def __init__(
            self,
            title="PyVisual Window",
            width=800,
            height=600,
            bg_color=(255, 255, 255, 1),
            icon=None,
            bg_image=None,
            is_frameless=False,
            is_resizable=False
    ):
        super().__init__()

        # Initialize parameters
        self.title = title
        self.width = width
        self.height = height
        self.bg_color = bg_color
        self.is_frameless = is_frameless
        self.is_resizable = is_resizable
        self.bg_image = bg_image

        # We'll store the QPixmap for your background image
        self._bg_pixmap = None

        # Resolve the default icon path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        self.default_icon_path = os.path.join(current_dir, "..", "assets", "icons", "window", "window.png")
        self.icon_path = icon or self.default_icon_path

        # Apply window configurations
        self._configure_window()

        # Root widget container
        self.root_widget = QWidget()
        self.layout = QVBoxLayout(self.root_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove margins
        self.layout.setSpacing(0)  # Remove spacing between widgets
        self.setCentralWidget(self.root_widget)

        # If a background image is provided, load it into a QPixmap
        if self.bg_image:
            self._bg_pixmap = QPixmap(self.bg_image)
            # Remove the style sheet so it doesn’t override the palette-based background
            self.setStyleSheet("")
        else:
            # If there’s no image, keep your background color
            r, g, b, a = self.bg_color
            self.setStyleSheet(f"background-color: rgba({r},{g},{b},{a});")

    def _configure_window(self):
        """Configure the window properties."""
        self.setWindowTitle(self.title)
        self.setGeometry(100, 100, self.width, self.height)

        # Set window icon
        if os.path.exists(self.icon_path):
            self.setWindowIcon(QIcon(self.icon_path))

        # Frameless and resizable settings
        if self.is_frameless:
            self.setWindowFlags(Qt.FramelessWindowHint)
        if not self.is_resizable:
            self.setFixedSize(self.width, self.height)

    def set_bg_image(self, bg_image):
        """Called if you ever want to change the background image at runtime."""
        self.bg_image = bg_image
        self._bg_pixmap = QPixmap(bg_image)
        # Remove style sheet so it doesn't conflict
        self.setStyleSheet("")
        # Trigger a manual resize event so it updates immediately
        self.resizeEvent(None)

    def add_widget(self, widget):
        """Add a widget to the main container."""
        self.layout.addWidget(widget)

    def resizeEvent(self, event):
        """
        Automatically update/scale the background image when the window is resized.
        Qt.KeepAspectRatioByExpanding will fill the area without stretching.
        This modified version centers the scaled image.
        """
        super().resizeEvent(event)  # Let the parent do its normal work

        if self._bg_pixmap:
            # Scale the pixmap to cover the entire root_widget size
            scaled_pixmap = self._bg_pixmap.scaled(
                self.root_widget.size(),
                Qt.KeepAspectRatioByExpanding,
                Qt.SmoothTransformation
            )
            # Create a new pixmap with the size of the root widget
            result_pixmap = QPixmap(self.root_widget.size())
            result_pixmap.fill(Qt.transparent)

            # Calculate offsets to center the scaled image
            x_offset = round((self.root_widget.width() - scaled_pixmap.width()) / 2)
            y_offset = round((self.root_widget.height() - scaled_pixmap.height()) / 2)
            # Draw the scaled pixmap onto the result pixmap at the computed offset
            painter = QPainter(result_pixmap)
            painter.drawPixmap(x_offset, y_offset, scaled_pixmap)
            painter.end()

            # Use the palette to set this composite pixmap as the background
            palette = self.root_widget.palette()
            palette.setBrush(self.root_widget.backgroundRole(), QBrush(result_pixmap))
            self.root_widget.setPalette(palette)
            # Ensure the background is actually drawn
            self.root_widget.setAutoFillBackground(True)

    def show(self):
        """Show the window."""
        super().show()


# Example Usage
if __name__ == "__main__":
    import sys
    import pyvisual as pv  # or however your PvApp is defined

    app = pv.PvApp()

    # Replace 'path_to_your_image.jpg' with your actual image path
    window = PvWindow("PyVisual Window", bg_image="path_to_your_image.jpg")
    window2 = PvWindow("Another Window", bg_image="path_to_your_image.jpg")

    window.show()
    window2.show()

    app.run()
