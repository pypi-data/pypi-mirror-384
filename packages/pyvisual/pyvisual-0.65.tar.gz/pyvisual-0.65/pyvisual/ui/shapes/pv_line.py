from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtCore import QPoint


class PvLine(QWidget):
    def __init__(self, container, points, thickness=1, color=(255, 0, 0, 1), is_visible=True, opacity=1, tag=None):
        super().__init__(container)

        # Store properties
        self._points = points
        self._thickness = thickness
        self._color = color
        self._is_visible = is_visible
        self._opacity = opacity
        self._tag = tag

        # Set visibility
        self.setVisible(is_visible)

        # Set opacity
        self.setWindowOpacity(opacity)

        # Adjust widget size to fit points
        self.adjust_size()

    def adjust_size(self):
        """Adjust the widget size to encompass the line points."""
        x_coords = [point[0] for point in self._points]
        y_coords = [point[1] for point in self._points]

        # Calculate the bounding box
        self._min_x = min(x_coords)
        self._min_y = min(y_coords)
        self._max_x = max(x_coords)
        self._max_y = max(y_coords)

        # Set geometry
        self.setGeometry(self._min_x, self._min_y, self._max_x - self._min_x, self._max_y - self._min_y)

    def paintEvent(self, event):
        if not self._is_visible:
            return

        painter = QPainter(self)
        # Enable antialiasing
        painter.setRenderHint(QPainter.Antialiasing)
        # Set opacity
        painter.setOpacity(self._opacity)

        pen = QPen()
        pen.setWidth(self._thickness)
        pen.setColor(QColor(int(self._color[0]),
                            int(self._color[1]),
                            int(self._color[2]),
                            int(self._color[3] * 255)))
        painter.setPen(pen)

        # Draw lines using normalized points
        for i in range(len(self._points) - 1):
            start_point = QPoint(self._points[i][0] - self._min_x, self._points[i][1] - self._min_y)
            end_point = QPoint(self._points[i + 1][0] - self._min_x, self._points[i + 1][1] - self._min_y)
            painter.drawLine(start_point, end_point)

    # Getters and Setters
    @property
    def points(self):
        return self._points

    @points.setter
    def points(self, points):
        self._points = points
        self.adjust_size()
        self.update()

    @property
    def thickness(self):
        return self._thickness

    @thickness.setter
    def thickness(self, thickness):
        self._thickness = thickness
        self.update()

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.update()

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, is_visible):
        self._is_visible = is_visible
        self.setVisible(is_visible)

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, opacity):
        self._opacity = opacity
        self.setWindowOpacity(opacity)


# Example Usage
if __name__ == "__main__":
    import pyvisual as pv

    app = pv.PvApp()

    # Create a window
    window = pv.PvWindow(title="PvLine Example")

    # Create a PvLine
    line = PvLine(
        container=window,
        points=[(10, 10), (100, 100), (200, 50)],
        thickness=2,
        color=(255, 0, 0, 1),  # Red color
        is_visible=True,
    )
    # Show the window
    window.show()

    # Run the application
    app.run()
