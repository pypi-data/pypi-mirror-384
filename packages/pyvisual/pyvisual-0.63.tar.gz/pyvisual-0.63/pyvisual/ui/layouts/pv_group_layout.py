from PySide6.QtWidgets import QWidget, QGraphicsDropShadowEffect
from PySide6.QtGui import QPainter, QColor, QBrush, QPen
from PySide6.QtCore import QRect, Qt
from pyvisual.utils.helper_functions import add_shadow_effect, draw_border


class PvGroupLayout(QWidget):
    def __init__(self, container, orientation="horizontal", x=100, y=100, spacing=10, margin=(10, 10, 10, 10),
                 bg_color=(225, 225, 225, 1), border_color=(0, 0, 0, 0), border_thickness=0, corner_radius=0,
                 box_shadow=None):
        super().__init__(container)

        # Initialize layout properties
        self._orientation = orientation.lower()  # "horizontal" or "vertical"
        self._x = x
        self._y = y
        self._spacing = spacing
        self._margin = margin
        self._bg_color = bg_color
        self._border_color = border_color
        self._border_thickness = border_thickness
        self._corner_radius = corner_radius
        self._box_shadow = box_shadow  # Box shadow in CSS-like format
        self._children = []  # Store child widgets

        # Set position and default size
        self.move(*(self._x, self._y))
        self.setFixedSize(100, 100)  # Default size (will update dynamically)
        self.show()  # Make sure the widget is visible

        # # Apply shadow effect if specified
        if self._box_shadow:
            add_shadow_effect(self, self._box_shadow)

    def add_widget(self, widget):
        """Add a child widget or a list of widgets to the layout."""
        if isinstance(widget, list):
            for w in widget:
                self._children.append(w)
                w.setParent(self)
        else:
            self._children.append(widget)
            widget.setParent(self)
        self.update_layout()

    def set_orientation(self, orientation):
        """Set the orientation of the layout."""
        self._orientation = orientation.lower()
        self.update_layout()

    def update_layout(self):
        """Update the size and position of child widgets based on the orientation."""
        x_offset = self._margin[0]
        y_offset = self._margin[1]
        max_width = 0
        max_height = 0

        for widget in self._children:
            if self._orientation == "horizontal":
                widget.move(x_offset, y_offset)
                x_offset += widget.width() + self._spacing
                max_height = max(max_height, widget.height())
            elif self._orientation == "vertical":
                widget.move(x_offset, y_offset)
                y_offset += widget.height() + self._spacing
                max_width = max(max_width, widget.width())

        # Calculate total width and height
        if self._orientation == "horizontal":
            total_width = x_offset - self._spacing + self._margin[2]
            total_height = max_height + self._margin[1] + self._margin[3]
        elif self._orientation == "vertical":
            total_width = max_width + self._margin[0] + self._margin[2]
            total_height = y_offset - self._spacing + self._margin[1] + self._margin[3]

        # Prevent overlapping by adjusting size before painting
        self.setFixedSize(total_width, total_height)

    def paintEvent(self, event):
        super().paintEvent(event)

        """Custom paint event to draw the background, border, and shadow."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)  # Enable antialiasing for smooth edges

        # Draw background rectangle
        # Normalize colors to 0–255 integers
        bg_r, bg_g, bg_b, bg_a = [int(c * 255) if c <= 1 else c for c in self._bg_color]
        brush = QBrush(QColor(bg_r, bg_g, bg_b, bg_a), Qt.SolidPattern)
        painter.setBrush(brush)
        painter.setPen(Qt.NoPen)  # No border for the background
        rect = QRect(self._border_thickness // 2, self._border_thickness // 2,
                     self.width() - self._border_thickness, self.height() - self._border_thickness)
        painter.drawRoundedRect(rect, self._corner_radius, self._corner_radius)
        draw_border(self, painter, self._border_color, self._border_thickness, self._corner_radius)

    def get_position(self):
        return (self._x, self._y)

    def print_properties(self):
        """Prints all the current properties of the layout."""
        print(f"""
        PvGroupLayout Properties:
        -------------------------
  
        orientation: {self._orientation}
        pos: {(self._x, self._y)}
        spacing: {self._spacing}
        margin: {self._margin}
        bg_color: {self._bg_color}
        border_color: {self._border_color}
        border_thickness: {self._border_thickness}
        corner_radius: {self._corner_radius}
        box_shadow: {self._box_shadow}
        """)

    def set_spacing(self, spacing):
        """Set the spacing between child widgets and update the layout."""
        self._spacing = spacing
        self.update_layout()

    def get_spacing(self):
        return self._spacing

if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()

    # Create a window
    window = pv.PvWindow(title="Unified PvGroupLayout Example with Box Shadow", width=1000, height=700)

    # Create the main layout with a box shadow
    layout = PvGroupLayout(window, orientation="vertical", x=50,y=50, spacing=20, margin=(20, 20, 10, 20),
                           border_color=(0.5, 0.5, 0.5, 1), border_thickness=2, corner_radius=0,
                           box_shadow="15px 15px 15px 10px rgba(0,0,0,0.2)")

    layout.print_properties()
    # # Add buttons to the main layout
    button_1 = pv.PvButton(None, size=(100, 50), text="Button 1")
    button_2 = pv.PvButton(None, size=(150, 50), text="Button 2")
    button_3 = pv.PvButton(None, size=(120, 200), text="Button 3")

    # text1 = pv.PvText(None, box_width=200, bg_color=(200, 200, 0, 1))
    # text2 = pv.PvText(None, bg_color=(200, 0, 200, 1))
    # input_text = pv.PvTextInput(None)
    # layout.add_widget(text1)
    #
    # layout.add_widget(input_text)
    # layout.add_widget(text2)
    layout.add_widget(button_1)
    #
    # button9 = pv.PvButton(None, x=50, y=50, size=(100, 40), text="Like",
    #                       icon_path="../../assets/icons/like/like.svg", button_color=(255, 255, 255, 1),
    #                       hover_color=(255, 255, 255, 1), font_color_hover=(56, 182, 255, 1),
    #                       clicked_color=(245, 245, 245, 1), bold=True, border_thickness=1, corner_radius=10,
    #                       font_color=(136, 136, 136, 1), font_size=14, icon_scale=1, icon_spacing=10,
    #                       icon_position="right", border_color_hover=(56, 182, 255, 1),
    #                       box_shadow_hover="2px 2px 5px 0px rgba(56,182,255,0.5)")  # Red border on hover)
    # layout.add_widget(button9)
    # layout3 = PvGroupLayout(window, orientation="horizontal", x=50, y=50, bg_color=(0.9, 0.9, 0.9, 1),
    #                         border_color=(0.5, 0.5, 0.5, 1), border_thickness=2, corner_radius=15,
    #                         box_shadow="15px 15px 15px 10px rgba(0, 0,0 ,0.2)")
    # #
    # #
    # # # Add buttons to the main layout
    # button_4 = pv.PvButton(None, size=(100, 50), text="Button 1")
    # button_5 = pv.PvButton(None, size=(150, 50), text="Button 2")
    # button_6 = pv.PvButton(None, size=(120, 200), text="Button 3")
    # layout3.add_widget(button_4)
    # layout3.add_widget(button_5)
    # layout3.add_widget(button_6)
    # layout.add_widget(layout3)
    # layout.add_widget(button_1)
    # layout.add_widget(button_2)
    # layout.add_widget(button_3)

    # Show the window
    window.show()
    app.run()
