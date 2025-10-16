import os
from PySide6.QtWidgets import QStackedWidget, QWidget, QVBoxLayout, QMainWindow
from PySide6.QtCore import Qt, QPoint, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup


# --- PvPages Class Definition ---
class PvPages(QStackedWidget):
    """
    A pagination container that manages full-size pages.
    Initialize it by passing your PvWindow instance (which should have
    a 'root_widget' and a 'layout' attribute), and it automatically adds itself
    to the window's layout.

    Each page is created internally as a plain QWidget, and you can add elements
    to a page with add_element_to_page().

    If animation_duration > 0, page transitions will be animated (slide effect)
    in the specified orientation: "horizontal" or "vertical".
    """

    def __init__(self, window: QWidget, animation_duration: int = 0, animation_orientation: str = "horizontal"):
        # Use the window's root widget as the parent.
        super().__init__(window.root_widget)
        self._pages = []
        self.setContentsMargins(0, 0, 0, 0)
        self.animation_duration = animation_duration  # Duration in milliseconds.
        # Normalize orientation input.
        self.animation_orientation = animation_orientation.lower() if animation_orientation.lower() in ("horizontal", "vertical") else "horizontal"
        self._current_animation = None
        self._on_page_change = None  # Callback function for page changes
        # Automatically add this PvPages widget to the window's layout.
        window.layout.addWidget(self)

    def create_page(self, name: str = None, bg_color: str = None, bg_image: str = None) -> int:
        """
        Creates a new page as a plain QWidget, adds it to the stack, and returns its index.
        Optionally, specify an object name, a background color (CSS color string, e.g. "#FFCCCC"),
        and/or a background image (file path or URL).
        """
        page = QWidget()
        page.setContentsMargins(0, 0, 0, 0)
        style_str = ""
        if bg_color:
            style_str += f"background-color: {bg_color};"
        if bg_image:
            style_str += (
                f"background-image: url({bg_image}); "
                "background-repeat: no-repeat; "
                "background-position: center; "
                "background-size: cover;"
            )
        if style_str:
            page.setStyleSheet(style_str)
        if name:
            page.setObjectName(name)
        self.addWidget(page)
        self._pages.append(page)
        # Set the initial geometry for the new page.
        page.setGeometry(0, 0, self.width(), self.height())
        return len(self._pages) - 1

    def add_element_to_page(self, page_index: int, element: QWidget, x: int = None, y: int = None):
        """
        Adds an element (e.g. PvButton, PvLabel) to the page specified by page_index.
        If x and y coordinates are provided, the element is moved to that location.
        """
        if 0 <= page_index < len(self._pages):
            page = self._pages[page_index]
            element.setParent(page)
            if x is not None and y is not None:
                element.move(x, y)
            element.show()

    def remove_page(self, index: int):
        """
        Remove the page at the given index.
        """
        if 0 <= index < self.count():
            page = self.widget(index)
            self.removeWidget(page)
            self._pages.remove(page)
            page.deleteLater()

    def set_current_page(self, index: int):
        """
        Switch to the page at the given index.
        If animation_duration > 0, animate the transition by sliding the pages
        either horizontally or vertically based on animation_orientation.
        """
        if 0 <= index < self.count():
            prev_index = self.currentIndex()
            
            if self.animation_duration > 0 and prev_index != index:
                current_page = self.currentWidget()
                next_page = self.widget(index)
                # Determine slide direction based on index ordering.
                direction = 1 if index > prev_index else -1

                # Position the next page off-screen based on the animation orientation.
                if self.animation_orientation == "horizontal":
                    next_page.setGeometry(self.width() * direction, 0, self.width(), self.height())
                    start_value_next = QPoint(self.width() * direction, 0)
                    end_value_current = QPoint(-self.width() * direction, 0)
                else:  # vertical animation
                    next_page.setGeometry(0, self.height() * direction, self.width(), self.height())
                    start_value_next = QPoint(0, self.height() * direction)
                    end_value_current = QPoint(0, -self.height() * direction)

                next_page.show()

                # Animate current page moving out.
                anim_current = QPropertyAnimation(current_page, b"pos")
                anim_current.setDuration(self.animation_duration)
                anim_current.setEasingCurve(QEasingCurve.OutCubic)
                anim_current.setStartValue(current_page.pos())
                anim_current.setEndValue(end_value_current)

                # Animate next page moving in.
                anim_next = QPropertyAnimation(next_page, b"pos")
                anim_next.setDuration(self.animation_duration)
                anim_next.setEasingCurve(QEasingCurve.OutCubic)
                anim_next.setStartValue(start_value_next)
                anim_next.setEndValue(QPoint(0, 0))

                group = QParallelAnimationGroup()
                group.addAnimation(anim_current)
                group.addAnimation(anim_next)
                self._current_animation = group  # Keep a reference so it isn't garbage collected.
                # When finished, set the current index to the new page and call callback.
                def on_animation_finished():
                    self.setCurrentIndex(index)
                    if self._on_page_change:
                        self._on_page_change(prev_index, index)
                
                group.finished.connect(on_animation_finished)
                group.start()
            else:
                if prev_index != index:
                    self.setCurrentIndex(index)
                    if self._on_page_change:
                        self._on_page_change(prev_index, index)

    def next_page(self):
        """
        Move to the next page with wrap-around behavior.
        """
        next_index = (self.currentIndex() + 1) % self.count()
        self.set_current_page(next_index)

    def previous_page(self):
        """
        Move to the previous page with wrap-around behavior.
        """
        prev_index = (self.currentIndex() - 1) % self.count()
        self.set_current_page(prev_index)

    @property
    def current_page(self) -> QWidget:
        """
        Returns the currently displayed page.
        """
        return self.currentWidget()

    @property
    def on_page_change(self):
        """
        Gets the callback function for page changes.
        The callback receives (prev_index, current_index) as parameters.
        """
        return self._on_page_change

    @on_page_change.setter
    def on_page_change(self, callback):
        """
        Sets the callback function for page changes.
        The callback should accept two parameters: (prev_index, current_index).
        Set to None to disable the callback.
        """
        self._on_page_change = callback

    def resizeEvent(self, event):
        """
        Ensure that each page is resized to fill the available area
        whenever the PvPages container is resized.
        """
        super().resizeEvent(event)
        for page in self._pages:
            page.setGeometry(0, 0, self.width(), self.height())


# --- Example Usage ---
if __name__ == "__main__":
    import pyvisual as pv  # Your custom framework providing PvApp, PvWindow, PvButton, etc.

    # Initialize the application and main window using your pv classes.
    app = pv.PvApp()
    window = pv.PvWindow(title="PvPages with Animations Example", is_resizable=True)

    # Create an instance of PvPages by passing the window,
    # setting animation_duration to 500ms and choosing vertical animation.
    pages = PvPages(window, animation_duration=500, animation_orientation="horizontal")

    # Create the first page with a light red background.
    page1_index = pages.create_page("page1", bg_color="#FFCCCC")
    # Create a button (without a parent) and add it to page1 at coordinates (0, 0).
    btn_to_page2 = pv.PvButton(None, text="Go to Page 2")
    pages.add_element_to_page(page1_index, btn_to_page2, x=0, y=0)

    # Create the second page with a light green background.
    page2_index = pages.create_page("page2", bg_color="#CCFFCC")
    btn_to_page1 = pv.PvButton(None, text="Go to Page 1")
    pages.add_element_to_page(page2_index, btn_to_page1, x=0, y=200)

    # Set callbacks on buttons to navigate between pages.
    btn_to_page2.on_click = lambda btn: pages.set_current_page(page2_index)
    btn_to_page1.on_click = lambda btn: pages.set_current_page(page1_index)

    window.show()
    app.run()
