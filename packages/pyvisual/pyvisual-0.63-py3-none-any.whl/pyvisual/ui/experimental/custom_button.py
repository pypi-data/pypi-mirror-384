import os
from kivy.core.window import Window as KivyWindow
from kivy.uix.label import Label
from pyvisual.ui.outputs.pv_image import Image


class CustomButton(Image):
    def __init__(self, window, x, y, scale=1.0, text=None,
                 font="Roboto", font_size=16, font_color=(1, 1, 1, 1),
                 bold=False, italic=False, underline=False, strikethrough=False,
                 idle_image=None, hover_image=None, clicked_image=None,
                 on_hover=None, on_click=None, on_release=None, name=None, visibility= True):

        # Get the base path to the assets folder by moving up two directory levels and then navigating to assets/buttons/sample/
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        default_image_folder = os.path.join(base_path, "assets", "buttons", "default")
        self.name = name  # Set the hidden access text for buttons without visible labels

        # Use default images if not provided
        self.idle_image_path = idle_image or os.path.join(default_image_folder, "idle.png")
        self.hover_image_path = hover_image or os.path.join(default_image_folder, "hover.png")
        self.clicked_image_path = clicked_image or os.path.join(default_image_folder, "clicked.png")

        # Store callback functions
        self.on_click = on_click
        self.on_release = on_release
        self.on_hover = on_hover

        # Initialize the button with the idle image (and add it to the window automatically)
        super().__init__(window, x, y, image_path=self.idle_image_path, scale=scale)

        # Monitor mouse position to simulate hover
        KivyWindow.bind(mouse_pos=self.on_mouse_pos)

        # Text styling options
        self.bold = bold
        self.italic = italic
        self.underline = underline
        self.strikethrough = strikethrough

        # Add text if provided
        self.text = text
        self.font_color = font_color
        self.font = font
        self.font_size = font_size

        if self.text:
            self.add_text(window)

    def apply_markup(self, text):
        """Apply markup tags to the text based on style properties."""
        styled_text = text
        if self.strikethrough:
            styled_text = f"[s]{styled_text}[/s]"
        if self.underline:
            styled_text = f"[u]{styled_text}[/u]"
        if self.italic:
            styled_text = f"[i]{styled_text}[/i]"
        if self.bold:
            styled_text = f"[b]{styled_text}[/b]"
        return styled_text

    def add_text(self, window):
        """Create and add a text label centered on top of the button image."""
        # Apply markup styles to the text
        styled_text = self.apply_markup(self.text)

        # Create a Kivy Label widget
        self.label = Label(
            text=styled_text,
            color=self.font_color,  # Set text color
            font_name=self.font,
            font_size=self.font_size,
            markup=True,  # Enable markup for BBCode-like styling
            size_hint=(None, None),  # Disable size hint
            halign='center',
            valign='middle'
        )

        # Update the text size and position
        self.label.bind(texture_size=self._update_text_position)

        # Set the position and size of the label based on the button
        self._update_text_position()

        # Add the label to the window
        window.add_widget(self.label)

    def set_font_color(self, color):
        """Set the text color of the label."""
        self.font_color = color
        if hasattr(self, 'label'):
            self.label.color = color

    def set_font_size(self, font_size):
        """Set the text size of the label."""
        self.font_size = font_size
        if hasattr(self, 'label'):
            self.label.font_size = font_size

    def set_font(self, font_name):
        """Set the text font of the label."""
        self.font = font_name
        if hasattr(self, 'label'):
            self.label.font_name = font_name

    def set_bold(self, bold):
        """Set the bold style for the text."""
        self.bold = bold
        self.label.text = self.apply_markup(self.text)

    def set_italic(self, italic):
        """Set the italic style for the text."""
        self.italic = italic
        self.label.text = self.apply_markup(self.text)

    def set_underline(self, underline):
        """Set the underline style for the text."""
        self.underline = underline
        self.label.text = self.apply_markup(self.text)

    def set_strikethrough(self, strikethrough):
        """Set the strikethrough style for the text."""
        self.strikethrough = strikethrough
        self.label.text = self.apply_markup(self.text)

    def _update_text_position(self, *args):
        """Update the text position to ensure it is centered over the image."""
        # Calculate the center position of the image and set the label position
        self.label.size = self.label.texture_size  # Set size to the texture size for proper positioning
        self.label.pos = (
            self.x + (self.width - self.label.texture_size[0]) / 2,
            self.y + (self.height - self.label.texture_size[1]) / 2
        )

    def on_mouse_pos(self, window, pos):
        """Detect hover by checking if the mouse is within the button area and switch to hover image."""
        if self.is_hovered(pos):
            self.source = self.hover_image_path
            if self.on_hover:
                self.on_hover(self)
        else:
            self.source = self.idle_image_path

    def on_touch_down(self, touch):
        """Handle mouse click by switching to clicked image and invoking the callback."""
        if self.is_hovered(touch.pos):
            self.source = self.clicked_image_path
            if self.on_click:
                self.on_click(self)
            return True  # Indicate that the touch was handled
        return False

    def on_touch_up(self, touch):
        """Handle mouse release by switching back to hover or idle state and invoking the callback."""
        if self.is_hovered(touch.pos):
            self.source = self.hover_image_path
            if self.on_release:
                self.on_release(self)
            return True  # Indicate that the touch was handled
        else:
            self.source = self.idle_image_path
        return False

    def is_hovered(self, pos):
        """Check if the mouse is within the button's boundaries."""
        return self.x <= pos[0] <= self.x + self.width and self.y <= pos[1] <= self.y + self.height

    def destroy(self):
        # Check if the widget is still part of the window
        if self.window and self in self.window.children:
            self.window.remove_widget(self)

    def set_visibility(self, visibility):
        # """Show or hide the image."""
        # if visibility and not self.visibility:
        #     self.parent.add_widget(self)  # Add image back to window if shown
        # elif not visibility and self.visibility:
        #     self.parent.remove_widget(self)  # Remove image from window if visibility
        # self.visibility = visibility

        if visibility:
            self.opacity = 1
        else:
            self.opacity = 0
        self.visibility = visibility

if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()

    # Create a ButtonImage with styled text and callbacks
    button = CustomButton(
        window=window,
        x=280, y=270,  # Adjusted position for better visibility
        idle_image="../assets/buttons/blue_round/idle.png",
        hover_image="../assets/buttons/blue_round/hover.png",
        clicked_image="../assets/buttons/blue_round/clicked.png",
        scale=1,
        text="Styled Text",
        # font_color=(1, 1, 1, 1),  # Set text color
        font="Roboto",
        font_size=32,
        bold=True,

        on_click=lambda instance: print("Button clicked!"),
        on_release=lambda instance: print("Button released!"),
        on_hover=lambda instance: print("Button hovered!")
    )

    window.show()
