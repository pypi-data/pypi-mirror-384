from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, ListProperty, StringProperty, OptionProperty
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.uix.label import Label

class BasicSlider(Widget):
    min_value = NumericProperty()
    max_value = NumericProperty()
    current_value = NumericProperty()
    bar_color = ListProperty()
    background_color = ListProperty()
    knob_shape = OptionProperty('circle', options=['circle', 'rectangle'])
    knob_color = ListProperty()
    show_text = StringProperty()
    font_name = StringProperty()
    font_size = NumericProperty()
    font_color = ListProperty()
    padding = NumericProperty()
    knob_radius = NumericProperty()
    knob_width = NumericProperty()
    knob_height = NumericProperty()

    def __init__(self, window, x, y, width=200, height=30,
                 min_value=0, max_value=100, current_value=0,
                 bar_color=[0.2, 0.6, 0.9, 0.8],
                 background_color=[0.9, 0.9, 0.9, 1],
                 knob_shape='circle', knob_color=[1, 0, 0, 1],
                 knob_radius=None, knob_width=None, knob_height=None,
                 show_text='center', font_name='Roboto', font_size=14, font_color=[0.5, 0.5, 0.5, 1],
                 padding=0,
                 visibility=True, disabled=False, disabled_opacity=0.3, tag=None,
                 **kwargs):
        super().__init__(**kwargs)
        self.window = window
        self.pos = (x, y)
        self.size = (width, height)
        self.size_hint = (None, None)
        self.tag = tag

        # Initialize properties with input parameters
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = current_value
        self.bar_color = bar_color
        self.background_color = background_color
        self.knob_shape = knob_shape.lower()
        self.knob_color = knob_color
        self.show_text = show_text
        self.font_name = font_name
        self.font_size = font_size
        self.font_color = font_color
        self.padding = padding  # Padding can be negative or positive
        self.disabled = disabled  # Initialize disabled state
        self.disabled_opacity = disabled_opacity

        # Set default knob sizes if not provided
        if self.knob_shape == 'circle':
            if knob_radius is None:
                self.knob_radius = self.height / 2
            else:
                self.knob_radius = knob_radius
            # For circle, width and height are diameter
            self.knob_width = self.knob_height = self.knob_radius * 2
        else:
            if knob_width is None:
                self.knob_width = self.height
            else:
                self.knob_width = knob_width
            if knob_height is None:
                self.knob_height = self.height
            else:
                self.knob_height = knob_height

        # Draw the slider
        with self.canvas:
            # Background
            self.bg_color_instruction = Color(rgba=self.background_color)
            self.bg_rect = Rectangle(pos=self.pos, size=self.size)

            # Bar
            self.bar_color_instruction = Color(rgba=self.bar_color)
            self.bar_rect = Rectangle(pos=self.pos, size=(0, self.height))

            # Knob
            self.knob_color_instruction = Color(rgba=self.knob_color)
            if self.knob_shape == 'circle':
                self.knob = Ellipse(pos=self.pos, size=(self.knob_width, self.knob_height))
            else:
                self.knob = Rectangle(pos=self.pos, size=(self.knob_width, self.knob_height))

        # Create the Label to display the current value
        self.value_label = Label(
            text=str(int(self.current_value)),
            font_name=self.font_name,
            font_size=self.font_size,
            color=self.font_color,
            size_hint=(None, None),
            halign='left',  # Will adjust based on alignment
            valign='middle',
        )

        # Add the label to the widget
        self.add_widget(self.value_label)

        # Bind properties to update methods
        self.bind(pos=self.update_all,
                  size=self.update_all,
                  current_value=self.update_current_value,
                  bar_color=self.update_bar_color,
                  background_color=self.update_background_color,
                  knob_color=self.update_knob_color,
                  knob_shape=self.update_knob_shape,
                  show_text=self.update_text_alignment,
                  font_name=self.update_font_properties,
                  font_size=self.update_font_properties,
                  font_color=self.update_font_properties,
                  padding=self.update_padding,
                  knob_radius=self.update_knob_size,
                  knob_width=self.update_knob_size,
                  knob_height=self.update_knob_size)

        # Initial updates
        self.update_all()

        self.visibility = visibility  # Initialize visibility state
        self.set_visibility(self.visibility)
        self.set_disabled(self.disabled)
        # Add the widget to the window
        window.add_widget(self)

    def update_all(self, *args):
        self.update_rectangles()
        self.update_label_properties()

    def update_rectangles(self, *args):
        # Update the positions and sizes of the rectangles
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size

        # Update bar size
        if self.max_value != self.min_value:
            relative_value = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        else:
            relative_value = 0
        bar_width = relative_value * self.width
        self.bar_rect.pos = self.pos
        self.bar_rect.size = (bar_width, self.height)

        # Update knob position
        knob_x = self.pos[0] + bar_width - self.knob_width / 2
        knob_y = self.pos[1] + (self.height - self.knob_height) / 2
        self.knob.pos = (knob_x, knob_y)
        # Adjust knob size if necessary
        if self.knob_shape == 'circle':
            self.knob.size = (self.knob_radius * 2, self.knob_radius * 2)
        else:
            self.knob.size = (self.knob_width, self.knob_height)

    def update_label_properties(self, *args):
        alignment = self.show_text.lower()
        padding = self.padding

        # Base label position and size
        label_x, label_y = self.pos
        label_width, label_height = self.size

        if alignment == 'left':
            self.value_label.halign = 'left'

            if padding >= 0:
                # Positive padding moves text right
                self.value_label.pos = (label_x + padding, label_y)
                self.value_label.size = (label_width - padding, label_height)
            else:
                # Negative padding moves text left; extend label width
                self.value_label.pos = (label_x + padding, label_y)
                self.value_label.size = (label_width + abs(padding), label_height)
        elif alignment == 'center':
            self.value_label.halign = 'center'
            self.value_label.pos = (label_x, label_y)
            self.value_label.size = (label_width, label_height)
            padding = 0  # Ignore padding for center alignment
        elif alignment == 'right':
            self.value_label.halign = 'right'

            if padding >= 0:
                # Positive padding moves text left
                self.value_label.pos = (label_x, label_y)
                self.value_label.size = (label_width - padding, label_height)
            else:
                # Negative padding moves text right; extend label width
                self.value_label.pos = (label_x - padding, label_y)
                self.value_label.size = (label_width + abs(padding), label_height)
        else:
            self.value_label.text = ''  # Hide text if 'none' or invalid value

        # Set text size to label size
        self.value_label.text_size = self.value_label.size
        # Set padding
        self.value_label.padding = (0, 0, 0, 0)

        self.value_label.texture_update()

    def update_current_value(self, *args):
        # Ensure current value is within min and max
        self.current_value = max(self.min_value, min(self.current_value, self.max_value))
        # Update bar and knob positions
        self.update_rectangles()
        # Update label text
        if self.show_text.lower() != 'none':
            self.value_label.text = str(int(self.current_value))
        else:
            self.value_label.text = ''
        # Update label properties
        self.update_label_properties()

    def update_bar_color(self, *args):
        # Update the color of the progress bar
        self.bar_color_instruction.rgba = self.bar_color

    def update_background_color(self, *args):
        # Update the background color
        self.bg_color_instruction.rgba = self.background_color

    def update_knob_color(self, *args):
        # Update the knob color
        self.knob_color_instruction.rgba = self.knob_color

    def update_knob_shape(self, *args):
        # Remove old knob
        self.canvas.remove(self.knob)
        # Add new knob with updated shape
        if self.knob_shape == 'circle':
            self.knob = Ellipse(pos=self.knob.pos, size=self.knob.size)
        else:
            self.knob = Rectangle(pos=self.knob.pos, size=self.knob.size)
        self.canvas.add(self.knob_color_instruction)
        self.canvas.add(self.knob)
        # Update positions
        self.update_rectangles()

    def update_knob_size(self, *args):
        # Update knob size based on the shape
        if self.knob_shape == 'circle':
            if self.knob_radius is None:
                self.knob_radius = self.height / 2
            self.knob_width = self.knob_height = self.knob_radius * 2
        else:
            if self.knob_width is None:
                self.knob_width = self.height
            if self.knob_height is None:
                self.knob_height = self.height
        # Update rectangles
        self.update_rectangles()

    def update_text_alignment(self, *args):
        # Update label properties when alignment changes
        self.update_label_properties()

    def update_font_properties(self, *args):
        # Update font properties
        self.value_label.font_name = self.font_name
        self.value_label.font_size = self.font_size
        self.value_label.color = self.font_color
        self.value_label.texture_update()

        # Update label properties
        self.update_label_properties()

    def update_padding(self, *args):
        # Update label properties when padding changes
        self.update_label_properties()

    def set_value(self, value):
        """Set the current value of the slider."""
        if not self.disabled:
            self.current_value = value

    def get_value(self):
        """Get the current value of the slider."""
        return self.current_value

    def on_touch_down(self, touch):
        if not self.disabled and self.collide_point(*touch.pos):
            # Update value based on touch position
            self.update_value_from_touch(touch)
            touch.grab(self)
            return True  # Event is handled
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if not self.disabled and touch.grab_current is self:
            # Update value based on touch position
            self.update_value_from_touch(touch)
            return True  # Event is handled
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            return True  # Event is handled
        return super().on_touch_up(touch)

    def update_value_from_touch(self, touch):
        x = touch.x
        # Calculate relative position
        relative_x = (x - self.pos[0]) / self.width
        # Clamp between 0 and 1
        relative_x = max(0.0, min(1.0, relative_x))
        # Update current value
        self.current_value = self.min_value + relative_x * (self.max_value - self.min_value)
        # Trigger update
        self.update_current_value()

    def set_visibility(self, visibility):
        """Show or hide the image."""
        if visibility:
            self.opacity = self.disabled_opacity if self.disabled else 1
        else:
            self.opacity = 0
        self.visibility = visibility

    def set_disabled(self, disabled):
        """Enable or disable the slider."""
        self.disabled = disabled
        self.opacity = self.disabled_opacity if self.disabled else 1

if __name__ == "__main__":
    import pyvisual as pv
    window = pv.Window()
    # Create an instance of BasicSlider with right alignment and negative padding
    slider = BasicSlider(
        window=window,
        x=100,
        y=300,
        width=400,
        height=15,
        min_value=0,
        max_value=100,
        current_value=50,
        bar_color=[0.2, 0.6, 0.9, 0.8],
        background_color=[0.9, 0.9, 0.9, 1],
        knob_shape='circle',
        knob_color=[0.2, 0.6, 0.9, 1],
        knob_radius=13,
        show_text='right',        # 'left', 'center', 'right', or 'none'
        font_name='Roboto',
        font_size=18,
        font_color=[0.1, 0.1, 0.1, 1],
        padding=-20,              # Negative padding
        visibility=True,
        disabled=False
    )


    # Another slider with center alignment and negative padding
    slider2 = BasicSlider(
        window=window,
        x=100,
        y=250,
        width=400,
        height=15,
        min_value=0,
        max_value=100,
        current_value=75,
        bar_color=[0.2, 0.6, 0.9, 0.8],
        background_color=[0.9, 0.9, 0.9, 1],
        knob_shape='rectangle',
        knob_color=[0.2, 0.6, 0.9, 1],
        knob_width=15,
        knob_height=30,
        show_text='center',
        font_name='Roboto',
        font_size=18,
        font_color=[0.1, 0.1, 0.1, 1],
        padding=-50,              # Negative padding (ignored for center alignment)
        disabled=True
    )

    window.show()
