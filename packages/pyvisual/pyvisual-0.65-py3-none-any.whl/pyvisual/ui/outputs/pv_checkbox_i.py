from PySide6.QtWidgets import QLabel, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QRect
from PySide6.QtGui import QPainter, QColor, QPen, QFont, QFontDatabase

from pyvisual.ui.outputs.pv_text import PvText


class PvCheckboxI(PvText):
    def __init__(self, container, 
                 checkbox_size=20, padding=4, spacing=10, text_position='right',
                 checked_color=(76, 204, 76, 1), unchecked_color=(255, 255, 255, 1),
                 border_color=(76, 76, 76, 1), border_thickness=10,
                 checkbox_border_color=(0, 0, 0, 1), checkbox_border_thickness=1,
                 checkmark_color=(0, 0, 0, 1), checkmark_size=12, checkmark_type="✓",
                 checkbox_corner_radius=0, is_checked=False, toggle_callback=None, 
                 **kwargs):
        
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
        self._paddings = kwargs_copy.get('paddings', [0, 0, 0, 0])
        self._on_hover = kwargs_copy.get('on_hover', None)
        self._on_click = kwargs_copy.get('on_click', None)
        self._on_release = kwargs_copy.get('on_release', None)
        self._tag = kwargs_copy.get('tag', None)
        
        # Checkbox-specific properties
        self._checkbox_size = checkbox_size
        self._padding = padding
        self._spacing = spacing
        self._text_position = text_position
        self._is_checked = is_checked
        self._toggle_callback = toggle_callback
        
        # Checkbox appearance
        self._checked_color = checked_color
        self._unchecked_color = unchecked_color
        self._border_color = border_color
        self._border_thickness = border_thickness
        self._checkbox_border_color = checkbox_border_color
        self._checkbox_border_thickness = checkbox_border_thickness
        self._checkmark_color = checkmark_color
        self._checkmark_size = checkmark_size
        self._checkmark_type = checkmark_type
        self._checkbox_corner_radius = checkbox_corner_radius
        
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
            # Avoid using self.text() here which causes the error
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
                adjusted_height = int(font_metrics.height() * self._line_spacing + self._paddings[1] + self._paddings[3])
            
            # Make sure height is at least as tall as checkbox
            min_height = self._checkbox_size + 2 * self._padding
            adjusted_height = max(adjusted_height, min_height)
            self.setFixedHeight(adjusted_height)
    
    def configure_style(self):
        """Override configure_style from PvText"""
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
        
    def _update_layout(self):
        """Update the layout based on text position"""
        # Adjust the text alignment based on the checkbox position
        if self._text_position == 'left':
            # Text on left, checkbox on right
            checkbox_x = self.width() - self._checkbox_size - self._padding
            text_width = self.width() - self._checkbox_size - self._spacing - self._padding * 2
            self.setContentsMargins(self._padding, 0, self._checkbox_size + self._spacing + self._padding, 0)
        else:  # 'right'
            # Checkbox on left, text on right
            checkbox_x = self._padding
            text_width = self.width() - self._checkbox_size - self._spacing - self._padding * 2
            self.setContentsMargins(self._checkbox_size + self._spacing + self._padding, 0, self._padding, 0)
            
        # Save the checkbox position for rendering
        self._checkbox_x = checkbox_x
        self._checkbox_y = (self.height() - self._checkbox_size) // 2
        
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
        
        if self._checkbox_corner_radius > 0:
            painter.drawRoundedRect(
                checkbox_rect,
                self._checkbox_corner_radius,
                self._checkbox_corner_radius
            )
        else:
            painter.drawRect(checkbox_rect)
        
        # Draw the checkbox border
        if self._checkbox_border_thickness > 0:
            r, g, b, a = self._checkbox_border_color
            border_pen = QPen(QColor(r, g, b, int(a * 255) if a <= 1 else a))
            border_pen.setWidth(self._checkbox_border_thickness)
            painter.setPen(border_pen)
            painter.setBrush(Qt.NoBrush)
            
            if self._checkbox_corner_radius > 0:
                painter.drawRoundedRect(
                    checkbox_rect,
                    self._checkbox_corner_radius,
                    self._checkbox_corner_radius
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
                font = painter.font()
                font.setPixelSize(self._checkmark_size)
                painter.setFont(font)
                
                r, g, b, a = self._checkmark_color
                painter.setPen(QColor(r, g, b, int(a * 255) if a <= 1 else a))
                
                painter.drawText(
                    checkbox_rect,
                    Qt.AlignCenter,
                    self._checkmark_type
                )
        
        painter.end()
    
    def mousePressEvent(self, event):
        """Handle mouse press event"""
        if event.button() == Qt.LeftButton:
            self._is_checked = not self._is_checked
            
            # Call the toggle callback if provided
            if self._toggle_callback:
                self._toggle_callback(self)
                
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


# ===================================================
# ================ Example Usage ====================
# ===================================================
if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()
    window = pv.PvWindow(title="PvCheckboxI Example", is_resizable=True)

    # Checkbox with text on right (default)
    checkbox1 = PvCheckboxI(window,
                           text="Checkbox with text on right",
                           x=50, y=50,
                           font_size=14,
                           text_position='right',
                           toggle_callback=lambda cb: print(f"Checkbox 1 state: {cb.is_checked}"))

    # Checkbox with text on left
    checkbox2 = PvCheckboxI(window,
                           text="Checkbox with text on left",
                           x=50, y=100,
                           font_size=14,
                           text_position='left',
                           toggle_callback=lambda cb: print(f"Checkbox 2 state: {cb.is_checked}"))

    # Checkbox with custom colors
    checkbox3 = PvCheckboxI(window,
                           text="Checkbox with custom colors",
                           x=50, y=150,
                           font_size=14,
                           checked_color=(100, 150, 255, 1),  # Blue checkbox when checked
                           border_color=(50, 50, 50, 1),
                           checkmark_color=(255, 255, 255, 1),  # White checkmark
                           toggle_callback=lambda cb: print(f"Checkbox 3 state: {cb.is_checked}"))

    window.show()
    app.run() 