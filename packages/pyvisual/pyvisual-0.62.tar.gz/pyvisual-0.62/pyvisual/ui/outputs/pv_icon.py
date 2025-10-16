from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen, QTransform
from PySide6.QtCore import Qt
from PySide6.QtSvg import QSvgRenderer

# Import the helper function to update the SVG color.
from pyvisual.utils.helper_functions import update_svg_color


class PvIcon(QWidget):
    def __init__(self, container=None, x=0, y=0, width=100, height=None, icon_path="",
                 idle_color=None, corner_radius=0, flip_v=False, flip_h=False, rotate=0,
                 is_visible=True, opacity=1, tag=None, border_color=None,
                 border_hover_color=None, border_thickness=5,
                 on_hover=None, on_click=None, on_release=None, preserve_original_colors=False, **kwargs):
        super().__init__(container)

        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._x = x
        self._y = y
        self._width = width
        self._height = height  # Will be calculated based on SVG aspect ratio
        self._icon_path = icon_path
        self._corner_radius = corner_radius
        self._flip_v = flip_v
        self._flip_h = flip_h
        self._rotate = rotate
        self._is_visible = is_visible
        self._opacity = opacity
        self._pixmap = None  # Not used in PvIcon but kept for consistency (we use _renderer)
        self._original_svg = None
        self._renderer = None
        self._preserve_original_colors = preserve_original_colors

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
        # Icon Color and Border Colors
        # ---------------------------------------------------------
        self._idle_color = idle_color  # Used to update the SVG color.
        self._border_color = (
            QColor(border_color[0], border_color[1], border_color[2],
                   int(border_color[3] * 255)) if border_color else None
        )
        self._border_hover_color = (
            QColor(border_hover_color[0], border_hover_color[1], border_hover_color[2],
                   int(border_hover_color[3] * 255)) if border_hover_color else self._border_color
        )
        # ---------------------------------------------------------
        # Call helper methods
        # ---------------------------------------------------------
        self.create_layout()

        # ---------------------------------------------------------
        # Mouse Events and Visibility Configuration
        # ---------------------------------------------------------
        self.setMouseTracking(True)
        self.setVisible(is_visible)

    # ---------------------------------------------------------
    # Create Layout
    # ---------------------------------------------------------
    def create_layout(self):
        self._renderer = None
        self._original_svg = ""
        if self._icon_path:
            try:
                with open(self._icon_path, 'r', encoding='utf-8') as f:
                    self._original_svg = f.read()
                self._renderer = QSvgRenderer(self._original_svg.encode("utf-8"))
                if self._idle_color and not self._preserve_original_colors:
                    update_svg_color(self, self._idle_color)
                
                # Calculate height based on SVG aspect ratio if height is None
                if self._height is None and self._renderer.isValid():
                    svg_size = self._renderer.defaultSize()
                    if svg_size.width() > 0:
                        aspect_ratio = svg_size.height() / svg_size.width()
                        self._height = int(self._width * aspect_ratio)
                    else:
                        self._height = self._width  # Fallback to square if SVG has no width
            except Exception as e:
                print(f"Error loading SVG: {e}")
                self._renderer = None
                if self._height is None:
                    self._height = self._width  # Fallback to square if SVG loading fails

        self.adjust_size()

    def load(self, data: bytes):
        """
        Load SVG data into the renderer.
        This method is needed by the update_svg_color helper function.
        """
        if self._renderer:
            self._renderer.load(data)
        self._original_svg = data.decode("utf-8")

    # ---------------------------------------------------------
    # Configure Style
    # ---------------------------------------------------------
    def paintEvent(self, event):
        """Custom painting of the icon."""
        if not self._is_visible or not self._renderer or not self._renderer.isValid():
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)
        painter.save()

        # Build transformation for flipping and rotation.
        transform = QTransform()
        if self._flip_h:
            transform.scale(-1, 1)
            transform.translate(-self._width, 0)
        if self._flip_v:
            transform.scale(1, -1)
            transform.translate(0, -self._height)
        if self._rotate:
            transform.translate(self._width / 2, self._height / 2)
            transform.rotate(self._rotate)
            transform.translate(-self._width / 2, -self._height / 2)
        painter.setTransform(transform, True)

        # Clip to rounded corners if specified.
        if self._corner_radius > 0:
            path = QPainterPath()
            path.addRoundedRect(0, 0, self._width, self._height, self._corner_radius, self._corner_radius)
            painter.setClipPath(path)

        self._renderer.render(painter, self.rect())
        painter.restore()

        # Draw border if a border color is provided.
        border_color = self._border_hover_color if self._hovered else self._border_color
        if border_color:
            pen = QPen(border_color, self._border_thickness)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
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
    def adjust_size(self):
        """Adjust the widget's geometry to the specified width and height."""
        self.setGeometry(self._x, self._y, self._width, self._height)

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
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        # Recalculate height based on aspect ratio when width changes
        if self._renderer and self._renderer.isValid():
            svg_size = self._renderer.defaultSize()
            if svg_size.width() > 0:
                aspect_ratio = svg_size.height() / svg_size.width()
                self._height = int(self._width * aspect_ratio)
        self.adjust_size()
        self.update()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self.adjust_size()
        self.update()

    @property
    def icon_path(self):
        return self._icon_path

    @icon_path.setter
    def icon_path(self, value):
        self._icon_path = value
        if value:
            try:
                with open(value, 'r', encoding='utf-8') as f:
                    self._original_svg = f.read()
                self._renderer = QSvgRenderer(self._original_svg.encode("utf-8"))
                if self._idle_color and not self._preserve_original_colors:
                    update_svg_color(self, self._idle_color)
            except Exception as e:
                print(f"Error loading SVG: {e}")
                self._renderer = None
        else:
            self._renderer = None
        self.adjust_size()
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
    def on_click(self):
        return self._on_click

    @on_click.setter
    def on_click(self, callback):
        self._on_click = callback

    @property
    def border_color(self):
        """Returns the base border color as an RGBA tuple (or None)."""
        if self._border_color:
            r = self._border_color.red()
            g = self._border_color.green()
            b = self._border_color.blue()
            a = self._border_color.alphaF()
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

    @property
    def preserve_original_colors(self):
        return self._preserve_original_colors

    @preserve_original_colors.setter
    def preserve_original_colors(self, value):
        self._preserve_original_colors = value
        # If turning off preserve colors and we have an idle color, update the SVG
        if not value and self._idle_color and self._renderer:
            update_svg_color(self, self._idle_color)
        # If turning on preserve colors, reload the original SVG
        elif value and self._original_svg and self._renderer:
            self._renderer.load(self._original_svg.encode("utf-8"))
        self.update()

    @property
    def idle_color(self):
        return self._idle_color

    @idle_color.setter
    def idle_color(self, value):
        self._idle_color = value
        # Update the SVG color if renderer is available and we're not preserving original colors
        if self._renderer and value and not self._preserve_original_colors:
            update_svg_color(self, value)
        self.update()

    # ---------------------------------------------------------
    # Print Properties
    # ---------------------------------------------------------
    def print_properties(self):
        """Prints all current properties of the PvIcon."""
        print(f"""
        PvIcon Properties:
        --------------------
        x: {self.x}
        y: {self.y}
        width: {self.width}
        height: {self.height}
        icon_path: {self.icon_path}
        corner_radius: {self.corner_radius}
        flip_v: {self.flip_v}
        flip_h: {self.flip_h}
        rotate: {self.rotate}
        is_visible: {self.is_visible}
        opacity: {self.opacity}
        idle_color: {self.idle_color}
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

    # Create a window for the icon.
    window = pv.PvWindow(title="PvIcon SVG Example")

    # Create a PvIcon instance using an SVG file.
    icon = PvIcon(
        container=window,
        x=50,
        y=50,
        width=120,
        height=None,
        icon_path=r"D:\Pycharm Projects\pyvisual\pyvisual\assets\icons\Like\like.svg",  # Replace with your SVG path
        corner_radius=20,
        flip_v=False,
        flip_h=False,
        rotate=0,
        opacity=1,
        border_color=(0, 0, 255, 1),  # Blue border (RGBA normalized)
        border_hover_color=(255, 0, 0, 1),  # Red on hover
        border_thickness=3,
        on_hover=lambda icon: print("Hovered over icon", icon.tag),
        on_click=lambda icon: print("Icon clicked", icon.tag),
        on_release=lambda icon: print("Icon released", icon.tag)
    )

    icon.tag = "Sample PvIcon"

    # Optionally print properties to the console.
    icon.print_properties()

    window.show()
    app.run()
