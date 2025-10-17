import pyvisual as pv
from kivy.uix.scrollview import ScrollView as KivyScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Color, RoundedRectangle, Line


class PvScroll:
    def __init__(self, container=None, x=0, y=0, width=500, height=300,
                 orientation="vertical", spacing=10, padding=(10, 10, 10, 10),
                 background_color=(1, 1, 1, 0), radius=0, border_color=(0.9, 0.9, 0.9, 1), border_width=2,
                 bar_color=(0.7, 0.7, 0.7, 0.9), bar_inactive_color=(0.7, 0.7, 0.7, 0.2),bar_width=5,
                 bar_margin=0, bar_pos_x="bottom", bar_pos_y="right",scroll_type=['bars', 'content']):
        self.container = container
        self.orientation = orientation
        self.spacing = spacing
        self.padding = padding
        self.background_color = background_color
        self.radius = radius
        self.border_color = border_color
        self.border_width = border_width

        # Create the main scroll view container
        self.scroll_view = KivyScrollView(
            size_hint=(None, None),
            size=(width, height),
            pos=(x, y),
            do_scroll_x=(orientation == "horizontal"),
            do_scroll_y=(orientation == "vertical"),
            bar_color=bar_color,
            bar_inactive_color=bar_inactive_color,
            bar_margin=bar_margin,
            bar_pos_x=bar_pos_x,
            bar_pos_y=bar_pos_y,
            bar_width=bar_width,
            scroll_type=scroll_type
        )

        # Create the content layout
        self.layout = BoxLayout(
            orientation=self.orientation,
            spacing=self.spacing,
            padding=self.padding,
            size_hint=(None, None)
        )
        self.layout.width = width if orientation == "vertical" else 0
        self.layout.height = 0 if orientation == "vertical" else height


        # Custom background and border
        with self.scroll_view.canvas.before:
            if self.background_color:
                Color(*self.background_color)
                self.bg_rect = RoundedRectangle(size=self.scroll_view.size, pos=self.scroll_view.pos, radius=[self.radius])

            if self.border_color and self.border_width > 0:
                Color(*self.border_color)
                self.border_line = Line(rounded_rectangle=(x, y, width, height, self.radius), width=self.border_width)

        # Bind size updates
        self.layout.bind(minimum_height=self.layout.setter('height'))
        self.layout.bind(minimum_width=self.layout.setter('width'))
        self.scroll_view.bind(size=self.update_background, pos=self.update_background)

        self.scroll_view.add_widget(self.layout)
        # Add the scroll view to the container if provided
        if self.container:

            self.container.add_widget(self.scroll_view)

    def on_touch_move(self, touch):
        """
        Pass touch move events to children for hover detection.
        """
        if self.scroll_view.collide_point(*touch.pos):
            for child in self.layout.children:
                if child.collide_point(*touch.pos) and hasattr(child, 'on_touch_move'):
                    child.on_touch_move(touch)
            return super().on_touch_move(touch)
        return False

    def add_widget(self, widget):
        """
        Add a widget to the ScrollView's content layout and auto-scroll only if the content height exceeds the visible height.
        """
        if widget.parent:
            widget.parent.remove_widget(widget)
        self.layout.add_widget(widget)
        self.update_content_size()

        # Check if the content height exceeds the ScrollView height
        if self.orientation == "vertical":
            if self.layout.height > self.scroll_view.height:
                self.scroll_view.scroll_y = 0  # Scroll to the bottom
            else:
                self.scroll_view.scroll_y = 1  # Keep at the top
        else:  # Horizontal orientation
            if self.layout.width > self.scroll_view.width:
                self.scroll_view.scroll_x = 1  # Scroll to the right
            else:
                self.scroll_view.scroll_x = 0  # Keep at the left

    def update_content_size(self):
        """
        Update the size of the content layout based on its children.
        """
        if self.orientation == "vertical":
            self.layout.height = sum(
                child.height for child in self.layout.children) + self.spacing * (len(self.layout.children) - 1)
            self.layout.width = self.scroll_view.width - self.padding[0] - self.padding[2]
        else:  # Horizontal orientation
            self.layout.width = sum(
                child.width for child in self.layout.children) + self.spacing * (len(self.layout.children) - 1)
            self.layout.height = self.scroll_view.height - self.padding[1] - self.padding[3]

    def update_background(self, *args):
        """
        Update the background and border on size changes.
        """
        if self.background_color:
            self.bg_rect.size = self.scroll_view.size
            self.bg_rect.pos = self.scroll_view.pos
            self.bg_rect.radius = [self.radius]

        if self.border_color and self.border_width > 0:
            self.border_line.rounded_rectangle = (
                self.scroll_view.x, self.scroll_view.y, self.scroll_view.width, self.scroll_view.height, self.radius
            )

    def clear_widgets(self):
        """
        Remove all widgets from the ScrollView's content layout.
        """
        self.layout.clear_widgets()
        self.update_content_size()

    def remove_widget(self, widget_or_index):
        """
        Remove a specific widget by instance or index from the content layout.

        Args:
            widget_or_index: The widget instance or the index of the widget to be removed.
        """
        try:
            if isinstance(widget_or_index, int):  # Remove by index
                widget = self.layout.children[::-1][widget_or_index]  # Access widget by index in reversed order
            else:  # Remove by instance
                widget = widget_or_index

            self.layout.remove_widget(widget)
            self.update_content_size()
        except (IndexError, ValueError):
            print(f"Invalid input: {widget_or_index}. No widget removed.")


def button_click(instance):
    print(instance.get_text())

# Example Usage
if __name__ == "__main__":
    # Initialize the pyvisual window
    window = pv.PvWindow(title="Scroll Example")

    # Create a ScrollView
    scroll_view = PvScroll(
        container=window, x=50, y=100, width=200, height=300, orientation="vertical",
        spacing=10, padding=(20, 20, 20, 20), background_color=(0.9, 0.9, 0.9, 1),
        radius=10, border_color=(0.3, 0.3, 0.3, 1), border_width=0,
        bar_color=(0.5, 0.5, 0.5, 0.8), bar_inactive_color=(0.5, 0.5, 0.5, 0.2),
        bar_margin=5, bar_pos_x="bottom", bar_pos_y="right"
    )

    # Add some widgets to the ScrollView
    for i in range(10):
        button = pv.PvButton(scroll_view, x=0, y=0, text=f"Button {i + 1}", on_click=button_click)

    # Show the window
    window.show()
