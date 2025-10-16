from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line

class BasicToggleButton(Widget):
    def __init__(self, window, x, y, width=60, height=30, padding=4, visibility=True,
                 on_color=(0.3, 0.8, 0.3, 1), off_color=(0.8, 0.3, 0.3, 1),
                 border_color=(0.3, 0.3, 0.3, 1), border_thickness=1,
                 switch_color=(1, 1, 1, 1), is_on=False,
                 toggle_callback=None, disabled=False, disabled_opacity=0.5,
                 radius=10):
        super().__init__()

        # Store properties
        self.size_hint = (None, None)
        self.size = (width, height)
        self.is_on = is_on
        self.on_color = on_color
        self.off_color = off_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.switch_color = switch_color
        self.toggle_callback = toggle_callback
        self.padding = padding
        self.disabled = disabled
        self.disabled_opacity = disabled_opacity
        self.visibility = visibility
        self.radius = radius  # Corner radius for rounded rectangles

        # Set widget position
        self.pos = (x, y)

        # Calculate switch size and initial position
        switch_size = (self.size[1] - 2 * self.padding, self.size[1] - 2 * self.padding)
        if self.is_on:
            switch_x = self.pos[0] + self.size[0] - self.padding - switch_size[0]
        else:
            switch_x = self.pos[0] + self.padding
        switch_y = self.pos[1] + self.padding
        self.switch_pos = (switch_x, switch_y)

        # Draw the toggle button
        with self.canvas:
            # Background with rounded corners
            self.bg_color_instruction = Color(*(self.on_color if self.is_on else self.off_color))
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])

            # Border with rounded corners
            Color(*self.border_color)
            self.border = Line(rounded_rectangle=(self.pos[0], self.pos[1],
                                                  self.size[0], self.size[1],
                                                  self.radius),
                               width=self.border_thickness)

            # Switch with rounded corners (make the switch rounded as well)
            Color(*self.switch_color)
            self.switch_rect = RoundedRectangle(pos=self.switch_pos, size=switch_size, radius=[self.radius])

        # Bind to position and size changes
        self.bind(pos=self.update_toggle_graphics, size=self.update_toggle_graphics)

        # Set initial states
        self.set_visibility(self.visibility)
        self.set_disabled(self.disabled)

        # Add the widget to the window
        window.add_widget(self)

    def on_touch_down(self, touch):
        """Toggle the button state on click."""
        # If disabled, do not toggle
        if self.disabled:
            return False

        if self.collide_point(*touch.pos):
            self.is_on = not self.is_on
            self.update_toggle_appearance()

            # Trigger callback if provided
            if self.toggle_callback:
                self.toggle_callback(self)
            return True
        return False

    def update_toggle_appearance(self):
        """Update the toggle button appearance based on the state."""
        # Update background color
        self.bg_color_instruction.rgba = self.on_color if self.is_on else self.off_color
        # Update switch position
        self.update_switch_position()

    def update_switch_position(self):
        """Move the switch to the appropriate position based on the state."""
        if self.is_on:
            new_x = self.pos[0] + self.size[0] - self.padding - self.switch_rect.size[0]
        else:
            new_x = self.pos[0] + self.padding

        self.switch_rect.pos = (new_x, self.pos[1] + self.padding)

    def update_toggle_graphics(self, *args):
        """Update the position/size of background, border, and switch."""
        # Update background
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.bg_rect.radius = [self.radius]

        # Update border
        self.canvas.remove(self.border)
        with self.canvas:
            Color(*self.border_color)
            self.border = Line(rounded_rectangle=(self.pos[0], self.pos[1],
                                                  self.size[0], self.size[1],
                                                  self.radius),
                               width=self.border_thickness)

        # Update switch size and position
        switch_size = (self.size[1] - 2 * self.padding, self.size[1] - 2 * self.padding)
        self.switch_rect.size = switch_size
        self.switch_rect.radius = [self.radius]
        self.update_switch_position()

    def set_border(self, border_color, border_thickness):
        """Set the border color and thickness."""
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.update_toggle_graphics()

    def set_padding(self, padding):
        """Set the padding and update the toggle button appearance."""
        self.padding = padding
        self.update_toggle_graphics()

    def set_switch_color(self, switch_color):
        """Set the switch color."""
        self.switch_color = switch_color
        with self.canvas:
            Color(*self.switch_color)
        self.update_toggle_graphics()

    def set_visibility(self, visibility):
        """Show or hide the button."""
        self.visibility = visibility
        self._update_opacity()

    def set_disabled(self, disabled):
        """Enable or disable the button."""
        self.disabled = disabled
        self._update_opacity()

    def _update_opacity(self):
        """Update the widget's opacity based on visibility and disabled state."""
        if not self.visibility:
            # If not visible, opacity is 0
            self.opacity = 0
        else:
            # If visible, depends on disabled state
            self.opacity = self.disabled_opacity if self.disabled else 1

        # Update canvas opacity as well
        self.canvas.opacity = self.opacity


if __name__ == "__main__":
    import pyvisual as pv
    window = pv.Window()

    def on_toggle_button_toggle(tb):
        print(f"Toggle Button State: {'On' if tb.is_on else 'Off'}")

    # Example usage
    custom_toggle_button = BasicToggleButton(
        window=window,
        x=200, y=300,
        width=60, height=30,
        padding=4,
        on_color=(0.3, 0.8, 0.3, 1),
        off_color=(0.8, 0.3, 0.3, 1),
        border_color=(0.3, 0.3, 0.3, 0),
        border_thickness=0,
        switch_color=(1, 1, 1, 1),
        is_on=False,
        toggle_callback=on_toggle_button_toggle,
        visibility=True,
        radius=0
    )

    window.show()
