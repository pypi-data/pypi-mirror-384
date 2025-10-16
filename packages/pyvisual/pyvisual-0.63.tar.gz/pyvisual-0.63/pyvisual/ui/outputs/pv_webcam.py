from typing import TYPE_CHECKING, Optional
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPixmap, QTransform, QPainterPath, QColor, QPen, QImage
from PySide6.QtCore import Qt, QThread, Signal, QSize
from PySide6.QtGui import QMovie
from pyvisual.ui.outputs.pv_text import PvText
import os

if TYPE_CHECKING:
    import cv2
    import numpy as np

# Global variables to hold our lazy-loaded modules
_cv2: Optional['cv2'] = None
_np: Optional['np'] = None


def get_cv2():
    """Lazily load and return the cv2 module."""
    global _cv2
    if _cv2 is None:
        import cv2 as cv2_module
        _cv2 = cv2_module
    return _cv2


def get_np():
    """Lazily load and return the numpy module."""
    global _np
    if _np is None:
        import numpy as np_module
        _np = np_module
    return _np


# Worker thread for capturing frames from the webcam.
class WebcamWorker(QThread):
    # Using Signal(object) to emit the frame (a NumPy array)
    frameCaptured = Signal(object)

    def __init__(self, webcam_id, width, height, frame_processor=None, parent=None):
        super().__init__(parent)
        self._webcam_id = webcam_id
        self._width = width
        self._height = height
        self._frame_processor = frame_processor
        self._running = True

    def run(self):
        cv2 = get_cv2()  # Lazy load cv2
        cap = cv2.VideoCapture(self._webcam_id)
        cap.set(3, self._width)
        cap.set(4, self._height)
        while self._running:
            ret, frame = cap.read()
            if not ret:
                continue
            if self._frame_processor:
                frame = self._frame_processor(frame)
            self.frameCaptured.emit(frame)
        cap.release()

    def stop(self):
        self._running = False
        self.wait()


# PvWebcam class that displays webcam frames using a separate thread.
class PvWebcam(QWidget):
    def __init__(self, container=None, x=0, y=0, webcam_id=0, width=640, height=360, corner_radius=0,
                 flip_v=False, flip_h=False, rotate=0, scale=1.0, is_visible=True, opacity=1, tag=None,
                 border_color=None, border_hover_color=None, border_thickness=5,
                 on_hover=None, on_click=None, on_release=None, frame_processor=None,
                 auto_start=True,placeholder_text="Press start to turn on the webcam", **kwargs):
        super().__init__(container)
        # ---------------------------------------------------------
        # Geometry and Basic Settings
        # ---------------------------------------------------------
        self._x = x
        self._y = y
        self._target_width = width
        self._target_height = height
        self._corner_radius = corner_radius
        self._flip_v = flip_v
        self._flip_h = flip_h
        self._rotate = rotate
        self._scale = scale
        self._is_visible = is_visible
        self._opacity = opacity
        self._pixmap = None  # Current frame as QPixmap
        self._tag = tag

        # ---------------------------------------------------------
        # Border and Hover Properties
        # ---------------------------------------------------------
        self._border_thickness = border_thickness * 2  # maintain doubling logic
        self._hovered = False

        # ---------------------------------------------------------
        # Callbacks for Mouse Events
        # ---------------------------------------------------------
        self._on_hover = on_hover
        self._on_click = on_click
        self._on_release = on_release

        # ---------------------------------------------------------
        # Convert provided color tuples to QColor if available
        # ---------------------------------------------------------
        self._border_color = (
            QColor(border_color[0], border_color[1], border_color[2], int(border_color[3] * 255))
            if border_color else None
        )
        self._border_hover_color = (
            QColor(border_hover_color[0], border_hover_color[1], border_hover_color[2],
                   int(border_hover_color[3] * 255))
            if border_hover_color else self._border_color
        )

        # Set up the spinner GIF using QMovie.
        current_dir = os.path.dirname(os.path.abspath(__file__))
        gif_path = os.path.join(current_dir, "../../assets/gifs/loading.gif")
        self._spinner_movie = QMovie(gif_path)
        self._spinner_movie.setScaledSize(QSize(40, 40))  # Set the desired size here

        self._spinner_movie.frameChanged.connect(self.update)
        self._spinner_movie.start()

        self._placeholderText = PvText(self,
                                       text=placeholder_text,
                                       x=0, y=0,
                                       width=self.width,
                                       height=self.height,
                                       text_alignment="center",
                                       font_size=14,
                                       font_color=(150, 150, 150, 1))
        # Show the placeholder only when the webcam is not running.
        self._placeholderText.setVisible(not auto_start)

        # ---------------------------------------------------------
        # Webcam and Frame Processing Setup
        # ---------------------------------------------------------
        self._webcam_id = webcam_id
        self._frame_processor = frame_processor
        if auto_start:
            self._worker = WebcamWorker(webcam_id, width, height, frame_processor)
            self._worker.frameCaptured.connect(self.update_frame)
            self._worker.start()
            self._is_running = True
        else:
            self._worker = None
            self._is_running = False

        # ---------------------------------------------------------
        # Widget Setup
        # ---------------------------------------------------------
        self.setMouseTracking(True)
        self.setGeometry(self._x, self._y, int(self._target_width * self._scale),
                         int(self._target_height * self._scale))
        self.setVisible(self._is_visible)

    def update_frame(self, frame: object):
        cv2 = get_cv2()  # Lazy load cv2
        np = get_np()  # Lazy load numpy
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channels = frame.shape
        bytes_per_line = channels * width
        q_img = QImage(frame.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self._pixmap = QPixmap.fromImage(q_img)
        self.configure_style()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
        painter.setOpacity(self._opacity)

        if self._corner_radius > 0:
            path = QPainterPath()
            path.addRoundedRect(self.rect(), self._corner_radius, self._corner_radius)
            painter.setClipPath(path)

        if self._pixmap is None:
            # Fill with a placeholder color
            placeholder_color = QColor(211, 211, 211)
            painter.fillRect(self.rect(), placeholder_color)
            # Only show the spinner if the webcam process is running.
            if self._is_running:
                spinner_pixmap = self._spinner_movie.currentPixmap()
                if not spinner_pixmap.isNull():
                    # Center the spinner gif in the widget
                    spinner_rect = spinner_pixmap.rect()
                    spinner_rect.moveCenter(self.rect().center())
                    painter.drawPixmap(spinner_rect.topLeft(), spinner_pixmap)
        else:
            painter.drawPixmap(0, 0, self._pixmap)

        border_color = self._border_hover_color if self._hovered else self._border_color
        if border_color and self._border_thickness > 0:
            pen = QPen(border_color, self._border_thickness)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect(), self._corner_radius, self._corner_radius)

    def configure_style(self):
        if self._pixmap is None or self._pixmap.isNull():
            return

        transform = QTransform()
        if self._flip_h:
            transform.scale(-1, 1)
        if self._flip_v:
            transform.scale(1, -1)
        transform.rotate(self._rotate)
        transformed = self._pixmap.transformed(transform, Qt.SmoothTransformation)
        final_width = int(self._target_width * self._scale)
        final_height = int(self._target_height * self._scale)
        self._pixmap = transformed.scaled(final_width, final_height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setGeometry(self._x, self._y, self._pixmap.width(), self._pixmap.height())

    def enterEvent(self, event):
        self._hovered = True
        if self._on_hover:
            self._on_hover(self)
        self.update()

    def leaveEvent(self, event):
        self._hovered = False
        self.update()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == Qt.LeftButton and self._on_click:
            self._on_click(self)

    def mouseReleaseEvent(self, event):
        super().mouseReleaseEvent(event)
        if event.button() == Qt.LeftButton and self._on_release:
            self._on_release(self)

    def closeEvent(self, event):
        self.stop()
        event.accept()

    # ---------------------------------------------------------
    # Methods for Running Control
    # ---------------------------------------------------------
    def start(self):
        """Starts the webcam if not already running."""
        if not self._is_running:
            self._worker = WebcamWorker(self._webcam_id, self._target_width, self._target_height, self._frame_processor)
            self._worker.frameCaptured.connect(self.update_frame)
            self._worker.start()
            self._is_running = True
            self._placeholderText.setVisible(False)

    def stop(self):
        """Stops the webcam if it is running."""
        if self._is_running and self._worker:
            try:
                self._worker.frameCaptured.disconnect(self.update_frame)
            except Exception:
                pass
            self._worker.stop()
            self._worker = None
            self._is_running = False
            self._pixmap = None  # Clear current frame.
            self._placeholderText.setVisible(True)
            self.update()

    def resizeEvent(self, event):
        """Keep the placeholder centered and sized with the widget."""
        super().resizeEvent(event)
        self._placeholderText.setGeometry(0, 0, self.width, self.height)

    @property
    def is_running(self):
        return self._is_running

    # ---------------------------------------------------------
    # Property Getters/Setters
    # ---------------------------------------------------------
    @property
    def scale(self):
        return self._scale

    @scale.setter
    def scale(self, value):
        self._scale = value
        self.configure_style()
        self.update()

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self.setGeometry(self._x, self._y, self.width, self.height)
        self.update()

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self.setGeometry(self._x, self._y, self.width, self.height)
        self.update()

    @property
    def width(self):
        return int(self._target_width * self._scale)

    @width.setter
    def width(self, value):
        self._target_width = value
        self.configure_style()
        self.update()

    @property
    def height(self):
        return int(self._target_height * self._scale)

    @height.setter
    def height(self, value):
        self._target_height = value
        self.configure_style()
        self.update()

    @property
    def corner_radius(self):
        return self._corner_radius

    @corner_radius.setter
    def corner_radius(self, value):
        self._corner_radius = value
        self.update()

    @property
    def flip_v(self):
        return self._flip_v

    @flip_v.setter
    def flip_v(self, value):
        self._flip_v = value
        self.update()

    @property
    def flip_h(self):
        return self._flip_h

    @flip_h.setter
    def flip_h(self, value):
        self._flip_h = value
        self.update()

    @property
    def rotate(self):
        return self._rotate

    @rotate.setter
    def rotate(self, value):
        self._rotate = value
        self.update()

    @property
    def is_visible(self):
        return self._is_visible

    @is_visible.setter
    def is_visible(self, value):
        self._is_visible = value
        self.setVisible(value)
        self.update()

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, value):
        self._opacity = value
        self.update()

    @property
    def tag(self):
        return self._tag

    @tag.setter
    def tag(self, value):
        self._tag = value

    @property
    def border_color(self):
        if self._border_color:
            return (self._border_color.red(), self._border_color.green(),
                    self._border_color.blue(), self._border_color.alphaF())
        return None

    @border_color.setter
    def border_color(self, value):
        if value is None:
            self._border_color = None
        else:
            self._border_color = QColor(value[0], value[1], value[2], int(value[3] * 255))
        self.update()

    @property
    def border_hover_color(self):
        if self._border_hover_color:
            return (self._border_hover_color.red(), self._border_hover_color.green(),
                    self._border_hover_color.blue(), self._border_hover_color.alphaF())
        return None

    @border_hover_color.setter
    def border_hover_color(self, value):
        if value is None:
            self._border_hover_color = self._border_color
        else:
            self._border_hover_color = QColor(value[0], value[1], value[2], int(value[3] * 255))
        self.update()

    @property
    def border_thickness(self):
        return self._border_thickness

    @border_thickness.setter
    def border_thickness(self, value):
        self._border_thickness = value * 2
        if value == 0:
            self._border_color = None
            self._border_hover_color = None
        self.update()

    @property
    def frame_processor(self):
        return self._frame_processor

    @frame_processor.setter
    def frame_processor(self, func):
        self._frame_processor = func
        if hasattr(self, "_worker"):
            self._worker._frame_processor = func

    # ---------------------------------------------------------
    # Utility: Print Current Properties
    # ---------------------------------------------------------
    def print_properties(self):
        print(f"""
        PvWebcam Properties:
        ---------------------
        x: {self.x}
        y: {self.y}
        width: {self.width}
        height: {self.height}
        corner_radius: {self.corner_radius}
        flip_v: {self.flip_v}
        flip_h: {self.flip_h}
        rotate: {self.rotate}
        scale: {self.scale}
        is_visible: {self.is_visible}
        opacity: {self.opacity}
        border_color: {self.border_color}
        border_hover_color: {self.border_hover_color}
        border_thickness: {self.border_thickness}
        tag: {self.tag}
        is_running: {self.is_running}
        """)


# ---------------------------------------------------------
# Example Usage
# ---------------------------------------------------------
if __name__ == "__main__":
    import pyvisual as pv  # Assuming your pyvisual application module


    def my_frame_processor(frame):
        cv2 = get_cv2()  # Lazy load cv2 inside the frame processor
        cv2.rectangle(frame, (50, 50), (200, 200), (0, 0, 255), 3)
        return frame


    app = pv.PvApp()
    window = pv.PvWindow(title="PvWebcam Example with Running Control")
    webcam = PvWebcam(
        container=window,
        x=50,
        y=50,
        webcam_id=0,
        width=640,
        height=480,
        corner_radius=20,
        flip_h=False,
        rotate=0,
        scale=0.75,
        opacity=1,
        border_color=(255, 0, 0, 1),
        border_hover_color=(0, 255, 0, 1),
        border_thickness=5,
        on_hover=lambda w: print("Hovered over PvWebcam", w.tag),
        on_click=lambda w: print("PvWebcam clicked", w.tag),
        on_release=lambda w: print("PvWebcam released", w.tag),
        frame_processor=my_frame_processor
    )
    webcam.tag = "Sample PvWebcam"
    webcam.print_properties()
    webcam2 = PvWebcam(
        container=window,
        x=10,
        y=50,
        webcam_id=0,
        width=640,
        height=480,
        corner_radius=20,
        flip_h=False,
        rotate=0,
        scale=0.75,
        opacity=1,
        border_color=(255, 0, 0, 1),
        border_hover_color=(0, 255, 0, 1),
        border_thickness=0,
        on_hover=lambda w: print("Hovered over PvWebcam", w.tag),
        on_click=lambda w: print("PvWebcam clicked", w.tag),
        on_release=lambda w: print("PvWebcam released", w.tag),
        frame_processor=my_frame_processor
    )
    # For demonstration, you can later stop the webcam:
    # webcam.stop()

    window.show()
    app.run()
