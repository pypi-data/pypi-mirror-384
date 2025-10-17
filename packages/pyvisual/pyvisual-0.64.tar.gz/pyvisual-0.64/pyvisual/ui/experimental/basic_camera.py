import cv2
from kivy.graphics.texture import Texture
from kivy.uix.image import Image as KivyImage
from kivy.clock import Clock

class OpenCVCamera(KivyImage):
    def __init__(self, window=None, x=0, y=0, width=640, height=480, camera_index=0, is_visible=True, tag=None):
        super().__init__(size_hint=(None, None), pos=(x, y), size=(width, height))

        self.camera_index = camera_index
        self.cap = cv2.VideoCapture(self.camera_index)
        self.tag = tag
        self.is_visible = is_visible
        self.frame_texture = None
        self.current_frame = None
        self.is_playing = False

        # Check if the camera opened successfully
        if not self.cap.isOpened():
            raise ValueError(f"Could not open camera with index {self.camera_index}")

        # Add to window if provided
        if window:
            window.add_widget(self)

        self.set_visibility(self.is_visible)

    def play(self):
        """Start the camera feed."""
        if not self.is_playing:
            self.is_playing = True
            Clock.schedule_interval(self.update, 1 / 30.0)  # 30 FPS

    def pause(self):
        """Pause the camera feed."""
        if self.is_playing:
            self.is_playing = False
            Clock.unschedule(self.update)

    def update(self, dt):
        """Capture a frame from the OpenCV camera and update the texture."""
        if not self.cap.isOpened():
            return

        ret, frame = self.cap.read()
        if ret:
            self.current_frame = cv2.flip(frame, 0)  # Flip the frame vertically

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(self.current_frame, cv2.COLOR_BGR2RGB)

            # Create a texture
            self.frame_texture = Texture.create(size=(frame_rgb.shape[1], frame_rgb.shape[0]), colorfmt='rgb')
            self.frame_texture.blit_buffer(frame_rgb.tobytes(), colorfmt='rgb', bufferfmt='ubyte')

            # Assign the texture to the widget if visible
            if self.is_visible:
                self.texture = self.frame_texture

    def get_frame(self):
        """Return the latest OpenCV frame, applying any transformations."""
        if self.current_frame is not None:
            return self.current_frame
        else:
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    self.current_frame = cv2.flip(frame, 0)  # Apply the same flip as in update
                    return self.current_frame
        return None

    def set_visibility(self, is_visible):
        """Set the visibility of the widget without stopping the camera feed."""
        self.is_visible = is_visible
        self.opacity = 1 if is_visible else 0

    def set_position(self, x, y):
        """Update the position of the camera widget."""
        self.pos = (x, y)

    def set_size(self, width, height):
        """Update the size of the camera widget."""
        self.size = (width, height)

    def release(self):
        """Release the OpenCV camera resource."""
        if self.cap:
            self.cap.release()

    def __del__(self):
        self.release()

if __name__ == "__main__":
    import pyvisual as pv
    from pyvisual.ui.more.opencv_image import OpenCVImage

    window = pv.Window()

    # Create an OpenCVCamera instance
    camera = OpenCVCamera(window=window, x=0, y=0, width=1280, height=720, camera_index=1, is_visible=False)
    image_widget = OpenCVImage(window=window, x=-200, y=0, width=1280, height=720)

    # Start the camera feed
    camera.play()

    is_recording = False
    video_filename = f"output.avi"

    def save_2sec_video(_):
        image_widget.start_saving(video_filename,duration=2)
        print("Video Recording Started")
    def process_frame(_):
        frame = camera.get_frame()
        if frame is not None:
            # Convert to grayscale for example processing
            # gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            image_widget.update_image(frame)


    # Start processing frames
    Clock.schedule_interval(process_frame, 1 / 30.0)  # 30 FPS

    pv.BasicButton(window,x=50,y=500,text="Start Saving",on_click=save_2sec_video)
    window.show()