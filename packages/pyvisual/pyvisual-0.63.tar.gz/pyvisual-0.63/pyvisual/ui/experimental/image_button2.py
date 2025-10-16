import os
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window as KivyWindow
from kivy.uix.widget import Widget
from kivy.uix.image import Image

class ImageButton(Widget):
    def __init__(self, window, x=100, y=100, width=140, height=50, image_path=None,
                 opacity=1, hover_opacity=0.7, clicked_opacity=0.5, disabled_opacity=0.3,
                 is_visible=True, is_disabled=False,
                 on_hover=None, on_click=None, on_release=None, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (width, height)
        self.pos = (x, y)

        self.opacity = opacity
        self.hover_opacity = hover_opacity
        self.clicked_opacity = clicked_opacity
        self.disabled_opacity = disabled_opacity

        self.is_visible = is_visible
        self.is_disabled = is_disabled

        self.on_hover = on_hover
        self.on_click = on_click
        self.on_release = on_release

        self.is_pressed = False

        # Set image path
        self.image_path = image_path or os.path.join(os.path.dirname(__file__), 'default_image.png')

        # Add the image as a background
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, opacity)  # Ensure alpha starts with opacity
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

        self.image = Image(source=self.image_path, size=self.size, pos=self.pos)
        self.add_widget(self.image)

        # Bind position and size updates
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # Bind mouse position for hover detection
        KivyWindow.bind(mouse_pos=self.on_mouse_pos)

        # Add to the window
        self.window = window
        self.window.add_widget(self)

    def _update_canvas(self, *args):
        """Update the button's visuals."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.image.pos = self.pos
        self.image.size = self.size

    def on_mouse_pos(self, window, pos):

        if not self.is_disabled:
            if self.collide_point(*pos):
                if not self.is_pressed:
                    self.bg_color.a = self.hover_opacity  # Set hover opacity
                    if self.on_hover:
                        self.on_hover(self)
            else:
                self.bg_color.a = self.opacity  # Reset to idle state if not hovering

        # """Handle mouse hover events."""
        # if self.is_visible and not self.is_disabled and self.collide_point(*pos):
        #     if not self.is_pressed:
        #         self.bg_color.a = self.hover_opacity
        #         if self.on_hover:
        #             self.on_hover(self)
        # else:
        #     self.bg_color.a = self.opacity

    def on_touch_down(self, touch):
        self.bg_color.a = 0.2

        #
        # """Handle mouse click events."""
        # if self.collide_point(*touch.pos) and not self.is_disabled:
        #     self.is_pressed = True
        #     self.bg_color.a = self.clicked_opacity
        #     if self.on_click:
        #         self.on_click(self)
        #     return True
        # return super().on_touch_down(touch)
    #
    def on_touch_up(self, touch):
        self.bg_color.a = 0.2

    #     """Handle mouse release events."""
    #     if self.is_pressed:
    #         self.is_pressed = False
    #         if self.collide_point(*touch.pos) and not self.is_disabled:
    #             self.bg_color.a = self.hover_opacity
    #             if self.on_release:
    #                 self.on_release(self)
    #         else:
    #             self.bg_color.a = self.opacity
    #         return True
    #     return super().on_touch_up(touch)

    def update_color(self, alpha):
        """Update the background color's alpha and force a redraw."""
        self.canvas.before.clear()  # Clear the previous canvas instructions
        with self.canvas.before:
            self.bg_color = Color(1, 1, 1, alpha)  # Rebind the Color instruction
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

    def set_visibility(self, is_visible):
        """Set button visibility."""
        self.is_visible = is_visible
        self.opacity = 1 if self.is_visible else 0
        self.bg_color.a = self.opacity

    def set_disabled(self, is_disabled):
        """Enable or disable the button."""
        self.is_disabled = is_disabled
        self.bg_color.a = self.disabled_opacity if self.is_disabled else self.opacity

    def set_opacity(self, opacity):
        """Set button opacity."""
        self.opacity = opacity
        self.bg_color.a = self.opacity

    def add_to_layout(self, layout):
        """Add the button to a layout."""
        if self.parent is not None:
            self.parent.remove_widget(self)
        layout.add_widget(self)

if __name__ == "__main__":
    import pyvisual as pv

    # Create a pyvisual window
    window = pv.Window()

    # Create multiple buttons
    button1 = ImageButton(
        window=window, x=100, y=100, width=200, height=60, image_path="/pyvisual/assets/buttons/blue_round/idle.png",
        on_click=lambda btn: print("Button 1 clicked"),
        on_release=lambda btn: print("Button 1 released"),
        on_hover=lambda btn: print("Button 1 hovered")
    )

    button2 = ImageButton(
        window=window, x=320, y=100, width=200, height=60, image_path="/pyvisual/assets/buttons/blue_round/idle.png",
        on_click=lambda btn: print("Button 2 clicked"),
        on_release=lambda btn: print("Button 2 released"),
        on_hover=lambda btn: print("Button 2 hovered")
    )

    button3 = ImageButton(
        window=window, x=540, y=100, width=200, height=60, image_path="/pyvisual/assets/buttons/blue_round/idle.png",
        on_click=lambda btn: print("Button 3 clicked"),
        on_release=lambda btn: print("Button 3 released"),
        on_hover=lambda btn: print("Button 3 hovered")
        ,opacity=0.5
    )

    # Show the window
    window.show()
