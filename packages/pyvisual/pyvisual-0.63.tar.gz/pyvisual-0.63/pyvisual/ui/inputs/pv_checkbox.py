from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase
from pyvisual.ui.outputs.pv_text import PvText


class PvCheckbox(PvText):
    def __init__(self, container,
                 checkbox_size=20, spacing=10, text_position='right',
                 checked_color=(76, 204, 76, 1), unchecked_color=(255, 255, 255, 1),
                 border_color=(0, 0, 0, 1), border_thickness=1,
                 checkmark_color=(0, 0, 0, 1), checkmark_size=10, checkmark_type="✓",
                 corner_radius=0, is_checked=False, checked=None, toggle_callback=None,
                 on_change=None, **kwargs):

        # Save the text value if it's in kwargs
        self._temp_text = kwargs.pop('text', "Checkbox") if 'text' in kwargs else "Checkbox"

        # Skip create_layout and configure_style from parent's __init__
        # We'll call our own versions after initialization
        self._skip_parent_layout = True

        # Initialize PvText with kwargs but with empty text
        kwargs_copy = kwargs.copy()
        QLabel.__init__(self, "", container)  # Initialize QLabel directly

        # Move relevant code from PvText.__init__ here
        x = kwargs_copy.get('x', 50)
        y = kwargs_copy.get('y', 50)
        width = kwargs_copy.get('width', 200)
        self.move(x, y)
        self.setFixedWidth(width)

        # Store attributes from PvText that we need
        self.font = None
        self._font = kwargs_copy.get('font', "Roboto")
        self._strikeout = kwargs_copy.get('strikeout', False)
        self._font_size = int(kwargs_copy.get('font_size', 14))
        self._font_color = kwargs_copy.get('font_color', (0, 0, 0, 1))
        self._bold = kwargs_copy.get('bold', False)
        self._italic = kwargs_copy.get('italic', False)
        self._underline = kwargs_copy.get('underline', False)
        self._idle_color = kwargs_copy.get('idle_color', (255, 255, 255, 0))
        self._text_alignment = kwargs_copy.get('text_alignment', "left")
        self._height = kwargs_copy.get('height', None)
        self._is_visible = kwargs_copy.get('is_visible', True)
        self._opacity = kwargs_copy.get('opacity', 1)
        self._multiline = kwargs_copy.get('multiline', True)
        self._line_spacing = kwargs_copy.get('line_spacing', 1.0)

        # Get paddings
        raw_paddings = kwargs_copy.get('paddings', [0, 0, 0, 0])
        if isinstance(raw_paddings, tuple):
            raw_paddings = list(raw_paddings)
        self._paddings = raw_paddings

        self._on_hover = kwargs_copy.get('on_hover', None)
        self._on_click = kwargs_copy.get('on_click', None)
        self._on_release = kwargs_copy.get('on_release', None)
        self._tag = kwargs_copy.get('tag', None)

        # Checkbox-specific properties
        self._checkbox_size = checkbox_size
        self._spacing = spacing
        self._text_position = text_position
        # Use 'checked' if provided, otherwise use 'is_checked'
        self._is_checked = checked if checked is not None else is_checked
        self._toggle_callback = toggle_callback
        self._on_change = on_change

        # Checkbox appearance
        self._checked_color = checked_color
        self._unchecked_color = unchecked_color
        self._border_color = border_color
        self._border_thickness = border_thickness
        self._checkmark_color = checkmark_color
        self._checkmark_size = checkmark_size
        self._checkmark_type = checkmark_type
        self._corner_radius = corner_radius


        # Now call our own layout functions
        self.create_layout()
        self.configure_style()

        # Set the text now that everything is set up
        self.setText(self._temp_text)

        # Update layout based on text position
        self._update_layout()

    def create_layout(self):
        """Override create_layout to avoid the text() issue"""
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
            font_metrics = self.fontMetrics()
            if self._multiline:
                # Use an empty string as placeholder
                rect = font_metrics.boundingRect(
                    QRect(0, 0, self.width(), 0),
                    Qt.TextWordWrap | Qt.AlignLeft,
                    ""
                )
                adjusted_height = int(rect.height() * self._line_spacing + self._paddings[1] + self._paddings[3])
            else:
                adjusted_height = int(
                    font_metrics.height() * self._line_spacing + self._paddings[1] + self._paddings[3])

            # Make sure height is at least as tall as checkbox
            min_height = self._checkbox_size + self._paddings[1] + self._paddings[
                3]  # Use actual top and bottom paddings
            adjusted_height = max(adjusted_height, min_height)
            self.setFixedHeight(adjusted_height)

    def configure_style(self):
        """Override configure_style from PvText"""
        # Style sheet configuration
        font_r, font_g, font_b, font_a = self._font_color
        style = f"color: rgba({font_r}, {font_g}, {font_b}, {font_a});"

        # Add background color if provided
        if self._idle_color is not None:
            bg_r, bg_g, bg_b, bg_a = self._idle_color
            style += f" background-color: rgba({bg_r}, {bg_g}, {bg_b}, {bg_a});"

        # Remove border styling
        style += " border: none;"

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

    def _update_layout(self):
        """Update the layout based on text position"""
        # Adjust the text alignment based on the checkbox position
        if self._text_position == 'left':
            # Text on left, checkbox on right
            checkbox_x = self.width() - self._checkbox_size - self._paddings[2]  # Use right padding
            text_width = self.width() - self._checkbox_size - self._spacing - self._paddings[0] - self._paddings[2]
            # Set margins with independent padding values (Left, Top, Right, Bottom)
            self.setContentsMargins(
                self._paddings[0],  # Left
                self._paddings[1],  # Top
                self._checkbox_size + self._spacing + self._paddings[2],  # Right
                self._paddings[3]  # Bottom
            )
        else:  # 'right'
            # Checkbox on left, text on right
            checkbox_x = self._paddings[0]  # Use left padding
            text_width = self.width() - self._checkbox_size - self._spacing - self._paddings[0] - self._paddings[2]
            # Set margins with independent padding values (Left, Top, Right, Bottom)
            self.setContentsMargins(
                self._checkbox_size + self._spacing + self._paddings[0],  # Left
                self._paddings[1],  # Top
                self._paddings[2],  # Right
                self._paddings[3]  # Bottom
            )

        # Save the checkbox position for rendering
        self._checkbox_x = checkbox_x
        # Adjust checkbox y position to account for top padding
        self._checkbox_y = self._paddings[1] + (
                    self.height() - self._paddings[1] - self._paddings[3] - self._checkbox_size) // 2

    def paintEvent(self, event):
        """Override paint event to draw the checkbox alongside the text"""
        # Call the parent class paint event to render the text
        super().paintEvent(event)

        # Create the painter
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate the checkbox position (already set in _update_layout)
        checkbox_rect = QRect(
            self._checkbox_x,
            self._checkbox_y,
            self._checkbox_size,
            self._checkbox_size
        )

        # Draw the checkbox background
        bg_color = self._checked_color if self._is_checked else self._unchecked_color
        painter.setPen(Qt.NoPen)
        r, g, b, a = bg_color
        painter.setBrush(QColor(r, g, b, int(a * 255) if a <= 1 else a))

        if self._corner_radius > 0:
            painter.drawRoundedRect(
                checkbox_rect,
                self._corner_radius,
                self._corner_radius
            )
        else:
            painter.drawRect(checkbox_rect)

        # Draw the checkbox border
        if self._border_thickness > 0:
            r, g, b, a = self._border_color
            border_pen = QPen(QColor(r, g, b, int(a * 255) if a <= 1 else a))
            border_pen.setWidth(self._border_thickness)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)

            if self._corner_radius > 0:
                painter.drawRoundedRect(
                    checkbox_rect,
                    self._corner_radius,
                    self._corner_radius
                )
            else:
                painter.drawRect(checkbox_rect)

        # Draw the checkmark if checked
        if self._is_checked:
            painter.setPen(Qt.NoPen)
            r, g, b, a = self._checkmark_color
            painter.setBrush(QColor(r, g, b, int(a * 255) if a <= 1 else a))

            if self._checkmark_type == "✓":  # Custom checkmark
                # Draw a checkmark
                pen = QPen(QColor(r, g, b, int(a * 255) if a <= 1 else a))
                pen.setWidth(2)
                painter.setPen(pen)

                # Calculate checkmark points
                center_x = checkbox_rect.x() + checkbox_rect.width() // 2
                center_y = checkbox_rect.y() + checkbox_rect.height() // 2

                # Adjust size based on checkbox size
                size_factor = self._checkmark_size / 20.0

                # Draw checkmark as a polyline
                points = [
                    (center_x - 5 * size_factor, center_y),
                    (center_x - 2 * size_factor, center_y + 4 * size_factor),
                    (center_x + 5 * size_factor, center_y - 5 * size_factor)
                ]

                # Draw the line segments
                painter.drawLine(int(points[0][0]), int(points[0][1]),
                                 int(points[1][0]), int(points[1][1]))
                painter.drawLine(int(points[1][0]), int(points[1][1]),
                                 int(points[2][0]), int(points[2][1]))
            else:
                # Draw the provided checkmark symbol as text
                font = QFont()  # Create a new font instead of using painter.font()
                font.setPixelSize(self._checkmark_size)
                # Reset all font properties to ensure no inheritance
                font.setBold(False)
                font.setItalic(False)
                font.setUnderline(False)
                font.setStrikeOut(False)
                painter.setFont(font)

                r, g, b, a = self._checkmark_color
                painter.setPen(QColor(r, g, b, int(a * 255) if a <= 1 else a))

                # Use font metrics to get the bounding rect of the checkmark
                font_metrics = painter.fontMetrics()
                text = self._checkmark_type
                text_rect = font_metrics.boundingRect(text)

                # Calculate the position to center the text in the checkbox
                x = checkbox_rect.x() + (checkbox_rect.width() - text_rect.width()) // 2 - text_rect.left()
                y = checkbox_rect.y() + (checkbox_rect.height() - text_rect.height()) // 2 - text_rect.top()

                painter.drawText(x, y, text)

        painter.end()

    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            old_state = self._is_checked
            self._is_checked = not self._is_checked

            # Call the toggle callback if provided
            if self._toggle_callback:
                self._toggle_callback(self)

            # Call on_change handler if provided
            if self._on_change:
                self._on_change(self._is_checked)

            # Call original on_click handler if set
            if self._on_click:
                self._on_click(self)

            # Update the widget
            self.update()

        super().mousePressEvent(event)

    def resizeEvent(self, event):
        """Handle resize event to update layout"""
        super().resizeEvent(event)
        self._update_layout()

    # Properties
    @property
    def is_checked(self):
        return self._is_checked

    @is_checked.setter
    def is_checked(self, value):
        if self._is_checked != value:
            self._is_checked = value
            self.update()

            # Call the toggle callback if provided
            if self._toggle_callback:
                self._toggle_callback(self)

    @property
    def text_position(self):
        return self._text_position

    @text_position.setter
    def text_position(self, value):
        if value in ['left', 'right']:
            self._text_position = value
            self._update_layout()
            self.update()

    @property
    def checked_color(self):
        return self._checked_color

    @checked_color.setter
    def checked_color(self, value):
        self._checked_color = value
        self.update()

    @property
    def unchecked_color(self):
        return self._unchecked_color

    @unchecked_color.setter
    def unchecked_color(self, value):
        self._unchecked_color = value
        self.update()

    @property
    def toggle_callback(self):
        return self._toggle_callback

    @toggle_callback.setter
    def toggle_callback(self, callback):
        self._toggle_callback = callback

    # Alias for is_checked
    @property
    def checked(self):
        return self._is_checked

    @checked.setter
    def checked(self, value):
        self.is_checked = value

    @property
    def spacing(self):
        return self._spacing

    @spacing.setter
    def spacing(self, value):
        self._spacing = value
        self._update_layout()
        self.update()

    @property
    def on_change(self):
        return self._on_change

    @on_change.setter
    def on_change(self, callback):
        self._on_change = callback

    @property
    def checkbox_size(self):
        return self._checkbox_size

    @checkbox_size.setter
    def checkbox_size(self, value):
        self._checkbox_size = value
        self._update_layout()
        self.update()

    @property
    def border_color(self):
        return self._border_color

    @border_color.setter
    def border_color(self, value):
        self._border_color = value
        self.update()

    @property
    def border_thickness(self):
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value
        self.update()

    @property
    def checkmark_color(self):
        return self._checkmark_color

    @checkmark_color.setter
    def checkmark_color(self, value):
        self._checkmark_color = value
        self.update()

    @property
    def checkmark_size(self):
        return self._checkmark_size

    @checkmark_size.setter
    def checkmark_size(self, value):
        self._checkmark_size = value
        self.update()

    @property
    def checkmark_type(self):
        return self._checkmark_type

    @checkmark_type.setter
    def checkmark_type(self, value):
        self._checkmark_type = value
        self.update()

    @property
    def corner_radius(self):
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
        self.update()


# ===================================================
# ================ Example Usage ====================
# ===================================================
if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()
    window = pv.PvWindow(title="PvCheckbox Example", is_resizable=True)


    def handle_checkbox_change(is_checked, checkbox_name):
        if is_checked:
            print(f"{checkbox_name} is checked now")
        else:
            print(f"{checkbox_name} is unchecked now")


    # Checkbox with custom colors
    checkbox1 = PvCheckbox(window,
                           text="Checkbox 1",
                           x=50, y=150, paddings=(8, 6, 0, 0),
                           font_size=14,
                           checked_color=(76, 204, 76, 1),
                           unchecked_color=(240, 240, 240, 1),
                           border_color=(0, 0, 0, 1),
                           border_thickness=2,
                           checkmark_color=(0, 0, 0, 1),
                           checkmark_size=12,
                           checkbox_size=20,
                           corner_radius=500,
                           is_checked=False,
                           on_change=lambda checked: print(
                               f"Checkbox 1 is {'checked' if checked else 'unchecked'} now"))

    # Checkbox with custom colors
    checkbox2 = PvCheckbox(window,
                           text="Checkbox 2",
                           x=50, y=200, paddings=(10, 0, 0, 0),
                           font_size=14,
                           checked_color=(76, 204, 76, 1),
                           unchecked_color=(240, 240, 240, 1),
                           border_color=(0, 0, 0, 1),
                           border_thickness=4,
                           checkmark_color=(0, 0, 0, 1),
                           checkmark_size=12,
                           checkbox_size=20,
                           corner_radius=4,
                           is_checked=False,
                           on_change=lambda checked: print(
                               f"Checkbox 2 is {'checked' if checked else 'unchecked'} now"))

    window.show()
    app.run()