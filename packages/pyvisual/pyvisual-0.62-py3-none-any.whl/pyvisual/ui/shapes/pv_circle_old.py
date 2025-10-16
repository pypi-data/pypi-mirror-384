from kivy.uix.widget import Widget
from kivy.graphics import Ellipse, Color, Line,Rectangle

class PvCircle(Widget):
    def __init__(self, container, radius, x=100, y=100,
                 bg_color=(0, 0.8, 0.8, 1), border_color=(0.3,0.3,0.3,1), border_thickness=0,
                 is_visible=True, opacity=1, tag=None):
        super().__init__(size_hint=(None, None), pos=(x, y))

        self.radius = radius
        self.bg_color = bg_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.tag = tag
        self.is_visible = is_visible
        self.opacity = opacity

        # Add the circle and border to the canvas
        # with self.canvas.before:
        #     self.background_color_instruction = Color(0.8, 0, 0.8, 0.3)  # Light gray with transparency
        #     self.background_rect = Rectangle(size=self.size, pos=self.pos)

        # Add the circle to the canvas
        with self.canvas:
            self.color_instruction = Color(*self.bg_color)  # RGBA color
            self.circle = Ellipse(size=(self.radius * 2, self.radius * 2), pos=self.pos)

            if self.border_thickness>0:
                self.border_color_instruction = Color(*self.border_color)  # RGBA border color
                self.border = Line(circle=(self.center_x, self.center_y, self.radius-self.border_thickness), width=self.border_thickness)


        if container:
            container.add_widget(self)
        # Set initial is_visible
        self.set_visibility(self.is_visible)
        # Bind the opacity property to update the canvas
        self.bind(opacity=self._on_opacity,pos=self._update_canvas, size=self._update_canvas)
        self.opacity = opacity  # Trigger the opacity bindinge canvas to update



    @property
    def center_x(self):
        return self.x + self.radius

    @property
    def center_y(self):
        return self.y + self.radius




    def _update_canvas(self, *args):
        # # Update circle position and size
        # self.background_rect.pos = self.pos
        # self.background_rect.size = self.size

        self.circle.pos = (self.x, self.y)
        self.circle.size = (self.radius * 2, self.radius * 2)
        #
        # Update border if it exists
        if self.border_thickness>0:
            self.border.circle = (self.center_x, self.center_y, self.radius-self.border_thickness)

        print(self.size)
        print(self.radius)

        self.size = [self.radius*2, self.radius*2]
        print(self.size)




    def set_radius(self, radius):
        """Update the radius of the circle."""
        self.radius = radius
        self.circle.size = (self.radius * 2, self.radius * 2)

        if self.border_thickness>0:
            self.border.circle = (self.center_x, self.center_y, self.radius)

    def set_position(self, x, y):
        """Update the position of the circle."""
        self.pos = (x, y)
        self.circle.pos = self.pos

        if self.border_thickness>0:
            self.border.circle = (self.center_x, self.center_y, self.radius)

    def set_bg_color(self, bg_color):
        """Update the bg_color of the circle."""
        self.bg_color = bg_color
        self.color_instruction.rgba = self.bg_color

    def set_border_color(self, border_color):
        """Update the color of the border."""
        self.border_color = border_color
        if self.border_thickness>0:
            self.border_color_instruction.rgba = self.border_color

    def set_border_thickness(self, border_thickness):
        """Update the width of the border."""
        self.border_thickness = border_thickness
        if self.border_thickness>0:
            self.border.width = self.border_thickness

    def set_visibility(self, is_visible):
        """Show or hide the circle."""
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

    # Create a circle with a border
    circle = PvCircle(window, 50, 50, 75,
                         bg_color=(0.5, 0.5, 0, 1), border_color=(0, 0.5, 0.5, 1), border_thickness=2, is_visible=True,
                         opacity=1,tag="circle1")
    circle2 = PvCircle(window, 50, 200, 75,
                         bg_color=(0.5, 0, 0.5, 1), border_color=(0, 0.5, 0.5, 1), border_thickness=2, is_visible=True,
                         opacity=1, tag="circle1")
    window.show()
