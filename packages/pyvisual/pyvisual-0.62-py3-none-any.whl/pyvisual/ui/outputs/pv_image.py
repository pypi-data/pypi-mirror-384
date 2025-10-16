from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QTransform, QPainterPath, QColor, QPen
from PySide6.QtCore import Qt


class PvImage(QWidget):
    def __init__(self, container=None, x=0, y=0, image_path="", scale=1.0, corner_radius=0,
                 flip_v=False, flip_h=False, rotate=0, is_visible=True, opacity=1, tag=None,
                 border_color=None, border_hover_color=None, border_thickness=5,
                 on_hover=None, on_click=None, on_release=None, **kwargs):
        super().__init__(container)

        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._x = x
        self._y = y
        self._image_path = image_path
        self._scale = scale
        self._corner_radius = corner_radius
        self._flip_v = flip_v
        self._flip_h = flip_h
        self._rotate = rotate
        self._is_visible = is_visible
        self._opacity = opacity
        self._pixmap = None

        # ---------------------------------------------------------
        # Border and Hover Properties
        # ---------------------------------------------------------
        # Note: border_thickness is doubled as per original code.
        self._border_thickness = border_thickness * 2
        self._hovered = False

        # ---------------------------------------------------------
        # Callbacks and Custom Tag
        # ---------------------------------------------------------
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release
        self._tag = tag

        # ---------------------------------------------------------
        # Convert provided color tuples to QColor if available
        # ---------------------------------------------------------
        self._border_color = (
            QColor(border_color[0], border_color[1], border_color[2],
                   int(border_color[3] * 255)) if border_color else None
        )
        self._border_hover_color = (
            QColor(border_hover_color[0], border_hover_color[1], border_hover_color[2],
                   int(border_hover_color[3] * 255)) if border_hover_color else self._border_color
        )

        # ---------------------------------------------------------
        # Call helper methods to configure image style and transformations
        # ---------------------------------------------------------
        self.create_layout()
        self.configure_style()

        # ---------------------------------------------------------
        # Mouse Events
        # ---------------------------------------------------------
        self.setMouseTracking(True)

    # -------------------------------------------------
    # Create Layout
    # -------------------------------------------------

    def create_layout(self):
        self._pixmap = QPixmap(self._image_path) if self._image_path else QPixmap()

    def paintEvent(self, event):
        if not self._is_visible or self._pixmap.isNull():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)

        # Set widget opacity
        painter.setOpacity(self._opacity)

        # If a corner radius is specified, clip the drawing region
        if self._corner_radius > 0:
            path = QPainterPath()
            path.addRoundedRect(self.rect(), self._corner_radius, self._corner_radius)
            painter.setClipPath(path)

        # Draw the image
        painter.drawPixmap(0, 0, self._pixmap)

        # Draw the border if a border color is provided
        border_color = self._border_hover_color if self._hovered else self._border_color
        if border_color:
            pen = QPen(border_color, self._border_thickness)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

    # -------------------------------------------------
    # Configure Style
    # -------------------------------------------------
    def configure_style(self):
        """Apply scaling, flipping, and rotation to the pixmap, and adjust widget size."""
        if not self._pixmap.isNull():
            transform = QTransform()

            # Flip horizontally or vertically
            if self._flip_h:
                transform.scale(-1, 1)
            if self._flip_v:
                transform.scale(1, -1)

            # Rotate
            transform.rotate(self._rotate)

            # Apply transformations
            self._pixmap = self._pixmap.transformed(transform, Qt.SmoothTransformation)

            # Scale the pixmap
            width = self._pixmap.width() * self._scale
            height = self._pixmap.height() * self._scale
            self._pixmap = self._pixmap.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)

            if not self._pixmap.isNull():
                self.setGeometry(self._x, self._y, self._pixmap.width(), self._pixmap.height())

            self.setVisible(self._is_visible)

    # -------------------------------------------------
    # Events
    # -------------------------------------------------

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
        """Handles mouse press events."""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and self._on_click:
            self._on_click(self)

    def mouseReleaseEvent(self, event):
        """Handles mouse release events."""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self._on_release:
            self._on_release(self)

    # ---------------------------------------------------------
    # Helper Functions
    # ---------------------------------------------------------
    def reload_pixmap(self):
        """
        Reloads the pixmap from the original image path and re-applies
        transformations (flip, rotate, scale). This is useful when any
        transform-related property changes.
        """
        if self._image_path:
            self._pixmap = QPixmap(self._image_path)
        else:
            self._pixmap = QPixmap()

        self.configure_style()
        self.update()

    def adjust_size(self):
        """Adjust the widget size to fit the transformed image."""
        if not self._pixmap.isNull():
            self.setGeometry(self._x, self._y, self._pixmap.width(), self._pixmap.height())

    # ---------------------------------------------------------
    # Properties using the @property decorator
    # ---------------------------------------------------------
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.adjust_size()
        self.update()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.adjust_size()
        self.update()

    @property
    def image_path(self):
        return self._image_path

    @image_path.setter
    def image_path(self, value):
        self._image_path = value
        self._pixmap = QPixmap(value) if value else QPixmap()
        self.configure_style()
        self.adjust_size()
        self.update()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.reload_pixmap()

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
        self.reload_pixmap()

    @property
    def flip_h(self):
        return self._flip_h

    @flip_h.setter
    def flip_h(self, value):
        self._flip_h = value
        self.reload_pixmap()

    @property
    def rotate(self):
        return self._rotate

    @rotate.setter
    def rotate(self, value):
        self._rotate = value
        self.reload_pixmap()

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
        """Returns the base border color as an RGBA tuple (or None)."""
        if self._border_color:
            r = self._border_color.red()
            g = self._border_color.green()
            b = self._border_color.blue()
            a = self._border_color.alphaF()  # 0..1 range
            return (r, g, b, a)
        return None

    @border_color.setter
    def border_color(self, value):
        """Sets the base border color from an RGBA tuple (0..255, 0..255, 0..255, 0..1)."""
        if value is None:
            self._border_color = None
        else:
            self._border_color = QColor(value[0], value[1], value[2], int(value[3] * 255))
        self.update()

    @property
    def border_hover_color(self):
        """Returns the hover border color as an RGBA tuple (or None)."""
        if self._border_hover_color:
            r = self._border_hover_color.red()
            g = self._border_hover_color.green()
            b = self._border_hover_color.blue()
            a = self._border_hover_color.alphaF()
            return (r, g, b, a)
        return None

    @border_hover_color.setter
    def border_hover_color(self, value):
        """Sets the hover border color from an RGBA tuple (0..255, 0..255, 0..255, 0..1)."""
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
        self._border_thickness = value
        self.update()

    # ---------------------------------------------------------
    # Print Properties
    # ---------------------------------------------------------
    def print_properties(self):
        """Prints all current properties of the PvImage."""
        print(f"""
        PvImage Properties:
        --------------------
        x: {self.x}
        y: {self.y}
        image_path: {self.image_path}
        scale: {self.scale}
        corner_radius: {self.corner_radius}
        flip_v: {self.flip_v}
        flip_h: {self.flip_h}
        rotate: {self.rotate}
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
    import pyvisual as pv

    app = pv.PvApp()

    # Create a window
    window = pv.PvWindow(title="PvImage Example")

    # Create a PvImage with callbacks
    image = PvImage(
        container=window,
        x=50,
        y=50,
        image_path="C:/Users/Murtaza Hassan/Pictures/IMG_6006.JPG",  # Replace with your image path
        scale=0.5,
        corner_radius=60,
        opacity=1,
        border_color=(255, 10, 10, 1),  # RGBA tuple (alpha in 0..1)
        border_hover_color=(0, 255, 0, 1),
        border_thickness=30,
        on_hover=lambda img: print("Hovered over image", img.tag),
        on_click=lambda img: print("Image clicked", img.tag),
        on_release=lambda: print("Image released")
    )

    image.tag = "Sample PvImage"

    # Optionally print properties to the console
    image.print_properties()

    # Show the window
    window.show()

    # Run the application
    app.run()
