from PySide6.QtWidgets import QProgressBar, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QFontDatabase
import pyvisual as pv


class PvProgressBar(QProgressBar):
    def __init__(self, container, x=100, y=100, width=230, height=None,
                 min_value=0, max_value=100, value=50,
                 suffix="",
                 track_color=(0, 0, 0, 1), track_border_color=(180, 180, 180, 1),
                 fill_color=(135, 206, 235, 1),
                 track_corner_radius=7,
                 is_disabled=False, is_visible=True, opacity=1,
                 track_border_thickness=0,
                 scale=1,
                 is_circular=False,
                 track_height=None,
                 font="Poppins", 
                 font_size=12,
                 font_color=(0, 0, 0, 1),
                 bold=False, 
                 italic=False,
                 underline=False,
                 strikeout=False,
                 on_click=None, on_hover=None, on_release=None,
                 tag=None, **kwargs):
        super().__init__(container)

        # font properties
        self._font = font
        self._font_size = font_size
        self._font_color = font_color
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._strikeout = strikeout
        
        # circular progress bar properties
        self._is_circular = is_circular

        # default height for circular is 80 if not set or set to 25
        if self._is_circular:
            if height is None or height == 25:
                height = 80
            if width is None:
                width = height
        else:
            if height is None:
                height = 40

        self._base_width = width
        self._base_height = height
        self._scale = max(1, scale)  # Ensure scale is at least 1
        self._base_track_corner_radius = track_corner_radius
        self._base_track_border_thickness = track_border_thickness

        # For circular, use width and height independently
        self._width = int(self._base_width * self._scale)
        self._height = int(self._base_height * self._scale)

        # Always use provided track_height if given, for 100% JS match
        if track_height is not None:
            self._track_height = track_height
        else:
            if self._is_circular:
                self._track_height = max(8, int(self._height * 0.15))
            else:
                self._track_height = max(5, int(self._height * 0.7))

        self._track_corner_radius = int(self._base_track_corner_radius * self._scale)
        self._track_border_thickness = self._base_track_border_thickness  # Don't scale border

        # --------------------------------------------------------------------
        # Geometry properties
        # --------------------------------------------------------------------
        self._x = x
        self._y = y

        # --------------------------------------------------------------------
        # Progress properties
        # --------------------------------------------------------------------
        self._min_value = min_value
        self._max_value = max_value  
        self._value = value
        self._suffix = suffix

        # --------------------------------------------------------------------
        # Colors and styling
        # --------------------------------------------------------------------
        self._track_color = track_color
        self._track_border_color = track_border_color
        self._fill_color = fill_color

        # --------------------------------------------------------------------
        # Visual effects and interactivity
        # --------------------------------------------------------------------
        self._is_disabled = is_disabled
        self._is_visible = is_visible
        self._opacity = max(0.0, min(1.0, opacity))

        # --------------------------------------------------------------------
        # Callbacks and custom tag
        # --------------------------------------------------------------------
        self._on_click = on_click
        self._on_hover = on_hover
        self._on_release = on_release
        self._tag = tag

        # --------------------------------------------------------------------
        # Initialize the progress bar
        # --------------------------------------------------------------------
        self.create_layout()
        # Create font object before configure_style
        self._setup_font()
        self.configure_style()


    # -------------------------------------------------
    # Create Layout
    # -------------------------------------------------
    def create_layout(self):
        """Set geometry and create the layout."""
        self.setGeometry(self._x, self._y, self._width, self._height)
        self.setFixedSize(self._width, self._height)
        # Set range and value
        self.setRange(self._min_value, self._max_value)
        self.setValue(self._value)


    # -------------------------------------------------
    # Configure Style
    # -------------------------------------------------
    def configure_style(self):
        """Configure the style of the progress bar."""
        # Set visibility and enabled state
        self.setVisible(self._is_visible)
        self.setEnabled(not self._is_disabled)

        # Set opacity
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(self._opacity)
        self.setGraphicsEffect(effect)

        if not self._is_circular:
            # Set text format to show percentage
            self.setTextVisible(True)
            self.setFormat(f"%v{self._suffix}")
            
            max_radius = min(self._track_height * 0.44, self._track_height / 2)
            corner_radius = min(self._track_corner_radius, max_radius)
            
            # Set colors for linear progress bar
            self.setStyleSheet(f"""
                QProgressBar {{
                    border: {self._track_border_thickness}px solid rgba{self._track_border_color};
                    border-radius: {corner_radius}px;
                    background-color: rgba{self._track_color};
                    text-align: center;
                    height: {self._track_height}px;
                    color: rgba({self._font_color[0]}, {self._font_color[1]}, {self._font_color[2]}, {self._font_color[3]});
                }}
                QProgressBar::chunk {{
                    background-color: rgba{self._fill_color};
                    border-radius: {max(0, corner_radius - self._track_border_thickness*0.8)}px;
                    margin: -{self._track_border_thickness/8}px;
                }}
            """)
            self.setFont(self._qfont)
        else:
            # For circular progress bar, we don't need any stylesheet
            self.setStyleSheet("")


    # -------------------------------------------------
    # Paint Event -- used for circular progress bar
    # -------------------------------------------------
    def paintEvent(self, event):
        if not self._is_circular:
            # Use default linear progress bar painting
            super().paintEvent(event)
            return
        # Custom painting for circular progress bar
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        try:
            width = self._width
            height = self._height
            # radius = min(width, height)/2 - trackHeight/2 - 2
            center_x = width / 2
            center_y = height / 2
            radius = min(width, height) / 2 - self._track_height / 2 - 2
            # Create rect for arc
            progress_rect = QRectF(
                center_x - radius,
                center_y - radius,
                2 * radius,
                2 * radius
            )
            # Convert color tuples to QColor objects
            track_color = QColor()
            track_color.setRgb(
                self._track_color[0],
                self._track_color[1],
                self._track_color[2],
                int(self._track_color[3] * 255)
            )
            fill_color = QColor()
            fill_color.setRgb(
                self._fill_color[0],
                self._fill_color[1],
                self._fill_color[2],
                int(self._fill_color[3] * 255)
            )
            border_color = QColor()
            border_color.setRgb(
                self._track_border_color[0],
                self._track_border_color[1],
                self._track_border_color[2],
                int(self._track_border_color[3] * 255)
            )
            # Draw outer border if needed
            if self._track_border_thickness > 0:
                border_pen = QPen(border_color)
                border_pen.setWidth(self._track_border_thickness)
                painter.setPen(border_pen)
                painter.drawEllipse(progress_rect)
            # Draw background track
            pen = QPen(track_color)
            pen.setWidth(self._track_height)
            pen.setCapStyle(Qt.RoundCap)
            painter.setPen(pen)
            painter.drawArc(progress_rect, 0, 360 * 16)
            # Draw progress
            if self._value > 0:
                pen = QPen(fill_color)
                pen.setWidth(self._track_height)
                pen.setCapStyle(Qt.RoundCap)
                painter.setPen(pen)
                progress = (self._value - self._min_value) / (self._max_value - self._min_value)
                span_angle = -progress * 360 * 16  # Negative for clockwise
                painter.drawArc(progress_rect, 90 * 16, span_angle)
            # Draw text in center
            text = f"{int(self._value)}{self._suffix if self._suffix is not None else ''}"
            painter.setFont(self._qfont)
            font_r, font_g, font_b, font_a = self._font_color
            text_color = QColor()
            text_color.setRgb(font_r, font_g, font_b, int(font_a * 255))
            painter.setPen(text_color)
            # Center text
            painter.drawText(QRectF(0, 0, width, height), Qt.AlignCenter, text)
        finally:
            painter.end()


    # -------------------------------------------------
    # Setup Font
    # -------------------------------------------------
    def _setup_font(self):
        """Configure font settings"""
        if isinstance(self._font, str) and (self._font.endswith('.ttf') or self._font.endswith('.otf')):
            font_id = QFontDatabase.addApplicationFont(self._font)
            families = QFontDatabase.applicationFontFamilies(font_id) if font_id != -1 else []
            font_family = families[0] if families else "Arial"
        else:
            font_family = self._font

        self._qfont = QFont(font_family)
        self._qfont.setPixelSize(self._font_size)
        self._qfont.setBold(self._bold)
        self._qfont.setItalic(self._italic)
        self._qfont.setUnderline(self._underline)
        self._qfont.setStrikeOut(self._strikeout)




    # -------------------------------------------------
    # Events
    # -------------------------------------------------
    def enterEvent(self, event):
        """Handle mouse enter events."""
        super().enterEvent(event)
        if not self._is_disabled and self._on_hover:
            self._on_hover(self)

    def leaveEvent(self, event):
        """Handle mouse leave events."""
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and not self._is_disabled and self._on_click:
            self._on_click(self)

    def mouseReleaseEvent(self, event):
        """Handle mouse release events."""
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and not self._is_disabled and self._on_release:
            self._on_release(self)



    # ----------------------------------------
    # Properties using the @property decorator
    # ----------------------------------------
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
        self._base_width = value
        if self._is_circular:
            # For circular progress bar, set both width and height to maintain perfect circle
            size = value
            self._base_width = self._base_height = size
            self._width = self._height = int(size * self._scale)
        else:
            self._width = int(value * self._scale)
        self.setFixedSize(self._width, self._height)
        self.configure_style()

    @property
    def height(self):
        return self._height

    @height.setter
    def height(self, value):
        self._base_height = value
        if self._is_circular:
            # For circular progress bar, set both width and height to maintain perfect circle
            size = value
            self._base_width = self._base_height = size
            self._width = self._height = int(size * self._scale)
        else:
            self._height = int(value * self._scale)
        self.setFixedSize(self._width, self._height)
        self.configure_style()

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        if value <= 0:
            return  # Prevent invalid scale values
        self._scale = value
        
        # Update all scaled dimensions
        self._width = int(self._base_width * value)
        self._height = int(self._base_height * value)
        self._track_corner_radius = int(self._base_track_corner_radius * value)
        # Don't scale border thicknesses
        self._track_border_thickness = self._base_track_border_thickness
        self._border_thickness = self._base_border_thickness
        
        # Update the widget's size and style
        self.setFixedSize(self._width, self._height)
        self.configure_style()

    @property
    def min_value(self):
        return self._min_value

    @min_value.setter
    def min_value(self, min_value):
        self._min_value = min_value
        self.setRange(self._min_value, self._max_value)
        if self._value < self._min_value:
            self._value = self._min_value
            self.setValue(self._value)

    @property
    def max_value(self):
        return self._max_value

    @max_value.setter
    def max_value(self, max_value):
        self._max_value = max_value
        self.setRange(self._min_value, self._max_value)
        if self._value > self._max_value:
            self._value = self._max_value
            self.setValue(self._value)

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = max(self._min_value, min(self._max_value, value))
        self.setValue(self._value)

    @property
    def track_color(self):
        return self._track_color

    @track_color.setter
    def track_color(self, value):
        self._track_color = value
        self.configure_style()

    @property
    def fill_color(self):
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._fill_color = value
        self.configure_style()

    @property
    def track_corner_radius(self):
        return self._track_corner_radius

    @track_corner_radius.setter
    def track_corner_radius(self, value):
        self._base_track_corner_radius = value
        self._track_corner_radius = int(value * self._scale)
        self.configure_style()

    @property
    def track_border_thickness(self):
        return self._track_border_thickness

    @track_border_thickness.setter
    def track_border_thickness(self, value):
        self._base_track_border_thickness = value
        self._track_border_thickness = value  # Don't scale border thickness
        self.configure_style()

    @property
    def is_disabled(self):
        return self._is_disabled

    @is_disabled.setter
    def is_disabled(self, value):
        self._is_disabled = value
        self.setEnabled(not value)

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)

    @property
    def is_circular(self):
        return self._is_circular

    @is_circular.setter
    def is_circular(self, value):
        self._is_circular = value
        if value:
            self._width = self._height = max(self._base_width, self._base_height)
            self.setFixedSize(self._width, self._height)

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = max(0.0, min(1.0, value))  # Clamp opacity between 0 and 1
        effect = QGraphicsOpacityEffect(self)
        effect.setOpacity(self._opacity)
        self.setGraphicsEffect(effect)

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value

    @property
    def track_border_color(self):
        return self._track_border_color

    @track_border_color.setter
    def track_border_color(self, value):
        self._track_border_color = value
        self.configure_style()

    @property
    def suffix(self):
        return self._suffix

    @suffix.setter
    def suffix(self, value):
        self._suffix = value
        self.setFormat(f"%v{self._suffix}")

        self.configure_style()

    @property
    def track_height(self):
        return self._track_height

    @track_height.setter
    def track_height(self, value):
        self._track_height = value
        if not self._is_circular:
            # For linear progress bar, update the height
            self.setFixedHeight(value)
            self.create_layout()
        self.configure_style()
        self.update()  # Trigger repaint

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = value
        self._qfont.setPixelSize(value)
        self.setFont(self._qfont)
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
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, value):
        self._bold = value
        self._qfont.setBold(value)
        self.setFont(self._qfont)
        self.update()

    @property
    def italic(self):
        return self._italic

    @italic.setter
    def italic(self, value):
        self._italic = value
        self._qfont.setItalic(value)
        self.setFont(self._qfont)
        self.update()

    @property
    def underline(self):
        return self._underline

    @underline.setter
    def underline(self, value):
        self._underline = value
        self._qfont.setUnderline(value)
        self.setFont(self._qfont)
        self.update()

    @property
    def strikeout(self):
        return self._strikeout

    @strikeout.setter
    def strikeout(self, value):
        self._strikeout = value
        self._qfont.setStrikeOut(value)
        self.setFont(self._qfont)
        self.update()



    # ------------------------------------------------------------
    # Print Properties
    # ------------------------------------------------------------
    def print_properties(self):
        """Print all properties of the progress bar."""
        print(f"""
        ProgressBar Properties:
        ----------------------
        Position: ({self.x}, {self.y})
        Size: {self.width}x{self.height}
        Value: {self.value} ({self.min_value} to {self.max_value})
        Track Color: {self.track_color}
        Fill Color: {self.fill_color}
        Track Corner Radius: {self.track_corner_radius}
        Track Border Thickness: {self.track_border_thickness}
        Is Disabled: {self.is_disabled}
        Is Visible: {self.is_visible}
        Opacity: {self.opacity}
        Tag: {self.tag}
        """)


# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------
if __name__ == "__main__":

    app = pv.PvApp()
    window = pv.PvWindow(title="ProgressBar Example", is_resizable=True)

    # Create a linear progress bar
    progress1 = PvProgressBar(
        container=window,
        x=100,
        y=150,
        width=240,
        height=220,
        track_height=33,
        value=70,
        track_color=(200, 200, 200, 1),
        track_border_color=(0, 0, 0, 1),
        track_border_thickness=3,
        track_corner_radius=20,
        fill_color=(0, 0, 255, 1),
        is_disabled=False,
        is_visible=True,
        opacity=1,
        suffix="%",
        is_circular=True
    )

    window.show()
    app.run()