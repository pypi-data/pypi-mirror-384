from PySide6.QtWidgets import QWidget, QHBoxLayout, QLineEdit, QLabel
from PySide6.QtGui import QFont, QPixmap, QPainter, QColor
from PySide6.QtSvgWidgets import QSvgWidget
from pyvisual.utils.helper_functions import add_shadow_effect, draw_border, update_svg_color
from PySide6.QtCore import Qt
from PySide6.QtGui import QRegularExpressionValidator
from PySide6.QtCore import QRegularExpression
from PySide6.QtWidgets import QGraphicsOpacityEffect


class PvTextInput(QWidget):
    def __init__(self, container, x=50, y=50, width=200, height=50, background_color=(255, 255, 255, 1),
                 placeholder="Enter your text here...", text_alignment="left",
                 text="", paddings=(10, 0, 20, 0), font="Roboto", font_size=10,
                 font_color=(0, 0, 0, 1), border_color=(0, 0, 0, 1), border_thickness=1,border_style="solid",
                 corner_radius=5, box_shadow=None, icon_path=None, icon_scale=1.0, icon_position="left",
                 icon_spacing=10, icon_color=None, text_type="text", opacity=1,
                 is_visible=True, on_hover=None, on_click=None, on_release=None, tag=None,
                 max_length=None, **kwargs):
        super().__init__(container)

        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self.setGeometry(x, y, width, height)

        # ---------------------------------------------------------
        # Background and Border Properties
        # ---------------------------------------------------------
        self._background_color = background_color
        self._border_color = border_color
        self._border_thickness = border_thickness
        self._corner_radius = corner_radius
        self._border_style = border_style
        # Enforce maximum corner radius (half of height - 1)
        max_corner_radius = (height / 2) - 1
        if self._corner_radius > max_corner_radius:
            self._corner_radius = max_corner_radius

        # ---------------------------------------------------------
        # Text and Font Properties
        # ---------------------------------------------------------
        self._placeholder = placeholder
        self._text = text
        self._font = font
        self._font_size = font_size
        self._font_color = font_color
        self._text_alignment = text_alignment
        self._text_type = text_type
        self._max_length = max_length

        # ---------------------------------------------------------
        # Icon and Layout Properties
        # ---------------------------------------------------------
        self._paddings = paddings  # (top, right, bottom, left)
        self._layout = None
        self._icon_path = icon_path
        self._icon_widget = None
        self._icon_scale = icon_scale
        self._icon_position = icon_position
        self._icon_spacing = icon_spacing
        self._icon_color = icon_color
        self._box_shadow = box_shadow
        self._is_visible = is_visible
        self._opacity = opacity
        # ---------------------------------------------------------
        # Callbacks and Custom Tag
        # ---------------------------------------------------------
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release
        self._tag = tag

        self._box_shadow_hover = None
        self._font_color_hover = None
        self._icon_color_hover = None

        # ---------------------------------------------------------
        # Create Layout and Configure Element
        # ---------------------------------------------------------
        self.create_layout()
        self.configure_style()

    # ---------------------------------------------------------
    # Create Layout
    # ---------------------------------------------------------
    def create_layout(self):
        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(*self._paddings)
        self._layout.setSpacing(self._icon_spacing)
        self._layout.setAlignment(Qt.AlignCenter)

        # If an icon is provided, create the icon widget
        self._icon_widget = None
        if self._icon_path:
            self._icon_widget = self._create_icon_widget()
            if self._icon_color:
                update_svg_color(self._icon_widget, self._icon_color)
            # Add icon widget based on position "left"
            if self._icon_widget and self._icon_position == "left":
                self._layout.addWidget(self._icon_widget)

        # Create QLineEdit widget
        self._line_edit = QLineEdit(self)
        self._line_edit.setPlaceholderText(self._placeholder)
        self._line_edit.setText(self._text)

        # Set font for QLineEdit
        qfont = QFont(self._font)
        qfont.setPixelSize(self._font_size)
        self._line_edit.setFont(qfont)
        self._line_edit.setStyleSheet("background: transparent;")  # Make background transparent

        # Configure text type (validator, echo mode, etc.)
        self._configure_text_type()

        # Set text alignment
        alignment_map = {
            "left": Qt.AlignLeft,
            "center": Qt.AlignCenter,
            "right": Qt.AlignRight
        }
        self._line_edit.setAlignment(alignment_map.get(self._text_alignment, Qt.AlignLeft))

        self._layout.addWidget(self._line_edit)

        # Add icon widget if position is "right"
        if self._icon_path:
            if self._icon_widget and self._icon_position == "right":
                self._layout.addWidget(self._icon_widget)

    # ---------------------------------------------------------
    # Configure Style
    # ---------------------------------------------------------
    def configure_style(self):
        """Update the styles of the parent widget and QLineEdit."""
        # Apply background color and border radius to the parent widget
        r, g, b, a = self._background_color

        self.setStyleSheet(f"""
            background-color: rgba({r}, {g}, {b}, {a});
            border-radius: {self._corner_radius}px;

        """)
        # Apply styles to QLineEdit for font color and transparent background
        font_r, font_g, font_b, font_a = self._font_color
        self._line_edit.setStyleSheet(f"""
            QLineEdit {{
                background-color: transparent;
                color: rgba({font_r}, {font_g}, {font_b}, {font_a});
                border: none;
            }}
        """)
        if self._box_shadow:
            add_shadow_effect(self, self._box_shadow)
        self.setVisible(self._is_visible)

        # -------------------------------
        # Configure element opacity
        # -------------------------------
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(self._opacity)
        self.setGraphicsEffect(effect)

    def paintEvent(self, event):
        """Override paint event to handle custom background and border."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Draw background with rounded corners
        r, g, b, a = self._background_color
        color = QColor(r, g, b, int(a * 255))
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

        # Draw border
        draw_border(self, painter, self._border_color, self._border_thickness, self._corner_radius)

        super().paintEvent(event)

    # ---------------------------------------------------------
    # Events
    # ---------------------------------------------------------
    def enterEvent(self, event):
        """Handles hover (mouse enter) events."""
        super().enterEvent(event)
        if self._box_shadow_hover:
            add_shadow_effect(self, self._box_shadow_hover)
        if self._font_color_hover and self._line_edit:
            hover_font_color = f"rgba({self._font_color_hover[0]}, {self._font_color_hover[1]}, {self._font_color_hover[2]}, {self._font_color_hover[3]})"
            self._line_edit.setStyleSheet(f"color: {hover_font_color}; background: transparent;")
        if self._icon_color_hover and self._icon_widget and isinstance(self._icon_widget, QSvgWidget):
            update_svg_color(self._icon_widget, self._icon_color_hover)
        if self._on_hover:
            self._on_hover(self)
        self.update()

    def leaveEvent(self, event):
        """Handles hover (mouse leave) events."""
        super().leaveEvent(event)
        if self._box_shadow_hover:
            add_shadow_effect(self, self._box_shadow)
        default_font_color = f"rgba({self._font_color[0]}, {self._font_color[1]}, {self._font_color[2]}, {self._font_color[3]})"
        if self._line_edit:
            self._line_edit.setStyleSheet(f"color: {default_font_color}; background: transparent;")
        if self._icon_widget and isinstance(self._icon_widget, QSvgWidget):
            update_svg_color(self._icon_widget, self._icon_color)
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

    # ---------------------------------------------------------
    # Helper Functions: Icon Creation and Text Type Configuration
    # ---------------------------------------------------------
    def _create_icon_widget(self):
        """Creates the QLabel or QSvgWidget for the icon."""
        if self._icon_path.endswith(".svg"):
            try:
                with open(self._icon_path, "r") as file:
                    svg_content = file.read()
                    icon_widget = QSvgWidget(self)
                    icon_widget.load(svg_content.encode("utf-8"))
                    icon_widget._original_svg = svg_content  # Store original SVG content
                    icon_size = int(24 * self._icon_scale)
                    icon_widget.setFixedSize(icon_size, icon_size)
                    icon_widget.setStyleSheet("background-color: transparent;")
                    return icon_widget
            except FileNotFoundError:
                print(f"SVG file '{self._icon_path}' not found.")
                return None
        else:
            icon_widget = QLabel(self)
            pixmap = QPixmap(self._icon_path)
            icon_size = int(24 * self._icon_scale)
            icon_widget.setPixmap(pixmap.scaled(icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon_widget.setFixedSize(icon_size, icon_size)
            icon_widget.setStyleSheet("background: transparent;")
            return icon_widget

    def _configure_text_type(self):
        """Configure the QLineEdit based on the text type."""
        if not hasattr(self, '_line_edit') or self._line_edit is None:
            return  # Exit if line_edit is not yet created
            
        # Clear existing setup
        self._line_edit.setValidator(None)
        self._line_edit.setEchoMode(QLineEdit.Normal)
        
        # Safely disconnect any existing textChanged signals
        try:
            # Only disconnect if there are connections to the textChanged signal
            if self._line_edit.receivers(self._line_edit.textChanged) > 0:
                self._line_edit.textChanged.disconnect()
        except (TypeError, RuntimeError):
            pass  # Handle any disconnection errors
            
        # Set maximum length if specified
        if self._max_length is not None:
            self._line_edit.setMaxLength(self._max_length)
            
        if self._text_type == "number":
            number_regex = QRegularExpression(r"^\d*$")
            number_validator = QRegularExpressionValidator(number_regex, self._line_edit)
            self._line_edit.setValidator(number_validator)
        elif self._text_type == "email":
            email_regex = QRegularExpression(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
            email_validator = QRegularExpressionValidator(email_regex, self._line_edit)
            self._line_edit.setValidator(email_validator)
        elif self._text_type == "password":
            self._line_edit.setEchoMode(QLineEdit.Password)
        elif self._text_type == "creditCard":
            credit_card_regex = QRegularExpression(r"^\d{0,4}( ?\d{0,4}){0,3}$")
            credit_card_validator = QRegularExpressionValidator(credit_card_regex, self._line_edit)
            self._line_edit.setValidator(credit_card_validator)
            self._line_edit.setPlaceholderText("0000 0000 0000 0000")
            self._line_edit.setAlignment(Qt.AlignLeft)
            self._line_edit.textChanged.connect(self._format_credit_card)
        else:
            self._line_edit.setInputMask("")

    def _format_credit_card(self, text):
        """
        Reformats the input text to insert a space after every 4 digits.
        This avoids using an input mask so that placeholder text or underscores are not shown.
        """
        digits = text.replace(" ", "")
        groups = [digits[i:i + 4] for i in range(0, len(digits), 4)]
        new_text = " ".join(groups)
        if new_text != text:
            self._line_edit.blockSignals(True)
            self._line_edit.setText(new_text)
            self._line_edit.setCursorPosition(len(new_text))
            self._line_edit.blockSignals(False)

    # ---------------------------------------------------------
    # Properties
    # ---------------------------------------------------------
    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.update()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.update()

    @property
    def width(self):
        return self._width

    @width.setter
    def width(self, value):
        self._width = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.update()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._height = value
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.update()

    # -----------------------------------
    # Properties: Background & Border
    # -----------------------------------
    @property
    def background_color(self):
        return self._background_color

    @background_color.setter
    def background_color(self, value):
        self._background_color = value
        self.configure_style()
        self.update()

    @property
    def border_color(self):
        return self._border_color

    @border_color.setter
    def border_color(self, value):
        self._border_color = value
        self.configure_style()
        self.update()

    @property
    def border_thickness(self):
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value
        self.configure_style()
        self.update()

    @property
    def corner_radius(self):
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
        self.configure_style()
        self.update()

    # -----------------------------------
    # Properties: Text and Font
    # -----------------------------------
    @property
    def placeholder(self):
        return self._placeholder

    @placeholder.setter
    def placeholder(self, value):
        self._placeholder = value
        self._line_edit.setPlaceholderText(value)
        self.update()

    @property
    def text(self):
        """Gets the current text in the input field."""
        if hasattr(self, '_line_edit'):
            return self._line_edit.text()
        return self._text

    @text.setter
    def text(self, value):
        self._text = value
        if hasattr(self, '_line_edit'):
            self._line_edit.setText(value)
        self.update()

    @property
    def font_family(self):
        return self._font

    @font_family.setter
    def font_family(self, value):
        self._font = value
        qfont = QFont(self._font)
        qfont.setPixelSize(self._font_size)
        self._line_edit.setFont(qfont)
        self.update()

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = value
        qfont = QFont(self._font)
        qfont.setPixelSize(value)
        self._line_edit.setFont(qfont)
        self.update()

    @property
    def font_color(self):
        return self._font_color

    @font_color.setter
    def font_color(self, value):
        self._font_color = value
        self.configure_style()
        self.update()

    @property
    def text_type(self):
        return self._text_type

    @text_type.setter
    def text_type(self, value):
        self._text_type = value
        self._configure_text_type()
        self.update()

    @property
    def max_length(self):
        """Gets the maximum allowed length of text input."""
        return self._max_length

    @max_length.setter
    def max_length(self, value):
        self._max_length = value
        if self._line_edit:
            if value is not None:
                self._line_edit.setMaxLength(value)
            else:
                self._line_edit.setMaxLength(32767)  # Default Qt maximum
        self.update()

    # -----------------------------------
    # Properties: Icon & Layout
    # -----------------------------------
    @property
    def icon_path(self):
        return self._icon_path

    @icon_path.setter
    def icon_path(self, value):
        self._icon_path = value
        self.create_layout()
        self.update()

    @property
    def icon_scale(self):
        return self._icon_scale

    @icon_scale.setter
    def icon_scale(self, value):
        self._icon_scale = value
        self.create_layout()
        self.update()

    @property
    def icon_position(self):
        return self._icon_position

    @icon_position.setter
    def icon_position(self, value):
        self._icon_position = value
        self.create_layout()
        self.update()

    @property
    def icon_spacing(self):
        return self._icon_spacing

    @icon_spacing.setter
    def icon_spacing(self, value):
        self._icon_spacing = value
        self.create_layout()
        self.update()

    @property
    def icon_color(self):
        return self._icon_color

    @icon_color.setter
    def icon_color(self, value):
        self._icon_color = value
        if self._icon_widget:
            update_svg_color(self._icon_widget, value)
        self.update()

    # -----------------------------------
    # Properties: Widget State
    # -----------------------------------
    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.configure_style()
        self.update()

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)
        self.update()

    # -----------------------------------
    # Properties: Event Callbacks and Tag
    # -----------------------------------
    @property
    def on_hover(self):
        return self._on_hover

    @on_hover.setter
    def on_hover(self, callback):
        self._on_hover = callback

    @property
    def on_click(self):
        return self._on_click

    @on_click.setter
    def on_click(self, callback):
        self._on_click = callback

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
    def tag(self, value):
        self._tag = value

    @property
    def cursor_position(self):
        """Gets the current cursor position in the input."""
        return self._line_edit.cursorPosition() if hasattr(self, '_line_edit') else 0

    @cursor_position.setter
    def cursor_position(self, position):
        if hasattr(self, '_line_edit'):
            self._line_edit.setCursorPosition(position)

    # ---------------------------------------------------------
    # Print Properties
    # ---------------------------------------------------------
    def print_properties(self):
        """Prints all current properties of the PvTextInput."""
        print(f"""
        PvTextInput Properties:
        -------------------------
        text: {self.text}
        cursor_position: {self.cursor_position}
        pos: ({self._x}, {self._y})
        size: ({self._width}, {self._height})
        placeholder: {self._placeholder}
        text: {self._text}
        font: {self._font}
        font_size: {self._font_size}
        font_color: {self._font_color}
        background_color: {self._background_color}
        border_color: {self._border_color}
        border_thickness: {self._border_thickness}
        corner_radius: {self._corner_radius}
        icon_path: {self._icon_path}
        icon_color: {self._icon_color}
        icon_position: {self._icon_position}
        icon_spacing: {self._icon_spacing}
        paddings: {self._paddings}
        text_type: {self._text_type}
        max_length: {self._max_length}
        is_visible: {self._is_visible}
        opacity: {self._opacity}
        on_hover: {self._on_hover}
        on_click: {self._on_click}
        on_release: {self._on_release}
        tag: {self._tag}
        """)


# ===================================================
# ================ Example Usage ====================
# ===================================================

if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()
    window = pv.PvWindow(title="PvTextInput with Icon Example")

    text_input = PvTextInput(
        container=window,
        x=50,
        y=50,
        width=300,
        height=50,
        background_color=(240, 240, 240, 1),
        placeholder="Type here...",
        font_color=(0, 0, 0, 1),
        border_color=(0, 120, 215, 1),
        corner_radius=25,
        text="",
        border_thickness=0,
        icon_path="../../assets/icons/more/play.svg",  # Replace with your icon path
        icon_position="right",
        icon_scale=1.2,
        icon_spacing=10,
        icon_color=(150, 0, 0, 1),
        paddings=(30, 0, 30, 0),
        text_type="number",  # For example, only allow numeric input
        # New event callbacks and custom tag:
        on_hover=lambda inp: print("Hovered over text input", inp.tag),
        on_click=lambda inp: print("Text input clicked", inp.tag),
        on_release=lambda inp: print("Text input released", inp.tag),
        tag="Sample PvTextInput"
    )

    text_input2 = PvTextInput(
        container=window,
        x=50,
        y=120,
        width=300,
        height=50,
        background_color=(240, 240, 240, 1),
        placeholder="Password",
        font_color=(0, 0, 0, 1),
        border_color=(0, 120, 215, 1),
        corner_radius=0,
        text="",
        border_thickness=0,
        icon_path="../../assets/icons/more/lock.svg",  # Replace with your icon path
        icon_position="left",
        icon_scale=0.8,
        icon_spacing=10,
        icon_color=(150, 150, 150, 1),
        text_type="password",
        max_length=12  # Limit password to 12 characters
    )

    text_input3 = PvTextInput(
        container=window,
        x=50,
        y=220,
        width=300,
        height=50, opacity=0.2,
        background_color=(245, 245, 245, 1),
        placeholder="Email",
        font_color=(0, 0, 0, 1),
        border_color=(0, 120, 215, 1),
        corner_radius=0,
        text="",
        border_thickness=(0, 0, 0, 3),
        icon_path="../../assets/icons/more/email.svg",  # Replace with your icon path
        icon_color=(150, 150, 150, 1),
        text_type="creditCard",
    )

    text_input4 = PvTextInput(
        container=window,
        x=50,
        y=320,
        width=300,
        height=50, opacity=0.2,
        background_color=(245, 245, 245, 1),
        placeholder="Email",
        font_color=(0, 0, 0, 1),
        border_color=(0, 120, 215, 1),
        border_style="dashed",
        corner_radius=0,
        text="",
        border_thickness=3,
        icon_path="../../assets/icons/more/email.svg",  # Replace with your icon path
        icon_color=(150, 150, 150, 1),
        text_type="email",
    )

    text_input.print_properties()
    text_input.text_type="text"

    window.show()
    app.run()
