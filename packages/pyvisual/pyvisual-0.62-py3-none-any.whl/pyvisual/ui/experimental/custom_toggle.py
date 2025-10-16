import os
from pyvisual.ui.outputs.pv_image import Image  # Ensure this is the correct import path


class CustomToggle(Image):
    def __init__(self, window, x, y, toggle_on_image=None, toggle_off_image=None, scale=1.0,
                 toggle_on_callback=None, toggle_off_callback=None):
        """
        Initialize the CustomToggle.

        :param window: The window to which the toggle will be added.
        :param x: The x-coordinate position of the toggle.
        :param y: The y-coordinate position of the toggle.
        :param toggle_on_image: Path to the image representing the "On" state.
        :param toggle_off_image: Path to the image representing the "Off" state.
        :param scale: Scale factor for the toggle images.
        :param toggle_on_callback: Function to call when toggled to "On".
        :param toggle_off_callback: Function to call when toggled to "Off".
        """
        # Get the base path to the assets folder by moving up two directory levels
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_folder = os.path.join(base_path, "assets", "toggles", "default")

        # Use default images if not provided
        self.toggle_on_image_path = toggle_on_image or os.path.join(default_image_folder, "on.png")
        self.toggle_off_image_path = toggle_off_image or os.path.join(default_image_folder, "off.png")

        # Store callback functions
        self.toggle_on_callback = toggle_on_callback
        self.toggle_off_callback = toggle_off_callback

        # Initial toggle state
        self.is_on = False  # Default state is "Off"

        # Initialize the toggle image with the "Off" image path
        super().__init__(window, x, y, image_path=self.toggle_off_image_path, scale=scale)

    def on_touch_down(self, touch):
        """
        Handle mouse click to toggle the state and update image.

        :param touch: The touch event.
        :return: True if the touch is handled, else calls the superclass method.
        """
        if self.collide_point(*touch.pos):
            # Toggle the state
            self.is_on = not self.is_on

            # Update the toggle image
            self.source = self.toggle_on_image_path if self.is_on else self.toggle_off_image_path

            # Trigger the appropriate callback
            if self.is_on and self.toggle_on_callback:
                self.toggle_on_callback(self)
            elif not self.is_on and self.toggle_off_callback:
                self.toggle_off_callback(self)

            return True  # Indicate that the touch was handled

        return super().on_touch_down(touch)  # Pass the event to other widgets if not handled

    def set_images(self, toggle_on_image, toggle_off_image):
        """
        Set new images for "On" and "Off" states.

        :param toggle_on_image: Path to the new "On" state image.
        :param toggle_off_image: Path to the new "Off" state image.
        """
        self.toggle_on_image_path = toggle_on_image
        self.toggle_off_image_path = toggle_off_image
        self.source = self.toggle_on_image_path if self.is_on else self.toggle_off_image_path

    def set_toggle_state(self, state=True):
        """
        Manually set the toggle state.

        :param state: Boolean indicating the desired state. True for "On", False for "Off".
        """
        self.is_on = state
        self.source = self.toggle_on_image_path if self.is_on else self.toggle_off_image_path

        # Trigger the appropriate callback
        if self.is_on and self.toggle_on_callback:
            self.toggle_on_callback(self)
        elif not self.is_on and self.toggle_off_callback:
            self.toggle_off_callback(self)


# Example usage of the CustomToggle class
if __name__ == "__main__":
    import pyvisual as pv
    window = pv.Window()

    # Define callback functions
    def on_toggle_on(toggle):
        print("Toggle is turned ON!")

    def on_toggle_off(toggle):
        print("Toggle is turned OFF!")

    # Create a custom toggle with default images
    custom_toggle = CustomToggle(
        window=window,
        x=200, y=250,  # Position on the screen
        scale=1.0,  # Scale factor for the toggle size
        toggle_on_callback=on_toggle_on,
        toggle_off_callback=on_toggle_off
    )



    # Display the window with the added toggles
    window.show()
