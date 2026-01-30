from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QMessageBox
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
        self.simulation_running = False  # Flag to track simulation status

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
        
        # Dropdowns with default values
        self.simulation_mode = CustomComboBox(
            "Simulation Mode", 
            ["Manual Parameter Mode", "Experiment Mode"],
            default_value="Manual Parameter Mode"
        )
        self.cell_type = CustomComboBox(
            "Cell Type", 
            ["NMC", "LFP", "NCA"],
            default_value="NMC"
        )
        self.model_type = CustomComboBox(
            "Model", 
            ["SPM", "SPMe", "DFN"],
            default_value="SPM"
        )
        self.cell_config = CustomComboBox(
            "Cell Config", 
            ["6s74p", "8s24p", "12s48p", "14s96p", "16s1p"],
            default_value="16s1p"
        )
        self.mode_config = CustomComboBox(
            "Charging/Discharging Mode", 
            ["Charging", "Discharging"],
            default_value="Discharging"
        )

        # Sliders with default values
        self.c_rate_slider = CustomSlider("C-Rate", 1, 50, 10, 10)  # Default: 1.0C rate
        self.voltage_slider = CustomSlider("Voltage (V)", 20, 40, 5, 30)  # Default: 30V

        # Line Edit with default values
        self.simulation_time_lineEdit = CustomLineEdit(
            "Simulation Time (seconds)", 
            placeholder_text="Enter simulation duration in seconds",
            default_value="3600"  # Default: 1 hour (3600 seconds)
        )
        self.initial_temperature_lineEdit = CustomLineEdit(
            "Initial Temperature (°C)", 
            placeholder_text="Enter temperature in Celsius",
            default_value="25"  # Default: 25°C (will be converted to Kelvin)
        )

        # Buttons
        self.control_buttons = CustomButton(["Start", "Stop", "Reset"])

        # Graphs
        self.voltage_graph = CustomGraph("Voltage vs Time", "Time (s)", "Voltage (V)")
        self.soc_graph = CustomGraph("SOC vs Time", "Time (s)", "SOC (%)")
        self.soh_graph = CustomGraph("SOH vs Time", "Time (s)", "SOH (%)")
        self.current_graph = CustomGraph("Current vs Time", "Time (s)", "Current (A)")
        self.internal_resistance_graph = CustomGraph("Internal Resistance vs Time", "Time (s)", "Internal Resistance (Ohm)")
        self.temperature_graph = CustomGraph("Temperature vs Time", "Time (s)", "Temperature (K)")

        # Add to UI Layouts
        configuration_panel.addLayout(self.simulation_mode)
        configuration_panel.addLayout(self.model_type)
        configuration_panel.addLayout(self.cell_type)
        configuration_panel.addLayout(self.cell_config)
        configuration_panel.addLayout(self.mode_config)
        configuration_panel.addLayout(self.c_rate_slider)
        configuration_panel.addLayout(self.voltage_slider)
        configuration_panel.addLayout(self.simulation_time_lineEdit)
        configuration_panel.addLayout(self.initial_temperature_lineEdit)

        control_panel.addLayout(configuration_panel)
        control_panel.addStretch()
        control_panel.addLayout(self.control_buttons)
        
        graph_panel = QVBoxLayout()

        graph_panel2 = QHBoxLayout()
        graph_panel2.addLayout(self.voltage_graph)
        graph_panel2.addLayout(self.soc_graph)
        graph_panel1 = QHBoxLayout()
        graph_panel1.addLayout(self.current_graph)
        graph_panel1.addLayout(self.temperature_graph)

        graph_panel.addLayout(graph_panel1)
        graph_panel.addLayout(graph_panel2)

        self.main_layout.addLayout(control_panel)
        self.main_layout.addLayout(graph_panel)
        self.main_widget.setLayout(self.main_layout)

        # Connect Buttons
        self.control_buttons.get_button("Start").clicked.connect(self.start_simulation)
        self.control_buttons.get_button("Stop").clicked.connect(self.stop_simulation)
        self.control_buttons.get_button("Reset").clicked.connect(self.reset_simulation)

        # Timer for Updating Graphs
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_graph)
        
        # Check PyBaMM availability on startup
        self._check_pybamm_availability()

    def _check_pybamm_availability(self):
        """Check if PyBaMM parameter sets are available and show warning if not."""
        try:
            import pybamm
            # Try to load a common parameter set
            try:
                pybamm.ParameterValues("Ai2020")
                return True  # PyBaMM is available
            except Exception:
                # Parameter sets not available
                self._show_pybamm_warning()
                return False
        except ImportError:
            # PyBaMM not installed
            self._show_pybamm_warning(installed=False)
            return False
    
    def _show_pybamm_warning(self, installed=True):
        """Show a warning message about PyBaMM parameter sets."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("PyBaMM Configuration Warning")
        
        if installed:
            msg.setText("PyBaMM parameter sets are not available.\n\nSimulation may fail until fixed.")
            detailed_text = (
                "PyBaMM is installed but parameter sets are missing.\n\n"
                "QUICK FIX:\n"
                "  Run this command in your terminal:\n"
                "  python fix_pybamm_params.py\n\n"
                "OR manually:\n"
                "  1. pip uninstall pybamm\n"
                "  2. pip install pybamm\n"
                "  3. Or: pip install pybamm[all]\n\n"
                "See INSTALL_PYBAMM_PARAMS.md for detailed instructions.\n\n"
                "You can continue, but simulations will fail until PyBaMM parameter sets are installed."
            )
        else:
            msg.setText("PyBaMM is not installed.\n\nSimulation will not work until PyBaMM is installed.")
            detailed_text = (
                "PyBaMM is required for battery simulations.\n\n"
                "Please install PyBaMM:\n"
                "  pip install pybamm\n\n"
                "Or with all extras:\n"
                "  pip install pybamm[all]\n\n"
                "See INSTALL_PYBAMM_PARAMS.md for detailed instructions."
            )
        
        msg.setDetailedText(detailed_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()  # Show warning but allow user to continue

    def start_simulation(self):
        try:
            # Get simulation time with default
            simu_time_str = self.simulation_time_lineEdit.get_text().strip()
            if simu_time_str == "":
                simu_time_int = 3600  # Default: 1 hour
            else:
                simu_time_int = int(simu_time_str)
            
            # Get temperature with default
            temp_str = self.initial_temperature_lineEdit.get_text().strip()
            if temp_str == "" or temp_str is None:
                initial_temperature = 298.15  # Default to 25°C in Kelvin
            else:
                temp_value = float(temp_str)
                # If temperature is in reasonable Celsius range (0-100), convert to Kelvin
                if temp_value < 100:
                    initial_temperature = temp_value + 273.15  # Convert Celsius to Kelvin
                else:
                    initial_temperature = temp_value  # Already in Kelvin

            model_type = self.model_type.get_value()
            chemistry = self.cell_type.get_value()
            simulation_mode = self.simulation_mode.get_value()

            print(f"Simulation Time: {simu_time_int}, Initial Temp: {initial_temperature}, Model: {model_type}, Chemistry: {chemistry}, Mode: {simulation_mode}")

            # Initialize Simulator Manager
            self.simulator_manager = SimulatorManager(model_type, chemistry, initial_temperature)

            if simulation_mode == "Experiment Mode":
                experiment_data = self.simulator_manager.load_experiment()
                if not experiment_data:
                    print("Failed to load experiment!")
                    return  # Stop execution if loading fails
                # Experiment simulation is already run inside load_experiment()
                print("Experiment loaded and simulation completed.")
            else:
                self.simulator_manager.run_battery_simulation(simu_time_int)

            # Start timer to update graph
            self.simulation_running = True
            self.timer.start(1000)

        except ValueError as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')  # Handle encoding issues
            self._show_error("Invalid Input", f"Please check your input values:\n{error_msg}")
            print(f"Invalid input! Error: {error_msg}")
        except RuntimeError as e:
            # PyBaMM parameter set error
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')
            self._show_pybamm_error(error_msg)
            print(f"PyBaMM Error: {error_msg}")
        except Exception as e:
            error_msg = str(e).encode('ascii', 'replace').decode('ascii')  # Handle encoding issues
            self._show_error("Simulation Error", f"An error occurred during simulation:\n{error_msg}")
            print(f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
    
    def _show_error(self, title, message):
        """Show an error message dialog."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
    
    def _show_pybamm_error(self, error_message):
        """Show a detailed PyBaMM error message with instructions."""
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)
        msg.setWindowTitle("PyBaMM Configuration Error")
        msg.setText("PyBaMM parameter sets are not available.")
        
        detailed_text = (
            f"Error Details:\n{error_message}\n\n"
            "SOLUTION:\n"
            "1. Run this command in your terminal:\n"
            "   python fix_pybamm_params.py\n\n"
            "2. OR manually install/reinstall PyBaMM:\n"
            "   pip uninstall pybamm\n"
            "   pip install pybamm\n\n"
            "3. OR install with all extras:\n"
            "   pip install pybamm[all]\n\n"
            "4. Check PyBaMM installation:\n"
            "   python -c \"import pybamm; print(pybamm.__version__)\"\n\n"
            "See INSTALL_PYBAMM_PARAMS.md for detailed instructions."
        )
        
        msg.setDetailedText(detailed_text)
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec_()
            
    def update_graph(self):
        """Retrieve simulation data and update the graph."""
        if self.simulator_manager and self.simulation_running:
            time_data, voltage_data, soc_data, temperature_data, current_data = self.simulator_manager.get_simulation_results()

            if len(time_data) > 0:
                self.voltage_graph.update_plot(time_data, voltage_data)
                self.soc_graph.update_plot(time_data, soc_data)
                self.temperature_graph.update_plot(time_data, temperature_data)
                self.current_graph.update_plot(time_data, current_data)

    def stop_simulation(self):
        if self.simulator_manager:
            print("Simulation stopped!")
            self.simulation_running = False
            self.timer.stop()

    def reset_simulation(self):
        if self.simulator_manager:
            print("Resetting Simulation...")
            self.stop_simulation()
            self.simulator_manager = None

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AppWindow()
    window.show()
    sys.exit(app.exec_())
