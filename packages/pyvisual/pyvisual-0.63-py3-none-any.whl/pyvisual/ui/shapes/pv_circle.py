from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QBrush


class PvCircle(QWidget):
    def __init__(self, container, radius=30, x=100, y=100, width=None, height=None,
                 idle_color=(0, 0, 255, 1), border_color=None, border_thickness=0,
                 is_visible=True, opacity=1, tag=None,
                 on_hover=None, on_click=None, on_release=None, **kwargs):
        super().__init__(container)

        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._radius = radius  # Reference value for circle
        self._x = x
        self._y = y
        # If width or height not provided, default to diameter based on radius.
        if width is None:
            width = radius * 2
        if height is None:
            height = radius * 2
        self._width = width
        self._height = height

        # ---------------------------------------------------------
        # Appearance Settings
        # ---------------------------------------------------------
        self._idle_color = idle_color
        self._border_color = border_color  # Expected as RGBA tuple (r, g, b, alpha in 0..1)
        self._border_thickness = border_thickness

        # ---------------------------------------------------------
        # Element State
        # ---------------------------------------------------------
        self._is_visible = is_visible
        self._opacity = opacity

        # ---------------------------------------------------------
        # Callbacks and Custom Tag
        # ---------------------------------------------------------
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release
        self._tag = tag

        # ---------------------------------------------------------
        # Element Configuration
        # ---------------------------------------------------------
        self.setVisible(is_visible)
        self.adjust_size()
        self.setMouseTracking(True)

    # -------------------------------------------------
    # Create Layout and Configure Style
    # -------------------------------------------------
    def paintEvent(self, event):
        if not self._is_visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setOpacity(self._opacity)

        # ---------------------------------------------------------
        # Set Background Brush
        # ---------------------------------------------------------
        if self._idle_color is not None:
            bg = QColor(
                int(self._idle_color[0]),
                int(self._idle_color[1]),
                int(self._idle_color[2]),
                int(self._idle_color[3] * 255)
            )
            painter.setBrush(QBrush(bg))
        else:
            painter.setBrush(Qt.NoBrush)

        # ---------------------------------------------------------
        # Set Border Pen
        # ---------------------------------------------------------
        if self._border_thickness > 0 and self._border_color is not None:
            border = QColor(
                int(self._border_color[0]),
                int(self._border_color[1]),
                int(self._border_color[2]),
                int(self._border_color[3] * 255)
            )
            pen = QPen(border, self._border_thickness)
            painter.setPen(pen)
        else:
            painter.setPen(Qt.NoPen)

        # ---------------------------------------------------------
        # Draw the Circle/Ellipse
        # ---------------------------------------------------------
        # Draw ellipse so that any border thickness is rendered inward, keeping
        # the outer visual bounds consistent with `width`/`height`.
        if self._border_thickness > 0:
            inset = self._border_thickness / 2.0
            draw_width = max(0, self._width - self._border_thickness)
            draw_height = max(0, self._height - self._border_thickness)
            painter.drawEllipse(inset, inset, draw_width, draw_height)
        else:
            painter.drawEllipse(0, 0, self._width, self._height)

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    def enterEvent(self, event):
        """Handle mouse hover enter event."""
        if self._on_hover:
            self._on_hover(self)
        self.update()

    def leaveEvent(self, event):
        """Handle mouse hover leave event."""
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
        """Adjust the element size to fit the circle (or ellipse), accounting for border thickness."""
        # Keep geometry equal to the intended outer visual bounds. Border, if
        # any, is drawn inward during paint and should not affect geometry.
        self.setGeometry(
            self._x,
            self._y,
            self._width,
            self._height
        )

    # ---------------------------------------------------------
    # Properties using the @property decorator
    # ---------------------------------------------------------
    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        self._radius = value
        # Optionally update width and height to maintain a circle
        self._width = value * 2
        self._height = value * 2
        self.adjust_size()
        self.update()

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
    def idle_color(self):
        return self._idle_color

    @idle_color.setter
    def idle_color(self, value):
        self._idle_color = value
        self.update()

    @property
    def border_color(self):
        """Returns the border color as an RGBA tuple (or None)."""
        return self._border_color

    @border_color.setter
    def border_color(self, value):
        self._border_color = value
        self.update()

    @property
    def border_thickness(self):
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value
        self.adjust_size()
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
    def on_hover(self):
        return self._on_hover

    @on_hover.setter
    def on_hover(self, value):
        self._on_hover = value

    @property
    def on_click(self):
        return self._on_click

    @on_click.setter
    def on_click(self, value):
        self._on_click = value

    @property
    def on_release(self):
        return self._on_release

    @on_release.setter
    def on_release(self, value):
        self._on_release = value

    # ---------------------------------------------------------
    # Print Properties
    # ---------------------------------------------------------
    def print_properties(self):
        """Prints all current properties of the PvCircle."""
        print(f"""
        PvCircle Properties:
        ---------------------
        radius: {self.radius}
        x: {self.x}
        y: {self.y}
        width: {self.width}
        height: {self.height}
        idle_color: {self.idle_color}
        border_color: {self.border_color}
        border_thickness: {self.border_thickness}
        is_visible: {self.is_visible}
        opacity: {self.opacity}
        tag: {self.tag}
        on_hover: {self.on_hover}
        on_click: {self.on_click}
        on_release: {self.on_release}
        """)


# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------
if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()

    # Create a window
    window = pv.PvWindow(title="PvCircle Example",width=300,height=300)

    # Create a PvCircle with explicit width and height and event callbacks
    circle = PvCircle(
        container=window,
        radius=50,
        x=0,
        y=50,
        idle_color=(255,0,255,1),  # No background fill
        border_color=(255,0,0,1),  # No border color
        border_thickness=20,
        is_visible=True,
        opacity=1,  # Semi-transparent
        tag="Sample PvCircle",
        on_hover=lambda circ: print("Hovered over circle", circ.tag),
        on_click=lambda circ: print("Circle clicked", circ.tag),
        on_release=lambda circ: print("Circle released", circ.tag)
    )

    # Optionally demonstrate setter/getter usage:
    print("Initial x:", circle.x)
    circle.x = 200
    print("Updated x:", circle.x)

    # Show the window
    window.show()
    app.run()
