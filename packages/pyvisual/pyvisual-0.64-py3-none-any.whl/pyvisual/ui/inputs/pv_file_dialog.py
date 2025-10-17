from pyvisual.ui.inputs.pv_button import PvButton
from PySide6.QtWidgets import QFileDialog
import os


class PvFileDialog(PvButton):
    """
    A file browser button that opens a file dialog on click,
    with a dashed border style, and optionally supports file drag-and-drop.

    The dialog mode determines what type of dialog is shown:
      - "open": Open a file (default)
      - "save": Save a file as...
      - "folder": Select a folder

    :param container: The parent container.
    :param file_filter: The file filter for the file dialog (used in "open" or "save" modes).
    :param on_file_selected: A callback function called when a file or folder is selected.
    :param enable_drag_drop: If True, allows drag-and-drop of files/folders onto the button.
    :param dialog_mode: Specifies the dialog type: "open", "save", or "folder".
    """

    def __init__(self, container, files_filter="All Files (*.*)", on_file_selected=None, enable_drag_drop=True,
                 dialog_mode="open",show_file_name=False, **kwargs):
        super().__init__(container, **kwargs)
        # Initialize new properties
        self.files_filter = files_filter
        self.on_file_selected = on_file_selected
        self.enable_drag_drop = enable_drag_drop
        self.dialog_mode = dialog_mode
        self.show_file_name= show_file_name
        self._path = ""  # Initialize the path variable
        self._on_click = self.open_dialog
        # self.configure_style()  # Optionally call if needed

    def open_dialog(self, btn):
        result = None
        if self.dialog_mode == "open":
            result, _ = QFileDialog.getOpenFileName(self, "Select File", "", self.files_filter)
        elif self.dialog_mode == "save":
            result, _ = QFileDialog.getSaveFileName(self, "Save File As", "", self.files_filter)
        elif self.dialog_mode == "folder":
            result = QFileDialog.getExistingDirectory(self, "Select Folder")
        else:
            # Fallback to open file if mode is unrecognized
            result, _ = QFileDialog.getOpenFileName(self, "Select File", "", self.files_filter)

        if result:
            self.path = result  # Store the selected path
            if self.show_file_name:
                file_name = os.path.basename(result)
                self.text = file_name
            if self.on_file_selected:
                self.on_file_selected(result)

    # --- Drag & Drop Event Handlers ---
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        urls = event.mimeData().urls()
        if urls:
            # Only process the first file/folder dropped
            file_path = urls[0].toLocalFile()
            self.path = file_path  # Store the selected path
            file_name = os.path.basename(file_path)
            self.text = file_name
            if self.on_file_selected:
                self.on_file_selected(file_path)

    # --- Getter and Setter Properties ---
    @property
    def path(self):
        """Get the currently selected file or folder path."""
        return self._path

    @path.setter
    def path(self, value):
        """Set the file or folder path."""
        self._path = value

    @property
    def files_filter(self):
        return self._files_filter

    @files_filter.setter
    def files_filter(self, value):
        self._files_filter = value

    @property
    def on_file_selected(self):
        return self._on_file_selected

    @on_file_selected.setter
    def on_file_selected(self, callback):
        self._on_file_selected = callback

    @property
    def enable_drag_drop(self):
        return self._enable_drag_drop

    @enable_drag_drop.setter
    def enable_drag_drop(self, flag):
        self._enable_drag_drop = flag
        self.setAcceptDrops(flag)

    @property
    def dialog_mode(self):
        return self._dialog_mode

    @dialog_mode.setter
    def dialog_mode(self, mode):
        self._dialog_mode = mode


# ---------------------------------------------------------------------------
# Example Usage
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import pyvisual as pv


    # Callback functions for each dialog mode
    def file_open_callback(path):
        print("Open selected:", path)


    def file_save_callback(path):
        print("Save selected:", path)


    def folder_callback(path):
        print("Folder selected:", path)


    app = pv.PvApp()
    window = pv.PvWindow(title="FileBrowser Examples", is_resizable=True)

    # File Open: Opens a file selection dialog.
    file_open_browser = PvFileDialog(window,
                                    x=50, y=50,
                                    width=300, height=50,
                                    text="Open File",
                                    font_size=14,
                                    files_filter="Images (*.png *.jpg *.jpeg);;All Files (*.*)",
                                    dialog_mode="open",
                                    on_file_selected=file_open_callback,
                                    enable_drag_drop=True)

    # File Save: Opens a dialog for saving a file.
    file_save_browser = PvFileDialog(window,
                                    x=50, y=120,
                                    width=300, height=50,
                                    text="Save File",
                                    font_size=14,
                                    files_filter="Text Files (*.txt);;All Files (*.*)",
                                    dialog_mode="save",
                                    on_file_selected=file_save_callback,
                                    enable_drag_drop=True)

    # Folder Selection: Opens a folder selection dialog.
    folder_browser = PvFileDialog(window,
                                 x=50, y=190,
                                 width=300, height=50,
                                 text="Select Folder",
                                 font_size=14,
                                 dialog_mode="folder",
                                 on_file_selected=folder_callback,
                                 enable_drag_drop=True)

    window.show()
    app.run()
