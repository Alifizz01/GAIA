from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QSlider, QLabel, 
    QDesktopWidget, QPushButton, QHBoxLayout, QLineEdit, QComboBox, QCheckBox
)
from PyQt5.QtCore import Qt
import sys

class AppWindow(QMainWindow):
    def __init__(self):   
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the main window."""
        self.setWindowTitle("GAIA Simulator")
        self.set_geometry_to_fullscreen()
        self.setup_ui()

    def set_geometry_to_fullscreen(self):
        """Set the window to full-screen size."""
        screen = QDesktopWidget().screenGeometry()
        self.setGeometry(0, 0, screen.width(), int(screen.height() * 0.90))
    
    def setup_ui(self):
        """Set up the UI components."""
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        layout1 = QVBoxLayout()
        layout2 = QVBoxLayout()

        control_label = QLabel("Control")
        control_label.setFixedHeight(50)
        control_panel_layout = QVBoxLayout()
        control_panel_layout.addWidget(control_label)

        # Cell Selection
        cell_layout = QHBoxLayout()
        cell_type_combo_box = QComboBox()
        cell_type_combo_box.setFixedWidth(100)
        cell_type_combo_box.addItems(["NMC", "LTO", "LFP", "LMO", "NCA"])
        choose_button = QPushButton("Choose", self)
        cell_layout.addWidget(cell_type_combo_box)
        cell_layout.addWidget(choose_button)

        # Cell Configurations
        cell_configuration_layout = QHBoxLayout()
        cell_configuration = QComboBox()
        cell_configuration.setFixedWidth(100)
        cell_configuration.addItems(["6s74p", "8s24p", "12s48p", "14s96p", "16s1p", "24s1p", "48s1p", "96s74p", "112s96p"])
        cell_configuration_choose = QPushButton("Choose", self)
        cell_configuration_layout.addWidget(cell_configuration)
        cell_configuration_layout.addWidget(cell_configuration_choose)

        # C-rate Slider
        c_rate_layout = QVBoxLayout()
        c_rate_slider_label = QLabel("C-Rate: ")
        c_rate_slider_label.setFixedHeight(50)
        c_rate_slider = QSlider(Qt.Horizontal)
        c_rate_slider.setRange(1, 50)
        c_rate_slider.setTickInterval(10)
        c_rate_slider.valueChanged.connect(lambda x: c_rate_slider_label.setText(f"C-Rate: {x/10}"))
        c_rate_layout.addWidget(c_rate_slider_label)
        c_rate_layout.addWidget(c_rate_slider)

        # SOC Slider
        soc_slider_layout = QVBoxLayout()
        soc_slider = QSlider(Qt.Horizontal)
        soc_slider.setTickInterval(10)
        soc_slider.setRange(0, 100)
        soc_slider.setValue(50)  # Default value
        soc_slider_label = QLabel("SOC (%): 50")
        soc_slider_label.setFixedHeight(50)
        soc_slider.valueChanged.connect(lambda x: soc_slider_label.setText(f"SOC (%): {x}"))
        soc_slider_layout.addWidget(soc_slider_label)
        soc_slider_layout.addWidget(soc_slider)

        # Voltage Slider
        voltage_slider_layout = QVBoxLayout()
        voltage_slider = QSlider(Qt.Horizontal)
        voltage_slider.setRange(20, 40)
        voltage_slider.setValue(30)
        voltage_slider.setTickInterval(5)
        voltage_slider_label = QLabel("Voltage (V): 3.0")  # Corrected initial value
        voltage_slider_label.setFixedHeight(50)
        voltage_slider.valueChanged.connect(lambda x: voltage_slider_label.setText(f"Voltage (V): {x/10:.1f}"))
        voltage_slider_layout.addWidget(voltage_slider_label)
        voltage_slider_layout.addWidget(voltage_slider)

        # Control Buttons
        button_layout = QHBoxLayout()
        start_button = QPushButton("Start", self)
        stop_button = QPushButton("Stop", self)
        reset_button = QPushButton("Reset", self)
        button_layout.addWidget(start_button)
        button_layout.addWidget(stop_button)
        button_layout.addWidget(reset_button)

        # Save & Load Buttons
        save_load_layout = QHBoxLayout()
        save_button = QPushButton("SAVE", self)
        load_button = QPushButton("LOAD", self)
        save_load_layout.addWidget(save_button)
        save_load_layout.addWidget(load_button)

        # Ambient Temperature Input
        temperature_layout = QHBoxLayout()
        ambient_temperature_input = QLineEdit()
        ambient_temperature_input.setPlaceholderText("Input your Ambient temperature")
        apply_button = QPushButton("Apply", self)
        temperature_layout.addWidget(ambient_temperature_input)
        temperature_layout.addWidget(apply_button)

        # Fault Injection Checkboxes
        fault_injection_layout = QVBoxLayout()
        overvoltage_checkbox = QCheckBox("Overvoltage")
        overtemperature_checkbox = QCheckBox("Overtemperature")
        cell_imbalance_checkbox = QCheckBox("Cell Imbalance")
        fault_injection_layout.addWidget(overvoltage_checkbox)
        fault_injection_layout.addWidget(overtemperature_checkbox)
        fault_injection_layout.addWidget(cell_imbalance_checkbox)

        # Control Panel Assembly
        control_panel_layout.addLayout(cell_layout)
        control_panel_layout.addLayout(cell_configuration_layout)
        control_panel_layout.addLayout(soc_slider_layout)
        control_panel_layout.addLayout(voltage_slider_layout)
        control_panel_layout.addLayout(c_rate_layout)
        control_panel_layout.addLayout(fault_injection_layout)
        control_panel_layout.addLayout(temperature_layout)
        control_panel_layout.addStretch()
        control_panel_layout.addLayout(button_layout)
        control_panel_layout.addLayout(save_load_layout)

        # Main Layout Assembly
        layout1.addLayout(control_panel_layout)
        layout2.addStretch()
        main_layout.addLayout(layout1)
        main_layout.addLayout(layout2)
        main_layout.setStretchFactor(layout1, 1)
        main_layout.setStretchFactor(layout2, 4)
        main_widget.setLayout(main_layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())