from PySide6.QtWidgets import QApplication

class PvApp:
    """Class to manage the QApplication singleton."""
    _instance = None

    def __init__(self):
        if PvApp._instance is not None:
            raise RuntimeError("PvApp instance already exists! Use PvApp.instance() to get it.")
        PvApp._instance = self
        self._app = QApplication([])

    @staticmethod
    def instance():
        if PvApp._instance is None:
            PvApp()
        return PvApp._instance._app

    def run(self):
        """Run the application event loop."""
        self._app.exec()



# Example Usage
if __name__ == "__main__":
    # Initialize the application
    import pyvisual as pv

    app = PvApp()

    # Create a window
    window = pv.PvWindow(title="PyVisual APP")
    # Show the window
    window.show()

    # Run the application
    app.run()
