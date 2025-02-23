from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gui.widget_class import CustomComboBox, CustomSlider, CustomButton, CustomGraph, CustomLineEdit

class AppWindow(QMainWindow):
    def __init__(self):   
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """Initialize the main window."""
        self.setWindowTitle("GAIA Simulator")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()
        self.time_data = []
        self.voltage_data = []
        self.soc_data = []

    def setup_ui(self):
        """Set up the UI components."""
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()

        control_panel = QVBoxLayout()
        configuration_panel = QVBoxLayout()
        # Dropdowns
        self.cell_type = CustomComboBox("Cell Type", ["NMC", "LTO", "LFP", "LMO", "NCA"])
        self.model_type = CustomComboBox("Model", ["SPM", "SPMe", "DFN"])
        self.cell_config = CustomComboBox("Cell Config", ["6s74p", "8s24p", "12s48p", "14s96p", "16s1p"])
        self.mode_config = CustomComboBox("Charging/Discharging Mode", ["Charging", "Discharging"])

        # Sliders
        self.c_rate_slider = CustomSlider("C-Rate", 1, 50, 10, 0)
        self.soc_slider = CustomSlider("SOC (%)", 0, 100, 10, 0)
        self.voltage_slider = CustomSlider("Voltage (V)", 20, 40, 5, 0)

        # Line Edit
        self.ambient_temperature_lineedit = CustomLineEdit(label= "Ambient Temperature")
        self.simulation_time_lineEdit = CustomLineEdit("Simulation Time")

        # Buttons
        self.control_buttons = CustomButton(["Start", "Stop", "Reset"])

        # Graphs
        self.soc_graph = CustomGraph("SOC vs Time", "Time (s)", "SOC (%)")
        self.voltage_graph = CustomGraph("Voltage vs Time", "Time (s)", "Voltage (V)")

        # Adding to configuration Panel
        configuration_panel.addLayout(self.model_type)
        configuration_panel.addLayout(self.cell_type)
        configuration_panel.addLayout(self.cell_config)
        configuration_panel.addLayout(self.mode_config)
        configuration_panel.addLayout(self.c_rate_slider)
        configuration_panel.addLayout(self.soc_slider)
        configuration_panel.addLayout(self.voltage_slider)
        configuration_panel.addLayout(self.ambient_temperature_lineedit)
        configuration_panel.addLayout(self.simulation_time_lineEdit)

        # Adding to control Panel
        control_panel.addLayout(configuration_panel)
        control_panel.addStretch()
        control_panel.addLayout(self.control_buttons)

        # Main Layout Assembly
        graph_panel = QVBoxLayout()
        graph_panel.addLayout(self.soc_graph)
        graph_panel.addLayout(self.voltage_graph)

        self.main_layout.addLayout(control_panel)
        self.main_layout.addLayout(graph_panel)
        self.main_layout.setStretchFactor(graph_panel, 3)
        self.main_widget.setLayout(self.main_layout)

        # Connect Buttons to Functions
        self.control_buttons.get_button("Start").clicked.connect(self.start_simulation)
    
    def start_simulation(self):
        try:
            # Get simulation time input and convert to integer safely
            simu_time_str = self.simulation_time_lineEdit.get_text()
            simu_time_int = int(simu_time_str)  # Convert to integer

            # Generate time array
            self.time_data = np.arange(0, simu_time_int, 1)

            # For now, simulate SOC and voltage drop over time
            self.soc_data = np.linspace(100, 10, simu_time_int)  # Fake SOC decreasing
            self.voltage_data = np.linspace(4.2, 3.0, simu_time_int)  # Fake voltage drop

            # Update Graphs
            self.soc_graph.update_plot(self.time_data, self.soc_data)
            self.voltage_graph.update_plot(self.time_data, self.voltage_data)
        
        except ValueError:
            print("Invalid input for simulation time! Please enter a valid number.")


    def get_data(self):
        """Retrieve user input from GUI"""
        user_data = {
            "Model Type": self.model_type.get_value(),
            "Cell Type": self.cell_type.get_value(),
            "Cell Configuration": self.cell_config.get_value(),
            "C-Rate": self.c_rate_slider.get_value(),
            "SOC (%)": self.soc_slider.get_value(),
            "Voltage (V)": self.voltage_slider.get_value(),
            "Simulation Time" : self.simulation_time_lineEdit.get_text()
        }
        print("User Inputs:", user_data)
        return user_data

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())