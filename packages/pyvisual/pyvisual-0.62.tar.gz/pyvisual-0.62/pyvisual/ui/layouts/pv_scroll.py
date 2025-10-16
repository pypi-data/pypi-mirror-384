from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QSizePolicy, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPainter, QBrush, QPen
from pyvisual.utils.helper_functions import add_shadow_effect, update_svg_color, draw_border


class PvScroll(QWidget):
    def __init__(self, container=None, x=0, y=0, width=500, height=300,
                 orientation="vertical", spacing=10, padding=(10, 10, 10, 10),
                 background_color=(255, 255, 255, 255), radius=0,
                 border_color=(200, 200, 200, 255), border_thickness=1, box_shadow=None):
        super().__init__(container)

        self.setGeometry(x, y, width, height)
        self.orientation = orientation
        self.spacing = spacing
        self.padding = padding
        self.background_color = QColor(*background_color)
        self.radius = radius
        self.border_color = QColor(*border_color)
        self.border_thickness = border_thickness
        self.box_shadow = box_shadow

        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(*self.padding)
        self.main_layout.setSpacing(self.spacing)
        self.setLayout(self.main_layout)

        # Scroll area setup
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setGeometry(0, 0, width, height)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarAlwaysOff if orientation == "vertical" else Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(
            Qt.ScrollBarAsNeeded if orientation == "vertical" else Qt.ScrollBarAlwaysOff)

        self.scroll_area.setStyleSheet(f"""
            QScrollArea {{
                border: none;
            }}
            QScrollArea > QWidget {{
                border: none;
            }}
        """)

        # Set the background color of the scroll area
        self.scroll_area.viewport().setStyleSheet(f"""
            background-color: rgba({self.background_color.red()}, {self.background_color.green()}, {self.background_color.blue()}, {self.background_color.alpha()});
            border: none;
        """)

        # Scroll content setup
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout() if orientation == "vertical" else QHBoxLayout()
        self.scroll_layout.setSpacing(self.spacing)
        self.scroll_layout.setContentsMargins(0, 0, 0, 0)
        self.scroll_content.setLayout(self.scroll_layout)

        # Ensure content respects children sizes
        self.scroll_content.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Minimum)
        self.scroll_area.setWidget(self.scroll_content)

        self.main_layout.addWidget(self.scroll_area)

        if self.box_shadow:
            add_shadow_effect(self, self.box_shadow)

    def add_widget(self, widget, alignment="left"):
        """
        Add a widget to the scroll area with optional alignment.

        Parameters:
            widget (QWidget): The widget to add.
            alignment (str): Alignment for the widget. Accepted values:
                             "left", "center", "right" for vertical orientation.
                             "top", "center", "bottom" for horizontal orientation.
        """
        alignment_map = {
            "left": Qt.AlignLeft,
            "center": Qt.AlignCenter,
            "right": Qt.AlignRight,
            "top": Qt.AlignTop,
            "bottom": Qt.AlignBottom,
        }

        qt_alignment = alignment_map.get(alignment.lower(), Qt.AlignCenter)

        widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)  # Ensure widget keeps its size
        self.scroll_layout.addWidget(widget, 0, qt_alignment)

    def remove_widget(self, widget):
        """
        Remove a widget from the scroll area.
        """
        self.scroll_layout.removeWidget(widget)
        widget.setParent(None)

    def clear_widgets(self):
        """
        Remove all widgets from the scroll area.
        """
        while self.scroll_layout.count():
            child = self.scroll_layout.takeAt(0)
            if child.widget():
                child.widget().setParent(None)

    def paintEvent(self, event):
        """
        Custom painting for background and border with proper handling of border thickness.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Adjust the rectangle to account for border thickness
        half_border = self.border_thickness / 2.0
        rect = self.rect().adjusted(
            half_border,
            half_border,
            -half_border,
            -half_border
        )

        # Draw background
        painter.setBrush(QBrush(self.background_color))
        painter.setPen(Qt.NoPen)
        painter.drawRoundedRect(rect, self.radius, self.radius)

        # Draw border
        # if self.border_thickness > 0:
        pen = QPen(self.border_color)
        pen.setWidth(self.border_thickness)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)  # No fill for the border, only outline
        painter.drawRoundedRect(rect, self.radius, self.radius)


if __name__ == "__main__":
    import sys
    from pyvisual import PvApp, PvWindow, PvButton
    import pyvisual as pv

    app = PvApp()

    # Main window
    main_window = PvWindow(title="Scroll Example", width=600, height=400)

    # Scroll area
    scroll = PvScroll(main_window, x=50, y=50, width=500, height=300, padding=(0, 0, 0, 0),
                      background_color=(220, 0, 220, 255), radius=10,
                      border_color=(50, 50, 50, 255), border_thickness=5)

    # myGroup = pv.PvGroupLayout(main_window,orientation="vertical")
    # Add some widgets with different alignments
    # for i in range(5):
    #     button = PvButton(main_window, x=0, y=0, text=f"Left {i + 1}")
    #     myGroup.add_widget(button)

    # scroll.add_widget(myGroup)

    for i in range(10):
        button = PvButton(main_window, x=0, y=0, text=f"Right {i + 1}")
        scroll.add_widget(button, alignment="left")

    main_window.show()
    app.run()
