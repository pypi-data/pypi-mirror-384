import os
from pyvisual.ui.outputs.pv_image import Image  # Ensure this is the correct import path
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.core.window import Window

class CustomCheckbox(Image):
    def __init__(self, window, x, y, checked_image=None, unchecked_image=None, scale=1.0,
                 checked_callback=None, unchecked_callback=None,
                 text=None, text_position='none', text_padding=5,
                 font_name='Roboto', font_color=(0, 0, 0, 1), font_size=14):
        """
        Initialize the CustomCheckbox.
        """
        # Store reference to the window as an instance attribute
        self.window = window

        # Get the base path to the assets folder by moving up two directory levels
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_folder = os.path.join(base_path, "assets", "checkboxes", "sample")

        # Use default images if not provided
        self.checked_image_path = checked_image or os.path.join(default_image_folder, "checked.png")
        self.unchecked_image_path = unchecked_image or os.path.join(default_image_folder, "unchecked.png")

        # Store callback functions
        self.checked_callback = checked_callback
        self.unchecked_callback = unchecked_callback

        # Initial checkbox state
        self.is_checked = False  # Default state is unchecked

        # Initialize the checkbox image with the unchecked image path
        super().__init__(window, x, y, image_path=self.unchecked_image_path, scale=scale)

        # Text properties
        self.text = text
        self.text_position = text_position.lower()
        self.text_padding = text_padding
        self.font_name = font_name
        self.font_color = font_color
        self.font_size = font_size

        # Initialize the label if text is provided
        self.label = None
        if self.text and self.text_position != 'none':
            self.create_label()

    def create_label(self):
        """Create and add a Label widget based on the text properties."""
        # Register the font if it's a custom font file
        if os.path.isfile(self.font_name):
            font_name_without_ext = os.path.splitext(os.path.basename(self.font_name))[0]
            LabelBase.register(name=font_name_without_ext, fn_regular=self.font_name)
            font_name_to_use = font_name_without_ext
        else:
            font_name_to_use = self.font_name  # Use default Kivy font

        # Create the label widget with the specified properties
        self.label = Label(
            text=self.text,
            font_name=font_name_to_use,
            color=self.font_color,
            font_size=self.font_size,
            size_hint=(None, None),
            size=(Window.width, Window.height)  # Temporary size; will be updated
        )

        # Add label to the stored window instance
        self.window.add_widget(self.label)
        self.update_label_position()

    def on_touch_down(self, touch):
        """Handle mouse click to toggle checkbox state and update image."""
        if self.collide_point(*touch.pos):
            # Toggle the checked state
            self.is_checked = not self.is_checked

            # Update the checkbox image
            self.source = self.checked_image_path if self.is_checked else self.unchecked_image_path

            # Trigger the appropriate callback
            if self.is_checked and self.checked_callback:
                self.checked_callback(self)
            elif not self.is_checked and self.unchecked_callback:
                self.unchecked_callback(self)

            return True  # Indicate that the touch was handled
        return super().on_touch_down(touch)  # Ensure the event is correctly passed to other widgets

    def set_images(self, checked_image, unchecked_image):
        """Set new images for checked and unchecked states."""
        self.checked_image_path = checked_image
        self.unchecked_image_path = unchecked_image
        self.source = self.checked_image_path if self.is_checked else self.unchecked_image_path

    def set_checked(self, state=True):
        """Set the checked state manually."""
        self.is_checked = state
        self.source = self.checked_image_path if self.is_checked else self.unchecked_image_path

        # Trigger the appropriate callback
        if self.is_checked and self.checked_callback:
            self.checked_callback(self)
        elif not self.is_checked and self.unchecked_callback:
            self.unchecked_callback(self)

    def update_label_position(self):
        """Position the label based on the text_position and padding."""
        if not self.label:
            return

        # Update label's size to fit the text
        self.label.texture_update()
        self.label.size = self.label.texture_size

        # Get checkbox position and size
        checkbox_x, checkbox_y = self.pos
        checkbox_width, checkbox_height = self.size
        label_width, label_height = self.label.size

        if self.text_position == 'left':
            label_x = checkbox_x - self.text_padding - label_width
            label_y = checkbox_y + (checkbox_height - label_height) / 2
        elif self.text_position == 'right':
            label_x = checkbox_x + checkbox_width + self.text_padding
            label_y = checkbox_y + (checkbox_height - label_height) / 2
        elif self.text_position == 'top':
            label_x = checkbox_x + (checkbox_width - label_width) / 2
            label_y = checkbox_y + checkbox_height + self.text_padding
        elif self.text_position == 'bottom':
            label_x = checkbox_x + (checkbox_width - label_width) / 2
            label_y = checkbox_y - self.text_padding - label_height
        else:
            label_x, label_y = self.label.pos  # Default to current position if invalid

        self.label.pos = (label_x, label_y)

    def set_text(self, text, position='none', padding=5,
                font_name='Roboto', font_color=(0, 0, 0, 1), font_size=14):
        """Set or update the text and its properties."""
        self.text = text
        self.text_position = position.lower()
        self.text_padding = padding
        self.font_name = font_name
        self.font_color = font_color
        self.font_size = font_size

        if self.text and self.text_position != 'none':
            if not self.label:
                # Create the label if it doesn't exist
                self.create_label()
            else:
                # Update existing label properties
                if os.path.isfile(self.font_name):
                    font_name_without_ext = os.path.splitext(os.path.basename(self.font_name))[0]
                    LabelBase.register(name=font_name_without_ext, fn_regular=self.font_name)
                    self.label.font_name = font_name_without_ext
                else:
                    self.label.font_name = self.font_name
                self.label.text = self.text
                self.label.color = self.font_color
                self.label.font_size = self.font_size
                self.label.texture_update()
                self.label.size = self.label.texture_size
            self.update_label_position()
        else:
            # Remove the label if text is set to 'none' or empty
            if self.label:
                self.window.remove_widget(self.label)  # Use self.window to remove the label
                self.label = None

    def set_text_properties(self, font_name=None, font_color=None, font_size=None):
        """Update the text properties."""
        if not self.label:
            return

        if font_name:
            if os.path.isfile(font_name):
                font_name_without_ext = os.path.splitext(os.path.basename(font_name))[0]
                LabelBase.register(name=font_name_without_ext, fn_regular=font_name)
                self.label.font_name = font_name_without_ext
            else:
                self.label.font_name = font_name

        if font_color:
            self.label.color = font_color

        if font_size:
            self.label.font_size = font_size

        self.label.texture_update()
        self.label.size = self.label.texture_size
        self.update_label_position()




# Example usage of the Enhanced CustomCheckbox class
if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()

    # Add a custom checkbox with text on the right
    custom_checkbox1 = CustomCheckbox(
        window=window,
        x=200, y=250,
        scale=1,
        text="Accept Terms",
        text_position='right',
    )

    window.show()
