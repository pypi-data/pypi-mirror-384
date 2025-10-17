from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button as KivyButton
from kivy.uix.boxlayout import BoxLayout
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.clock import Clock

class BasicMenuBar:
    def __init__(
            self,
            window,
            x, y,
            menu_button_width=150,
            menu_button_height=50,
            menu_item_width=150,
            menu_item_height=50,
            alignment="center",
            menus=None,
            font="Roboto",
            font_size=16,
            font_color=(0, 0, 0, 1),
            idle_color=(0.9, 0.9, 0.9, 1),
            hover_color=(0.9, 0.9, 0.9, 1),
            clicked_color=(0.8, 0.8, 0.8, 1),
            border_color=(0, 0, 0, 1),
            border_thickness=1,
            hover_opacity=1,
            item_hover_opacity=1,
            on_select=None,
    ):
        self.x = x
        self.y = y
        self.menu_button_width = menu_button_width
        self.menu_button_height = menu_button_height
        self.menu_item_width = menu_item_width
        self.menu_item_height = menu_item_height
        self.alignment = alignment
        self.menus = menus if menus is not None else {}
        self.font = font
        self.font_size = font_size
        self.font_color = font_color
        self.idle_color = idle_color
        self.hover_color = hover_color
        self.clicked_color = clicked_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.hover_opacity = hover_opacity
        self.item_hover_opacity = item_hover_opacity
        self.on_select = on_select

        if self.font.endswith((".ttf", ".otf")):
            LabelBase.register(name="CustomFont", fn_regular=self.font)
            self.font_name = "CustomFont"
        else:
            self.font_name = self.font

        self.menu_bar = BoxLayout(
            orientation="horizontal",
            size=(Window.width, self.menu_button_height),
            pos=(self.x, self.y),
            size_hint=(None, None)
        )

        self.dropdowns = {}
        self._populate_menus()
        if window:
            window.add_widget(self.menu_bar)
        self.opened_dropdown = None

    def _populate_menus(self):
        Window.bind(mouse_pos=self._on_mouse_move)

        for menu_name, items in self.menus.items():
            menu_button = KivyButton(
                text=menu_name,
                size=(self.menu_button_width, self.menu_button_height),
                size_hint=(None, None),
                background_normal='',
                background_down='',
                background_color=self.idle_color,
                color=self.font_color,
                font_name=self.font_name,
                font_size=self.font_size,
                markup=True
            )

            dropdown = DropDown()
            dropdown.container.width = self.menu_item_width  # Ensure dropdown width is set
            self._populate_dropdown(dropdown, menu_name, items)

            self.dropdowns[menu_name] = dropdown

            menu_button.bind(on_release=lambda btn, dd=dropdown: self._on_click(btn, dd))
            self.menu_bar.add_widget(menu_button)

    def _populate_dropdown(self, dropdown, parent_menu_name, items):
        for item in items:
            if isinstance(item, dict):
                submenu_name = list(item.keys())[0]
                submenu_items = item[submenu_name]

                submenu_button = KivyButton(
                    text=submenu_name + " >",
                    size_hint_y=None,
                    size=(self.menu_item_width, self.menu_item_height),
                    background_normal='',
                    background_down='',
                    background_color=self.idle_color,
                    color=self.font_color,
                    font_name=self.font_name,
                    font_size=self.font_size,
                    markup=True
                )

                submenu_dropdown = DropDown()
                submenu_dropdown.container.width = self.menu_item_width  # Ensure submenu dropdown width is set
                self._populate_dropdown(submenu_dropdown, submenu_name, submenu_items)

                submenu_button.bind(on_release=lambda btn, sd=submenu_dropdown: self._on_click(btn, sd))
                dropdown.add_widget(submenu_button)
            else:
                item_button = KivyButton(
                    text=item,
                    size_hint_y=None,
                    size=(self.menu_item_width, self.menu_item_height),
                    background_normal='',
                    background_down='',
                    background_color=self.idle_color,
                    color=self.font_color,
                    font_name=self.font_name,
                    font_size=self.font_size,
                    markup=True
                )
                item_button.bind(
                    on_release=lambda btn, pm=parent_menu_name, it=item: self._on_click(btn, pm, it)
                )
                dropdown.add_widget(item_button)

        dropdown.width = self.menu_item_width

    def _on_click(self, btn, *args):
        btn.background_color = self.clicked_color

        if len(args) == 2:
            parent_menu_name, item_name = args
            self._select_item(parent_menu_name, item_name)
        else:
            dropdown = args[0]

            if self.opened_dropdown and self.opened_dropdown != dropdown:
                self.opened_dropdown.dismiss()

            if not dropdown.attach_to:
                dropdown.open(btn)
                self.opened_dropdown = dropdown
            else:
                dropdown.dismiss()
                self.opened_dropdown = None

        Clock.schedule_once(lambda dt: self._reset_color(btn), 0.1)

    def _reset_color(self, btn):
        btn.background_color = self.idle_color

    def _on_mouse_move(self, window, pos):
        for button in self.menu_bar.children:
            if self._is_hovering(button, pos):
                button.background_color = self.hover_color
            else:
                button.background_color = self.idle_color

        for dropdown in self.dropdowns.values():
            for item_button in dropdown.container.children:
                if self._is_hovering(item_button, pos):
                    item_button.background_color = self.hover_color
                else:
                    item_button.background_color = self.idle_color

    def _is_hovering(self, widget, mouse_pos):
        if not widget.get_parent_window():
            return False
        widget_x, widget_y = widget.to_window(widget.x, widget.y)
        return (widget_x <= mouse_pos[0] <= widget_x + widget.width and
                widget_y <= mouse_pos[1] <= widget_y + widget.height)

    def _select_item(self, menu_name, item_name):
        if self.on_select:
            self.on_select(menu_name, item_name)

if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()

    def menu_item_selected(menu, item):
        print(f"Menu: {menu}, Selected Item: {item}")

    menu_bar = BasicMenuBar(
        window=window,
        x=0, y=550,

        menus={
            "File": ["New", "Open", "Save", "Exit"],
            "Edit": ["Find", "Redo", "Advanced"],
            "View": ["Zoom In", "Zoom Out", "Reset"],
        },
        font_size=14,
        hover_opacity=0.8,
        item_hover_opacity=0.6,
        clicked_color=(0.7, 0.7, 0.7, 1),
        on_select=menu_item_selected,
    )

    window.show()
