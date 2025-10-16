from PySide6.QtWidgets import QGraphicsDropShadowEffect
import re
from PySide6.QtCore import Qt, QPointF, QRectF
from PySide6.QtGui import QPainter, QPen, QColor, QPixmap


def add_shadow_effect(object, shadow_config=None):
    """Adds or updates the shadow effect on the button."""
    shadow = QGraphicsDropShadowEffect(object)

    if shadow_config is None:
        object.setGraphicsEffect(None)
        return

    try:
        # Use the provided shadow config or the default
        shadow_config = shadow_config or object._box_shadow
        shadow_values = shadow_config.split()
        offset_x = float(shadow_values[0].replace('px', ''))
        offset_y = float(shadow_values[1].replace('px', ''))
        blur_radius = float(shadow_values[2].replace('px', ''))
        rgba_string = " ".join(shadow_values[4:]).replace('rgba(', '').replace(')', '')
        rgba_values = [float(v) for v in rgba_string.split(',')]
        # Set shadow properties
        if offset_x != 0 or offset_y != 0:
            shadow.setOffset(offset_x, offset_y)
        shadow.setBlurRadius(blur_radius)
        shadow.setColor(QColor(
            int(rgba_values[0]),  # Red
            int(rgba_values[1]),  # Green
            int(rgba_values[2]),  # Blue
            int(rgba_values[3] * 255)  # Alpha (scaled to 0-255)
        ))

        object.setGraphicsEffect(shadow)

    except (IndexError, ValueError) as e:
        print(f"Failed to parse shadow: {shadow_config}. Error: {e}")


def update_svg_color(svg_widget, color):
    """
    Updates the SVG path fill and stroke colors to the same value,
    unless the fill is 'none', in which case it is left unchanged.

    Args:
        svg_widget: The widget where the SVG content is loaded.
        color: Tuple of RGB values (R, G, B) for the fill and stroke color.

    Notes:
        The SVG content must be preloaded into the widget as `svg_widget._original_svg`.
    """
    try:
        # Convert color to RGB format
        svg_color = f"rgb({int(color[0])}, {int(color[1])}, {int(color[2])})"

        # Retrieve the original SVG content
        if not hasattr(svg_widget, "_original_svg"):
            raise AttributeError("The SVG content must be preloaded into the widget as _original_svg.")

        svg_content = svg_widget._original_svg

        # Update fill and stroke attributes
        def update_attributes(match):
            tag_content = match.group(0)

            # Update fill attribute unless it is 'none'
            if 'fill="none"' not in tag_content:
                if 'fill="' in tag_content:
                    tag_content = re.sub(r'fill="[^"]*"', f'fill="{svg_color}"', tag_content)
                else:
                    # Update or add stroke attribute
                    if 'stroke="' in tag_content:
                        tag_content = re.sub(r'stroke="[^"]*"', f'stroke="{svg_color}"', tag_content)
                    else:
                        tag_content = tag_content.replace('<path', f'<path fill="{svg_color}"', 1)

            return tag_content

        # Apply the attribute updates to all relevant SVG elements
        updated_svg = re.sub(
            r'<(path|rect|circle|ellipse|line|polygon|polyline)([^>/]*)(/?)>',
            update_attributes,
            svg_content
        )
        # Reload the updated SVG content into the widget
        svg_widget.load(updated_svg.encode("utf-8"))

    except Exception as e:
        print(f"Error updating SVG color: {e}")


def draw_border(widget, painter: QPainter, border_color, border_thickness, corner_radius=0):
    """
    Draws a border around the given widget using QPainter.

    :param widget: The widget to draw the border for.
    :param painter: The QPainter instance used for drawing.
    :param border_color: The color of the border as a tuple (R, G, B, A) or QColor-compatible value.
    :param border_thickness: Thickness of the border in pixels (int or tuple with 4 values for each side).
    :param corner_radius: Radius of the border corners for rounded edges.
    """
    painter.setRenderHint(QPainter.Antialiasing)

    color = QColor(border_color[0], border_color[1], border_color[2], int(border_color[3] * 255))
    pen = QPen(color)
    if isinstance(border_thickness, int):
        if border_thickness <= 0:
            return

        # Create a pen with the specified color and thickness

        pen.setWidth(border_thickness)
        painter.setPen(pen)

        # Adjust the rectangle to account for the border thickness
        rect = QRectF(widget.rect())
        rect.adjust(border_thickness / 2, border_thickness / 2, -border_thickness / 2, -border_thickness / 2)

        # Draw the rounded rectangle
        painter.setBrush(Qt.NoBrush)  # Only draw the border
        painter.drawRoundedRect(rect, corner_radius, corner_radius)

    elif isinstance(border_thickness, tuple) and len(border_thickness) == 4:
        if corner_radius > 0:
            print("Corner radius must be zero when using tuple border thickness.")

        # Unpack the border thickness values
        left, top, right, bottom = border_thickness
        # Adjust the rectangle for drawing lines
        rect = widget.rect()

        # Top border
        if top > 0:
            pen.setWidth(top)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(rect.left() + left / 2, rect.top() + top / 2),
                QPointF(rect.right() - right / 2, rect.top() + top / 2)
            )

        # Right border
        if right > 0:
            pen.setWidth(right)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(rect.right() - right / 2, rect.top() + top / 2),
                QPointF(rect.right() - right / 2, rect.bottom() - bottom / 2)
            )

        # Bottom border
        if bottom > 0:
            pen.setWidth(bottom)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(rect.right() - right / 2, rect.bottom() - bottom / 2),
                QPointF(rect.left() + left / 2, rect.bottom() - bottom / 2)
            )

        # Left border
        if left > 0:
            pen.setWidth(left)
            painter.setPen(pen)
            painter.drawLine(
                QPointF(rect.left() + left / 2, rect.top() + top / 2),
                QPointF(rect.left() + left / 2, rect.bottom() - bottom / 2)
            )

    else:
        raise TypeError("border_thickness must be an int or a tuple with 4 values (top, right, bottom, left).")
