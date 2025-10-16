from PySide6.QtCore import Qt, Signal, QRect
from PySide6.QtGui import QColor, QPainter, QBrush, QPen
from PySide6.QtWidgets import QWidget
import pyvisual as pv
from pyvisual.ui.outputs.pv_text import PvText
from pyvisual.utils.helper_functions import add_shadow_effect, update_svg_color


class PvSlider(PvText):
    value_changed = Signal(int)

    def __init__(self, container, x=100, y=100, width=230, height=50,
                 min_value=0, max_value=100, value=80,
                 track_color=(200, 200, 200, 1), track_border_color=(180, 180, 180, 1),
                 fill_color=(255, 182, 255, 1),
                 knob_color=(255, 155, 255, 1), knob_border_color=(245, 245, 245, 1),
                 hover_knob_color=None, disabled_knob_color=(150, 150, 150, 1),
                 track_corner_radius=2, knob_corner_radius=11,
                 knob_width=20, knob_height=20,
                 is_disabled=False,
                 track_border_thickness=0, knob_border_thickness=2, on_change=None,
                 scale=1, track_height=10,
                 is_visible=True,
                 show_text=False,
                 font_color=(0, 0, 0, 1),
                 bold=False, italic=False,
                 underline=False, strikeout=False,
                 font_size=12,
                 opacity=1,
                 **kwargs):

        self._label_offset_below = 20
        self._label_offset_above = 25

        # Initialize is_disabled before calling super().__init__ so it's available in configure_style
        self._is_disabled = is_disabled

        # Initialize the parent PvText class with common properties
        super().__init__(
            container=container,
            x=x, y=y,
            width=width, height=height,
            is_visible=is_visible,
            opacity=opacity,
            **kwargs
        )

        # Store original dimensions for scaling
        self._base_width = width
        self._base_height = height
        self._scale = scale
        self._base_track_height = track_height
        self._base_knob_width = knob_width
        self._base_knob_height = knob_height
        self._base_track_corner_radius = track_corner_radius
        self._base_knob_corner_radius = knob_corner_radius
        self._base_track_border_thickness = track_border_thickness
        self._base_knob_border_thickness = knob_border_thickness

        # Calculate initial dimensions based on scale
        self._track_height = int(self._base_track_height * self._scale)
        self._knob_width = int(self._base_knob_width * self._scale)
        self._knob_height = int(self._base_knob_height * self._scale)
        self._track_corner_radius = int(self._base_track_corner_radius * self._scale)
        self._knob_corner_radius = int(self._base_knob_corner_radius * self._scale)
        self._track_border_thickness = int(self._base_track_border_thickness * self._scale)
        self._knob_border_thickness = int(self._base_knob_border_thickness * self._scale)

        # Value range properties
        self._min_value = min_value
        self._max_value = max_value
        self._value = value

        # Track colors
        self._track_color = track_color
        self._track_border_color = track_border_color
        self._fill_color = fill_color

        # Knob colors
        self._knob_color = knob_color
        self._knob_border_color = knob_border_color
        self._hover_knob_color = hover_knob_color or knob_color
        self._disabled_knob_color = disabled_knob_color

        # State
        self._is_hovered = False
        self._is_dragging = False

        # Callbacks
        self._on_change = on_change

        # Labels settings
        self._show_text = show_text
        self._font_color = font_color
        self._bold = bold
        self._italic = italic
        self._underline = underline
        self._strikeout = strikeout
        self._font_size = font_size
        self._min_label = None
        self._max_label = None
        self._value_label = None

        # Opacity
        self._opacity = opacity

        # Connect the `on_change` function to the `value_changed` signal if provided
        if callable(self._on_change):
            self.value_changed.connect(self._on_change)

        # Call helper methods to set up the widget
        self.create_layout()
        self.configure_style()

        # Add shadow effect
        add_shadow_effect(self, "0 2 4 5 rgba(0,0,0,0.2)")

        # Create labels if enabled
        if self._show_text:
            self._create_labels()
            # Propagate initial visibility to labels
            if self._min_label:
                self._min_label.is_visible = self._is_visible
            if self._max_label:
                self._max_label.is_visible = self._is_visible
            if self._value_label:
                self._value_label.is_visible = self._is_visible

    # -------------------------------------------------
    # Create Layout
    # -------------------------------------------------
    def create_layout(self):
        """Set up the basic layout and geometry of the slider."""
        # Set the widget geometry - we can use super() to set this
        super().create_layout()

        # Enable mouse tracking for hover effects
        self.setMouseTracking(True)

    # -------------------------------------------------
    # Configure Style
    # -------------------------------------------------
    def configure_style(self):
        """Configure the visual appearance of the slider."""
        # Use parent class method for visibility
        super().configure_style()
        # Set disabled state
        self.setEnabled(not self._is_disabled)

    def paintEvent(self, event):
        """Custom painting for the slider."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        # Set opacity
        painter.setOpacity(self._opacity)

        knob_radius = self._knob_width / 2

        # Track geometry: only inset by knob radius
        track_left = int(knob_radius)
        track_right = int(self.width() - knob_radius)
        track_top = int((self.height() - self._track_height) // 2)
        track_height = int(self._track_height)
        track_width = int(track_right - track_left)

        # Adjust track rectangle to account for border thickness
        border_offset = self._track_border_thickness / 2
        track_rect = QRect(
            int(track_left + border_offset),
            int(track_top + border_offset),
            int(track_width - self._track_border_thickness),
            int(track_height - self._track_border_thickness)
        )

        # Draw track
        self._track_corner_radius = min(self._track_height / 2, self._track_corner_radius)
        # Conversion from RGBA tuples to QColor using a list comprehension
        track_border_color = QColor(*[int(c * 255) if i == 3 else c for i, c in enumerate(self._track_border_color)])
        track_color = QColor(*[int(c * 255) if i == 3 else c for i, c in enumerate(self._track_color)])
        fill_color = QColor(*[int(c * 255) if i == 3 else c for i, c in enumerate(self._fill_color)])

        # Only set pen if border thickness is greater than 0
        if self._track_border_thickness > 0:
            painter.setPen(QPen(track_border_color, self._track_border_thickness))
        else:
            painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(track_color))
        painter.drawRoundedRect(track_rect, self._track_corner_radius, self._track_corner_radius)

        # Knob center calculation
        value_range = self._max_value - self._min_value if self._max_value != self._min_value else 1
        percent = (self._value - self._min_value) / value_range
        knob_center_x = int(track_left + percent * (track_width - self._knob_width) + self._knob_width / 2)

        # Only draw fill if value is greater than min_value
        if self._value > self._min_value:
            # Fill rect: from track_left to knob_center_x, accounting for border thickness
            fill_rect = QRect(
                int(track_left + border_offset),
                int(track_top + border_offset),
                int(knob_center_x - track_left - self._track_border_thickness),
                int(track_height - self._track_border_thickness)
            )

            painter.save()
            painter.setClipRect(track_rect)
            painter.setPen(Qt.NoPen)
            painter.setBrush(QBrush(fill_color))
            painter.drawRoundedRect(fill_rect, self._track_corner_radius, self._track_corner_radius)
            painter.restore()

        # Draw knob centered at knob_center_x
        knob_rect = QRect(
            int(knob_center_x - knob_radius),
            int(track_rect.center().y() - self._knob_height / 2),
            int(self._knob_width),
            int(self._knob_height)
        )

        # Limit knob corner radius to half of the smaller dimension (width or height)
        self._knob_corner_radius = min(min(self._knob_width, self._knob_height) / 2, self._knob_corner_radius)

        knob_color = self._knob_color if not self._is_disabled else self._disabled_knob_color
        if self._is_hovered and not self._is_disabled:
            knob_color = self._hover_knob_color

        knob_color = QColor(*[int(c * 255) if i == 3 else c for i, c in enumerate(knob_color)])
        knob_border_color = QColor(*[int(c * 255) if i == 3 else c for i, c in enumerate(self._knob_border_color)])

        # Only set pen if border thickness is greater than 0
        if self._knob_border_thickness > 0:
            painter.setPen(QPen(knob_border_color, self._knob_border_thickness))
            # Adjust knob rect to account for border thickness
            border_offset = self._knob_border_thickness / 2
            knob_rect = QRect(
                int(knob_center_x - knob_radius + border_offset),
                int(track_rect.center().y() - self._knob_height / 2 + border_offset),
                int(self._knob_width - self._knob_border_thickness),
                int(self._knob_height - self._knob_border_thickness)
            )
        else:
            painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(knob_color))
        painter.drawRoundedRect(knob_rect, self._knob_corner_radius, self._knob_corner_radius)

    # -------------------------------------------------
    # Event Handling
    # -------------------------------------------------
    def update_value(self, x):
        """Update the slider value based on mouse position."""
        # Calculate the effective track width considering knob width
        effective_width = self.width() - self._knob_width

        # Clamp the x position so the knob stays within the effective track
        clamped_x = max(self._knob_width / 2, min(x, self.width() - self._knob_width / 2))

        # Map the clamped x position to the slider value
        new_value = self._min_value + ((clamped_x - self._knob_width / 2) / (effective_width - self._knob_width)) * (
                    self._max_value - self._min_value)

        # Update the slider value only if it has changed
        new_value = int(max(self._min_value, min(self._max_value, new_value)))
        if new_value != self._value:
            self._value = new_value
            self.value_changed.emit(self._value)

            # Update the value label if it exists
            if self._show_text and self._value_label:
                self._update_value_label_position()

            self.update()

    def mousePressEvent(self, event):
        """Handle mouse press events."""
        if event.button() == Qt.LeftButton and not self._is_disabled:
            self.update_value(int(event.position().x()))

    def mouseMoveEvent(self, event):
        """Handle mouse move events."""
        if event.buttons() == Qt.LeftButton and not self._is_disabled:
            self.update_value(int(event.position().x()))

    def enterEvent(self, event):
        """Handle mouse enter events."""
        super().enterEvent(event)
        self._is_hovered = True
        self.update()

    def leaveEvent(self, event):
        """Handle mouse leave events."""
        super().leaveEvent(event)
        self._is_hovered = False
        self.update()

    # -------------------------------------------------
    # Getters and Setters (only for PvSlider-specific properties)
    # -------------------------------------------------
    # We inherit x, y, width, height, is_visible from PvText

    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        if value <= 0:
            return  # Prevent invalid scale values
        self._scale = value
        # Update all dimensions based on scale
        self.setFixedWidth(int(self._base_width * value))  # Use proper method to set width
        self.setFixedHeight(int(self._base_height * value))  # Use proper method to set height
        self._track_height = int(self._base_track_height * value)
        self._knob_width = int(self._base_knob_width * value)
        self._knob_height = int(self._base_knob_height * value)
        self._track_corner_radius = int(self._base_track_corner_radius * value)
        self._knob_corner_radius = int(self._base_knob_corner_radius * value)
        # Don't scale track border thickness
        self._track_border_thickness = self._base_track_border_thickness
        # Don't scale knob border thickness
        self._knob_border_thickness = self._base_knob_border_thickness

        # Update label positions if they exist
        if self._show_text:
            knob_radius = self._knob_width // 2
            if self._min_label:
                self._min_label.x = self.x + knob_radius
                self._min_label.y = self.y + self.height() - self._label_offset_below
            if self._max_label:
                self._max_label.x = self.x + self.width() - knob_radius - self._max_label.width
                self._max_label.y = self.y + self.height() - self._label_offset_below
            if self._value_label:
                self._update_value_label_position()

        self.update()

    @property
    def min_value(self):
        return self._min_value

    @min_value.setter
    def min_value(self, value):
        self._min_value = value
        if self._show_text and self._min_label:
            self._min_label.text = str(value)
        self.update()

    @property
    def max_value(self):
        return self._max_value

    @max_value.setter
    def max_value(self, value):
        self._max_value = value
        if self._show_text and self._max_label:
            self._max_label.text = str(value)
        self.update()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        new_value = int(max(self._min_value, min(self._max_value, value)))
        if new_value != self._value:
            self._value = new_value
            if self._show_text and self._value_label:
                self._update_value_label_position()
            self.value_changed.emit(self._value)
            self.update()

    @property
    def track_color(self):
        return self._track_color

    @track_color.setter
    def track_color(self, value):
        self._track_color = value
        self.update()

    @property
    def track_border_color(self):
        return self._track_border_color

    @track_border_color.setter
    def track_border_color(self, value):
        self._track_border_color = value
        self.update()

    @property
    def fill_color(self):
        return self._fill_color

    @fill_color.setter
    def fill_color(self, value):
        self._fill_color = value
        self.update()

    @property
    def knob_color(self):
        return self._knob_color

    @knob_color.setter
    def knob_color(self, value):
        self._knob_color = value
        self.update()

    @property
    def knob_border_color(self):
        return self._knob_border_color

    @knob_border_color.setter
    def knob_border_color(self, value):
        self._knob_border_color = value
        self.update()

    @property
    def track_corner_radius(self):
        return self._track_corner_radius

    @track_corner_radius.setter
    def track_corner_radius(self, value):
        self._base_track_corner_radius = value
        self._track_corner_radius = int(value * self._scale)
        self.update()

    @property
    def knob_corner_radius(self):
        return self._knob_corner_radius

    @knob_corner_radius.setter
    def knob_corner_radius(self, value):
        self._base_knob_corner_radius = value
        self._knob_corner_radius = int(value * self._scale)
        self.update()

    @property
    def knob_width(self):
        return self._knob_width

    @knob_width.setter
    def knob_width(self, value):
        self._base_knob_width = value
        self._knob_width = int(value * self._scale)
        self.update()

    @property
    def knob_height(self):
        return self._knob_height

    @knob_height.setter
    def knob_height(self, value):
        self._base_knob_height = value
        self._knob_height = int(value * self._scale)
        self.update()

    @property
    def track_border_thickness(self):
        return self._track_border_thickness

    @track_border_thickness.setter
    def track_border_thickness(self, value):
        self._base_track_border_thickness = value
        # Don't scale border thickness
        self._track_border_thickness = value
        self.update()

    @property
    def knob_border_thickness(self):
        return self._knob_border_thickness

    @knob_border_thickness.setter
    def knob_border_thickness(self, value):
        self._base_knob_border_thickness = value
        self._knob_border_thickness = value  # Don't apply scale to border thickness
        self.update()

    @property
    def track_height(self):
        return self._track_height

    @track_height.setter
    def track_height(self, value):
        self._base_track_height = value
        self._track_height = int(value * self._scale)
        self.update()

    @property
    def on_change(self):
        return self._on_change

    @on_change.setter
    def on_change(self, callback):
        self._on_change = callback
        # Connect the callback to the value_changed signal if provided
        if callable(callback):
            self.value_changed.connect(callback)

    @property
    def show_text(self):
        return self._show_text

    @show_text.setter
    def show_text(self, value):
        if self._show_text != value:
            self._show_text = value
            if value and not self._min_label:
                # Create labels if they don't exist yet
                self._create_labels()
            elif not value and self._min_label:
                # Remove labels if they exist
                if self._min_label:
                    self._min_label.deleteLater()
                    self._min_label = None
                if self._max_label:
                    self._max_label.deleteLater()
                    self._max_label = None
                if self._value_label:
                    self._value_label.deleteLater()
                    self._value_label = None

    @property
    def font_color(self):
        return self._font_color

    @font_color.setter
    def font_color(self, value):
        self._font_color = value
        self._update_label_properties()

    @property
    def bold(self):
        return self._bold

    @bold.setter
    def bold(self, value):
        self._bold = value
        self._update_label_properties()

    @property
    def italic(self):
        return self._italic

    @italic.setter
    def italic(self, value):
        self._italic = value
        self._update_label_properties()

    @property
    def underline(self):
        return self._underline

    @underline.setter
    def underline(self, value):
        self._underline = value
        self._update_label_properties()

    @property
    def strikeout(self):
        return self._strikeout

    @strikeout.setter
    def strikeout(self, value):
        self._strikeout = value
        self._update_label_properties()

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, value):
        self._font_size = value
        self._update_label_properties()

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)
        # Propagate visibility to labels
        if self._show_text:
            self._update_label_properties()
        self.update()

    @property
    def is_disabled(self):
        return self._is_disabled

    @is_disabled.setter
    def is_disabled(self, value):
        self._is_disabled = value
        self.setEnabled(not value)
        # Propagate disabled state to labels
        # if self._show_text:
        #     self._update_label_properties()
        # self.update()

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = max(0.0, min(1.0, value))
        self.update()
        # Propagate to labels if they exist
        self._update_label_properties()

    # -------------------------------------------------
    # Helper to update label properties
    # -------------------------------------------------
    def _update_label_properties(self):
        if self._min_label:
            self._min_label.font_color = self._font_color
            self._min_label.bold = self._bold
            self._min_label.italic = self._italic
            self._min_label.underline = self._underline
            self._min_label.strikeout = self._strikeout
            self._min_label.font_size = self._font_size
            self._min_label.opacity = self._opacity
            self._min_label.is_disabled = self._is_disabled
            self._min_label.is_visible = self._is_visible
        if self._max_label:
            self._max_label.font_color = self._font_color
            self._max_label.bold = self._bold
            self._max_label.italic = self._italic
            self._max_label.underline = self._underline
            self._max_label.strikeout = self._strikeout
            self._max_label.font_size = self._font_size
            self._max_label.opacity = self._opacity
            self._max_label.is_disabled = self._is_disabled
            self._max_label.is_visible = self._is_visible
        if self._value_label:
            self._value_label.font_color = self._font_color
            self._value_label.bold = self._bold
            self._value_label.italic = self._italic
            self._value_label.underline = self._underline
            self._value_label.strikeout = self._strikeout
            self._value_label.font_size = self._font_size
            self._value_label.opacity = self._opacity
            self._value_label.is_disabled = self._is_disabled
            self._value_label.is_visible = self._is_visible

    # -------------------------------------------------
    # Print Properties
    # -------------------------------------------------
    def print_properties(self):
        """Prints all the current properties of the slider."""
        print(f"""
        Slider Properties:
        ------------------
        Position: ({self.x}, {self.y})
        Size: ({self.width()}, {self.height()})
        Scale: {self.scale}

        Value Range:
        ------------
        Min Value: {self.min_value}
        Max Value: {self.max_value}
        Current Value: {self.value}

        Track Properties:
        ----------------
        Track Color: {self.track_color}
        Track Border Color: {self.track_border_color}
        Fill Color: {self.fill_color}
        Track Height: {self.track_height}
        Track Corner Radius: {self.track_corner_radius}
        Track Border Thickness: {self.track_border_thickness}

        Knob Properties:
        ---------------
        Knob Color: {self.knob_color}
        Knob Border Color: {self.knob_border_color}
        Hover Knob Color: {self._hover_knob_color}
        Disabled Knob Color: {self._disabled_knob_color}
        Knob Corner Radius: {self.knob_corner_radius}
        Knob Border Thickness: {self.knob_border_thickness}

        State:
        ------
        Is Disabled: {self.is_disabled}
        Is Visible: {self.is_visible}
        """)

    def _create_labels(self):
        """Create PvText labels for minimum, maximum, and current values."""
        knob_radius = self._knob_width // 2
        label_width = 50
        label_height = 20

        # Min label: positioned at the start (left) of the track
        min_label_x = self.x + knob_radius
        min_label_y = self.y + self.height() - self._label_offset_below
        self._min_label = PvText(
            container=self.parent(),
            x=min_label_x,
            y=min_label_y,
            width=label_width,
            height=label_height,
            text=str(self._min_value),
            font_color=self._font_color,
            font_size=self._font_size,
            bold=self._bold,
            italic=self._italic,
            underline=self._underline,
            strikeout=self._strikeout
        )
        self._min_label.opacity = self._opacity

        # Max label: positioned at the end (right) of the track
        max_label_x = self.x + self.width() - knob_radius - label_width
        max_label_y = min_label_y  # Same vertical alignment as min label
        self._max_label = PvText(
            container=self.parent(),
            x=max_label_x,
            y=max_label_y,
            width=label_width,
            height=label_height,
            text=str(self._max_value),
            font_color=self._font_color,
            font_size=self._font_size,
            bold=self._bold,
            italic=self._italic,
            underline=self._underline,
            strikeout=self._strikeout
        )
        # Align the max label text to the right so digits end at the track edge
        self._max_label.text_alignment = "right"
        self._max_label.opacity = self._opacity

        # Value label: positioned above the knob (centered horizontally)
        value_label_x = self.x + self.width() // 2 - label_width // 2
        value_label_y = self.y - self._label_offset_above
        self._value_label = PvText(
            container=self.parent(),
            x=value_label_x,
            y=value_label_y,
            width=label_width,
            height=label_height,
            text=str(self._value),
            font_color=self._font_color,
            font_size=self._font_size,
            bold=self._bold,
            italic=self._italic,
            underline=self._underline,
            strikeout=self._strikeout
        )
        self._value_label.opacity = self._opacity

        self._update_value_label_position()

    def _update_value_label_position(self):
        """Update the value label position according to current slider value."""
        if not self._value_label:
            return

        self._value_label.text = str(self._value)
        label_height = self._value_label.height()

        knob_radius = self._knob_width // 2
        track_left_x = knob_radius
        track_right_x = self.width() - knob_radius
        track_width = track_right_x - track_left_x

        # Normalize the value within [0, 1]
        value_range = self._max_value - self._min_value
        if value_range == 0:
            value_range = 1  # Prevent division by zero

        value_percent = (self._value - self._min_value) / value_range

        # Calculate knob X position (left edge)
        knob_x = int(track_left_x + value_percent * (track_width - self._knob_width))

        # Center the knob vertically within the track
        knob_y = self.y + (self.height() - self._knob_height) // 2

        # Position value label slightly to the right of the knob
        value_label_offset_x = 2
        self._value_label.x = self.x + knob_x + value_label_offset_x
        self._value_label.y = knob_y - self._label_offset_above


# -------------------------------------------------
# Example Usage
# -------------------------------------------------

# Example Usage with PyVisual
if __name__ == "__main__":
    # Create PyVisual app
    app = pv.PvApp()

    # Create PyVisual window
    window = pv.PvWindow(title="PvSlider Example", is_resizable=True)

    # Standard slider with labels
    slider = PvSlider(
        window, x=50, y=70, width=300, height=40,
        min_value=0, max_value=100, value=30,
        track_color=(220, 220, 220, 1),
        track_border_color=(0, 0, 0, 1),
        fill_color=(70, 130, 180, 1),
        knob_color=(255, 255, 255, 1),
        knob_border_color=(100, 100, 100, 1),
        show_text=True,
        underline=True,
        opacity=0.2,
        on_change=lambda value: print(f"Slider 1 value changed to: {value}")
    )

    # Colored slider with custom styling and labels
    slider2 = PvSlider(
        window, x=50, y=200, width=300, height=40, value=50,
        min_value=0, max_value=200,
        track_color=(220, 220, 220, 1),
        track_border_color=(180, 180, 180, 1),
        track_height=20,
        fill_color=(255, 100, 100, 1),
        knob_color=(200, 0, 0, 1),
        knob_border_color=(150, 150, 150, 1),
        track_corner_radius=10,
        knob_corner_radius=15,
        knob_width=30,
        knob_height=30,
        show_text=True,
        font_size=10,
        on_change=lambda value: print(f"Slider 2 value changed to: {value}"),
        bold=True,
        italic=True,
        strikeout=True,
        is_visible=True,
        opacity=0.2
    )

    # Show the window
    window.show()

    # Run the PyVisual app
    app.run()