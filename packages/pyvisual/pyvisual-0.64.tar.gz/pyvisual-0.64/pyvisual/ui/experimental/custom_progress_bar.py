import os
from kivy.uix.widget import Widget
from kivy.uix.image import Image as KivyImage
from kivy.uix.stencilview import StencilView
from kivy.properties import NumericProperty, StringProperty, ListProperty
from kivy.uix.label import Label


class CustomProgressBar(Widget):
    # Properties for the progress bar
    progress = NumericProperty()
    max_progress = NumericProperty()
    knob_size = NumericProperty()
    track_image = StringProperty()
    fill_image = StringProperty()
    knob_image = StringProperty()
    scale = NumericProperty(1.0)

    # Text-related properties
    show_text = StringProperty("center")  # Display text at the center by default
    font_name = StringProperty("Roboto")  # Default font name
    font_size = NumericProperty(18)  # Default font size
    font_color = ListProperty([0.5, 0.5, 0.5, 1])  # Default text color

    # Padding for left and right positioning
    padding = NumericProperty(0)

    def __init__(self, window, x, y, progress=0, max_progress=100, knob_size=30, scale=1.0,
                 track_image=None, fill_image=None, knob_image=None,
                 show_text="center", font_name="Roboto", font_size=14, font_color=[0.5, 0.5, 0.5, 1],
                 padding=0,
                 **kwargs):
        super().__init__(**kwargs)

        # Set position (size will be derived from the images)
        self.pos = (x, y)
        self.size_hint = (None, None)
        self.scale = scale

        # Initialize properties with input values
        self.progress = progress
        self.max_progress = max_progress
        self.knob_size = knob_size
        self.show_text = show_text
        self.font_name = font_name
        self.font_size = font_size
        self.font_color = font_color
        self.padding = padding

        # Base path to the assets folder
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_folder = os.path.join(base_path, "assets", "progressbars", "default")

        # Use default images if not provided
        self.track_image = track_image or os.path.join(default_image_folder, "track.png")
        self.fill_image = fill_image or os.path.join(default_image_folder, "fill.png")
        self.knob_image = knob_image or os.path.join(default_image_folder, "knob.png")

        # Load the track image to get its size
        track_image_widget = KivyImage(source=self.track_image)
        track_image_widget.texture_update()  # Ensure the texture size is updated

        # Get the dimensions of the track image and scale them
        self.track_width = int(track_image_widget.texture_size[0] * self.scale)
        self.track_height = int(track_image_widget.texture_size[1] * self.scale)

        # Update the main widget size based on the track image size
        self.size = (self.track_width, self.track_height)

        # Create the track image widget
        self.track_widget = KivyImage(
            source=self.track_image,
            size_hint=(None, None),
            size=self.size,  # Set track size based on the image dimensions
            pos=self.pos
        )

        # Create the fill image widget (full size, initially hidden by stencil)
        self.fill_widget = KivyImage(
            source=self.fill_image,
            size_hint=(None, None),
            size=self.size,  # Full size of the track
            pos=self.pos  # Same position as the track
        )

        # Create a StencilView to mask the fill image
        self.fill_stencil = StencilView(
            size_hint=(None, None),
            size=(0, self.track_height),  # Start with zero width, will reveal fill as progress increases
            pos=self.pos
        )
        self.fill_stencil.add_widget(self.fill_widget)

        # Create the knob image widget and scale it
        knob_scaled_size = int(self.knob_size * self.scale)
        self.knob_widget = KivyImage(
            source=self.knob_image,
            size_hint=(None, None),
            size=(knob_scaled_size, knob_scaled_size),
            pos=(self.pos[0] - knob_scaled_size / 2, self.pos[1] + (self.track_height - knob_scaled_size) / 2)  # Start knob at the beginning of the track
        )

        # Create the text label widget
        self.text_label = Label(
            text=f"{int(self.progress / self.max_progress * 100)}%",  # Initial text
            font_name=self.font_name,
            font_size=self.font_size,
            color=self.font_color,
            size_hint=(None, None),
            halign='left',
            valign='middle'
        )
        # Bind the texture_size to the size so the label updates its size
        self.text_label.bind(texture_size=self.text_label.setter('size'))
        # Bind texture_size to update the text position whenever the size changes
        self.text_label.bind(texture_size=self.update_text_position)

        # Add the widgets to the main window
        window.add_widget(self.track_widget)
        window.add_widget(self.fill_stencil)  # Add the StencilView containing the fill
        window.add_widget(self.knob_widget)
        window.add_widget(self.text_label)

        # Bind progress property to the update function
        self.bind(progress=self.update_progress, size=self.update_widgets, pos=self.update_widgets)

        # Initial update
        self.update_widgets()
        self.update_progress()

    def update_progress(self, *args):
        """Update the fill and knob positions based on the progress."""
        # Calculate the progress ratio
        progress_ratio = self.progress / self.max_progress if self.max_progress > 0 else 0

        # Calculate the width of the fill based on the progress ratio
        fill_width = self.track_width * progress_ratio

        # Adjust the fill stencil to reveal the fill image gradually without changing its size
        self.fill_stencil.size = (fill_width, self.track_height)  # Reveal up to the calculated width
        self.fill_stencil.pos = self.pos  # Keep the stencil aligned with the track

        # Ensure the fill image remains at full size and position is anchored to the start
        self.fill_widget.size = self.size
        self.fill_widget.pos = self.pos  # Keep the fill starting at the beginning of the track

        # Update the knob position based on the fill width
        knob_x = self.pos[0] + fill_width - (self.knob_widget.width / 2)  # Adjust knob position
        self.knob_widget.pos = (knob_x, self.knob_widget.pos[1])

        # Update the label's text
        self.text_label.text = f"{int(self.progress / self.max_progress * 100)}%"

    def update_text_position(self, *args):
        """Update the text label position based on the text alignment and padding."""
        alignment = self.show_text.lower()
        padding = self.padding

        # Use the track's position instead of the widget position to ensure alignment with the track
        track_x, track_y = self.track_widget.pos
        label_width, label_height = self.track_widget.size

        if alignment == 'left':
            self.text_label.pos = (track_x + padding, track_y + (label_height - self.text_label.height) / 2)
        elif alignment == 'right':
            self.text_label.pos = (track_x + label_width - self.text_label.width - padding, track_y + (label_height - self.text_label.height) / 2)
        else:  # Center position is handled separately
            self.text_label.pos = (track_x + label_width / 2 - self.text_label.width / 2, track_y + (label_height - self.text_label.height) / 2)

    def update_widgets(self, *args):
        """Update the position and size of all widgets when the main widget size or position changes."""
        self.update_progress()

    def set_progress(self, value):
        """Set the progress value within the allowable range."""
        self.progress = max(0, min(value, self.max_progress))

    def get_progress(self):
        """Get the current progress value."""
        return self.progress


# Example usage of the CustomProgressBar class
if __name__ == "__main__":
    from kivy.clock import Clock

    import pyvisual as pv
    window = pv.Window()

    # Create a custom progress bar with default images and scaling
    custom_progress_bar = CustomProgressBar(
        window=window,
        x=100, y=300,
        progress=0,
        max_progress=100,
        scale=1.0,  # Scale the entire progress bar
        show_text="center",  # Display text on the left
        font_name="Roboto",
        font_size=18,
        font_color=[0.2, 0.6, 0.9, 1],
        padding=20,  # Set padding for left and right positions
    )

    def increment_progress(dt):
        new_progress = custom_progress_bar.get_progress() + 5
        if new_progress > custom_progress_bar.max_progress:
            new_progress = 0  # Reset progress
        custom_progress_bar.set_progress(new_progress)

    # Schedule the progress increment
    Clock.schedule_interval(increment_progress, 0.5)  # Update every 0.5 seconds

    # Display the window
    window.show()
