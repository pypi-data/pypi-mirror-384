from kivy.uix.widget import Widget
from kivy.graphics import Line, Color


class PvLine(Widget):
    def __init__(self, container, points, thickness=1, color=(0, 0, 1, 1), is_visible=True, opacity=1, tag=None):
        super().__init__(size_hint=(None, None))

        self.points = points  # List of (x, y) coordinates for the line
        self.thickness = thickness
        self.color = color
        self.tag = tag
        self.is_visible = is_visible
        self.opacity = opacity

        # Add the line to the canvas
        with self.canvas:
            self.color_instruction = Color(*self.color)  # RGBA color
            self.line = Line(points=self._adjust_points(), width=self.thickness)

        # Add the widget to the container
        container.add_widget(self)

        # Set initial is_visible
        self.set_visibility(self.is_visible)
        self.bind(opacity=self._on_opacity, pos=self._update_canvas, size=self._update_canvas)
        self.opacity = opacity  # Trigger the opacity bindinge canvas to update


    def _adjust_points(self):
        """Adjust the line's points relative to the widget's position."""
        x, y = self.pos
        size = [coord + offset for coord, offset in zip(self.points, [x, y] * (len(self.points) // 2))]
        self._adjust_widget_size()
        return size

    def _adjust_widget_size(self):
        """Update the widget's size and position to match the line's bounding box, considering thickness."""
        x_coords = self.points[0::2]
        y_coords = self.points[1::2]

        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        # Adjust for line thickness
        padding = self.thickness / 2
        self.pos = (min_x - padding, min_y - padding)
        self.size = (max_x - min_x + self.thickness, max_y - min_y + self.thickness)

    def _update_canvas(self, *args):
        print(self.size)
        """Update the canvas properties for the line."""
        # Update line properties
        self.line.points = self._adjust_points()
        self.line.width = self.thickness

        # Update color
        if self.color:
            self.color_instruction.rgba = self.color
        self._adjust_widget_size()  # Recalculate size and position


    def set_points(self, points):
        """Update the points of the line."""
        self.points = points
        self.line.points = self.points

    def set_thickness(self, thickness):
        """Update the thickness of the line."""
        self.thickness = thickness
        self.line.width = self.thickness

    def set_color(self, color):
        """Update the color of the line."""
        self.color = color
        self.color_instruction.rgba = self.color

    def set_visibility(self, is_visible):
        """Show or hide the line."""
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

    # Create a line
    line = PvLine(window, points=[0, 0, 100, 100], thickness=5, color=(0, 0.8, 0, 1),
                     is_visible=True,opacity=0.3, tag="line1")
    window.show()
