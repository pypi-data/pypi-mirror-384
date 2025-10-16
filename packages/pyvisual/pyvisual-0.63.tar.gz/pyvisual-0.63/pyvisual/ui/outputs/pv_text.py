from PySide6.QtWidgets import QLabel
from PySide6.QtGui import QFont, QFontDatabase, Qt
from PySide6.QtCore import QRect
from PySide6.QtWidgets import QGraphicsOpacityEffect


class PvText(QLabel):
    def __init__(self, container, text="Hello", x=50, y=50,
                 font="Roboto", font_size=20, font_color=(200, 200, 200, 1),
                 bold=False, italic=False, underline=False, strikeout=False,
                 idle_color=(255, 255, 255, 0), width=300, height=None, text_alignment="left",
                 is_visible=True, opacity=1, on_hover=None, on_click=None, on_release=None, tag=None, multiline=True,
                 paddings=[0, 0, 0, 0], line_spacing=1.0, **kwargs):
        super().__init__(text, container)
        self.move(x, y)
        self.setFixedWidth(width)

        # --------------------------------------------------------------------
        # Text Color and Font properties
        # --------------------------------------------------------------------
        self.font = None
        self._font = font
        self._strikeout = strikeout
        self._font_size = int(font_size)
        self._font_color = font_color
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._idle_color = idle_color
        self._text_alignment = text_alignment
        self._height = height

        # --------------------------------------------------------------------
        # Visual effects and interactivity
        # --------------------------------------------------------------------
        self._is_visible = is_visible
        self._opacity = opacity
        self._multiline = multiline
        self._line_spacing = line_spacing
        self._paddings = paddings

        # --------------------------------------------------------------------
        # Callbacks and custom tag
        # --------------------------------------------------------------------
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release
        self._tag = tag

        # --------------------------------------------------------------------
        # Additional attributes for events (excluding shadow effects)
        # --------------------------------------------------------------------
        self._line_edit = None
        self._icon_widget = None
        self._icon_color_hover = None
        self._icon_color = None

        # ------------------------------------------------------------
        # Call helper methods to configure the element
        # ------------------------------------------------------------
        self.create_layout()
        self.configure_style()

    # -------------------------------------------------
    # Create Layout
    # -------------------------------------------------
    def create_layout(self):
        # Font loading logic
        if isinstance(self._font, str) and (self._font.endswith('.ttf') or self._font.endswith('.otf')):
            font_id = QFontDatabase.addApplicationFont(self._font)
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
            font_family = families[0] if families else "Arial"
        else:
            font_family = self._font  # Use the font name directly

        self.font = QFont(font_family)
        self.font.setPixelSize(self._font_size)
        self.font.setBold(self._bold)
        self.font.setItalic(self._italic)
        self.font.setUnderline(self._underline)
        self.font.setStrikeOut(self._strikeout)
        self.setFont(self.font)

        if self._multiline:
            self.setWordWrap(True)

        if self._height is not None:
            self.setFixedHeight(self._height)
        else:
            self._adjust_height(self.text(), self.width(), self._paddings)

    # -------------------------------------------------
    # Configure Style
    # -------------------------------------------------
    def configure_style(self):
        # Style sheet configuration
        font_r, font_g, font_b, font_a = self._font_color
        style = f"color: rgba({font_r}, {font_g}, {font_b}, {font_a});"
        if self._idle_color is not None:
            bg_r, bg_g, bg_b, bg_a = self._idle_color
            style += f" background-color: rgba({bg_r}, {bg_g}, {bg_b}, {bg_a});"
        self.setStyleSheet(style)

        alignment_map = {
            "left": Qt.AlignLeft | Qt.AlignVCenter,
            "center": Qt.AlignHCenter | Qt.AlignVCenter,
            "right": Qt.AlignRight | Qt.AlignVCenter
        }
        self.setAlignment(alignment_map.get(self._text_alignment, Qt.AlignLeft | Qt.AlignVCenter))
        self.setContentsMargins(*self._paddings)

        self.setVisible(self._is_visible)
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(self._opacity)
        self.setGraphicsEffect(effect)

    # -------------------------------------------------
    # Events
    # -------------------------------------------------
    def enterEvent(self, event):
        """Handles hover (mouse enter) events."""
        super().enterEvent(event)
        if self._on_hover:
            self._on_hover(self)
        self.update()

    def leaveEvent(self, event):
        """Handles hover (mouse leave) events."""
        super().leaveEvent(event)
        self.update()

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

    # -------------------------------------------------
    # Helper Functions
    # -------------------------------------------------
    def _adjust_height(self, text, width, paddings):
        font_metrics = self.fontMetrics()
        if self._multiline:
            rect = font_metrics.boundingRect(
                QRect(0, 0, width, 0),
                Qt.TextWordWrap | Qt.AlignLeft,
                text
            )
            adjusted_height = int(rect.height() * self._line_spacing + paddings[1] + paddings[3])
        else:
            adjusted_height = int(font_metrics.height() * self._line_spacing + paddings[1] + paddings[3])
        self.setFixedHeight(adjusted_height)

    # -------------------------------------------------
    # Properties using the @property decorator
    # -------------------------------------------------
    @property
    def x(self):
        return self.geometry().x()

    @x.setter
    def x(self, value):
        self.move(value, self.geometry().y())

    @property
    def y(self):
        return self.geometry().y()

    @y.setter
    def y(self, value):
        self.move(self.geometry().x(), value)

    @property
    def text(self):
        return super().text()

    @text.setter
    def text(self, value):
        self.setText(value)
        # self._adjust_height(value, self.width(), self._paddings)

    @property
    def font_size(self):
        return self.font.pixelSize()

    @font_size.setter
    def font_size(self, size):
        self.font.setPixelSize(size)
        self.setFont(self.font)
        self._adjust_height(self.text(), self.width(), self._paddings)

    @property
    def bold(self):
        return self.font.bold()

    @bold.setter
    def bold(self, value: bool):
        self.font.setBold(value)
        self.setFont(self.font)

    @property
    def italic(self):
        return self.font.italic()

    @italic.setter
    def italic(self, value: bool):
        self.font.setItalic(value)
        self.setFont(self.font)

    @property
    def underline(self):
        return self.font.underline()

    @underline.setter
    def underline(self, value: bool):
        self.font.setUnderline(value)
        self.setFont(self.font)

    @property
    def strikeout(self):
        return self.font.strikeOut()

    @strikeout.setter
    def strikeout(self, value: bool):
        self.font.setStrikeOut(value)
        self.setFont(self.font)

    @property
    def font_color(self):
        return self._font_color

    @font_color.setter
    def font_color(self, value):
        self._font_color = value
        font_r, font_g, font_b, font_a = value
        new_style = f"color: rgba({font_r}, {font_g}, {font_b}, {font_a});"
        if self._idle_color is not None:
            bg_r, bg_g, bg_b, bg_a = self._idle_color
            new_style += f" background-color: rgba({bg_r}, {bg_g}, {bg_b}, {bg_a});"
        self.setStyleSheet(new_style)

    @property
    def idle_color(self):
        return self._idle_color

    @idle_color.setter
    def idle_color(self, value):
        self._idle_color = value
        style = self.styleSheet()
        style = "\n".join([line for line in style.split(";") if "background-color" not in line])
        if value is not None:
            bg_r, bg_g, bg_b, bg_a = value
            style += f" background-color: rgba({bg_r}, {bg_g}, {bg_b}, {bg_a});"
        self.setStyleSheet(style)

    @property
    def text_alignment(self):
        return self._text_alignment

    @text_alignment.setter
    def text_alignment(self, value):
        self._text_alignment = value
        alignment_map = {
            "left": Qt.AlignLeft | Qt.AlignVCenter,
            "center": Qt.AlignHCenter | Qt.AlignVCenter,
            "right": Qt.AlignRight | Qt.AlignVCenter
        }
        self.setAlignment(alignment_map.get(value, Qt.AlignLeft | Qt.AlignVCenter))

    @property
    def multiline(self):
        return self._multiline

    @multiline.setter
    def multiline(self, value: bool):
        self._multiline = value
        self.setWordWrap(value)
        self._adjust_height(self.text(), self.width(), self._paddings)

    @property
    def line_spacing(self):
        return self._line_spacing

    @line_spacing.setter
    def line_spacing(self, value: float):
        self._line_spacing = value
        self._adjust_height(self.text(), self.width(), self._paddings)

    @property
    def paddings(self):
        return self._paddings

    @paddings.setter
    def paddings(self, value):
        self._paddings = value
        self.setContentsMargins(*value)
        self._adjust_height(self.text(), self.width(), value)

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.setWindowOpacity(self._opacity)

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
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)

    # -------------------------------------------------
    # Print Properties
    # -------------------------------------------------
    def print_properties(self):
        print("PvText Properties:")
        print("  x:", self.x)
        print("  y:", self.y)
        print("  font_size:", self.font_size)
        print("  bold:", self.bold)
        print("  italic:", self.italic)
        print("  underline:", self.underline)
        print("  strikeout:", self.strikeout)
        print("  font_color:", self.font_color)
        print("  idle_color:", self.idle_color)
        print("  text_alignment:", self.text_alignment)
        print("  multiline:", self.multiline)
        print("  line_spacing:", self.line_spacing)
        print("  paddings:", self.paddings)
        print("  tag:", self.tag)
        print("  opacity:", self.opacity)


# ===================================================
# ================ Example Usage ====================
# ===================================================
if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()
    window = pv.PvWindow(title="PvApp Example", is_resizable=True)

    text = PvText(window,
                  text="Transparent Background Example",
                  x=50, y=50,
                  font_size=14,
                  idle_color=None,
                  width=300,
                  height=100,
                  text_alignment="left",
                  multiline=True,
                  on_click=lambda e: print("Clicked"))

    # Print all properties
    text.print_properties()
    text.is_visible = False

    window.show()
    app.run()
