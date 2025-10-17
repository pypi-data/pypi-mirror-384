from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QCheckBox, QPushButton, QLabel


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PySide6 Checkbox Demo")
        self.setGeometry(100, 100, 300, 200)

        # Main layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Checkboxes
        self.checkbox1 = QCheckBox("Option 1")
        self.checkbox2 = QCheckBox("Option 2")
        self.checkbox3 = QCheckBox("Option 3")

        # Add checkboxes to the layout
        self.layout.addWidget(self.checkbox1)
        self.layout.addWidget(self.checkbox2)
        self.layout.addWidget(self.checkbox3)

        # Label to display results
        self.result_label = QLabel("")
        self.layout.addWidget(self.result_label)

        # Button to check states
        self.check_button = QPushButton("Check States")
        self.check_button.clicked.connect(self.show_states)
        self.layout.addWidget(self.check_button)

    def show_states(self):
        # Get states of the checkboxes
        state1 = "Checked" if self.checkbox1.isChecked() else "Unchecked"
        state2 = "Checked" if self.checkbox2.isChecked() else "Unchecked"
        state3 = "Checked" if self.checkbox3.isChecked() else "Unchecked"

        # Update the label
        self.result_label.setText(f"Option 1: {state1}, Option 2: {state2}, Option 3: {state3}")


if __name__ == "__main__":
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
