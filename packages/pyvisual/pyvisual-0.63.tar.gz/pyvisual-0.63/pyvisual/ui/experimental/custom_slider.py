import os
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty
from kivy.uix.label import Label
from kivy.uix.image import Image
from kivy.uix.stencilview import StencilView


class CustomSlider(Widget):
    min_value = NumericProperty()
    max_value = NumericProperty()
    current_value = NumericProperty()
    show_text = StringProperty()
    font_name = StringProperty()
    font_size = NumericProperty()
    font_color = ListProperty()
    padding = NumericProperty()
    knob_virtual_padding_y = NumericProperty(0)  # New property for vertical virtual padding

    # Image properties
    track_image = StringProperty()
    fill_image = StringProperty()
    knob_image = StringProperty()

    def __init__(self, window, x, y, width=200, height=30,
                 min_value=0, max_value=100, current_value=0,
                 show_text='center', font_name='Roboto', font_size=14, font_color=[0.5, 0.5, 0.5, 1],
                 padding=0, knob_virtual_padding_y=0,
                 track_image=None, fill_image=None, knob_image=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.pos = (x, y)
        self.size = (width, height)
        self.size_hint = (None, None)

        # Set default paths for images if not provided
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_folder = os.path.join(base_path, "assets", "sliders", "sample")

        # Use default images if not provided
        self.track_image = track_image or os.path.join(default_image_folder, "track.png")
        self.fill_image = fill_image or os.path.join(default_image_folder, "fill.png")
        self.knob_image = knob_image or os.path.join(default_image_folder, "knob.png")

        # Initialize properties with input parameters
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.show_text = show_text
        self.font_name = font_name
        self.font_size = font_size
        self.font_color = font_color
        self.padding = padding
        self.knob_virtual_padding_y = knob_virtual_padding_y

        # Create the track image widget
        self.track = Image(source=self.track_image, pos=self.pos, size=self.size)

        # Create the fill image widget and use StencilView to control its visibility
        self.fill_stencil = StencilView(size=(0, self.height), pos=self.pos)
        self.fill = Image(source=self.fill_image, size=self.size)
        self.fill_stencil.add_widget(self.fill)

        # Create the knob image widget
        self.knob = Image(source=self.knob_image, size_hint=(None, None), size=(self.height, self.height))

        # Create the text label widget to display the current value
        self.text_label = Label(
            text=f"{int(self.current_value)}",  # Initial text
            font_name=self.font_name,
            font_size=self.font_size,
            color=self.font_color,
            size_hint=(None, None),
            halign='center',
            valign='middle'
        )

        # Bind the texture size of the label to its size and trigger text position updates
        self.text_label.bind(texture_size=self.text_label.setter('size'))
        self.text_label.bind(texture_size=self.update_text_position)

        # Add widgets to the main widget
        self.add_widget(self.track)
        self.add_widget(self.fill_stencil)
        self.add_widget(self.knob)
        self.add_widget(self.text_label)

        # Bind properties to update methods
        self.bind(pos=self.update_all, size=self.update_all, current_value=self.update_current_value)
        self.update_all()
        window.add_widget(self)

    def update_all(self, *args):
        self.update_rectangles()
        self.update_text_position()

    def update_rectangles(self, *args):
        # Update positions and sizes of the track and fill images
        self.track.pos = self.pos
        self.track.size = self.size

        if self.max_value != self.min_value:
            relative_value = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        else:
            relative_value = 0
        bar_width = relative_value * self.width

        # Adjust the fill stencil to reveal the fill image gradually without changing its size
        self.fill_stencil.size = (bar_width, self.height)
        self.fill_stencil.pos = self.pos  # Keep the stencil aligned with the track

        # Ensure the fill image remains at full size and position is anchored to the start
        self.fill.size = self.size
        self.fill.pos = self.pos

        # Update the knob position based on the fill width and add virtual vertical padding
        knob_x = self.pos[0] + bar_width - (self.knob.width / 2)
        knob_y = self.pos[1] + (self.height - self.knob.height) / 2 + self.knob_virtual_padding_y
        self.knob.pos = (knob_x, knob_y)

    def update_text_position(self, *args):
        """Update the text label position based on the text alignment and padding."""
        alignment = self.show_text.lower()
        padding = self.padding

        # Use the track's position to ensure alignment with the track
        track_x, track_y = self.track.pos
        label_width, label_height = self.track.size

        # Adjust position based on alignment
        if alignment == 'left':
            self.text_label.pos = (track_x + padding, track_y + (label_height - self.text_label.height) / 2)
        elif alignment == 'right':
            self.text_label.pos = (track_x + label_width - self.text_label.width - padding, track_y + (label_height - self.text_label.height) / 2)
        else:  # Center alignment
            self.text_label.pos = (track_x + label_width / 2 - self.text_label.width / 2, track_y + (label_height - self.text_label.height) / 2)

    def update_current_value(self, *args):
        # Ensure current value is within min and max
        self.current_value = max(self.min_value, min(self.current_value, self.max_value))
        # Update bar and knob positions
        self.update_rectangles()
        # Update text label
        self.text_label.text = str(int(self.current_value))

    def on_touch_down(self, touch):
        if self.knob.collide_point(touch.x, touch.y):  # Adjust touch area to match knob position
            # Update value based on touch position
            self.update_value_from_touch(touch)
            touch.grab(self)
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if touch.grab_current is self:
            # Update value based on touch position
            self.update_value_from_touch(touch)
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True
        return super().on_touch_up(touch)

    def update_value_from_touch(self, touch):
        x = touch.x
        # Calculate relative position
        relative_x = (x - self.pos[0]) / self.width
        # Clamp between 0 and 1
        relative_x = max(0.0, min(1.0, relative_x))
        # Update current value
        self.current_value = self.min_value + relative_x * (self.max_value - self.min_value)
        # Trigger update
        self.update_current_value()


if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()

    # Example usage with images for track, fill, and knob
    custom_slider = CustomSlider(
        window=window,
        x=50,
        y=300,
        width=400,
        height=50,
        min_value=0,
        max_value=100,
        current_value=62,
        show_text='center',
        font_name='Roboto',
        font_size=18,
        font_color=[0, 0, 0, 1],
        padding=10,
        knob_virtual_padding_y=-0  # Add vertical padding for the knob
    )

    window.show()
