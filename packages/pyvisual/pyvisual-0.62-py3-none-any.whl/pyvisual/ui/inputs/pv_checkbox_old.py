import os
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.core.window import Window



class PvCheckbox(Widget):
    def __init__(self, container, x=0, y=0, size=30, padding=4, visibility = True,
                 checked_color=(0.3, 0.8, 0.3, 1), unchecked_color=(1, 1, 1, 1),
                 border_color=(0.3, 0.3, 0.3, 1), border_thickness=1, is_checked=False,
                 toggle_callback=None, text=None, text_position='none',corner_radius=5,
                 text_padding=5, font_name='Roboto', font_color=(0, 0, 0, 1),
                 font_size=14, disabled=False,disabled_opacity=0.3):
        """
        Initialize the BasicCheckbox.

        :param container: The container to which the checkbox will be added.
        :param x: The x-coordinate position of the checkbox.
        :param y: The y-coordinate position of the checkbox.
        :param size: The size of the checkbox (width and height).
        :param padding: Padding between the checkbox border and the inner rectangle.
        :param checked_color: Color when the checkbox is checked.
        :param unchecked_color: Color when the checkbox is unchecked.
        :param border_color: Color of the checkbox border.
        :param border_thickness: Thickness of the checkbox border.
        :param is_checked: Initial checked state of the checkbox.
        :param toggle_callback: Function to call when the checkbox state changes.
        :param text: Text to display alongside the checkbox.
        :param text_position: Position of the text relative to the checkbox ('none', 'left', 'right', 'top', 'bottom').
        :param text_padding: Padding between the checkbox and the text.
        :param font_name: Font name or path for the text.
        :param font_color: Color of the text.
        :param font_size: Size of the text font.
        """
        super().__init__()

        # Store properties
        self.size_hint = (None, None)
        self.size = (size, size)  # Size of the checkbox
        self.is_checked = is_checked
        self.checked_color = checked_color
        self.unchecked_color = unchecked_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.toggle_callback = toggle_callback
        self.padding = padding  # Padding between border and inner rectangle
        self.corner_radius = corner_radius

        # Text properties
        self.text = text
        self.text_position = text_position.lower()
        self.text_padding = text_padding
        self.font_name = font_name
        self.font_color = font_color
        self.font_size = font_size
        self.disabled_opacity = disabled_opacity
        # Set widget position
        self.pos = (x, y)

        # Calculate inner rectangle position and size based on padding
        self.inner_pos = (self.pos[0] + self.padding, self.pos[1] + self.padding)
        self.inner_size = (self.size[0] - 2 * self.padding, self.size[1] - 2 * self.padding)

        with self.canvas:
            # Draw the background rectangle with rounded corners based on the state
            self.color_instruction = Color(*self.unchecked_color)
            self.rect = RoundedRectangle(pos=self.inner_pos, size=self.inner_size, radius=[self.corner_radius-(self.padding/2)])

            # Draw the border with rounded corners
            Color(*self.border_color)
            self.border = Line(rounded_rectangle=(self.pos[0], self.pos[1],
                                                  self.size[0], self.size[1],
                                                  self.corner_radius),
                               width=self.border_thickness)




        # Initialize the label if text is provided

        if container:
            # Add the checkbox widget to the container
            container.add_widget(self)
        self.label = None
        if self.text and self.text_position != 'none':
            self.create_label(container)

        self.visibility = visibility  # Initialize visibility state
        self.set_visibility(self.visibility)
        self.disabled = disabled
        self.set_disabled(self.disabled)
        # Bind to position and size changes if necessary
        self.bind(pos=self.update_checkbox_graphics, size=self.update_checkbox_graphics)

        self.set_is_checked(self.is_checked)
    def create_label(self, container):
        """
        Create and add a Label widget based on the text properties.

        :param window: The window to which the label will be added.
        """
        # Register the font if it's a custom font file
        if os.path.isfile(self.font_name):
            LabelBase.register(name='CustomFont', fn_regular=self.font_name)
            font_name_to_use = 'CustomFont'
        else:
            font_name_to_use = self.font_name  # Use default Kivy font

        self.label = Label(text=self.text,
                           font_name=font_name_to_use,
                           color=self.font_color,
                           font_size=self.font_size,
                           size_hint=(None, None),
                           size=(Window.width, Window.height))  # Temporary size; will be updated
        container.add_widget(self.label)
        self.update_label_position()

    def on_touch_down(self, touch):
        if self.disabled:
            return False
        if self.collide_point(*touch.pos):
            self.is_checked = not self.is_checked
            self.update_checkbox_appearance()

            # Trigger callback if provided
            if self.toggle_callback:
                self.toggle_callback(self)
            return True
        return super().on_touch_down(touch)

    def update_checkbox_appearance(self):
        """Update the checkbox appearance (color) based on the state."""
        self.color_instruction.rgba = self.checked_color if self.is_checked else self.unchecked_color

    def set_is_checked(self,value):
        self.is_checked = value
        self.update_checkbox_appearance()

    def update_checkbox_graphics(self, *args):
        """Update the position and size of the rectangle and border when the widget properties change."""
        # Update inner rectangle position and size based on padding
        self.inner_pos = (self.pos[0] + self.padding, self.pos[1] + self.padding)
        self.inner_size = (self.size[0] - 2 * self.padding, self.size[1] - 2 * self.padding)
        self.rect.pos = self.inner_pos
        self.rect.size = self.inner_size

        # Redraw the border with rounded corners
        self.canvas.remove(self.border)
        with self.canvas:
            Color(*self.border_color)
            self.border = Line(rounded_rectangle=(self.pos[0], self.pos[1],
                                                  self.size[0], self.size[1],
                                                  self.corner_radius),
                               width=self.border_thickness)

        # Update the label position if it exists
        if self.label:
            self.update_label_position()

    def update_label_position(self):
        """Position the label based on the text_position and padding."""
        if not self.label:
            return

        # Update label's size to fit the text
        self.label.texture_update()
        self.label.size = self.label.texture_size

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

    def set_border(self, border_color, border_thickness):
        """Set the border color and thickness."""
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.update_checkbox_graphics()

    def set_padding(self, padding):
        """Set the padding and update the checkbox appearance."""
        self.padding = padding
        self.update_checkbox_graphics()

    def set_text(self, text, position='none', padding=5,
                font_name='Roboto', font_color=(0, 0, 0, 1), font_size=14):
        """
        Set or update the text and its properties.

        :param text: The text to display.
        :param position: Position of the text relative to the checkbox ('none', 'left', 'right', 'top', 'bottom').
        :param padding: Padding between the checkbox and the text.
        :param font_name: Font name or path for the text.
        :param font_color: Color of the text.
        :param font_size: Size of the text font.
        """
        self.text = text
        self.text_position = position.lower()
        self.text_padding = padding
        self.font_name = font_name
        self.font_color = font_color
        self.font_size = font_size

        if self.text and self.text_position != 'none':
            if not self.label:
                # Create the label if it doesn't exist
                self.create_label(Window)
            else:
                # Update existing label properties
                if os.path.isfile(self.font_name):
                    LabelBase.register(name='CustomFont', fn_regular=self.font_name)
                    self.label.font_name = 'CustomFont'
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
                Window.remove_widget(self.label)
                self.label = None

    def set_corner_radius(self, corner_radius):
        """Set the corner radius and update the checkbox appearance."""
        self.corner_radius = corner_radius
        self.update_checkbox_graphics()

    def set_text_properties(self, font_name=None, font_color=None, font_size=None):
        """
        Update the text properties.

        :param font_name: New font name or path.
        :param font_color: New font color.
        :param font_size: New font size.
        """
        if not self.label:
            return

        if font_name:
            if os.path.isfile(font_name):
                LabelBase.register(name='CustomFont', fn_regular=font_name)
                self.label.font_name = 'CustomFont'
            else:
                self.label.font_name = font_name

        if font_color:
            self.label.color = font_color

        if font_size:
            self.label.font_size = font_size

        self.label.texture_update()
        self.label.size = self.label.texture_size
        self.update_label_position()

    def set_disabled(self, disabled):
        """Enable or disable the slider."""
        self.disabled = disabled
        new_opacity = self.disabled_opacity if self.disabled else 1
        self.opacity = new_opacity
        if self.label:
            # Convert label color to a list so we can modify the alpha component
            label_color = list(self.label.color)
            label_color[3] = new_opacity
            self.label.color = tuple(label_color)

    def set_visibility(self, visibility):
        """Show or hide the image."""
        if visibility:
            if self.disabled:
                self.opacity = self.disabled_opacity
                if self.label:
                    self.label.color[3] =  self.disabled_opacity
            else:
                self.opacity = 1
                if self.label:
                    self.label.color[3] = 1

        else:
            self.opacity = 0
            self.label.color = (0, 0, 0, 0)
        self.visibility = visibility

# Example usage of the Enhanced BasicCheckbox class
if __name__ == "__main__":
    import pyvisual as pv

    window = pv.PvWindow()

    # Toggle callback function
    def on_toggle(cb):
        print(f"Checkbox State: {'Checked' if cb.is_checked else 'Unchecked'}")

    # Add a color-based checkbox with custom border, padding, and text
    custom_checkbox = PvCheckbox(
        container=window,
        x=100, y=300,
        padding=5,  # Padding between border and inner rectangle
        toggle_callback=lambda cb: print(f"Checkbox2 State: {'Checked' if cb.is_checked else 'Unchecked'}"),
        text="Accept Terms",  # Text to display
        text_position='right',  # Position of the text relative to the checkbox
        text_padding=10,  # Padding between checkbox and text
        font_name='Roboto',  # Font name or path
        font_color=(0, 0, 0, 1),  # Black color
        font_size=16,  # Font size
        visibility=True,
        disabled= True
    )

    # Optionally, create another checkbox with text at different positions
    custom_checkbox2 = PvCheckbox(
        container=window,
        x=100, y=250,
        padding=5,
        toggle_callback=lambda cb: print(f"Checkbox3 State: {'Checked' if cb.is_checked else 'Unchecked'}"),
        text="Subscribe to Newsletter",
        text_position='bottom',  # Text below the checkbox
        text_padding=8,
        font_name='Roboto',
        font_color=(0, 0, 1, 1),  # Blue color
        font_size=14
    )

    # Create a checkbox without text
    custom_checkbox3 = PvCheckbox(
        container=window,
        x=100, y=200,
        padding=5,
        toggle_callback=lambda cb: print(f"Checkbox4 State: {'Checked' if cb.is_checked else 'Unchecked'}"),
        text=None,  # No text
        text_position='none'
    )

    # Create a checkbox with text on the left
    custom_checkbox4 = PvCheckbox(
        container=window,
        x=100, y=150,
        padding=5,
        toggle_callback=lambda cb: print(f"Checkbox5 State: {'Checked' if cb.is_checked else 'Unchecked'}"),
        text="Enable Notifications",
        text_position='left',
        text_padding=10,
        font_name='Roboto',
        font_color=(1, 0, 0, 1),  # Red color
        font_size=16,
        is_checked=True
    )

    # Optionally, dynamically update the text of a checkbox after creation
    # custom_checkbox.set_text("New Text", position='top', padding=12, font_color=(0, 1, 0, 1), font_size=18)

    window.show()
