from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen
from PySide6.QtCore import Qt


class PvLayout(QWidget):
    def __init__(self, container=None, x=0,
                 orientation="vertical", border_color=None, border_hover_color=None,
                 border_thickness=5, alignment=None, padding=0, spacing=0, tag=None,
                 on_hover=None, on_click=None, on_release=None, **kwargs):
        """
        A container widget that can be configured as a vertical or horizontal layout.
        It supports an x offset (its y offset is determined by the parent's layout),
        a border (with hover effects), alignment (provided as a string like "center" or "top left"),
        padding (as an int or a 4-tuple), and spacing between elements.
        """
        super().__init__(container)

        # Set the x offset (y offset will be handled by the parent's layout)
        self._x = x
        self.move(x, 0)

        # Orientation
        self._orientation = orientation.lower()

        # Border settings (border_color and border_hover_color are expected as RGBA tuples)
        self._border_color = QColor(border_color[0], border_color[1], border_color[2],
                                    int(border_color[3] * 255)) if border_color else None
        self._border_hover_color = (
            QColor(border_hover_color[0], border_hover_color[1], border_hover_color[2],
                   int(border_hover_color[3] * 255)) if border_hover_color else self._border_color
        )
        self._border_thickness = border_thickness
        self._hovered = False

        # Callbacks, tag, and alignment string
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release
        self._tag = tag
        self._alignment = alignment  # alignment as string, e.g. "center" or "top left"
        self._padding = padding  # either int or 4-tuple (left, top, right, bottom)
        self._spacing = spacing

        # Initialize internal layout based on orientation.
        if self._orientation == "vertical":
            self._layout = QVBoxLayout(self)
        else:
            self._layout = QHBoxLayout(self)

        # Set padding (contents margins)
        if isinstance(padding, int):
            self._layout.setContentsMargins(padding, padding, padding, padding)
        else:
            self._layout.setContentsMargins(*padding)

        # Set spacing between child widgets
        self._layout.setSpacing(spacing)

        # Set alignment if provided (convert string to Qt flags)
        if self._alignment:
            self._layout.setAlignment(self._convert_alignment(self._alignment))

        self.setLayout(self._layout)

    @staticmethod
    def _convert_alignment(alignment_str):
        """Convert a string (e.g., 'top left') into a Qt alignment flag."""
        mapping = {
            "left": Qt.AlignLeft,
            "right": Qt.AlignRight,
            "center": Qt.AlignCenter,
            "top": Qt.AlignTop,
            "bottom": Qt.AlignBottom,
        }
        flags = 0
        for token in alignment_str.lower().split():
            if token in mapping:
                flags |= mapping[token]
        return flags

    # -------------------------------------------------
    # Overriding sizeHint to reflect internal layout
    # -------------------------------------------------
    def sizeHint(self):
        """Return the recommended size based on the layout's size hint."""
        return self._layout.sizeHint()

    def minimumSizeHint(self):
        """Return the minimum size required by the layout."""
        return self._layout.minimumSize()

    # -------------------------------------------------
    # Layout Management
    # -------------------------------------------------
    def add_element(self, element):
        """Adds a new widget (pyvisual element) to the layout container."""
        self._layout.addWidget(element)
        self.update()

    def remove_element(self, element):
        """Removes the given widget from the layout container."""
        self._layout.removeWidget(element)
        element.setParent(None)
        self.update()

    # -------------------------------------------------
    # Painting and Border Drawing
    # -------------------------------------------------
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        border_color = self._border_hover_color if self._hovered else self._border_color
        if border_color:
            pen = QPen(border_color, self._border_thickness)
            painter.setPen(pen)
            painter.drawRect(self.rect())

    # -------------------------------------------------
    # Mouse Event Handlers
    # -------------------------------------------------
    def enterEvent(self, event):
        self._hovered = True
        if self._on_hover:
            self._on_hover(self)
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and self._on_click:
            self._on_click(self)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self._on_release:
            self._on_release(self)

    # -------------------------------------------------
    # Property Getters and Setters
    # -------------------------------------------------
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.move(self._x, self.y)
        self.update()

    @property
    def y(self):
        return self.geometry().y()

    @y.setter
    def y(self, value):
        self.move(self._x, value)
        self.update()

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, value):
        self._orientation = value.lower()
        if self._orientation == "vertical":
            new_layout = QVBoxLayout(self)
        else:
            new_layout = QHBoxLayout(self)
        # Reapply padding and spacing
        if isinstance(self._padding, int):
            new_layout.setContentsMargins(self._padding, self._padding, self._padding, self._padding)
        else:
            new_layout.setContentsMargins(*self._padding)
        new_layout.setSpacing(self._spacing)
        if self._alignment:
            new_layout.setAlignment(self._convert_alignment(self._alignment))
        # Move existing widgets
        while self._layout.count():
            item = self._layout.takeAt(0)
            widget = item.widget()
            if widget:
                new_layout.addWidget(widget)
        self._layout = new_layout
        self.setLayout(self._layout)
        self.update()

    @property
    def alignment(self):
        return self._alignment

    @alignment.setter
    def alignment(self, value):
        self._alignment = value
        if self._layout:
            self._layout.setAlignment(self._convert_alignment(value))
        self.update()

    @property
    def padding(self):
        return self._padding

    @padding.setter
    def padding(self, value):
        self._padding = value
        if isinstance(value, int):
            self._layout.setContentsMargins(value, value, value, value)
        else:
            self._layout.setContentsMargins(*value)
        self.update()

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, value):
        self._spacing = value
        self._layout.setSpacing(value)
        self.update()

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
        self._border_thickness = value
        self.update()

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value

    def print_properties(self):
        print(f"""
        PvLayout Properties:
        --------------------
        x: {self.x}
        y: {self.y}
        orientation: {self.orientation}
        alignment: {self.alignment}
        padding: {self.padding}
        spacing: {self.spacing}
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

    # Initialize the pyvisual application
    app = pv.PvApp()

    # Create a window using pv.PvWindow
    window = pv.PvWindow(title="PvLayout Example")

    # Create a PvLayout container with vertical orientation, border settings,
    # and alignment specified as a string ("center" in this example).
    # Width and height parameters are removed; the widget's size will be determined by its contents.
    layout_container = PvLayout(
        container=window,
        orientation="horizontal",
        padding=50,
        spacing=150,
        border_color=(255, 0, 0, 1),
        border_thickness=5
    )

    button1 = pv.PvButton(None, text="Button 1")
    button2 = pv.PvButton(None, text="Button 2")
    layout_container.add_element(button1)
    layout_container.add_element(button2)
    layout_container.adjustSize()
    # Force the container to recalc its size based on its contents:


    # Now move the container to x=50, y=50 with the newly adjusted width/height:
    layout_container.move(50, 50)

    window.show()
    app.run()
