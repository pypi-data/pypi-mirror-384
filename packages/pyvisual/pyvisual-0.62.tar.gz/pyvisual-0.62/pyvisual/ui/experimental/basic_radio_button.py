import os
from kivy.uix.widget import Widget
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.uix.label import Label
from kivy.core.text import LabelBase
from kivy.core.window import Window


class BasicRadioButton(Widget):
    def __init__(self, window, x, y, items=None, size=30, padding=4, spacing=10,
                 orientation='vertical', visibility=True,
                 selected_color=(0.3, 0.8, 0.3, 1), unselected_color=(1, 1, 1, 1),
                 border_color=(0.3, 0.3, 0.3, 1), border_thickness=2,
                 on_select=None, on_click=None,
                 font_name='Roboto', font_color=(0, 0, 0, 1),
                 font_size=14, disabled=False, disabled_opacity=0.3,
                 text_position='right', text_padding=5,
                 radius=0):
        """
        A BasicRadioButton group that creates a series of rounded radio buttons with optional text.

        :param window: The window (layout) where the radio group will be added.
        :param x, y: Position of the top-left corner of the radio group.
        :param items: A list of option labels for the radio buttons.
        :param size: The width/height of each radio button (square).
        :param padding: Padding between the radio button border and the inner area.
        :param spacing: Spacing between radio buttons.
        :param orientation: 'vertical' or 'horizontal' layout.
        :param visibility: Initial visibility of the group.
        :param selected_color: Color of a selected radio button inner area.
        :param unselected_color: Color of an unselected radio button inner area.
        :param border_color: Border color of the radio button.
        :param border_thickness: Thickness of the border line.
        :param on_select: Callback when a radio button is selected (on_select(selected_text)).
        :param on_click: Callback when any radio button is clicked (on_click(instance, selected_text)).
        :param font_name: Font name or path for label text.
        :param font_color: Color of the label text (r, g, b, a).
        :param font_size: Font size of the label text.
        :param disabled: Whether the radio group is initially disabled.
        :param disabled_opacity: Opacity when disabled.
        :param text_position: Position of the text relative to each button ('left', 'right', 'top', 'bottom', 'none').
        :param text_padding: Padding between the radio button and the text.
        :param radius: Corner radius of the rounded radio buttons.
        """
        super().__init__()
        self.size_hint = (None, None)
        self.items = items if items is not None else []
        self.size_each = size
        self.padding = padding
        self.spacing = spacing
        self.orientation = orientation
        self.visibility = visibility
        self.selected_color = selected_color
        self.unselected_color = unselected_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.on_select = on_select
        self.on_click = on_click
        self.font_name = font_name
        self.font_color = font_color
        self.font_size = font_size
        self.disabled = disabled
        self.disabled_opacity = disabled_opacity
        self.text_position = text_position.lower()
        self.text_padding = text_padding
        self.radius = radius

        # Set the widget position
        self.pos = (x, y)

        # Register font if needed
        if os.path.isfile(self.font_name):
            LabelBase.register(name='CustomFont', fn_regular=self.font_name)
            self.font_name_to_use = 'CustomFont'
        else:
            self.font_name_to_use = self.font_name

        # Track radio button states
        self.radio_buttons = []
        self.selected_index = None

        self._create_radio_buttons()

        window.add_widget(self)
        self.set_visibility(self.visibility)
        self.set_disabled(self.disabled)

        self.bind(pos=self._redraw_all, size=self._redraw_all)

    def _create_radio_buttons(self):
        """Create the radio buttons and their labels."""
        self.canvas.clear()
        total_width, total_height = self._calculate_total_size()
        self.size = (total_width, total_height)

        # We position from self.pos downward (if vertical) or rightward (if horizontal)
        current_x, current_y = self.pos

        with self.canvas:
            for i, text in enumerate(self.items):
                if self.orientation == 'vertical':
                    btn_x = current_x
                    btn_y = current_y - i * (self.size_each + self.spacing)
                else:
                    btn_x = current_x + i * (self.size_each + self.spacing)
                    btn_y = current_y

                # Draw border
                Color(*self.border_color)
                border = Line(rounded_rectangle=(btn_x, btn_y, self.size_each, self.size_each, self.radius),
                              width=self.border_thickness)

                # Draw inner area with a separate color instruction
                color_inst = Color(*self.unselected_color)
                rounded_rect = RoundedRectangle(pos=(btn_x + self.padding, btn_y + self.padding),
                                                size=(
                                                self.size_each - 2 * self.padding, self.size_each - 2 * self.padding),
                                                radius=[self.radius])

                label = None
                if text and self.text_position != 'none':
                    label = Label(text=text,
                                  font_name=self.font_name_to_use,
                                  color=self.font_color,
                                  font_size=self.font_size,
                                  size_hint=(None, None))
                    label.texture_update()
                    label.size = label.texture_size
                    lx, ly = self._calculate_label_position(btn_x, btn_y, label.size)
                    label.pos = (lx, ly)
                    Window.add_widget(label)

                self.radio_buttons.append({
                    'index': i,
                    'text': text,
                    'is_selected': False,
                    'border': border,
                    'rect': rounded_rect,
                    'color_inst': color_inst,
                    'label': label,
                    'pos': (btn_x, btn_y)
                })

    def _calculate_total_size(self):
        count = len(self.items)
        if count == 0:
            return (0, 0)
        if self.orientation == 'vertical':
            total_width = self.size_each
            total_height = self.size_each + (count - 1) * (self.size_each + self.spacing)
        else:
            total_width = self.size_each + (count - 1) * (self.size_each + self.spacing)
            total_height = self.size_each
        return (total_width, total_height)

    def _calculate_label_position(self, bx, by, label_size):
        label_w, label_h = label_size
        if self.text_position == 'left':
            lx = bx - self.text_padding - label_w
            ly = by + (self.size_each - label_h) / 2
        elif self.text_position == 'right':
            lx = bx + self.size_each + self.text_padding
            ly = by + (self.size_each - label_h) / 2
        elif self.text_position == 'top':
            lx = bx + (self.size_each - label_w) / 2
            ly = by + self.size_each + self.text_padding
        elif self.text_position == 'bottom':
            lx = bx + (self.size_each - label_w) / 2
            ly = by - self.text_padding - label_h
        else:
            lx, ly = (bx, by)
        return lx, ly

    def on_touch_down(self, touch):
        if self.disabled:
            return False

        for btn_data in self.radio_buttons:
            bx, by = btn_data['pos']
            if (bx <= touch.x <= bx + self.size_each and
                    by <= touch.y <= by + self.size_each):
                # Clicked this radio button
                self._select_button(btn_data['index'])
                if self.on_click:
                    self.on_click(self, btn_data['text'])
                return True

        return super().on_touch_down(touch)

    def _select_button(self, index):
        if self.selected_index == index:
            return

        if self.selected_index is not None:
            old_btn = self.radio_buttons[self.selected_index]
            self._update_button_appearance(old_btn, selected=False)

        new_btn = self.radio_buttons[index]
        self._update_button_appearance(new_btn, selected=True)
        self.selected_index = index

        if self.on_select:
            self.on_select(new_btn['text'])

    def _update_button_appearance(self, btn_data, selected):
        btn_data['is_selected'] = selected
        c = self.selected_color if selected else self.unselected_color
        btn_data['color_inst'].rgba = c

    def _redraw_all(self, *args):
        self._reposition_buttons()

    def _reposition_buttons(self):
        total_width, total_height = self._calculate_total_size()
        self.size = (total_width, total_height)
        current_x, current_y = self.pos

        for i, btn_data in enumerate(self.radio_buttons):
            if self.orientation == 'vertical':
                btn_x = current_x
                btn_y = current_y - i * (self.size_each + self.spacing)
            else:
                btn_x = current_x + i * (self.size_each + self.spacing)
                btn_y = current_y

            btn_data['pos'] = (btn_x, btn_y)
            btn_data['border'].rounded_rectangle = (btn_x, btn_y, self.size_each, self.size_each, self.radius)

            btn_data['rect'].pos = (btn_x + self.padding, btn_y + self.padding)
            btn_data['rect'].size = (self.size_each - 2 * self.padding, self.size_each - 2 * self.padding)
            btn_data['rect'].radius = [self.radius]

            if btn_data['label']:
                lx, ly = self._calculate_label_position(btn_x, btn_y, btn_data['label'].size)
                btn_data['label'].pos = (lx, ly)

    def set_visibility(self, visibility):
        self.visibility = visibility
        if self.visibility:
            self.opacity = self.disabled_opacity if self.disabled else 1
            for btn_data in self.radio_buttons:
                if btn_data['label']:
                    lc = list(btn_data['label'].color)
                    lc[3] = self.opacity
                    btn_data['label'].color = tuple(lc)
        else:
            self.opacity = 0
            for btn_data in self.radio_buttons:
                if btn_data['label']:
                    lc = list(btn_data['label'].color)
                    lc[3] = 0
                    btn_data['label'].color = tuple(lc)

    def set_disabled(self, disabled):
        self.disabled = disabled
        new_opacity = self.disabled_opacity if self.disabled else 1
        self.opacity = new_opacity
        for btn_data in self.radio_buttons:
            if btn_data['label']:
                lc = list(btn_data['label'].color)
                lc[3] = new_opacity
                btn_data['label'].color = tuple(lc)

    def set_items(self, items):
        self.items = items
        # Remove old labels
        for btn_data in self.radio_buttons:
            if btn_data['label']:
                Window.remove_widget(btn_data['label'])
        self.radio_buttons.clear()
        self.selected_index = None
        self._create_radio_buttons()

    def set_text_properties(self, font_name=None, font_color=None, font_size=None):
        if font_name:
            if os.path.isfile(font_name):
                LabelBase.register(name='CustomFont', fn_regular=font_name)
                self.font_name_to_use = 'CustomFont'
            else:
                self.font_name_to_use = font_name
            self.font_name = font_name

        if font_color:
            self.font_color = font_color

        if font_size:
            self.font_size = font_size

        for btn_data in self.radio_buttons:
            if btn_data['label']:
                btn_data['label'].font_name = self.font_name_to_use
                btn_data['label'].color = self.font_color
                btn_data['label'].font_size = self.font_size
                btn_data['label'].texture_update()
                btn_data['label'].size = btn_data['label'].texture_size
                bx, by = btn_data['pos']
                btn_data['label'].pos = self._calculate_label_position(bx, by, btn_data['label'].size)

    def set_text_position(self, position='right', text_padding=5):
        self.text_position = position.lower()
        self.text_padding = text_padding
        for btn_data in self.radio_buttons:
            if btn_data['label']:
                bx, by = btn_data['pos']
                lx, ly = self._calculate_label_position(bx, by, btn_data['label'].size)
                btn_data['label'].pos = (lx, ly)

    def set_radius(self, radius):
        self.radius = radius
        # Update all buttons
        for btn_data in self.radio_buttons:
            btn_data['border'].rounded_rectangle = (
            btn_data['pos'][0], btn_data['pos'][1], self.size_each, self.size_each, self.radius)
            btn_data['rect'].radius = [self.radius]

    def get_selected_text(self):
        if self.selected_index is not None:
            return self.radio_buttons[self.selected_index]['text']
        return None


if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()


    def on_select(selected_text):
        print("Selected:", selected_text)


    def on_click(radio_instance, selected_text):
        print("Clicked:", selected_text)


    # Example usage with radius
    radio_group = BasicRadioButton(
        window=window,
        x=100, y=400,
        items=["Option A", "Option B", "Option C"],
        size=20,
        padding=5,
        spacing=100,
        orientation='horizontal',
        on_select=on_select,
        on_click=on_click,
        text_position='left',
        text_padding=10,
        font_name='Roboto',
        font_color=(0, 0, 1, 1),
        font_size=16,
        visibility=True,
        disabled=False,
        radius=0,

    )


    window.show()
