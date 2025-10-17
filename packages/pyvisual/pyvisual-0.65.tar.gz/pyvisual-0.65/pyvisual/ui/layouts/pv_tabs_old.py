from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.graphics import Color, Rectangle, Line
import pyvisual as pv
from pyvisual.ui.inputs.pv_button import PvButton
from kivy.graphics.stencil_instructions import StencilPush, StencilUse, StencilUnUse, StencilPop
from kivy.clock import Clock


class PvTabs(Widget):
    def __init__(self, container, x=100, y=400, content_area_width=500, content_area_height=200,
                 # Button_Area
                 button_width=120, button_height=40, bg_color_button_area=(0.2, 0.6, 0.8, 0),
                 active_color=(0.13, 0.73, 0.73, 1), non_active_color=(0.92, 0.93, 0.94, 1),
                 active_font_color=(1, 1, 1, 1), non_active_font_color=(0.38, 0.68, 0.68, 1),
                 button_corner_radius=(10, 10, 0, 0), padding=(0, 0, 0, 0), spacing=10,
                 default_tab_index=0, line_color=(0.13, 0.73, 0.73, 1), line_thickness=0,
                 tab_position="top",
                 # Content_Area
                 bg_color_content_area=(1, 1, 0, 1), border_color=(0.88, 0.88, 0.88, 1), border_thickness=None,
                 corner_radius=0,show_add_tab_button=True, on_tab_add=None,

                 **kwargs):
        super().__init__(**kwargs)

        self.container = container
        self.x = x
        self.y = y
        self.button_height = button_height
        self.content_area_width = content_area_width
        self.content_area_height = content_area_height
        self.tabs = []
        self.bg_color_button_area = bg_color_button_area
        self.bg_color_content_area = bg_color_content_area
        self.active_color = active_color
        self.non_active_color = non_active_color
        self.active_font_color = active_font_color
        self.non_active_font_color = non_active_font_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.button_corner_radius = button_corner_radius
        self.button_width = button_width
        self.corner_radius = corner_radius
        self.padding = padding
        self.spacing = spacing
        self.line_color = line_color
        self.line_thickness = line_thickness
        self.tab_position = tab_position

        self.on_tab_add = on_tab_add  # Store the callback function


        self.active_line = None  # Placeholder for the line below the active button
        self.active_tab = None  # Keeps track of the active tab
        self.show_add_tab_button = show_add_tab_button  # Store the flag

        self._set_tab_position()

        with self.button_area_layout.canvas.before:
            Color(*self.bg_color_button_area)  # Set background color
            self.top_bg = Rectangle(size=self.button_area_layout.size, pos=self.button_area_layout.pos)

        self.button_area_layout.bind(size=self._update_top_bg, pos=self._update_top_bg)
        self.button_area_layout.bind(size=self._set_tab_position, pos=self._set_tab_position)

        self._set_panel_position()

        with self.content_area_layout.canvas.before:
            # Push stencil for clipping content
            StencilPush()
            Rectangle(size=self.content_area_layout.size, pos=self.content_area_layout.pos)
            StencilUse()
            # Background color and rectangle
            Color(*self.bg_color_content_area)  # Set background color
            self.bottom_bg = Rectangle(size=self.content_area_layout.size, pos=self.content_area_layout.pos)

        with self.content_area_layout.canvas.after:
            StencilUnUse()
            StencilPop()
            # Draw the border after content clipping
            self._draw_borders()

        self.content_area_layout.bind(size=self._draw_borders, pos=self._draw_borders)

        self.content_area_layout.bind(size=self._update_bottom_bg, pos=self._update_bottom_bg)

        self.default_tab_index = default_tab_index

        if container:
            # Add layouts to the container
            container.add_widget(self.button_area_layout)
            container.add_widget(self.content_area_layout)

        # Schedule switching to the default tab after layout initialization
        Clock.schedule_once(lambda dt: self._initialize_default_tab())



    def _set_tab_position(self,*args, **kwargs):
        if self.tab_position == 'top':
            self.orientation = 'horizontal'
            self.button_area_width = self.button_width * len(self.tabs)
            self.button_area_height = self.button_height
            self.button_area_start_y = self.y - self.button_height - self.padding[1] - self.padding[3]
            self.button_area_start_x = self.x
            # Top BoxLayout for buttons
            self.button_area_layout = BoxLayout(
                pos=(self.button_area_start_x, self.button_area_start_y),
                size=(self.button_area_width, self.button_area_height),
                size_hint=(None, None),
                padding=self.padding,
                spacing=self.spacing,
                orientation=self.orientation,

            )

        elif self.tab_position == "left":
            self.orientation = 'vertical'
            self.button_area_start_x = self.x
            self.button_area_start_y = self.y - self.content_area_height - self.padding[1] - self.padding[3]
            self.total_height = self.button_height * len(self.tabs) + self.padding[1] + self.padding[2]
            self.button_area_layout = BoxLayout(
                pos=(self.button_area_start_x, self.button_area_start_y),
                size=(self.button_width, self.total_height),
                size_hint=(None, None),
                padding=self.padding,
                spacing=self.spacing,
                orientation=self.orientation
            )

        elif self.tab_position == "right":
            self.orientation = 'vertical'
            self.button_area_start_x = self.x + self.content_area_width + self.padding[0] + self.padding[2]
            self.button_area_start_y = self.y - self.content_area_height - self.padding[1] - self.padding[3]
            self.total_height = self.button_height * len(self.tabs) + self.padding[1] + self.padding[2]
            self.button_area_layout = BoxLayout(
                pos=(self.button_area_start_x, self.button_area_start_y),
                size=(self.button_width, self.total_height),
                size_hint=(None, None),
                padding=self.padding,
                spacing=self.spacing,
                orientation=self.orientation
            )

        elif self.tab_position == "bottom":
            self.orientation = 'horizontal'
            self.button_area_width = self.button_width * len(self.tabs)
            self.button_area_height = self.button_height
            self.button_area_start_y = self.y - self.content_area_height - self.button_height - self.padding[1] - \
                                       self.padding[3]
            self.button_area_start_x = self.x
            self.button_area_layout = BoxLayout(
                pos=(self.button_area_start_x, self.button_area_start_y),
                size=(self.button_area_width, self.button_area_height),
                size_hint=(None, None),
                padding=self.padding,
                spacing=self.spacing,
                orientation=self.orientation
            )
        # # Add the "+" button dynamically
        # self.add_tab_button = BasicButton(
        #     container=None,  # The button is added to the layout, not directly to the container
        #     x=0,  # Position will be handled by BoxLayout
        #     y=0,
        #     width=self.button_width,
        #     height=self.button_height,
        #     text="+",
        #     font_size=14,
        #     button_color=self.non_active_color,
        #     corner_radius=self.button_corner_radius,
        #     on_click=self._add_new_tab,  # Add a new tab when clicked
        #     font_color=self.non_active_font_color,
        #     pos_hint={"center_x": 0.5, "center_y": 0.5}  # Center-align
        #
        # )

    def _add_new_tab(self, *args):
        new_tab_name = f"Tab {len(self.tabs) + 1}"
        self.add_tab(new_tab_name)
        self.switch_tab(new_tab_name)

    def _set_panel_position(self):
        if self.tab_position == "top":
            self.orientation = 'horizontal'
            self.content_area_start_y = self.button_area_start_y - self.content_area_height
            self.content_area_layout = FloatLayout(
                pos=(self.button_area_start_x, self.content_area_start_y),
                size=(self.content_area_width, self.content_area_height),
                size_hint=(None, None)
            )

        elif self.tab_position == "left":
            self.orientation = 'vertical'
            self.content_area_start_x = self.x + self.button_width + self.padding[0] + self.padding[2]
            self.content_area_start_y = self.y - self.content_area_height
            self.content_area_layout = FloatLayout(
                pos=(self.content_area_start_x, self.content_area_start_y),
                size=(self.content_area_width, self.content_area_height),
                size_hint=(None, None)
            )

        elif self.tab_position == "right":
            self.orientation = 'vertical'
            self.content_area_start_x = self.x
            self.content_area_start_y = self.y - self.content_area_height
            self.content_area_layout = FloatLayout(
                pos=(self.content_area_start_x, self.content_area_start_y),
                size=(self.content_area_width, self.content_area_height),
                size_hint=(None, None)
            )

        elif self.tab_position == "bottom":
            self.orientation = 'horizontal'
            self.content_area_start_y = self.y - self.content_area_height
            self.content_area_layout = FloatLayout(
                pos=(self.button_area_start_x, self.content_area_start_y),
                size=(self.content_area_width, self.content_area_height),
                size_hint=(None, None)
            )

    def _initialize_default_tab(self):
        if self.tabs:
            default_tab_name = self.tabs[self.default_tab_index]["name"]
            self.switch_tab(default_tab_name)

    def _draw_borders(self, *args):
        """Draws borders with different thicknesses for each side."""
        # Clear existing border instructions
        self.content_area_layout.canvas.clear()
        if self.border_thickness:
            # Retrieve thickness for each side

            with self.content_area_layout.canvas.after:
                Color(*self.border_color)  # Set border color

                if isinstance(self.border_thickness, (int, float)):
                    if self.border_thickness > 0:
                        self.bottom_border = Line(rounded_rectangle=(self.content_area_layout.x, self.content_area_layout.y,
                                                                     self.content_area_layout.width,
                                                                     self.content_area_layout.height,
                                                                     self.corner_radius),
                                                  width=self.border_thickness)
                else:
                    top, right, bottom, left = self.border_thickness
                    print(f"Drawing borders with thicknesses: top={top}, right={right}, bottom={bottom}, left={left}")

                    # Top border
                    if top > 0:
                        print("Drawing top border")
                        Line(points=[self.content_area_layout.x, self.content_area_layout.top,
                                     self.content_area_layout.right, self.content_area_layout.top], width=top)

                    # Right border
                    if right > 0:
                        print("Drawing right border")
                        Line(points=[self.content_area_layout.right, self.content_area_layout.top,
                                     self.content_area_layout.right, self.content_area_layout.y], width=right)

                    # Bottom border
                    if bottom > 0:
                        print("Drawing bottom border")
                        Line(points=[self.content_area_layout.right, self.content_area_layout.y,
                                     self.content_area_layout.x, self.content_area_layout.y], width=bottom)

                    # Left border
                    if left > 0:
                        print("Drawing left border")
                        Line(points=[self.content_area_layout.x, self.content_area_layout.y,
                                     self.content_area_layout.x, self.content_area_layout.top], width=left)

    # def _update_bottom_border(self, instance, value):
    #     self._draw_borders()

    def add_tab(self, tab_name):
        # Create a new button for the tab
        button = PvButton(
            container=None,  # Add to the layout, not directly to the window
            x=0,  # Position is managed by the layout
            y=0,
            width=self.button_width,
            height=self.button_height,
            text=tab_name,
            font_size=14,
            button_color=self.non_active_color,
            corner_radius=self.button_corner_radius,
            on_click=lambda btn: self.switch_tab(btn.text),
            font_color=self.non_active_font_color
        )

        # Create a new FloatLayout for the tab's content
        tab_content = FloatLayout(
            size=(self.content_area_width, self.content_area_height),
            pos=self.content_area_layout.pos,
            size_hint=(None, None)
        )
        tab_content.active = False  # Custom attribute to track active state



        # Override `on_touch_down` to block events for inactive tabs
        def on_touch_down_override(instance, touch):
            if not instance.active:
                return False  # Ignore touch events for inactive tabs
            return super(FloatLayout, instance).on_touch_down(touch)

        tab_content.on_touch_down = on_touch_down_override.__get__(tab_content)

        # Store the tab information
        self.tabs.append({"name": tab_name, "button": button, "content": tab_content})

        # Add the tab content to the main content layout
        self.content_area_layout.add_widget(tab_content)

        # Rebuild the button area layout to ensure the "+" button remains at the right
        self.button_area_layout.clear_widgets()
        for tab in self.tabs:
            self.button_area_layout.add_widget(tab["button"])

        if self.show_add_tab_button:
            # Add the "+" button at the end with smaller dimensions
            self.add_tab_button = PvButton(
                container=None,  # The button is added to the layout, not directly to the window
                x=0,  # Position will be handled by BoxLayout
                y=0,  # Center vertically
                width=20,  # Smaller width
                height=20,  # Smaller height
                text="+",
                font_size=20,  # Slightly smaller font
                button_color=self.non_active_color,
                corner_radius=20,  # Rounded for distinction
                on_click=self._add_new_tab,  # Add a new tab when clicked
                font_color=self.active_font_color,
                pos_hint={"center_x": 0.5, "center_y": 0.5} , # Center-align
                bold=True,

            )
            self.button_area_layout.add_widget(self.add_tab_button)



        # Trigger the on_tab_add callback if it exists
        if self.on_tab_add:
            self.on_tab_add(self)

        # Set the default tab active
        if len(self.tabs) == self.default_tab_index + 1:
            self.switch_tab(tab_name)

    def add_to_tab(self, tab_name, widgets):
        # Find the tab by name and add the list of widgets to its content layout
        for tab in self.tabs:
            if tab["name"] == tab_name:
                for widget in widgets:
                    # Calculate relative position based on the tab's content layout
                    content_layout = tab["content"]
                    widget_x = widget.x + content_layout.x
                    widget_y = widget.y + content_layout.y
                    widget.pos = (widget_x, widget_y)
                    if isinstance(widget, pv.PvGroup):
                        content_layout.add_widget(widget.layout)
                    else:
                        content_layout.add_widget(widget)

    def switch_tab(self, tab_name):
        for tab in self.tabs:
            if tab["name"] == tab_name:
                tab["content"].opacity = 1  # Show selected tab
                tab["content"].active = True  # Enable events for active tab
                self.content_area_layout.remove_widget(tab["content"])
                self.content_area_layout.add_widget(tab["content"])  # Bring to front
                tab["button"].set_color(self.active_color)
                tab["button"].set_font_color(self.active_font_color)
                self.active_tab = tab  # Set the active tab

            else:
                tab["content"].opacity = 0  # Hide inactive tabs
                tab["content"].active = False  # Disable events for inactive tabs
                tab["button"].set_color(self.non_active_color)
                tab["button"].set_font_color(self.non_active_font_color)

    def _update_top_bg(self, instance, value):
        self.top_bg.size = instance.size
        self.top_bg.pos = instance.pos

    def _update_bottom_bg(self, instance, value):
        self.bottom_bg.size = instance.size
        self.bottom_bg.pos = instance.pos

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            print(f"Touch received by: {self}")
        return super().on_touch_down(touch)

    def get_active_tab_instance(self):
        """Returns the content (FloatLayout) of the active tab."""
        return self.active_tab["content"] if self.active_tab else None

    def get_active_tab_name(self):
        """Returns the name of the active tab."""
        return self.active_tab["name"] if self.active_tab else None


if __name__ == "__main__":
    window = pv.PvWindow()
    tabs = PvTabs(window, x=50, y=580, content_area_height=50,border_thickness=(1,0,0,0))

    tabs.add_tab("Tab 1")
    tabs.add_tab("Tab 2")
    tabs.add_tab("Tab 3")
    #
    # #
    tabs2 = PvTabs(window, x=50, y=500,button_height=40, content_area_width=500, content_area_height=50,
                 bg_color_button_area=(0.2, 0.6, 0.8, 0), bg_color_content_area=(1, 1, 0, 1),
                 active_color=(1, 1, 1, 1), non_active_color=(1, 1, 1, 1),
                 active_font_color=(0.28, 0.4, 1, 1), non_active_font_color=(0.68, 0.68, 0.68, 1),
                 default_tab_index=0, border_color=(0.88, 0.88, 0.88, 1), border_thickness=(1,0,0,0),
                 corner_radius=0,
                 button_corner_radius=(10, 10, 0, 0),
                 button_width=120,
                 padding=(0, 0, 0, 3), spacing=10,
                 line_color=(0.28, 0.4, 1, 1), line_thickness=(0, 0, 2, 0))
    tabs2.add_tab("Tab 1")
    tabs2.add_tab("Tab 2")
    tabs2.add_tab("Tab 3")

    tabs3 = PvTabs(window, x=50, y=380, button_height=50, content_area_width=500, content_area_height=200,
                 bg_color_button_area=(0.1, 0.1, 0.1, 1), bg_color_content_area=(1, 1, 0, 1),
                 active_color=(0.1, 0.1, 0.1, 1), non_active_color=(0.1, 0.1, 0.1, 1),
                 active_font_color=(0.25, 0.58, 0.8, 1), non_active_font_color=(0.68, 0.68, 0.68, 1),
                 default_tab_index=0, border_color=(0.93, 0.93, 0.93, 1), border_thickness=(2,0,0,0),
                 corner_radius=0,
                 button_corner_radius=(0, 0, 0, 0),
                 button_width=120,
                 padding=(5, 0, 0, 0), spacing=10, tab_position='top',
                 line_color=(0.25, 0.58, 0.8, 1), line_thickness=(0, 0, 5, 0))
    tabs3.add_tab("Tab 1")
    tabs3.add_tab("Tab 2")
    tabs3.add_tab("Tab 3")

    tabs4 = PvTabs(window, x=50, y=250,button_width=100, button_height=60, tab_position="left",button_corner_radius=(10,0,0,10),border_thickness=1)
    tabs4.add_tab("Tab 1")
    tabs4.add_tab("Tab 2")
    tabs4.add_tab("Tab 3")

    tabs4.add_to_tab("Tab 1",[pv.PvButton(None)])


    # tabs4 = Tabs(window, x=50, y=580, button_height=50, content_area_width=500, content_area_height=100,
    #              bg_color_button_area=(0.1, 0.1, 0.1, 1), bg_color_content_area=(1, 1, 0, 1),
    #              active_color=(0.1, 0.1, 0.1, 1), non_active_color=(0.1, 0.1, 0.1, 1),
    #              active_font_color=(0.25, 0.58, 0.8, 1), non_active_font_color=(0.68, 0.68, 0.68, 1),
    #              default_tab_index=0, border_color=(1, 0, 0, 1), border_thickness=1,
    #              corner_radius=0,
    #              button_corner_radius=(0, 0, 0, 0),
    #              button_width=120,
    #              padding=(0, 0, 0, 0), spacing=10, tab_position='bottom',
    #              line_color=(0.25, 0.58, 0.8, 1), line_thickness=(0, 0, 5, 0))
    # tabs4.add_tab("Tab 1")
    # tabs4.add_to_tab("Tab 1", [pv.BasicButton(None, x=20, y=20, text="Button1", corner_radius=10)])
    # tabs4.add_tab("Tab 2")
    # tabs4.add_to_tab("Tab 2", [pv.BasicButton(None, x=100, y=20, text="Button2", corner_radius=10)])
    # tabs4.add_tab("Tab 3")
    #
    # tabs5 = Tabs(window, x=50, y=300, button_height=50, content_area_width=500, content_area_height=200,
    #              bg_color_button_area=(0.5, 0.1, 0.5, 1), bg_color_content_area=(1, 1, 0, 1),
    #              active_color=(0.1, 0.1, 0.1, 1), non_active_color=(0.1, 0.1, 0.1, 1),
    #              active_font_color=(0.25, 0.58, 0.8, 1), non_active_font_color=(0.68, 0.68, 0.68, 1),
    #              default_tab_index=0, border_color=(1, 0, 0, 1), border_thickness=1,
    #              corner_radius=0,
    #              button_corner_radius=(0, 0, 0, 0),
    #              button_width=120,
    #              padding=(0, 0, 0, 0), spacing=10, tab_position='right',
    #              line_color=(0.25, 0.58, 0.8, 1), line_thickness=(0, 0, 5, 0))
    # tabs5.add_tab("Tab 1")
    # tabs5.add_to_tab("Tab 1", [pv.BasicButton(None, x=50, y=50, text="Button1", corner_radius=10)])
    # tabs5.add_tab("Tab 2")
    # tabs5.add_to_tab("Tab 2", [pv.BasicButton(None, x=150, y=50, text="Button2", corner_radius=10)])
    # tabs5.add_tab("Tab 3")

    window.show()
