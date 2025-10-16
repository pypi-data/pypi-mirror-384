import pyvisual as pv
from pyvisual.ui.input.pv_button import BasicButton
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.boxlayout import BoxLayout
from kivy.core.window import Window


class GroupLayout:
    def __init__(self, window=None, x=0, y=0, orientation="horizontal", spacing=10,
                 padding=(10, 10, 10, 10), background_color=(1, 1, 1, 0),
                 radius=0, border_color=(1, 0, 0, 1), border_width=1):
        self.window = window
        self.orientation = orientation
        self.spacing = spacing
        self.padding = padding
        self.background_color = background_color
        self.radius = radius
        self.border_color = border_color
        self.border_width = border_width

        self.scroll_offset = 0  # For scrolling
        self.scroll_speed = 20

        # Create the container layout using Kivy's BoxLayout
        self.layout = BoxLayout(
            orientation=self.orientation,
            spacing=self.spacing,
            padding=self.padding,
            size_hint=(None, None),
            pos=(x, y)
        )

        # Custom background and border
        with self.layout.canvas.before:
            if self.background_color:
                Color(*self.background_color)
                self.bg_rect = RoundedRectangle(size=self.layout.size, pos=self.layout.pos, radius=[self.radius])

            if self.border_color and self.border_width > 0:
                Color(*self.border_color)
                self.border_line = Line(rounded_rectangle=(x, y, self.layout.size[0], self.layout.size[1], self.radius), width=self.border_width)

        # Bind size updates
        self.layout.bind(size=self.update_background, pos=self.update_background)

        # Add the layout to the window if a window is provided
        if self.window:
            self.window.add_widget(self.layout)

        # Bind mouse scroll events
        Window.bind(on_scroll=self.on_scroll)

    def add_widget(self, widget):
        """
        Add a widget to the GroupLayout.
        """
        if isinstance(widget, GroupLayout):
            self.layout.add_widget(widget.layout)  # Add nested layout
        else:
            # Ensure BasicButton or similar widgets are added correctly
            if hasattr(widget, "button_widget"):  # Check if widget is a BasicButton
                self.layout.add_widget(widget.button_widget)
            else:
                self.layout.add_widget(widget)

        # Update layout size dynamically
        self.update_layout_size()

    def update_layout_size(self):
        """
        Calculate and adjust layout size based on children.
        """
        if len(self.layout.children) == 0:
            total_width = self.padding[0] + self.padding[2]
            total_height = self.padding[1] + self.padding[3]
        elif self.orientation == "horizontal":
            total_width = (
                sum(child.width for child in self.layout.children) +
                (len(self.layout.children) - 1) * self.spacing +
                self.padding[0] + self.padding[2]
            )
            total_height = (
                max(child.height for child in self.layout.children) +
                self.padding[1] + self.padding[3]
            )
        else:  # Vertical orientation
            total_width = (
                max(child.width for child in self.layout.children) +
                self.padding[0] + self.padding[2]
            )
            total_height = (
                sum(child.height for child in self.layout.children) +
                (len(self.layout.children) - 1) * self.spacing +
                self.padding[1] + self.padding[3]
            )

        self.layout.size = (total_width, total_height)

    def update_background(self, *args):
        """
        Update the background and border on size changes.
        """
        if self.background_color:
            self.bg_rect.size = self.layout.size
            self.bg_rect.pos = self.layout.pos
            self.bg_rect.radius = [self.radius]

        if self.border_color and self.border_width > 0:
            self.border_line.rounded_rectangle = (
                self.layout.x, self.layout.y, self.layout.width, self.layout.height, self.radius
            )

    def on_scroll(self, window, scroll_x, scroll_y, scroll_dx, scroll_dy):
        """
        Handle mouse scroll events for scrolling the layout.
        """
        if self.orientation == "vertical":
            self.scroll_offset += scroll_dy * self.scroll_speed
            max_scroll = max(0, self.layout.height - Window.height)
            self.scroll_offset = max(-max_scroll, min(0, self.scroll_offset))
            self.layout.y = self.scroll_offset
        else:
            self.scroll_offset += scroll_dx * self.scroll_speed
            max_scroll = max(0, self.layout.width - Window.width)
            self.scroll_offset = max(-max_scroll, min(0, self.scroll_offset))
            self.layout.x = self.scroll_offset

        self.update_layout_size()


if __name__ == "__main__":
    window = pv.Window(title="Scrollable GroupLayout Example")

    vertical_group = GroupLayout(
        window=window, x=50, y=200, orientation="vertical", spacing=20,
        padding=(30, 30, 30, 30), background_color=(0.9, 0.9, 0.9, 1),
        radius=5, border_color=(0.3, 0.3, 0.3, 1), border_width=0
    )

    # Add buttons to the vertical group
    for i in range(20):
        button = BasicButton(window=None, x=0, y=0, text=f"Button {i + 1}", font_size=16, width=120, height=40)
        vertical_group.add_widget(button)

    window.show()

