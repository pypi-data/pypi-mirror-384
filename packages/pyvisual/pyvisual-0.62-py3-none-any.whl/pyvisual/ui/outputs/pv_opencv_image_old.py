import cv2
from kivy.clock import Clock
from kivy.graphics import Color, Line, RoundedRectangle, Rectangle, StencilPush, StencilUse, StencilPop, StencilUnUse
from kivy.graphics.texture import Texture
from kivy.uix.widget import Widget
from pyvisual.utils.pv_timer import PvTimer




class PvOpenCVImage(Widget):
    def __init__(self, container=None, x=0, y=0, width=640, height=480,
                 is_visible=True, tag=None, border_color=(1, 1, 1, 1),
                 border_thickness=2, corner_radius=10):
        super().__init__(size_hint=(None, None), pos=(x, y), size=(width, height))

        # Bind position and size changes to update the canvas dynamically
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # Existing initialization code
        self.tag = tag
        self.is_visible = is_visible
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.corner_radius = corner_radius

        self.frame_texture = None
        self.video_writer = None  # For saving video
        self.is_saving = False
        self.video_filename = None
        self.fps = 30

        # Add to window if provided
        if container:
            container.add_widget(self)

        self.set_visibility(self.is_visible)
        self._update_canvas()

    def _update_canvas(self, *args):
        """Update the canvas elements, ensuring rounded corners for the image and the border."""
        self.canvas.clear()
        with self.canvas:
            # Step 1: Stencil to clip the image into a rounded rectangle shape
            StencilPush()
            Color(1, 1, 1, 1)  # White mask for stencil
            RoundedRectangle(pos=self.pos, size=self.size,
                             radius=[self.corner_radius] * 4)
            StencilUse()

            # Step 2: Draw the image texture within the stencil
            if self.frame_texture:
                Rectangle(texture=self.frame_texture, pos=self.pos, size=self.size)

            StencilUnUse()
            StencilPop()

            # Step 3: Draw the border on top
            if self.border_thickness:
                Color(*self.border_color)
                Line(rounded_rectangle=(
                    self.x + self.border_thickness / 2,  # Offset inward
                    self.y + self.border_thickness / 2,  # Offset inward
                    self.width - self.border_thickness,  # Adjust width
                    self.height - self.border_thickness,  # Adjust height
                    self.corner_radius,  # Corner radius
                ), width=self.border_thickness)

    def update_image(self, frame):
        """Update the displayed image with a given OpenCV frame."""
        if frame is not None:
            # Save the original BGR frame if saving is enabled
            if self.is_saving and self.video_writer is not None:
                self.video_writer.write(frame)

            # Convert BGR to RGB for display in Kivy
            flipped_frame = cv2.flip(frame, 0)
            frame_rgb = cv2.cvtColor(flipped_frame, cv2.COLOR_BGR2RGB)

            # Create a texture for Kivy display
            self.frame_texture = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
            self.frame_texture.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            # Redraw the canvas to update the image
            self._update_canvas()

    def set_border(self, color=None, thickness=None, corner_radius=None):
        """Set the border properties."""
        if color is not None:
            self.border_color = color
        if thickness is not None:
            self.border_thickness = thickness
        if corner_radius is not None:
            self.corner_radius = corner_radius
        self._update_canvas()

    def start_saving(self, filename, duration=None, width=640, height=480, fps=30,callback=None):
        """Start saving the displayed images to a video file."""
        if not self.is_saving:
            self.video_filename = filename
            self.fps = fps
            frame_width, frame_height = width, height  # Ensure consistent dimensions
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Use 'mp4v' for MP4 format
            self.video_writer = cv2.VideoWriter(self.video_filename, fourcc, self.fps, (frame_width, frame_height))
            self.is_saving = True

            print(f"Video saving started: {self.video_filename}")

            if duration:
                def stop_and_update(dt):
                    self.stop_saving(callback=callback)

                Clock.schedule_once(stop_and_update, duration)

    def stop_saving(self, callback=None):
        """Stop saving the video file and call the callback if provided."""
        if self.is_saving and self.video_writer is not None:
            self.video_writer.release()
            self.video_writer = None
            self.is_saving = False
            print(f"Video saved: {self.video_filename}")
            if callback:
                callback()  # Call the provided callback function


    def set_visibility(self, is_visible):
        """Show or hide the image."""
        self.is_visible = is_visible
        self.opacity = 1 if is_visible else 0


if __name__ == "__main__":
    import pyvisual as pv

    window = pv.PvWindow()

    # Create an OpenCVImage instance with a border
    image_widget = PvOpenCVImage(
        container=window, x=50, y=50, width=480, height=480,
        border_color=(1, 0, 0, 1), border_thickness=2, corner_radius=240
    )

    # Simulate video frames
    cap = cv2.VideoCapture(0)  # Open webcam or replace with your video source

    def update_frame(dt):
        ret, frame = cap.read()
        if ret:
            frame = frame[:,400:880]
            image_widget.update_image(frame)

    PvTimer.schedule_function(update_frame, 1 / 30)  # Update at 30 FPS

    window.show()
    cap.release()
