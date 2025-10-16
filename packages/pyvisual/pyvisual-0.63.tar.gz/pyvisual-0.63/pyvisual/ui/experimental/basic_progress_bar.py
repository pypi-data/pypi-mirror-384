from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.graphics import Color, Rectangle
from kivy.uix.label import Label

class BasicProgressBar(Widget):
    progress = NumericProperty()
    max_progress = NumericProperty()
    bar_color = ListProperty()
    background_color = ListProperty()
    show_text = StringProperty()
    font_name = StringProperty()
    font_size = NumericProperty()
    font_color = ListProperty()
    padding = NumericProperty()

    def __init__(self, window, x, y, width=200, height=30, visibility=True,
                 progress=0, max_progress=100,
                 bar_color=[0.2, 0.6, 0.9, 0.8], background_color=[0.9, 0.9, 0.9, 1],
                 show_text='center', font_name='Roboto', font_size=14, font_color=[0.5, 0.5, 0.5, 1],
                 padding=0, disabled=False, disabled_opacity=0.5,
                 **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.pos = (x, y)
        self.size = (width, height)
        self.size_hint = (None, None)

        # Initialize properties with input parameters
        self.progress = progress
        self.max_progress = max_progress
        self.bar_color = bar_color
        self.background_color = background_color
        self.show_text = show_text
        self.font_name = font_name
        self.font_size = font_size
        self.font_color = font_color
        self.padding = padding  # Padding can be negative or positive
        self.disabled_opacity = disabled_opacity

        # Initially store these states
        self.disabled = disabled
        self.visibility = visibility

        # Draw the progress bar
        with self.canvas:
            # Background
            self.bg_color_instruction = Color(rgba=self.background_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)
            # Progress bar
            self.bar_color_instruction = Color(rgba=self.bar_color)
            self.bar_rect = Rectangle(pos=self.pos, size=(0, self.height))

        # Create the Label to display the progress text
        self.progress_label = Label(
            text=f"{int(self.progress / self.max_progress * 100)}%",
            font_name=self.font_name,
            font_size=self.font_size,
            color=self.font_color,
            size_hint=(None, None),
            halign='left',
            valign='middle',
        )

        # Add the label to the widget
        self.add_widget(self.progress_label)

        # Initial updates
        self.update_all()

        # Set initial visibility and disabled state
        self.set_visibility(self.visibility)
        self.set_disabled(self.disabled)

        # Add the widget to the window
        window.add_widget(self)

    def update_all(self, *args):
        self.update_rectangles()
        self.update_label_properties()

    def update_rectangles(self, *args):
        # Update the positions and sizes of the rectangles
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

        progress_width = (self.progress / self.max_progress) * self.width
        self.bar_rect.pos = self.pos
        self.bar_rect.size = (progress_width, self.height)

    def update_label_properties(self, *args):
        alignment = self.show_text.lower()
        padding = self.padding

        # Base label position and size
        label_x, label_y = self.pos
        label_width, label_height = self.size

        if alignment == 'left':
            self.progress_label.halign = 'left'
            self.progress_label.pos = (label_x + padding, label_y)
            self.progress_label.size = (label_width - padding if padding >= 0 else label_width - padding, label_height)
        elif alignment == 'center':
            self.progress_label.halign = 'center'
            self.progress_label.pos = (label_x, label_y)
            self.progress_label.size = (label_width, label_height)
        elif alignment == 'right':
            self.progress_label.halign = 'right'
            self.progress_label.pos = (label_x, label_y)
            self.progress_label.size = (label_width - padding if padding >= 0 else label_width - padding, label_height)
        else:
            self.progress_label.text = ''  # Hide text if 'none' or invalid value

        # Set text size to label size
        self.progress_label.text_size = self.progress_label.size
        self.progress_label.texture_update()

    def update_progress(self, *args):
        # Update the size of the progress bar rectangle
        progress_width = (self.progress / self.max_progress) * self.width
        self.bar_rect.size = (progress_width, self.height)

        # Update the label text
        if self.max_progress == 0:
            percentage = 0
        else:
            percentage = int(self.progress / self.max_progress * 100)
        if self.show_text.lower() != 'none':
            self.progress_label.text = f"{percentage}%"
        else:
            self.progress_label.text = ''

        # Update label properties
        self.update_label_properties()

    def update_bar_color(self, *args):
        # Update the color of the progress bar
        self.bar_color_instruction.rgba = self.bar_color

    def update_background_color(self, *args):
        # Update the background color
        self.bg_color_instruction.rgba = self.background_color

    def set_progress(self, value):
        """Set the progress value."""
        self.progress = max(0, min(value, self.max_progress))
        self.update_progress()

    def get_progress(self):
        """Get the current progress value."""
        return self.progress

    def set_visibility(self, visibility):
        """Show or hide the widget."""
        self.visibility = visibility
        if not visibility:
            self.opacity = 0
        else:
            # If visible, use either full opacity or disabled_opacity
            self.opacity = self.disabled_opacity if self.disabled else 1

    def set_disabled(self, disabled):
        """Enable or disable the widget."""
        self.disabled = disabled
        if self.visibility:
            # Update opacity based on disabled state if visible
            self.opacity = self.disabled_opacity if self.disabled else 1

    # Override touch events to ignore input if disabled
    def on_touch_down(self, touch):
        if self.disabled:
            return False
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.disabled:
            return False
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self.disabled:
            return False
        return super().on_touch_up(touch)


if __name__ == "__main__":
    from kivy.clock import Clock
    import pyvisual as pv

    window = pv.Window()

    # Create an instance of BasicProgressBar
    progress_bar = BasicProgressBar(
        window=window,
        x=100,
        y=300,
        width=400,
        height=30,
        progress=50,
        max_progress=100,
        bar_color=[0.2, 0.6, 0.9, 0.8],
        background_color=[0.9, 0.9, 0.9, 1],
        show_text='center',
        font_name='Roboto',
        font_size=18,
        font_color=[0.1, 0.1, 0.1, 1],
    )

    # Function to simulate progress
    def increment_progress(dt):
        new_progress = progress_bar.get_progress() + 5
        if new_progress > progress_bar.max_progress:
            new_progress = 0  # Reset progress
        progress_bar.set_progress(new_progress)

    # Schedule the progress increment
    Clock.schedule_interval(increment_progress, 0.5)  # Update every 0.5 seconds

    window.show()
