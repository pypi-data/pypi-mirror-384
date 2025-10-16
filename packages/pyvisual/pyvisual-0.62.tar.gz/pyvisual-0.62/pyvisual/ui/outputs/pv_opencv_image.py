from typing import Optional, TYPE_CHECKING
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QTransform, QPainterPath, QColor, QPen, QImage
from PySide6.QtCore import Qt

if TYPE_CHECKING:
    import cv2
    import numpy as np

# Global variables to hold our lazy-loaded modules.
_cv2: Optional["cv2"] = None
_np: Optional["np"] = None


def get_cv2():
    """Lazily load and return the cv2 module."""
    global _cv2
    if _cv2 is None:
        import cv2 as cv2_module
        _cv2 = cv2_module
    return _cv2


def get_np():
    """Lazily load and return the numpy module."""
    global _np
    if _np is None:
        import numpy as np_module
        _np = np_module
    return _np


class PvOpencvImage(QWidget):
    def __init__(self, container=None, x=0, y=0, width=640, height=480, corner_radius=0,fill=None,
                 flip_v=False, flip_h=False, rotate=0, scale=1.0, is_visible=True, opacity=1, tag=None,
                 border_color=None, border_hover_color=None, border_thickness=5,
                 on_hover=None, on_click=None, on_release=None,**kwargs):
        super().__init__(container)
        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._x = x
        self._y = y
        self._target_width = width
        self._target_height = height
        self._corner_radius = corner_radius
        self._flip_v = flip_v
        self._flip_h = flip_h
        self._rotate = rotate
        self._scale = scale
        self._is_visible = is_visible
        self._opacity = opacity
        self._pixmap = None  # Holds the current image as QPixmap
        self._tag = tag
        self._fill = fill

        # ---------------------------------------------------------
        # Border and Hover Properties
        # ---------------------------------------------------------
        self._border_thickness = border_thickness * 2  # border thickness doubling logic
        self._hovered = False

        # ---------------------------------------------------------
        # Callbacks for Mouse Events
        # ---------------------------------------------------------
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release

        # ---------------------------------------------------------
        # Convert provided color tuples to QColor if available
        # ---------------------------------------------------------
        self._border_color = (
            QColor(border_color[0], border_color[1], border_color[2], int(border_color[3] * 255))
            if border_color else None
        )
        self._border_hover_color = (
            QColor(border_hover_color[0], border_hover_color[1], border_hover_color[2],
                   int(border_hover_color[3] * 255))
            if border_hover_color else self._border_color
        )

        # ---------------------------------------------------------
        # Widget Setup
        # ---------------------------------------------------------
        self.setMouseTracking(True)
        self.setGeometry(self._x, self._y, int(self._target_width * self._scale),
                         int(self._target_height * self._scale))
        self.setVisible(self._is_visible)

    def update_image(self, image: "np.ndarray"):
        """
        Accepts an OpenCV image (BGR or BGRA format) as a NumPy array,
        converts it to QPixmap (handling images with an alpha channel),
        applies transformations, and updates the widget.
        """
        if image is None:
            return

        cv2 = get_cv2()
        # Check if image has an alpha channel or gray scale/binary
        if len(image.shape) == 2:
            # Convert from BGR (OpenCV) to RGB (Qt)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            q_format = QImage.Format_RGB888
        elif image.shape[2] == 3:
            # Convert from BGR (OpenCV) to RGB (Qt)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            q_format = QImage.Format_RGB888
        elif image.shape[2] == 4:
            # Convert from BGRA (OpenCV) to RGBA (Qt)
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
            q_format = QImage.Format_RGBA8888
        else:
            # Fallback for unexpected channel numbers.
            image_rgb = image
            q_format = QImage.Format_RGB888

        height, width, channels = image_rgb.shape
        bytes_per_line = channels * width
        q_img = QImage(image_rgb.data, width, height, bytes_per_line, q_format)
        self._pixmap = QPixmap.fromImage(q_img)
        self.configure_style()
        self.update()

    def configure_style(self):
        """Apply transformations (flip, rotate), scaling, and resize to target dimensions.
           If self._fill is truthy, the image will fill the entire container while maintaining
           its aspect ratio (the image will be cropped as necessary).
           Otherwise, it will be scaled to fit inside the container and centered.
        """
        if self._pixmap is None or self._pixmap.isNull():
            return

        transform = QTransform()
        if self._flip_h:
            transform.scale(-1, 1)
        if self._flip_v:
            transform.scale(1, -1)
        transform.rotate(self._rotate)
        transformed = self._pixmap.transformed(transform, Qt.SmoothTransformation)

        # Calculate final container size based on the scale.
        final_width = int(self._target_width * self._scale)
        final_height = int(self._target_height * self._scale)

        if self._fill:
            # Scale the image to completely cover the container, keeping aspect ratio.
            # This may result in some parts being cropped.
            scaled = transformed.scaled(final_width, final_height, Qt.KeepAspectRatioByExpanding,
                                        Qt.SmoothTransformation)
            # Create a new pixmap with the container size.
            centered = QPixmap(final_width, final_height)
            centered.fill(Qt.transparent)
            # Compute offsets to crop the central region of the scaled image.
            x_offset = (scaled.width() - final_width) // 2
            y_offset = (scaled.height() - final_height) // 2
            # Draw the central region onto the new pixmap.
            painter = QPainter(centered)
            painter.drawPixmap(0, 0, scaled, x_offset, y_offset, final_width, final_height)
            painter.end()
        else:
            # Scale the image to fit within the container while preserving aspect ratio.
            scaled = transformed.scaled(final_width, final_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Create a new pixmap with the container size.
            centered = QPixmap(final_width, final_height)
            centered.fill(Qt.transparent)
            # Compute offsets to center the scaled image.
            x_offset = (final_width - scaled.width()) // 2
            y_offset = (final_height - scaled.height()) // 2
            painter = QPainter(centered)
            painter.drawPixmap(x_offset, y_offset, scaled)
            painter.end()

        self._pixmap = centered
        # Set the widget geometry to the target container size.
        self.setGeometry(self._x, self._y, final_width, final_height)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setOpacity(self._opacity)

        # Apply rounded corners if needed.
        if self._corner_radius > 0:
            path = QPainterPath()
            path.addRoundedRect(self.rect(), self._corner_radius, self._corner_radius)
            painter.setClipPath(path)

        # Draw the placeholder background if no image is available.
        if self._pixmap is None:
            placeholder_color = QColor(211, 211, 211)  # light gray
            painter.fillRect(self.rect(), placeholder_color)
        else:
            painter.drawPixmap(0, 0, self._pixmap)

        # Draw the border only if border_thickness is greater than zero.
        if self._border_thickness > 0:
            border_color = self._border_hover_color if self._hovered else self._border_color
            if border_color:
                pen = QPen(border_color, self._border_thickness)
                painter.setPen(pen)
                painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

    def enterEvent(self, event):
        """Handle mouse hover enter event."""
        self._hovered = True
        if self._on_hover:
            self._on_hover(self)
        self.update()

    def leaveEvent(self, event):
        """Handle mouse hover leave event."""
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and self._on_click:
            self._on_click(self)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self._on_release:
            self._on_release(self)

    # ---------------------------------------------------------
    # Property Getters/Setters for common attributes
    # ---------------------------------------------------------
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.setGeometry(self._x, self._y, self.width, self.height)
        self.update()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.setGeometry(self._x, self._y, self.width, self.height)
        self.update()

    @property
    def width(self):
        return int(self._target_width * self._scale)

    @width.setter
    def width(self, value):
        self._target_width = value
        self.configure_style()
        self.update()

    @property
    def height(self):
        return int(self._target_height * self._scale)

    @height.setter
    def height(self, value):
        self._target_height = value
        self.configure_style()
        self.update()

    @property
    def corner_radius(self):
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
        self.update()

    @property
    def flip_v(self):
        return self._flip_v

    @flip_v.setter
    def flip_v(self, value):
        self._flip_v = value
        self.update()

    @property
    def flip_h(self):
        return self._flip_h

    @flip_h.setter
    def flip_h(self, value):
        self._flip_h = value
        self.update()

    @property
    def rotate(self):
        return self._rotate

    @rotate.setter
    def rotate(self, value):
        self._rotate = value
        self.update()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.configure_style()
        self.update()

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)
        self.update()

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value

    @property
    def border_color(self):
        if self._border_color:
            return (self._border_color.red(), self._border_color.green(),
                    self._border_color.blue(), self._border_color.alphaF())
        return None

    @border_color.setter
    def border_color(self, value):
        if value is None:
            self._border_color = None
        else:
            self._border_color = QColor(value[0], value[1], value[2], int(value[3] * 255))
        self.update()

    @property
    def border_hover_color(self):
        if self._border_hover_color:
            return (self._border_hover_color.red(), self._border_hover_color.green(),
                    self._border_hover_color.blue(), self._border_hover_color.alphaF())
        return None

    @border_hover_color.setter
    def border_hover_color(self, value):
        if value is None:
            self._border_hover_color = self._border_color
        else:
            self._border_hover_color = QColor(value[0], value[1], value[2], int(value[3] * 255))
        self.update()

    @property
    def border_thickness(self):
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value * 2  # maintain doubling logic
        self.update()

    @property
    def image(self):
        """Return the original OpenCV image (as a NumPy array) if available."""
        return self._original_image

    @image.setter
    def image(self, value: "np.ndarray"):
        """
        Set a new OpenCV image.
        This method stores the original image and then updates the widget display.
        If value is None, it removes the current image.
        """
        if value is None:
            self._original_image = None
            self._pixmap = None
            self.update()
        else:
            self._original_image = value
            self.update_image(value)

    def print_properties(self):
        print(f"""
        PvOpenCVImage Properties:
        --------------------------
        x: {self.x}
        y: {self.y}
        width: {self.width}
        height: {self.height}
        corner_radius: {self.corner_radius}
        flip_v: {self.flip_v}
        flip_h: {self.flip_h}
        rotate: {self.rotate}
        scale: {self.scale}
        is_visible: {self.is_visible}
        opacity: {self.opacity}
        border_color: {self.border_color}
        border_hover_color: {self.border_hover_color}
        border_thickness: {self.border_thickness}
        tag: {self.tag}
        """)


# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------
if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    import pyvisual as pv  # Assuming your pyvisual application module

    app = pv.PvApp()
    window = pv.PvWindow(title="PvOpenCVImage Example with Scale Option")

    # Create an instance of PvOpenCVImage.
    img_widget = PvOpencvImage(
        container=window,
        x=50,
        y=50,
        width=100,
        height=100,
        corner_radius=20,
        flip_h=False,
        rotate=0,
        scale=1.5,  # scale factor: 150% of target dimensions
        opacity=1,
        border_color=(255, 0, 0, 1),  # Red border (RGBA)
        border_hover_color=(0, 255, 0, 1),  # Green border on hover
        border_thickness=5,
        on_hover=lambda w: print("Hovered over PvOpenCVImage", w.tag),
        on_click=lambda w: print("PvOpenCVImage clicked", w.tag),
        on_release=lambda w: print("PvOpenCVImage released", w.tag)
    )
    img_widget.tag = "Sample PvOpenCVImage"
    img_widget.print_properties()

    # For demonstration, read a PNG image (or any image with transparency) using OpenCV.
    cv2 = get_cv2()
    image = cv2.imread(r'D:\Pycharm Projects\pyvisual\pyvisual\assets\buttons\default\clicked.png',
                       cv2.IMREAD_UNCHANGED)
    if image is not None:
        img_widget.update_image(image)
    else:
        print("Could not load image.")

    window.show()
    app.run()
