from kivy.uix.widget import Widget
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image as KivyImage
import os


class CustomTextInput(Widget):
    def __init__(self, window, x, y, scale=1, text_color=(0.3, 0.3, 0.3, 1), font_size=32, font_name="Roboto",
                 placeholder="Enter your text here...", default_text="",
                 idle_image=None, active_image=None, text_callback=None,
                 padding_left=0, padding_right=0, padding_top=0, padding_bottom=0,
                 input_type="text"):
        super().__init__()

        # Restrict the scale to 1.0 or less
        if scale > 1.0:
            print("Scale value above 1.0 is not allowed. Setting scale to 1.0.")
            scale = 1.0

        # Get the base path to the assets folder
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_folder = os.path.join(base_path, "assets", "textinputs", "default")

        # Use default images if not provided
        self.idle_image_path = idle_image or os.path.join(default_image_folder, "idle.png")
        self.active_image_path = active_image or os.path.join(default_image_folder, "active.png")

        # Load the image to calculate the size
        image = KivyImage(source=self.idle_image_path)
        image.texture_update()  # Ensure texture is loaded and size is available

        # Calculate dimensions based on image size and scaling factor
        self.original_width = image.texture_size[0]
        self.original_height = image.texture_size[1]
        self.width = self.original_width * scale
        self.height = self.original_height * scale

        # Adjust paddings according to scale
        self.padding_left = padding_left * scale
        self.padding_right = padding_right * scale
        self.padding_top = padding_top * scale
        self.padding_bottom = padding_bottom * scale

        # Set widget properties
        self.size_hint = (None, None)
        self.size = (self.width, self.height)
        self.pos = (x, y)

        # Create the image widget for the text input background
        self.background_image = KivyImage(
            source=self.idle_image_path,  # Use the idle image initially
            size_hint=(None, None),
            size=self.size,  # Use the calculated size
            pos=self.pos,
        )

        # Add the image widget to the window
        window.add_widget(self.background_image)

        # Calculate padding-adjusted position and size for TextInput
        text_input_x = x + self.padding_left
        text_input_y = y + self.padding_bottom
        text_input_width = self.width - self.padding_left - self.padding_right
        text_input_height = self.height - self.padding_top - self.padding_bottom

        # Create the TextInput as an internal widget with placeholder and default text
        self.text_input = TextInput(
            size_hint=(None, None),
            size=(text_input_width, text_input_height),  # Adjust size to fit within the image
            pos=(text_input_x, text_input_y),  # Centered position inside the background
            font_size=font_size * scale,  # Adjust font size according to scale
            font_name=font_name,
            foreground_color=text_color,
            cursor_color=(0, 0, 0, 1),  # Cursor color (can be customized if needed)
            background_normal='',  # Remove background image
            background_active='',  # Remove active background
            background_color=(0, 0, 0, 0),  # Set transparent background to show custom background
            multiline=False,
            hint_text=placeholder,  # Set the placeholder text
            hint_text_color=(0.7, 0.7, 0.7, 1),  # Gray color for placeholder text
            text=default_text,  # Set the initial text value if provided
            password=input_type == "password"  # Enable password mode if input_type is "password"
        )

        # Apply input restrictions based on the `input_type`
        self.apply_input_restrictions(input_type)

        # If a text callback is provided, bind it
        if text_callback:
            self.text_input.bind(text=text_callback)

        # Add the internal TextInput to the main widget
        self.add_widget(self.text_input)

        # Update the image when the focus state changes
        self.text_input.bind(focus=self.on_focus)

        # Add the custom text input to the window
        window.add_widget(self)

    def apply_input_restrictions(self, input_type):
        """Apply input restrictions based on the input type."""
        if input_type == "number":
            self.text_input.input_filter = 'int'
        elif input_type == "float":
            self.text_input.input_filter = 'float'
        elif input_type == "email":
            self.text_input.input_filter = lambda text, from_undo: text.replace(" ", "")
        elif input_type == "alphabet":
            self.text_input.input_filter = lambda text, from_undo: "".join([c for c in text if c.isalpha()])
        else:
            self.text_input.input_filter = None

    def on_focus(self, instance, value):
        """Update the background image based on the focus state of the TextInput."""
        if value:
            self.background_image.source = self.active_image_path
        else:
            self.background_image.source = self.idle_image_path

    def get_text(self):
        """Get the current text value from the internal TextInput."""
        return self.text_input.text

    def set_text(self, value):
        """Set the text value of the internal TextInput."""
        self.text_input.text = value


# Example usage of the CustomTextInput class
if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()
    # Create a custom text input with restrictions for each input type
    text_input_password = CustomTextInput(
        window=window,
        x=100, y=400,
        placeholder="Enter password",
        input_type="password",  # Password type
        scale=0.7
    )

    text_input_email = CustomTextInput(
        window=window,
        x=100, y=300,
        placeholder="Enter email",
        input_type="email",  # Email type
        scale=0.5
    )

    # Display the window
    window.show()
