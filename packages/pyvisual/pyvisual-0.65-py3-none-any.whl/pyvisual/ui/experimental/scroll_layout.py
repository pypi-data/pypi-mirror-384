from kivy.uix.scrollview import ScrollView
from kivy.uix.boxlayout import BoxLayout
from kivy.properties import BooleanProperty


class ScrollLayout(ScrollView):
    is_vertical = BooleanProperty(True)

    def __init__(
        self,
        window=None,
        x=0,
        y=0,
        width=300,
        height=400,
        orientation="vertical",
        spacing=10,
        padding=(10, 10, 10, 10),
        **kwargs,
    ):
        super().__init__(
            size_hint=(None, None),
            size=(width, height),
            pos=(x, y),
            do_scroll_x=orientation == "horizontal",
            do_scroll_y=orientation == "vertical",
            bar_width=10,
            **kwargs,
        )

        self.is_vertical = orientation == "vertical"
        self.orientation = orientation
        self.spacing = spacing
        self.padding = padding

        # Create the inner BoxLayout
        self.layout = BoxLayout(
            orientation=orientation,
            spacing=spacing,
            padding=padding,
            size_hint_y=None if orientation == "vertical" else 1,
            size_hint_x=None if orientation == "horizontal" else 1,
        )
        super().add_widget(self.layout)  # Add the inner layout to the ScrollView
        self.update_layout_size()

        # Add the ScrollView to the window if provided
        if window:
            window.add_widget(self)

    def add_scroll_widget(self, widget):
        """
        Add a widget to the ScrollLayout and update the layout size.
        """
        # Check if the widget is a custom class (e.g., BasicButton)
        if hasattr(widget, "button_widget"):
            widget = widget.button_widget  # Extract the actual Kivy widget

        # Add the widget to the layout
        self.layout.add_widget(widget)
        self.update_layout_size()

    def update_layout_size(self):
        """
        Update the size of the BoxLayout inside the ScrollView.
        """
        if self.is_vertical:
            self.layout.height = (
                sum(child.height for child in self.layout.children)
                + self.spacing * (len(self.layout.children) - 1)
                + self.padding[1]
                + self.padding[3]
            )
        else:
            self.layout.width = (
                sum(child.width for child in self.layout.children)
                + self.spacing * (len(self.layout.children) - 1)
                + self.padding[0]
                + self.padding[2]
            )

    def on_touch_down(self, touch):
        """
        Ensure touch events are handled properly for both scrolling and button clicks.
        """
        if self.collide_point(touch.x, touch.y):
            # Let child widgets handle the touch event first
            if self.layout.collide_point(touch.x, touch.y):
                for child in self.layout.children:
                    if child.collide_point(*touch.pos):
                        return child.on_touch_down(touch)
            # If no child widget consumes the touch, handle it as a scroll
            return super().on_touch_down(touch)
        return False

    def on_scroll_move(self, touch):
        """
        Override on_scroll_move to handle vertical and horizontal scrolling.
        """
        if self.collide_point(touch.x, touch.y):
            # Detect vertical scrolling
            if abs(touch.dy) > abs(touch.dx):
                touch.ud[self._get_uid("svavoid")] = True
                return False
            # Allow horizontal scrolling
            return super().on_scroll_move(touch)


if __name__ == "__main__":
    import pyvisual as pv
    from pyvisual.ui.input.pv_button import BasicButton

    # Create the window
    window = pv.Window()

    # Create ScrollLayout
    scroll = ScrollLayout(
        window=window,
        x=50,
        y=50,
        width=300,
        height=400,
        orientation="vertical",
        spacing=10,
        padding=(10, 10, 10, 10),
    )

    # Add buttons to ScrollLayout
    def button_clicked(btn):
        print(f"Button clicked: {btn.text}")

    for i in range(10):
        button = BasicButton(
            window=None,
            x=0,
            y=0,
            width=260,
            height=50,
            text=f"Button {i + 1}",
            on_click=lambda btn: button_clicked(btn),
        )
        scroll.add_scroll_widget(button)

    # Show the window
    window.show()
