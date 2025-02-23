from PyQt5.QtWidgets import QComboBox, QSlider, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QLineEdit
from PyQt5.QtCore import Qt
import pyqtgraph as pg

# Class for Dropdown (ComboBox)
class CustomComboBox(QVBoxLayout):
    def __init__(self, label_text, options, width=100):
        super().__init__()
        self.label = QLabel(label_text)
        self.combo_box = QComboBox()
        self.combo_box.setFixedWidth(width)
        self.combo_box.addItems(options)
        self.addWidget(self.label)
        self.addWidget(self.combo_box)

    def get_value(self):
        return self.combo_box.currentText()

# Class for Sliders
class CustomSlider(QVBoxLayout):
    def __init__(self, label_text, min_val, max_val, tick_interval, default_value):
        super().__init__()
        self.label = QLabel(f"{label_text}: {default_value}")
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(min_val, max_val)
        self.slider.setTickInterval(tick_interval)
        self.slider.setValue(default_value)
        self.slider.valueChanged.connect(lambda x: self.label.setText(f"{label_text}: {x/10 if max_val > 10 else x}"))
        self.addWidget(self.label)
        self.addWidget(self.slider)

    def get_value(self):
        return self.slider.value() / 10 if self.slider.maximum() > 10 else self.slider.value()

# Class for Buttons
class CustomButton(QHBoxLayout):
    def __init__(self, buttons):
        super().__init__()
        self.buttons = {}
        for btn_text in buttons:
            btn = QPushButton(btn_text)
            self.buttons[btn_text] = btn
            self.addWidget(btn)

    def get_button(self, btn_text):
        return self.buttons[btn_text]
    
class CustomLineEdit(QVBoxLayout):
    def __init__(self, label, button_text="OK", placeholder_text="Enter text"):
        """Custom input field with label and button."""
        super().__init__()

        # Create layout for input field and button
        self.field_layout = QHBoxLayout()

        # Label for the input field
        self.label = QLabel(label)

        # Text input field
        self.text_field = QLineEdit()
        self.text_field.setPlaceholderText(placeholder_text)

        # OK button
        self.ok_button = QPushButton(button_text)

        # Add widgets to layout
        self.field_layout.addWidget(self.text_field)
        self.field_layout.addWidget(self.ok_button)

        self.addWidget(self.label)
        self.addLayout(self.field_layout)

        # Connect button to action
        self.ok_button.clicked.connect(self.get_text)

    def get_text(self):
        """Return text entered in the input field."""
        return self.text_field.text()


# Class for PyQtGraph
class CustomGraph(QVBoxLayout):
    def __init__(self, title, xlabel, ylabel):
        super().__init__()
        self.graph = pg.PlotWidget(title=title)
        self.graph.setLabel("left", ylabel)
        self.graph.setLabel("bottom", xlabel)
        self.addWidget(self.graph)

    def update_plot(self, x_data, y_data):
        self.graph.plot(x_data, y_data, clear=True)
