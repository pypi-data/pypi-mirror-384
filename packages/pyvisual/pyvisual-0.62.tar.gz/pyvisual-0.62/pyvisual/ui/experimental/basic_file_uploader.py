import pyvisual as vi
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import RoundedRectangle, Color, Line
from kivy.core.window import Window as KivyWindow
from kivy.core.text import LabelBase
from kivy.clock import Clock
import tkinter as tk
from tkinter import filedialog
import threading


class DropRegionUploader(Widget):
    def __init__(self, window, x, y, width=300, height=200,visibility = True,
                 text="Drag & Drop Files Here or Click to Upload",
                 idle_color=(0.9, 0.9, 0.9, 1),
                 hover_color=(0.7, 0.7, 0.7, 1),
                 text_color=(0.0, 0.0, 0.0, 1),
                 border_color=(0, 0, 0, 1),
                 border_thickness=2,
                 on_file_selected=None, on_cancel=None,
                 font="Roboto", font_size=16,
                 radius=0,
                 file_types=None,
                 clickable=True,
                 draggable=True):
        """
        Initialize the DropRegionUploader with optional rounded corners, file type filtering,
        and enable/disable for clicking and dragging.

        :param window: The pyvisual.Window instance to add the uploader to.
        :param x: X position of the region.
        :param y: Y position of the region.
        :param width: Width of the region.
        :param height: Height of the region.
        :param text: Instructional text displayed in the region.
        :param idle_color: Background color when idle.
        :param hover_color: Background color when hovered or files are dragged over.
        :param text_color: Color of the instructional text.
        :param border_color: Color of the border.
        :param border_thickness: Thickness of the border.
        :param on_file_selected: Callback function when a file is selected.
        :param on_cancel: Callback function when the dialog is canceled.
        :param font: Font name or file path.
        :param font_size: Size of the font.
        :param radius: Radius for rounded corners. Set to 0 for sharp corners.
        :param file_types: A list of (label, pattern) tuples for acceptable file types.
        :param clickable: If True, clicking the region will open a file dialog and hover color will apply.
        :param draggable: If True, files can be dragged and dropped onto the region.
        """
        super(DropRegionUploader, self).__init__()
        self.size_hint = (None, None)  # Ensure explicit sizing
        self.size = (width, height)
        self.pos = (x, y)
        self.text = text
        self.idle_color = idle_color
        self.hover_color = hover_color
        self.current_color = idle_color
        self.text_color = text_color
        self.border_color = border_color
        self.border_thickness = border_thickness
        self.on_file_selected = on_file_selected
        self.on_cancel = on_cancel
        self.font_size = font_size
        self.radius = radius
        self.file_types = file_types if file_types is not None else [("All Files", "*.*")]

        self.clickable = clickable
        self.draggable = draggable
        self.visibility = visibility

        self.set_visibility(self.visibility)

        # Register custom font if provided
        if font.endswith((".ttf", ".otf")):
            LabelBase.register(name="CustomFont", fn_regular=font)
            self.font_name = "CustomFont"
        else:
            self.font_name = font
        if self.border_thickness == 0:
            self.set_border(border_thickness, (0, 0, 0, 0))

        # Draw the region
        self.draw_region()

        # Add instructional label
        self.label = Label(text=self.text,
                           color=self.text_color,
                           font_name=self.font_name,
                           font_size=self.font_size,
                           halign='center',
                           valign='middle',
                           size_hint=(None, None),
                           size=self.size,
                           pos=self.pos)
        self.label.bind(size=self.update_label, pos=self.update_label)
        self.add_widget(self.label)

        # Bind events
        if self.draggable:
            KivyWindow.bind(on_drop_file=self.on_file_drop)
        # self.bind(on_touch_down=self.on_touch_down)
        KivyWindow.bind(mouse_pos=self.on_mouse_pos)

        # Add the region to the window
        window.add_widget(self)

    def draw_region(self):
        """Draw the rectangular (or rounded) region with border."""
        with self.canvas:
            self.canvas.clear()
            self.bg_color = Color(*self.current_color)
            # Draw a RoundedRectangle for the background
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[self.radius])
            # Draw a Line with the same rounded corners for the border
            self.border_color_instruction = Color(*self.border_color)
            self.border = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, self.radius),
                               width=self.border_thickness)

        # Bind to position and size changes to update the visuals
        self.bind(pos=self.update_region, size=self.update_region)

    def update_region(self, *args):
        """Update the region's background and border when its position or size changes."""
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.bg_rect.radius = [self.radius]
        self.border.rounded_rectangle = (self.x, self.y, self.width, self.height, self.radius)
        self.label.size = self.size
        self.label.pos = self.pos

    def update_label(self, *args):
        """Update the label's size and position."""
        self.label.size = self.size
        self.label.pos = self.pos

    def on_mouse_pos(self, window, pos):
        """Change background color on hover if clickable is True."""
        if not self.clickable:
            # If not clickable, do not change colors on hover.
            return

        if self.is_mouse_over(pos):
            if self.current_color != self.hover_color:
                self.current_color = self.hover_color
                Clock.schedule_once(lambda dt: self.update_bg_color())
        else:
            if self.current_color != self.idle_color:
                self.current_color = self.idle_color
                Clock.schedule_once(lambda dt: self.update_bg_color())

    def update_bg_color(self):
        """Update the background color."""
        self.bg_color.rgba = self.current_color

    def is_mouse_over(self, pos):
        """Check if the mouse is over the region."""
        return (self.x <= pos[0] <= self.x + self.width and
                self.y <= pos[1] <= self.y + self.height)

    def on_touch_down(self, touch):
        """Handle touch events to open file dialog when the region is clicked, if clickable."""
        if self.clickable and self.collide_point(*touch.pos):
            self.open_file_dialog()
            return True
        return False

    def open_file_dialog(self):
        """Open the native OS file chooser dialog in a separate thread."""
        thread = threading.Thread(target=self._open_file_dialog_thread, daemon=True)
        thread.start()

    def _open_file_dialog_thread(self):
        """Thread target to open the file dialog."""
        root = tk.Tk()
        root.withdraw()  # Hide the root window

        try:
            # Open the file dialog with specified file types
            file_path = filedialog.askopenfilename(
                title="Select a File",
                filetypes=self.file_types
            )

            if file_path:
                if self.on_file_selected:
                    Clock.schedule_once(lambda dt: self.on_file_selected(file_path))
            else:
                if self.on_cancel:
                    Clock.schedule_once(lambda dt: self.on_cancel())
        finally:
            root.destroy()  # Destroy the Tkinter root window

    def on_file_drop(self, window, file_path_bytes, *args):
        """
        Handle the file drop event if draggable is True.
        """
        if not self.draggable:
            return

        try:
            file_path = file_path_bytes.decode('utf-8')
        except UnicodeDecodeError:
            file_path = file_path_bytes.decode('latin-1')

        mouse_x, mouse_y = KivyWindow.mouse_pos
        if self.is_position_inside_region(mouse_x, mouse_y):
            if self._file_matches_types(file_path):
                if self.on_file_selected:
                    Clock.schedule_once(lambda dt: self.on_file_selected(file_path))

    def is_position_inside_region(self, x, y):
        """Check if the given position is within the region's boundaries."""
        return (self.x <= x <= self.x + self.width and
                self.y <= y <= self.y + self.height)

    def _file_matches_types(self, file_path):
        """Check if the given file matches the allowed file types."""
        if not self.file_types or self.file_types == [("All Files", "*.*")]:
            return True  # If no restrictions, always return True
        import fnmatch
        for label, pattern in self.file_types:
            # Allow multiple patterns in one spec separated by semicolons for convenience
            sub_patterns = pattern.split(';')
            for sub_pattern in sub_patterns:
                if fnmatch.fnmatch(file_path, sub_pattern.strip()):
                    return True
        return False

    def set_border(self, border_thickness, border_color):
        """Set the border thickness and color, and redraw the border."""
        self.border_thickness = border_thickness
        self.border_color = border_color
        self.draw_region()

    def set_font(self, font_name, font_size):
        """Set the font name or file path and font size."""
        if font_name.endswith((".ttf", ".otf")):
            LabelBase.register(name="CustomFont", fn_regular=font_name)
            self.label.font_name = "CustomFont"
        else:
            self.label.font_name = font_name
        self.label.font_size = font_size

    def set_radius(self, radius):
        """Set the corner radius and update the display."""
        self.radius = radius
        self.update_region()

    def set_visibility(self, visibility):
        """Show or hide the rounded rectangle."""
        if visibility:
            self.opacity = 1
        else:
            self.opacity = 0
        self.visibility = visibility


if __name__ == "__main__":
    import pyvisual as pv

    window = pv.Window()

    def on_file_selected(file_path):
        print(f"Selected file: {file_path}")

    def on_cancel():
        print("File selection canceled.")

    # Example file types: PNG and JPEG files, plus all files option
    file_types = [
        ("PNG Files", "*.png"),
        ("JPEG Files", "*.jpg;*.jpeg"),
        # ("All Files", "*.*")
    ]

    # Create a drop region uploader where clickable is False:
    # No hover color change or click action will occur.
    uploader = DropRegionUploader(
        window=window,
        x=150, y=150,
        width=500, height=300,
        text="Drag & Drop Files Here or Click to Upload",
        idle_color=(0.95, 0.95, 0.95, 1),
        hover_color=(0.8, 0.8, 0.8, 1),
        text_color=(0.2, 0.2, 0.2, 1),
        border_color=(0, 0, 0, 1),
        border_thickness=1,
        on_file_selected=on_file_selected,
        on_cancel=on_cancel,
        font="Roboto",
        font_size=18,
        radius=20,
        file_types=file_types,
        clickable=True,  # No hover change or click
        draggable=True,    # Drag-and-drop still allowed
        visibility=True
    )



    window.show()
