from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QColor, QBrush


class PvRectangle(QWidget):
    def __init__(self, container, x=100, y=100, width=100, height=100,
                 corner_radius=0, idle_color=(255, 0, 255, 1),
                 border_color=None, border_thickness=0,
                 is_visible=True, opacity=1, tag=None,
                 on_hover=None, on_click=None, on_release=None, **kwargs):
        super().__init__(container)

        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self._corner_radius = corner_radius
        self._idle_color = idle_color

        # ---------------------------------------------------------
        # Border Properties
        # ---------------------------------------------------------
        self._border_color = border_color  # Expected as RGBA tuple (r, g, b, alpha in 0..1)
        self._border_thickness = border_thickness

        # ---------------------------------------------------------
        # Element State and Appearance
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

    # -------------------------------------------------
    # Create Layout and Configure Style
    # -------------------------------------------------

    def paintEvent(self, event):
        if not self._is_visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Set Opacity
        painter.setOpacity(self._opacity)

        # Set Background Brush
        if self._idle_color is not None:
            # Convert idle_color to QColor (assuming idle_color is RGBA with alpha in 0..1)
            bg = QColor(
                int(self._idle_color[0]),
                int(self._idle_color[1]),
                int(self._idle_color[2]),
                int(self._idle_color[3] * 255)
            )
            painter.setBrush(QBrush(bg))
        else:
            painter.setBrush(Qt.NoBrush)

        # Set Border Pen
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

        # Draw the Rectangle with Optional Rounded Corners
        # Inset by half the pen width so the stroke is drawn inward, keeping
        # the outer visual bounds consistent with `width`/`height`.
        if self._border_thickness > 0:
            inset = self._border_thickness / 2.0
            draw_width = max(0, self._width - self._border_thickness)
            draw_height = max(0, self._height - self._border_thickness)
            # Adjust corner radius so the outer curvature remains consistent
            # when the path is inset by half the pen width.
            corner = max(0.0, float(self._corner_radius) - inset)
            painter.drawRoundedRect(
                inset,
                inset,
                draw_width,
                draw_height,
                corner,
                corner
            )
        else:
            painter.drawRoundedRect(
                0,
                0,
                self._width,
                self._height,
                self._corner_radius,
                self._corner_radius
            )

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
        """Adjust the widget size to fit the rectangle; border is drawn inward and does not affect geometry."""
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
    def corner_radius(self):
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
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
        """Prints all current properties of the PvRectangle."""
        print(f"""
        PvRectangle Properties:
        ------------------------
        x: {self.x}
        y: {self.y}
        width: {self.width}
        height: {self.height}
        corner_radius: {self.corner_radius}
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
    window = pv.PvWindow(title="PvRectangle Example")

    # Create a PvRectangle with callbacks for events
    rectangle = PvRectangle(
        container=window,
        x=50,
        y=50,
        width=200,
        height=100,
        corner_radius=15,
        idle_color=None,  # No background fill
        border_color=(0, 255, 0, 1),  # Green border
        border_thickness=3,
        is_visible=True,
        opacity=1,
        tag="Sample PvRectangle",
        on_hover=lambda rect: print("Hovered over rectangle", rect.tag),
        on_click=lambda rect: print("Rectangle clicked", rect.tag),
        on_release=lambda rect: print("Rectangle released", rect.tag)
    )

    # Optionally print properties to the console
    rectangle.print_properties()

    # Show the window
    window.show()
    app.run()
