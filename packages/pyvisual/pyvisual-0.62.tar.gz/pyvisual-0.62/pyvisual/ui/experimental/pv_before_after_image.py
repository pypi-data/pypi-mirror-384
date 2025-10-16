from kivy.uix.widget import Widget
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Line, StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.properties import NumericProperty, StringProperty

class PvBeforeAfterImage(Widget):
    def __init__(self, container=None, x=0, y=0, width=400, height=300, before_image="", after_image="", scale=1.0):
        super().__init__(size_hint=(None, None))
        self.size_hint=(None, None)

        self.before_image_path = before_image
        self.after_image_path = after_image
        self.pos = (x, y)
        self.width = width * scale
        self.height = height * scale

        self.clip_position = self.width // 2  # Initial clip position (middle of the widget)

        # Add images to canvas
        with self.canvas:
            # Draw the "after" image in full
            self.after_image_rect = Rectangle(source=self.after_image_path, pos=self.pos, size=(self.width, self.height))

            # Stencil area for the "before" image
            StencilPush()
            self.before_clip_rect = Rectangle(pos=self.pos, size=(self.clip_position, self.height))
            StencilUse()

            # Draw the "before" image clipped by the stencil
            self.before_image_rect = Rectangle(source=self.before_image_path, pos=self.pos, size=(self.width, self.height))

            StencilUnUse()
            StencilPop()

            # Draw the draggable divider line
            Color(0.8, 0.8, 0.8, 0.7)
            self.line = Line(points=[self.pos[0] + self.clip_position, self.pos[1],
                                     self.pos[0] + self.clip_position, self.pos[1] + self.height], width=5)

        if container:
            container.add_widget(self)

        self.bind(pos=self._update_positions, size=self._update_positions)
        self.update()

    def update(self):
        """Update the position and size of the images and divider line."""
        self.after_image_rect.pos = self.pos
        self.after_image_rect.size = (self.width, self.height)

        self.before_image_rect.pos = self.pos
        self.before_image_rect.size = (self.width, self.height)

        self.before_clip_rect.pos = self.pos
        self.before_clip_rect.size = (self.clip_position, self.height)

        self.line.points = [self.pos[0] + self.clip_position, self.pos[1],
                            self.pos[0] + self.clip_position, self.pos[1] + self.height]

    def _update_positions(self, *args):
        self.update()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            self.clip_position = max(0, min(self.width, touch.x - self.pos[0]))
            self.update()
            return True
        return super().on_touch_move(touch)



if __name__ == "__main__":
    import pyvisual as pv
    # Initialize the PyVisual window
    window = pv.PvWindow(width=800, height=600, title="Before and After Image Viewer")

    # Add the before-after widget
    before_after = PvBeforeAfterImage(
        container=window,
        x=160,
        y=50,
        width=500,
        height=600,
        before_image="C:/Users\Murtaza Hassan\Desktop/before.png",
        after_image="C:/Users\Murtaza Hassan\Desktop/after.png",
        scale=1.0,
    )

    window.show()



