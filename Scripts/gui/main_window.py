from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtCore import QTimer
import sys
import os
import time  # For real-time simulation control

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gui.widget_class import CustomComboBox, CustomSlider, CustomButton, CustomGraph, CustomLineEdit
from bms_core.simulation_manager import SimulatorManager

class AppWindow(QMainWindow):
    def __init__(self):   
        super().__init__()
        self.init_ui()
        self.simulator_manager = None  # Will be initialized when simulation starts
        self.simulation_running = False  # Flag to control real-time updates
        self.current_time_step = 0  # Tracks elapsed time in simulation

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
        graph_panel.addLayout(self.voltage_graph)

        self.main_layout.addLayout(control_panel)
        self.main_layout.addLayout(graph_panel)
        self.main_layout.setStretchFactor(graph_panel, 3)
        self.main_widget.setLayout(self.main_layout)

        # Connect Buttons
        self.control_buttons.get_button("Start").clicked.connect(self.start_simulation)
        self.control_buttons.get_button("Stop").clicked.connect(self.stop_simulation)

        # Timer for Real-Time Updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)

    def start_simulation(self):
        """Fetch GUI inputs and run the simulation in real-time."""
        try:
            simu_time_str = self.simulation_time_lineEdit.get_text()
            simu_time_int = int(simu_time_str)  # Convert to integer

            model_type = self.model_type.get_value()
            chemistry = self.cell_type.get_value()
            c_rate = self.c_rate_slider.get_value()

            # Initialize Simulator Manager with user-selected values
            self.simulator_manager = SimulatorManager(model_type, chemistry)
            self.simulator_manager.run_battery_simulation(simu_time_int)

            # Start real-time simulation
            self.simulation_running = True
            self.current_time_step = 0  # Reset simulation time tracking

            # Start timer to update graph in real-time (1000ms = 1 second)
            self.timer.start(1000)

        except ValueError:
            print("Invalid input! Please enter a valid number.")

    def stop_simulation(self):
        """Stop real-time updates"""
        self.simulation_running = False
        self.timer.stop()

    def update_graph(self):
        """Update the graph in real-time, one second at a time."""
        if self.simulation_running:
            time_data, voltage_data = self.simulator_manager.get_simulation_results()

            # Check if there’s still data to plot
            if self.current_time_step < len(time_data):
                # Plot only up to the current time step
                self.voltage_graph.update_plot(time_data[:self.current_time_step], voltage_data[:self.current_time_step])
                self.current_time_step += 1  # Move forward one second
            else:
                # Stop the simulation if we reach the end
                self.stop_simulation()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())
