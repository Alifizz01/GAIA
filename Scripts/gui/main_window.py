from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gui.widget_class import CustomComboBox, CustomSlider, CustomButton, CustomGraph, CustomLineEdit
from bms_core.simulation_manager import SimulatorManager

class AppWindow(QMainWindow):
    def __init__(self):   
        super().__init__()
        self.init_ui()
        self.simulator_manager = None  # Will be initialized when simulation starts

    def init_ui(self):
        """Initialize the main window."""
        self.setWindowTitle("GAIA Simulator")
        self.setGeometry(100, 100, 1200, 800)
        self.setup_ui()

    def setup_ui(self):
        """Set up the UI components."""
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.main_layout = QHBoxLayout()

        control_panel = QVBoxLayout()
        configuration_panel = QVBoxLayout()
        
        # Dropdowns
        self.cell_type = CustomComboBox("Cell Type", ["NMC", "LFP", "NCA"])
        self.model_type = CustomComboBox("Model", ["SPM", "SPMe", "DFN"])
        self.cell_config = CustomComboBox("Cell Config", ["6s74p", "8s24p", "12s48p", "14s96p", "16s1p"])
        self.mode_config = CustomComboBox("Charging/Discharging Mode", ["Charging", "Discharging"])

        # Sliders
        self.c_rate_slider = CustomSlider("C-Rate", 1, 50, 10, 0)
        self.voltage_slider = CustomSlider("Voltage (V)", 20, 40, 5, 0)

        # Line Edit
        self.simulation_time_lineEdit = CustomLineEdit("Simulation Time")

        # Buttons
        self.control_buttons = CustomButton(["Start", "Stop", "Reset"])

        # Graphs
        self.voltage_graph = CustomGraph("Voltage vs Time", "Time (s)", "Voltage (V)")
        self.soc_graph = CustomGraph("SOC vs Time", "Time (s)", "SOC (%)")
        self.soh_graph = CustomGraph("SOH vs Time", "Time (s)", "SOH (%)")

        self.capacity_graph = CustomGraph("Capacity vs Time", "Time (s)", "Capacity (Ah)")
        self.internal_resistance_graph = CustomGraph("Internal Resistance vs Time", "Time (s)", "Internal Resistance (Ohm)")
        self.temperature_graph = CustomGraph("Temperature vs Time", "Time (s)", "Temperature (K)")

        # Add to UI Layouts
        configuration_panel.addLayout(self.model_type)
        configuration_panel.addLayout(self.cell_type)
        configuration_panel.addLayout(self.cell_config)
        configuration_panel.addLayout(self.mode_config)
        configuration_panel.addLayout(self.c_rate_slider)
        configuration_panel.addLayout(self.voltage_slider)
        configuration_panel.addLayout(self.simulation_time_lineEdit)

        control_panel.addLayout(configuration_panel)
        control_panel.addStretch()
        control_panel.addLayout(self.control_buttons)
        
        graph_panel = QVBoxLayout()

        graph_panel2 = QHBoxLayout()
        graph_panel2.addLayout(self.voltage_graph)
        graph_panel2.addLayout(self.soc_graph)
        graph_panel2.addLayout(self.soh_graph)
        graph_panel1 = QHBoxLayout()
        graph_panel1.addLayout(self.capacity_graph)
        graph_panel1.addLayout(self.internal_resistance_graph)
        graph_panel1.addLayout(self.temperature_graph)

        graph_panel.addLayout(graph_panel1)
        graph_panel.addLayout(graph_panel2)

        self.main_layout.addLayout(control_panel)
        self.main_layout.addLayout(graph_panel)
        self.main_widget.setLayout(self.main_layout)

        # Connect Buttons
        self.control_buttons.get_button("Start").clicked.connect(self.start_simulation)

        # Timer for Updating Graphs
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)

    def start_simulation(self):
        """Fetch GUI inputs and run the simulation."""
        try:
            simu_time_str = self.simulation_time_lineEdit.get_text()
            simu_time_int = int(simu_time_str)  # Convert to integer

            model_type = self.model_type.get_value()
            chemistry = self.cell_type.get_value()
            c_rate = self.c_rate_slider.get_value()

            # Initialize Simulator Manager with user-selected values
            self.simulator_manager = SimulatorManager(model_type, chemistry)
            self.simulator_manager.run_battery_simulation(simu_time_int)

            # Start timer to update graph
            self.timer.start(1000)

        except ValueError:
            print("Invalid input! Please enter a valid number.")

    def update_graph(self):
        """Retrieve simulation data and update the graph."""
        if self.simulator_manager:
            time_data, voltage_data, soc_data, temperature_data = self.simulator_manager.get_simulation_results()

            if len(time_data) > 0:
                self.voltage_graph.update_plot(time_data, voltage_data)
                self.soc_graph.update_plot(time_data, soc_data)
                self.temperature_graph.update_plot(time_data, temperature_data)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())
