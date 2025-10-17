import os
from kivy.core.window import Window as KivyWindow
from pyvisual.ui.outputs.pv_image import Image


class ImageButton(Image):
    def __init__(self, window, x, y, scale=1.0, image_path=None, visibility=True,
                 idle_opacity=1.0, hover_opacity=0.7, clicked_opacity=0.5,
                 on_hover=None, on_click=None, on_release=None,
                 tag=None, disabled=False, disabled_opacity=0.3):

        # Set default image path if not provided
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_folder = os.path.join(base_path, "assets", "buttons", "default")
        self.image_path = image_path or os.path.join(default_image_folder, "idle.png")

        # Store opacity levels for different states
        self.hover_opacity = hover_opacity
        self.clicked_opacity = clicked_opacity
        self.idle_opacity = idle_opacity
        self.disabled_opacity = disabled_opacity
        self.default_opacity = idle_opacity

        # Store callback functions
        self.on_click = on_click
        self.on_release = on_release
        self.on_hover = on_hover
        self.tag = tag

        # Initialize the button with the given image
        super().__init__(window, x, y, image_path=self.image_path, scale=scale)

        # Monitor mouse position to simulate hover
        KivyWindow.bind(mouse_pos=self.on_mouse_pos)

        self.visibility = visibility  # Initialize visibility state
        self.disabled = disabled  # Initialize disabled state
        self.set_visibility(self.visibility)

    def on_mouse_pos(self, window, pos):
        """Detect hover by checking if the mouse is within the button area and adjust opacity."""
        if self.visibility and not self.disabled:
            if self.is_hovered(pos):
                self.opacity = self.hover_opacity
                if self.on_hover:
                    self.on_hover(self)
            else:
                self.opacity = self.idle_opacity

    def on_touch_down(self, touch):
        """Handle mouse click by changing opacity and invoking the callback."""
        if self.visibility and not self.disabled:
            if self.is_hovered(touch.pos):
                self.opacity = self.clicked_opacity
                if self.on_click:
                    self.on_click(self)
                return True  # Indicate that the touch was handled
            return False

    def on_touch_up(self, touch):
        """Handle mouse release by resetting opacity and invoking the callback."""
        if self.visibility and not self.disabled:
            if self.is_hovered(touch.pos):
                self.opacity = self.hover_opacity
                if self.on_release:
                    self.on_release(self)
                return True  # Indicate that the touch was handled
            else:
                self.opacity = self.idle_opacity
            return False

    def is_hovered(self, pos):
        """Check if the mouse is within the button's boundaries."""
        return self.x <= pos[0] <= self.x + self.width and self.y <= pos[1] <= self.y + self.height

    def set_visibility(self, visibility):
        """Show or hide the image."""
        if visibility:
            self.opacity = self.disabled_opacity if self.disabled else self.idle_opacity
        else:
            self.opacity = 0

        self.visibility = visibility

    def set_disabled(self, disabled):
        """Enable or disable the button."""
        self.disabled = disabled
        self.opacity = self.disabled_opacity if self.disabled else self.idle_opacity


if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()

    # Create an ImageButton with opacity effects and callbacks
    button = ImageButton(
        window=window,
        x=280, y=270,  # Adjusted position for better visibility
        image_path="../../assets/buttons/blue_round/idle.png",
        visibility=True,
        scale=1,
        idle_opacity=1.0,
        hover_opacity=0.7,
        clicked_opacity=0.5,
        disabled_opacity=0.2,
        on_click=lambda instance: print("Button clicked!"),
        on_release=lambda instance: print("Button released!"),
        on_hover=lambda instance: print("Button hovered!"),
        disabled=False
    )
    button.set_disabled(False)

    window.show()
