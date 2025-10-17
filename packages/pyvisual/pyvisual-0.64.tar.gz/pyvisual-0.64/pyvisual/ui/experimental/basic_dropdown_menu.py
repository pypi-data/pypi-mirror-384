from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button as KivyButton
from kivy.core.text import LabelBase
from kivy.core.window import Window as KivyWindow
from kivy.graphics import Line, Color


class BasicDropDown:
    def __init__(
        self,
        window,
        x, y,
        width=200,
        height=40,
        text="Select",
        items=None,
        font="Roboto",
        font_size=16,
        font_color=(0, 0, 0, 1),
        idle_color=(0.9, 0.9, 0.9, 1),
        hover_color=(1, 1, 1, 1),
        clicked_color=(0.8, 0.8, 0.8, 1),
        item_background_color=(0.95, 0.95, 0.95, 1),
        text_alignment="center",  # New parameter
        padding=(10, 10),  # New parameter
        border_color=(0, 0, 0, 1),
        border_thickness=1,
        on_click=None,
        on_select=None,
        visibility=True,
        disabled=False,
        disabled_opacity=0.3,
        item_idle_opacity=1.0,
        item_hover_opacity=0.8
    ):
        """
        A basic DropDown menu using Kivy's built-in DropDown widget.

        :param text_alignment: Text alignment ('left', 'center', 'right').
        :param padding: Padding (x, y) around the text.
        """
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.text = text
        self.font = font
        self.font_size = font_size
        self.font_color = font_color
        self.idle_color = idle_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.item_background_color = item_background_color
        self.text_alignment = text_alignment
        self.padding = padding
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.on_click = on_click
        self.on_select = on_select
        self.items = items if items is not None else []
        self.disabled = disabled
        self.disabled_opacity = disabled_opacity
        self.visibility = visibility
        self.item_idle_opacity = item_idle_opacity
        self.item_hover_opacity = item_hover_opacity

        # Register a custom font if provided as a file
        if self.font.endswith((".ttf", ".otf")):
            LabelBase.register(name="CustomFont", fn_regular=self.font)
            self.font_name = "CustomFont"
        else:
            self.font_name = self.font

        # Create the main trigger button for the dropdown
        self.main_button = KivyButton(
            text=self.text,
            size=(self.width, self.height),
            pos=(self.x, self.y),
            background_normal='',
            background_down='',
            background_color=self.idle_color,
            color=self.font_color,
            font_name=self.font_name,
            font_size=self.font_size,
            markup=True,
            size_hint=(None, None),
            text_size=(self.width - 2 * self.padding[0], None),  # Set text size to control alignment
            halign=self.text_alignment,  # Apply text alignment
            valign="middle"  # Vertical alignment always in the middle
        )

        # Draw border for the main button
        self._add_border(self.main_button)

        # Create the dropdown widget
        self.dropdown = DropDown(auto_dismiss=False)
        self.item_buttons = []  # Keep track of item buttons
        self._populate_dropdown()

        # Bind the main button's 'on_release' (click) to open/close the dropdown if not disabled
        self.main_button.bind(on_release=self._toggle_dropdown)
        KivyWindow.bind(on_touch_down=self._on_touch_down)

        # Mouse tracking for hover effect
        KivyWindow.bind(mouse_pos=self._on_mouse_pos)

        # Apply visibility and disabled states
        self.set_visibility(self.visibility)
        self.set_disabled(self.disabled)

        window.add_widget(self.main_button)

    def _populate_dropdown(self):
        """Populate the dropdown with items."""
        for item in self.items:
            btn = KivyButton(
                text=item,
                size_hint_y=None,
                height=self.height,
                background_normal='',
                background_down='',
                background_color=self.item_background_color,
                color=self.font_color,
                font_name=self.font_name,
                font_size=self.font_size,
                markup=True,
                opacity=self.item_idle_opacity,
                text_size=(self.width - 2 * self.padding[0], None),  # Set text size to control alignment
                halign=self.text_alignment,  # Apply text alignment
                valign="middle"  # Vertical alignment always in the middle
            )
            btn.bind(on_release=self._select_item)
            self._add_border(btn)
            self.dropdown.add_widget(btn)
            self.item_buttons.append(btn)

    def _add_border(self, widget):
        """Add a border around the given widget and ensure it updates with size/pos changes."""
        with widget.canvas.before:
            c = Color(*self.border_color)
            l = Line(width=self.border_thickness)

        def update_line(*args):
            # Update the rectangle coordinates whenever widget size or position changes
            l.rectangle = (widget.x, widget.y, widget.width, widget.height)

        # Bind the update function to size and position changes
        widget.bind(pos=update_line, size=update_line)
        # Initial update
        update_line()

    def _on_mouse_pos(self, window, pos):
        """Handle hover effects over the main button and items."""
        if not self.disabled and self.visibility:
            # Hover effect on main button
            if self._is_hovering_main(pos):
                if self.dropdown.attach_to is self.main_button:
                    # If dropdown is open, main button is "clicked"
                    self._update_main_button_color(self.clicked_color)
                else:
                    self._update_main_button_color(self.hover_color)
            else:
                # Idle if not hovering and not clicked
                if self.dropdown.attach_to is self.main_button:
                    self._update_main_button_color(self.clicked_color)
                else:
                    self._update_main_button_color(self.idle_color)

            # Hover effect on item buttons
            if self.dropdown.attach_to is self.main_button:
                # The dropdown is open, so we check if hovering over items
                for btn in self.item_buttons:
                    if self._is_hovering_item(btn, pos):
                        btn.opacity = self.item_hover_opacity
                    else:
                        btn.opacity = self.item_idle_opacity

    def _toggle_dropdown(self, instance):
        """Open or close the dropdown when the main button is clicked."""
        if not self.disabled and self.visibility:
            # Invoke on_click callback if provided
            if self.on_click:
                self.on_click(self)

            if self.dropdown.attach_to is None:
                # Open the dropdown
                self.dropdown.open(self.main_button)
                self._update_main_button_color(self.clicked_color)
            else:
                # Close the dropdown
                self._close_dropdown()

    def _on_touch_down(self, window, touch):
        """Close the dropdown if a click occurs outside of it."""
        if not self.dropdown.attach_to:
            return

        # Check if touch is outside the main button and dropdown items
        if not self._is_hovering_main(touch.pos) and not any(
            self._is_hovering_item(btn, touch.pos) for btn in self.item_buttons
        ):
            self._close_dropdown()

    def _close_dropdown(self):
        """Close the dropdown."""
        self.dropdown.dismiss()
        self._update_main_button_color(
            self.hover_color if self._is_hovering_main(KivyWindow.mouse_pos) else self.idle_color
        )

    def _select_item(self, instance):
        """Handle item selection."""
        selected_text = instance.text
        self.dropdown.dismiss()
        self.main_button.text = selected_text
        # Change button state based on hover after closing
        self._update_main_button_color(
            self.hover_color if self._is_hovering_main(KivyWindow.mouse_pos) else self.idle_color
        )
        # Invoke on_select callback if provided
        if self.on_select:
            self.on_select(selected_text)

    def _update_main_button_color(self, color):
        """Update main button's background color."""
        self.main_button.background_color = color

    def _is_hovering_main(self, pos):
        """Check if the mouse is over the main button."""
        return (self.main_button.x <= pos[0] <= self.main_button.x + self.main_button.width and
                self.main_button.y <= pos[1] <= self.main_button.y + self.main_button.height)

    def _is_hovering_item(self, btn, pos):
        """Check if the mouse is over a given item button."""
        btn_pos = btn.to_window(btn.x, btn.y)
        return (btn_pos[0] <= pos[0] <= btn_pos[0] + btn.width and
                btn_pos[1] <= pos[1] <= btn_pos[1] + btn.height)

    def set_visibility(self, visibility):
        """Show or hide the dropdown main button."""
        self.visibility = visibility
        if self.visibility:
            self.main_button.opacity = self.disabled_opacity if self.disabled else 1
        else:
            self.main_button.opacity = 0

    def set_disabled(self, disabled):
        """Enable or disable the dropdown."""
        self.disabled = disabled
        self.main_button.opacity = self.disabled_opacity if self.disabled and self.visibility else (1 if self.visibility else 0)


if __name__ == "__main__":
    import pyvisual as pv
    window = pv.Window()

    def main_button_clicked(dd_instance):
        print("Main button clicked:", dd_instance.main_button.text)

    def item_selected(item_text):
        print("Selected item:", item_text)

    dropdown = BasicDropDown(
        window=window,
        x=300, y=300,
        width=200, height=40,
        text="File",
        items=["Option 1", "Option 2", "Option 3"],
        font_size=18,
        on_click=main_button_clicked,
        on_select=item_selected,
        visibility=True,
        disabled=False,
        item_idle_opacity=1.0,
        item_hover_opacity=0.5,
        font_color=(0.2, 0.2, 0.2, 1),
        idle_color=(0.9, 0.9, 0.9, 1),
        hover_color=(0.8, 0.8, 0.8, 1),
        clicked_color=(0.9, 0.9, 0.9, 1),
        border_color=(0, 0, 0, 0),
        border_thickness=0,
        item_background_color=(0.85, 0.85, 0.85, 1),
        text_alignment="center",  # New: left alignment
        padding=(0, 0)  # New: Add padding
    )

    window.show()
