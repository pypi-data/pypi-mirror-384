from PySide6.QtCore import Qt
from PySide6.QtGui import QFontDatabase, QFont, QPixmap
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QPushButton, QLabel, QHBoxLayout
from pyvisual.utils.helper_functions import add_shadow_effect, update_svg_color
from PySide6.QtWidgets import QGraphicsOpacityEffect


class PvButton(QPushButton):
    def __init__(self, container, x=100, y=100, width=200, height=50, text="Submit",
                 font="Arial", font_size=16, font_color=(255, 255, 255, 1), font_color_hover=None,
                 bold=False, italic=False, underline=False, strikeout=False,
                 idle_color=(56, 182, 255, 1), hover_color=None, clicked_color=None,
                 disabled_color=(200, 200, 200, 1),
                 border_color=(200, 200, 200, 1), border_color_hover=None, border_thickness=0, corner_radius=0,
                 border_style="solid",
                 box_shadow=None, box_shadow_hover=None,
                 icon_path=None, icon_position="left", icon_spacing=10, icon_scale=1.0, icon_color=None,
                 icon_color_hover=None, is_visible=True, is_disabled=False, opacity=1, paddings=(0, 0, 0, 0),
                 on_hover=None, on_click=None, on_release=None, tag=None, alignment="center",
                 is_hover_disabled=False,
                 **kwargs):
        super().__init__(container)
        # --------------------------------------------------------------------
        # Geometry properties
        # --------------------------------------------------------------------
        self._x = x
        self._y = y
        self._width = width
        self._height = height

        # --------------------------------------------------------------------
        # Text and font properties
        # --------------------------------------------------------------------
        self._text = text
        self._font = font
        self._font_size = int(font_size)
        self._font_color = font_color
        self._font_color_hover = font_color_hover
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._strikeout = strikeout

        # --------------------------------------------------------------------
        # Button colors and borders
        # --------------------------------------------------------------------
        self._idle_color = idle_color
        self._disabled_color = disabled_color
        self._border_color = border_color
        self._border_color_hover = border_color_hover or border_color
        self._border_thickness = border_thickness
        self._corner_radius = corner_radius
        self._border_style = border_style

        # --------------------------------------------------------------------
        # Visual effects and interactivity
        # --------------------------------------------------------------------
        self._box_shadow = None
        self._box_shadow_hover = None
        # self._box_shadow = box_shadow
        # self._box_shadow_hover = box_shadow_hover or box_shadow
        self._opacity = opacity
        self._is_visible = is_visible
        self._is_disabled = is_disabled
        self._is_hover_disabled = is_hover_disabled

        # --------------------------------------------------------------------
        # Icon and layout properties
        # --------------------------------------------------------------------
        self._paddings = paddings
        self._icon_path = icon_path
        self._icon_position = icon_position
        self._icon_spacing = icon_spacing
        self._icon_scale = icon_scale
        # If icon_color is None, use font_color for icons by default
        self._icon_color = icon_color if icon_color is not None else font_color
        self._icon_color_hover = icon_color_hover
        self._alignment = alignment

        # --------------------------------------------------------------------
        # Callbacks and custom tag
        # --------------------------------------------------------------------
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release
        self._tag = tag

        # --------------------------------------------------------------------
        # Derived properties for hover and clicked colors
        # --------------------------------------------------------------------
        # Track whether the hover and clicked colors have been explicitly set
        self._hover_color_explicitly_set = hover_color is not None
        self._clicked_color_explicitly_set = clicked_color is not None

        self._hover_color = (
            hover_color if hover_color is not None else
            tuple(max(c - 15, 0) if idle_color[:3] != (0, 0, 0) else min(c + 50, 255)
                  for c in idle_color[:3]) + (idle_color[3],)
        )
        self._clicked_color = (
            clicked_color if clicked_color is not None else
            tuple(max(c - 30, 0) if idle_color[:3] != (0, 0, 0) else min(c + 90, 255)
                  for c in idle_color[:3]) + (idle_color[3],)
        )

        # --------------------------------------------------------------------
        # Enforce maximum corner radius
        # --------------------------------------------------------------------
        self.max_corner_radius = self._height // 2 - 1
        if self._corner_radius > self.max_corner_radius:
            self._corner_radius = self.max_corner_radius

        # ------------------------------------------------------------
        # Call helper methods to configure the element
        # ------------------------------------------------------------

        self.create_layout()
        self.configure_style()

    # -------------------------------------------------
    # Create Layout
    # -------------------------------------------------

    def create_layout(self):
        """Set geometry, fixed size, and create the layout in the order: Container → Text → Icon."""

        # -------------------------------------------------
        # 1) Container
        # -------------------------------------------------
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.setFixedSize(self._width, self._height)

        layout = QHBoxLayout()
        layout.setContentsMargins(*self._paddings)
        layout.setSpacing(self._icon_spacing)

        # Set alignment based on the alignment property
        if self._alignment == "left":
            layout.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        elif self._alignment == "right":
            layout.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        else:  # default to center
            layout.setAlignment(Qt.AlignCenter)

        # -------------------------------------------------
        # 2) Text
        # -------------------------------------------------
        # (Load and configure the font used by the text label)
        if self._font.endswith('.ttf') or self._font.endswith('.otf'):
            self._qfont = self.load_custom_font(self._font)
            if self._qfont is None:
                print(f"Failed to load custom font: {self._font}")
                self._qfont = QFont("Arial")
        else:
            self._qfont = QFont(self._font)

        font = self._qfont
        font.setPixelSize(self._font_size)
        font.setBold(self._bold)
        font.setItalic(self._italic)
        font.setUnderline(self._underline)
        font.setStrikeOut(self._strikeout)

        # -------------------------------------------------
        # 3) Icon
        # -------------------------------------------------
        # (Create the icon widget only once, then place it to the left or right)
        self._icon_label = None
        if self._icon_path:
            self._icon_label = self.create_icon_widget()

        # If the icon widget exists and the position is "left", add it now
        if self._icon_label and self._icon_position == "left":
            layout.addWidget(self._icon_label)

        # Add text label if text is provided
        if self._text:
            self._text_label = QLabel(self._text, self)
            self._text_label.setFont(font)
            self._text_label.setStyleSheet(
                f"color: rgba({self._font_color[0]}, {self._font_color[1]}, {self._font_color[2]}, {self._font_color[3]});"
                " background: transparent;")
            layout.addWidget(self._text_label)

        # If the icon widget exists and the position is "right", add it after the text
        if self._icon_label and self._icon_position == "right":
            layout.addWidget(self._icon_label)

        # -------------------------------------------------
        # Finalize layout
        # -------------------------------------------------
        self.setLayout(layout)
        self.setStyleSheet("background: transparent;")

    def create_icon_widget(self):
        """Creates and returns a widget for the icon based on its type."""
        # For SVG icons
        if self._icon_path.endswith('.svg'):
            try:
                with open(self._icon_path, "r") as file:
                    svg_content = file.read()
                    icon_widget = QSvgWidget(self)
                    icon_widget._original_svg = svg_content
                    icon_widget.load(svg_content.encode("utf-8"))
                    icon_size = int(24 * self._icon_scale)
                    icon_widget.setFixedSize(icon_size, icon_size)
                    icon_widget.setStyleSheet("background: transparent;")
                    update_svg_color(icon_widget, self._icon_color)
                    return icon_widget
            except FileNotFoundError:
                print(f"SVG file '{self._icon_path}' not found.")
                return None
        else:
            # For raster icons (PNG, JPG, etc.)
            icon_widget = QLabel(self)
            pixmap = QPixmap(self._icon_path)
            icon_size = int(24 * self._icon_scale)
            icon_widget.setPixmap(
                pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_widget.setFixedSize(icon_size, icon_size)
            icon_widget.setStyleSheet("background: transparent;")
            return icon_widget

    # -------------------------------------------------
    # Configure Style
    # -------------------------------------------------

    def configure_style(self):
        """Apply styling (colors, borders, etc.) to the button and configure general widget properties."""
        # -------------------------------
        # Configure button style (colors and borders)
        # -------------------------------
        r, g, b, a = self._idle_color
        br, bg, bb, ba = self._border_color
        border_style_str = (f"{self._border_thickness}px {self._border_style} rgba({br}, {bg}, {bb}, {ba})"
                            if self._border_thickness else "none")

        if self._is_hover_disabled:
            # If hover is disabled, don't include hover styles
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {a});
                    border-radius: {self._corner_radius}px;
                    border: {border_style_str};
                }}
                QPushButton:pressed {{
                    background-color: rgba({self._clicked_color[0]}, {self._clicked_color[1]}, {self._clicked_color[2]}, {self._clicked_color[3]});
                }}
            """)
        else:
            # Normal style with hover effects
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: rgba({r}, {g}, {b}, {a});
                    border-radius: {self._corner_radius}px;
                    border: {border_style_str};
                }}
                QPushButton:hover {{
                    background-color: rgba({self._hover_color[0]}, {self._hover_color[1]}, {self._hover_color[2]}, {self._hover_color[3]});
                }}
                QPushButton:pressed {{
                    background-color: rgba({self._clicked_color[0]}, {self._clicked_color[1]}, {self._clicked_color[2]}, {self._clicked_color[3]});
                }}
            """)

        if self._box_shadow:
            add_shadow_effect(self, self._box_shadow)

        # -------------------------------
        # Configure visibility and enabled state
        # -------------------------------
        self.setVisible(self._is_visible)
        self.setEnabled(not self._is_disabled)
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(self._opacity)
        self.setGraphicsEffect(effect)

        # -------------------------------
        # Configure element opacity
        # -------------------------------
        self.setWindowOpacity(self._opacity)

    # -------------------------------------------------
    # Events
    # -------------------------------------------------
    def enterEvent(self, event):
        """Handles hover (mouse enter) events."""
        super().enterEvent(event)
        # Skip hover effects if hover is disabled
        if self._is_hover_disabled:
            return

        if self._box_shadow_hover:
            add_shadow_effect(self, self._box_shadow_hover)
        if self._font_color_hover and hasattr(self, '_text_label'):
            hover_font_color = f"rgba({self._font_color_hover[0]}, {self._font_color_hover[1]}, {self._font_color_hover[2]}, {self._font_color_hover[3]})"
            self._text_label.setStyleSheet(f"color: {hover_font_color}; background: transparent;")
        if self._icon_color_hover and hasattr(self, '_icon_label') and isinstance(self._icon_label, QSvgWidget):
            update_svg_color(self._icon_label, self._icon_color_hover)
        if self._on_hover:
            self._on_hover(self)

    def leaveEvent(self, event):
        """Handles hover (mouse leave) events."""
        super().leaveEvent(event)

        # Skip hover effect handling if hover is disabled
        if self._is_hover_disabled:
            return

        if self._box_shadow_hover:
            add_shadow_effect(self, self._box_shadow)
        default_font_color = f"rgba({self._font_color[0]}, {self._font_color[1]}, {self._font_color[2]}, {self._font_color[3]})"
        if hasattr(self, '_text_label'):
            self._text_label.setStyleSheet(f"color: {default_font_color}; background: transparent;")
        if hasattr(self, '_icon_label') and isinstance(self._icon_label, QSvgWidget):
            update_svg_color(self._icon_label, self._icon_color)

    def mousePressEvent(self, event):
        """Handles mouse press events."""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and self._on_click:
            self._on_click(self)

    def mouseReleaseEvent(self, event):
        """Handles mouse release events."""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self._on_release:
            self._on_release(self)

    def load_custom_font(self, font_path):
        """Loads a custom font and returns the corresponding QFont object."""
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id != -1:
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            if font_families:
                return QFont(font_families[0])
        return None

    # ------------------------------------------------------------
    # Properties using the @property decorator
    # ------------------------------------------------------------
    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        if hasattr(self, '_text_label'):
            self._text_label.setText(value)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.setGeometry(self._x, self._y, self._width, self._height)

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.setGeometry(self._x, self._y, self._width, self._height)

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.setFixedSize(self._width, self._height)

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.setFixedSize(self._width, self._height)

    @property
    def font_family(self):
        return self._font

    @font_family.setter
    def font_family(self, value):
        self._font = value
        self._qfont.setFamily(value)
        self.setFont(self._qfont)

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, size):
        self._font_size = size
        self._qfont.setPointSize(size)
        self.setFont(self._qfont)

    @property
    def font_color(self):
        return self._font_color

    @font_color.setter
    def font_color(self, color):
        self._font_color = color
        self.configure_style()

    @property
    def font_color_hover(self):
        return self._font_color_hover

    @font_color_hover.setter
    def font_color_hover(self, color):
        self._font_color_hover = color
        self.configure_style()

    @property
    def idle_color(self):
        return self._idle_color

    @idle_color.setter
    def idle_color(self, color):
        self._idle_color = color
        # Recalculate hover and clicked colors using the same logic as in __init__
        # Only recalculate if they weren't explicitly set by the user (using direct hover_color setter)
        if not hasattr(self, '_hover_color_explicitly_set') or not self._hover_color_explicitly_set:
            self._hover_color = tuple(max(c - 15, 0) if color[:3] != (0, 0, 0) else min(c + 50, 255)
                                      for c in color[:3]) + (color[3],)
        if not hasattr(self, '_clicked_color_explicitly_set') or not self._clicked_color_explicitly_set:
            self._clicked_color = tuple(max(c - 30, 0) if color[:3] != (0, 0, 0) else min(c + 90, 255)
                                        for c in color[:3]) + (color[3],)
        self.configure_style()

    @property
    def hover_color(self):
        return self._hover_color

    @hover_color.setter
    def hover_color(self, color):
        self._hover_color = color
        self._hover_color_explicitly_set = True
        self.configure_style()

    @property
    def clicked_color(self):
        return self._clicked_color

    @clicked_color.setter
    def clicked_color(self, color):
        self._clicked_color = color
        self._clicked_color_explicitly_set = True
        self.configure_style()

    @property
    def disabled_color(self):
        return self._disabled_color

    @disabled_color.setter
    def disabled_color(self, color):
        self._disabled_color = color
        self.configure_style()

    @property
    def border_color(self):
        return self._border_color

    @border_color.setter
    def border_color(self, color):
        self._border_color = color
        self.configure_style()

    @property
    def border_color_hover(self):
        return self._border_color_hover

    @border_color_hover.setter
    def border_color_hover(self, color):
        self._border_color_hover = color
        self.configure_style()

    @property
    def border_thickness(self):
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, thickness):
        self._border_thickness = thickness
        self.configure_style()

    @property
    def border_style(self):
        return self._border_style

    @border_style.setter
    def border_style(self, style):
        self._border_style = style
        self.configure_style()

    @property
    def corner_radius(self):
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, radius):
        self._corner_radius = radius
        self.configure_style()

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(self._opacity)

    # @opacity.setter
    # def opacity(self, value):
    #     self.setWindowOpacity(value)

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, visible):
        self._is_visible = visible
        self.setVisible(self._is_visible)

    @property
    def is_disabled(self):
        return self._is_disabled

    @is_disabled.setter
    def is_disabled(self, disabled):
        self._is_disabled = disabled
        self.setEnabled(not self._is_disabled)
        self.configure_style()

    @property
    def box_shadow(self):
        return self._box_shadow

    @box_shadow.setter
    def box_shadow(self, shadow):
        self._box_shadow = shadow
        add_shadow_effect(self, self._box_shadow)

    @property
    def box_shadow_hover(self):
        return self._box_shadow_hover

    @box_shadow_hover.setter
    def box_shadow_hover(self, shadow):
        self._box_shadow_hover = shadow
        self.configure_style()

    @property
    def on_click(self):
        return self._on_click

    @on_click.setter
    def on_click(self, callback):
        self._on_click = callback

    @property
    def on_hover(self):
        return self._on_hover

    @on_hover.setter
    def on_hover(self, callback):
        self._on_hover = callback

    @property
    def on_release(self):
        return self._on_release

    @on_release.setter
    def on_release(self, callback):
        self._on_release = callback

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, tag_value):
        self._tag = tag_value

    @property
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, value):
        self._bold = value
        self.configure_style()

    @property
    def italic(self):
        return self._italic

    @italic.setter
    def italic(self, value):
        self._italic = value
        self.configure_style()

    @property
    def underline(self):
        return self._underline

    @underline.setter
    def underline(self, value):
        self._underline = value
        self.configure_style()

    @property
    def strikeout(self):
        return self._strikeout

    @strikeout.setter
    def strikeout(self, value):
        self._strikeout = value
        self.configure_style()

    @property
    def icon_path(self):
        return self._icon_path

    @icon_path.setter
    def icon_path(self, path):
        self._icon_path = path
        self.create_layout()

    @property
    def icon_position(self):
        return self._icon_position

    @icon_position.setter
    def icon_position(self, position):
        self._icon_position = position
        self.create_layout()

    @property
    def icon_spacing(self):
        return self._icon_spacing

    @icon_spacing.setter
    def icon_spacing(self, spacing):
        self._icon_spacing = spacing
        self.create_layout()

    @property
    def icon_scale(self):
        return self._icon_scale

    @icon_scale.setter
    def icon_scale(self, scale):
        self._icon_scale = scale
        self.create_layout()

    @property
    def icon_color(self):
        return self._icon_color

    @icon_color.setter
    def icon_color(self, color):
        self._icon_color = color
        if hasattr(self, '_icon_label') and isinstance(self._icon_label, QSvgWidget):
            update_svg_color(self._icon_label, self._icon_color)

    @property
    def icon_color_hover(self):
        return self._icon_color_hover

    @icon_color_hover.setter
    def icon_color_hover(self, color):
        self._icon_color_hover = color
        self.create_layout()

    @property
    def paddings(self):
        return self._paddings

    @paddings.setter
    def paddings(self, padding_values):
        self._paddings = padding_values
        self.create_layout()

    @property
    def alignment(self):
        return self._alignment

    @alignment.setter
    def alignment(self, value):
        if value in ["left", "center", "right"]:
            self._alignment = value
            self.create_layout()
        else:
            print(f"Invalid alignment value: {value}. Must be 'left', 'center', or 'right'.")

    @property
    def is_hover_disabled(self):
        return self._is_hover_disabled

    @is_hover_disabled.setter
    def is_hover_disabled(self, disabled):
        self._is_hover_disabled = disabled
        self.configure_style()

    # ---------------------------------------------------------
    # Print Properties
    # ---------------------------------------------------------
    def print_properties(self):
        """Prints all the current properties of the button."""
        print(f"""
        Button Properties:
        ------------------
        text: {self.text}
        pos: {self.position}
        size: {self.size}
        font: {self.font_family}
        font_size: {self.font_size}
        font_color: {self.font_color}
        idle_color: {self.idle_color}
        hover_color: {self.hover_color}
        clicked_color: {self.clicked_color}
        disabled_color: {self.disabled_color}
        border_color: {self.border_color}
        border_thickness: {self.border_thickness}
        corner_radius: {self.corner_radius}
        opacity: {self.opacity}
        is_visible: {self.is_visible}
        is_disabled: {self.is_disabled}
        box_shadow: {self.box_shadow}
        on_click: {self.on_click}
        on_hover: {self.on_hover}
        on_release: {self.on_release}
        tag: {self.tag}
        """)


# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------

if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()
    window = pv.PvWindow(title="PvApp Example", width=1200, height=800, is_resizable=True)

    button1 = PvButton(window, x=50, y=50)
    button2 = PvButton(window, x=300, y=50, width=50, height=50, corner_radius=25, text="GO", font_size=10)
    button3 = PvButton(window, x=50, y=150, border_color=(56, 182, 255, 1), border_thickness=2,
                       idle_color=(255, 255, 255, 1), font_color=(56, 182, 255, 1),
                       hover_color=(56, 182, 255, 1), clicked_color=(225, 225, 225, 1),
                       font_color_hover=(255, 255, 255, 1))
    button4 = PvButton(window, x=300, y=150, width=50, height=50, corner_radius=25, text="GO", font_size=10,
                       border_color=(56, 182, 255, 1), border_thickness=2,
                       idle_color=(255, 255, 255, 1), font_color=(56, 182, 255, 1),
                       hover_color=(56, 182, 255, 1), clicked_color=(225, 225, 225, 1),
                       font_color_hover=(255, 255, 255, 1))
    button5 = PvButton(window, x=400, y=50, width=50, height=50, corner_radius=10, text="GO", font_size=10)
    button6 = PvButton(window, x=400, y=150, width=50, height=50, corner_radius=10, text="GO", font_size=10,
                       border_color=(56, 182, 255, 1), border_thickness=2,
                       idle_color=(255, 255, 255, 1), font_color=(56, 182, 255, 1),
                       hover_color=(56, 182, 255, 1), clicked_color=(225, 225, 225, 1),
                       font_color_hover=(255, 255, 255, 1))
    button7 = PvButton(window, x=500, y=50, corner_radius=25)
    button8 = PvButton(window, x=500, y=150, corner_radius=25, text="Submit", font_size=16,
                       border_color=(56, 182, 255, 1), border_thickness=2,
                       idle_color=(255, 255, 255, 1), font_color=(56, 182, 255, 1),
                       hover_color=(56, 182, 255, 1), clicked_color=(225, 225, 225, 1),
                       font_color_hover=(255, 255, 255, 1))
    button9 = PvButton(window, x=50, y=250, width=100, height=40, text="Like",
                       icon_path="../../assets/icons/like/like.svg", idle_color=(255, 255, 255, 1),
                       hover_color=(255, 255, 255, 1), font_color_hover=(56, 182, 255, 1),
                       clicked_color=(245, 245, 245, 1), bold=True, border_thickness=1, corner_radius=10,
                       font_color=(136, 136, 136, 1), font_size=14, icon_scale=1, icon_spacing=10,
                       icon_position="right", border_color_hover=(56, 182, 255, 1),
                       box_shadow_hover="2px 2px 5px 0px rgba(56,182,255,0.5)")
    button10 = PvButton(window, x=200, y=250, width=50, height=50, text="",
                        icon_path="../../assets/icons/more/shopping.svg", idle_color=(161, 80, 157, 1),
                        hover_color=(255, 255, 255, 1), font_color_hover=(161, 80, 157, 1),
                        clicked_color=(161, 80, 157, 1), bold=True, border_thickness=1,
                        font_color=(255, 255, 255, 1), font_size=14, icon_scale=1, icon_spacing=10,
                        icon_position="right")
    button11 = PvButton(window, x=300, y=250, width=150, height=50, text="Next",
                        icon_path="../../assets/icons/more/arrow_right.svg", idle_color=(255, 255, 255, 1),
                        font_color_hover=(255, 255, 255, 1), hover_color=(161, 80, 157, 1), corner_radius=0,
                        clicked_color=(255, 255, 255, 1), bold=True, border_thickness=1, border_color=(161, 80, 157, 1),
                        font_color=(161, 80, 157, 1), font_size=14, icon_scale=1, icon_spacing=30,
                        icon_position="right")
    button12 = PvButton(window, x=500, y=250, width=135, height=50, text="Play",
                        icon_path="../../assets/icons/more/play.svg", icon_scale=1.7, icon_position="left",
                        icon_spacing=15, paddings=(0, 0, 23, 0),
                        idle_color=(255, 255, 255, 1), hover_color=(161, 80, 157, 1),
                        font_color_hover=(255, 255, 255, 1), clicked_color=(255, 255, 255, 1),
                        corner_radius=25, bold=True, border_thickness=2, border_color=(161, 80, 157, 1),
                        font_color=(161, 80, 157, 1), font_size=14)
    button13 = PvButton(window, x=300, y=325, width=150, height=50, text="Next",
                        icon_path="../../assets/icons/more/arrow_right.svg", idle_color=(255, 255, 255, 1),
                        corner_radius=0, bold=True, border_thickness=(0, 0, 2, 0),
                        border_color=(161, 80, 157, 1), font_color=(161, 80, 157, 1),
                        font_size=14, icon_scale=1, icon_spacing=30, icon_position="right")
    button14 = PvButton(window, x=50, y=400, idle_color=(200, 0, 200, 1))
    button14.position = (100, 450)

    # Alignment examples
    button_left = PvButton(window, x=50, y=520, width=200, height=50, text="Left Aligned",
                           alignment="left", idle_color=(100, 100, 255, 1))
    button_center = PvButton(window, x=50, y=580, width=200, height=50, text="Center Aligned",
                             alignment="center", idle_color=(100, 255, 100, 1))
    button_right = PvButton(window, x=50, y=640, width=200, height=50, text="Right Aligned",
                            alignment="right", idle_color=(255, 100, 100, 1))

    # Icon with alignment
    button_icon_left = PvButton(window, x=300, y=520, width=200, height=50, text="Icon Left",
                                alignment="left", idle_color=(100, 100, 255, 1),
                                icon_path="../../assets/icons/more/play.svg", icon_position="left")
    button_icon_center = PvButton(window, x=300, y=580, width=200, height=50, text="Icon Center",
                                  alignment="center", idle_color=(100, 255, 100, 1),
                                  icon_path="../../assets/icons/more/play.svg", icon_position="left")
    button_icon_right = PvButton(window, x=300, y=640, width=200, height=50, text="Icon Right",
                                 alignment="right", idle_color=(255, 100, 100, 1),
                                 icon_path="../../assets/icons/more/play.svg", icon_position="right")

    # Hover disabled button example
    button_no_hover = PvButton(window, x=700, y=400, width=200, height=50, text="No Hover Effect",
                               idle_color=(150, 150, 150, 1), is_hover_disabled=True)

    # Icon color examples
    button_icon_default = PvButton(window, x=700, y=520, width=200, height=50, text="Default Icon Color",
                                   font_color=(255, 0, 0, 1),  # Icon will use font color by default
                                   icon_path="../../assets/icons/more/play.svg")

    button_icon_custom = PvButton(window, x=700, y=580, width=200, height=50, text="Custom Icon Color",
                                  font_color=(255, 0, 0, 1),  # Font will be red
                                  icon_color=(0, 255, 0, 1),  # Icon will be green
                                  icon_path="../../assets/icons/more/play.svg")

    window.show()
    app.run()

# Fixed issue
# Directly called update_svg_color in the setter of icon_color instead of calling configure_style

# @icon_color.setter
#     def icon_color(self, color):
#         self._icon_color = color
#         if hasattr(self, '_icon_label') and isinstance(self._icon_label, QSvgWidget):
#             update_svg_color(self._icon_label, self._icon_color)