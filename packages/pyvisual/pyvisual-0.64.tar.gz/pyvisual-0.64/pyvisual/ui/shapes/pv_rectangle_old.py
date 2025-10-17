from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line


class PvRectangle(Widget):
    def __init__(self, container, x, y, width, height,
                 corner_radius=0,bg_color=(0.6, 0.6, 0.6, 1),
                 border_color=(0.8, 0.8, 0.8, 1), border_thickness=0,
                 is_visible=True, opacity=1, tag=None):
        super().__init__(size_hint=(None, None), pos=(x, y))

        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.tag = tag
        self.is_visible = is_visible
        self.opacity = opacity

        # Add the rounded rectangle and optional border to the canvas
        with self.canvas:
            self.color_instruction = Color(*self.bg_color)  # RGBA color
            self.rounded_rect = RoundedRectangle(size=(self.width, self.height), pos=self.pos,
                                                 radius=[self.corner_radius])

            if self.border_thickness>0:
                self.border_color_instruction = Color(*self.border_color)  # RGBA border color
                self.border_line = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.corner_radius),
                                        width=self.border_thickness)

        # Add the widget to the container
        if container:
            container.add_widget(self)

        # Set initial visibility and opacity
        self.set_visibility(self.is_visible)
        # Bind the opacity property to update the canvas
        self.bind(opacity=self._on_opacity, pos=self._update_canvas, size=self._update_canvas)
        self.opacity = opacity  # Trigger the opacity bindinge canvas to update

    def _update_canvas(self, *args):
        # Update button background
        self.rounded_rect.pos = self.pos
        self.rounded_rect.size = self.size

        # Adjust the border rectangle to be drawn inward
        if self.border_thickness:
            self.border_line.rounded_rectangle = (
                self.pos[0] + self.border_thickness,
                self.pos[1] + self.border_thickness,
                self.size[0] - 2 * self.border_thickness,
                self.size[1] - 2 * self.border_thickness,
                self.corner_radius
            )

    def set_size(self, width, height):
        """Update the size of the rounded rectangle."""
        self.width = width
        self.height = height
        self.rounded_rect.size = (self.width, self.height)

        if self.border_color:
            self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, self.corner_radius)

    def set_position(self, x, y):
        """Update the position of the rounded rectangle."""
        self.pos = (x, y)
        self.rounded_rect.pos = self.pos

        if self.border_color:
            self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, self.corner_radius)

    def set_corner_radius(self, corner_radius):
        """Update the corner corner_radius of the rounded rectangle."""
        self.corner_radius = corner_radius
        self.rounded_rect.corner_radius = [self.corner_radius]

        if self.border_color:
            self.border_line.rounded_rectangle = (self.x, self.y, self.width, self.height, self.corner_radius)

    def set_bg_color(self, bg_color):
        """Update the bg_color of the rounded rectangle."""
        self.bg_color = bg_color
        self.color_instruction.rgba = self.bg_color

    def set_border_color(self, border_color):
        """Update the color of the border."""
        self.border_color = border_color
        if self.border_color:
            self.border_color_instruction.rgba = self.border_color

    def set_border_thickness(self, border_thickness):
        """Update the width of the border."""
        self.border_thickness = border_thickness
        if self.border_color:
            self.border_line.width = self.border_thickness
            self.border_line.rounded_rectangle = (
                self.pos[0] + self.border_thickness / 2,
                self.pos[1] + self.border_thickness / 2,
                self.size[0] - self.border_thickness,
                self.size[1] - self.border_thickness,
                self.corner_radius
            )

    def set_visibility(self, is_visible):
        """Show or hide the rounded rectangle."""
        if is_visible:
            self.opacity = 1
            self.canvas.opacity = 1
        else:
            self.opacity = 0
            self.canvas.opacity = 0

        self.is_visible = is_visible

    def _on_opacity(self, instance, value):
        """Update the canvas opacity when the widget's opacity changes."""
        self.opacity = value
        self.canvas.opacity = value

    def set_opacity(self, opacity):
        self.opacity = opacity
        self.canvas.opacity = opacity

    def add_to_layout(self, layout):
        """Add the image to a layout."""
        if self.parent is not None:
            self.parent.remove_widget(self)
        layout.add_widget(self)


if __name__ == "__main__":
    import pyvisual as pv

    window = pv.PvWindow()

    # Create a rounded rectangle with a border
    rectangle = PvRectangle(
        window, 50, 50, 150, 100,
        bg_color=(1, 0.5, 1, 1), border_color=(1, 0, 0, 1), border_thickness=2,
        is_visible=True, tag="rounded1", corner_radius=50, opacity=1,
    )

    # Create a rounded rectangle with a border
    rectangle2 = PvRectangle(
        window, 300, 50, 150, 100,
        bg_color=(1, 0.5, 1, 1), border_color=(1, 0, 0, 1), border_thickness=2,
        is_visible=True, tag="rounded1", corner_radius=0, opacity=0.8,
    )
    window.show()
