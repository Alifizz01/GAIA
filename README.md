# GAIA - Generalized Advanced Intelligent Analytics for Battery Management Systems

![GAIA Logo](https://img.shields.io/badge/GAIA-BMS%20Framework-blue)
![Python](https://img.shields.io/badge/python-3.9--3.12-green.svg)
![License](https://img.shields.io/badge/license-MIT-blue.svg)

## ⚠️ Python Version Requirement

**IMPORTANT**: GAIA requires **Python 3.9, 3.10, 3.11, or 3.12**.

PyBaMM (the underlying battery modeling library) does not support Python 3.13+ yet. If you have Python 3.13 or later, please use Python 3.12 instead.

See [INSTALLATION.md](INSTALLATION.md) for detailed installation instructions and troubleshooting.

---

## 🌍 What is GAIA?

**GAIA** stands for **Generalized Advanced Intelligent Analytics** - a comprehensive, enterprise-grade Battery Management System (BMS) simulation framework designed for large-scale applications with high scalability requirements.

GAIA embodies the concept of "Mother Earth" - providing a nurturing, comprehensive environment where battery systems can be understood, simulated, and optimized. Just as Gaia represents the interconnected systems of our planet, GAIA represents the interconnected systems of modern battery technology.

### The GAIA Philosophy

- **Generalized**: Works with multiple battery chemistries (NMC, LFP, NCA, LMO, LTO) and configurations
- **Advanced**: Implements state-of-the-art algorithms (AEKF, active balancing, thermal modeling)
- **Intelligent**: Adaptive algorithms that learn and optimize battery performance
- **Analytics**: Comprehensive data logging, monitoring, and analysis capabilities

---

## 🎯 Purpose and Vision

GAIA is designed to be the most comprehensive, scalable, and user-friendly BMS simulation framework available. It addresses the critical need for accurate battery modeling and management in:

- **Electric Vehicles (EVs)**: Complete battery pack simulation for vehicle design
- **Grid Storage Systems**: Large-scale battery array management
- **Consumer Electronics**: Battery optimization for portable devices
- **Research & Development**: Advanced battery modeling and algorithm development
- **Educational Purposes**: Teaching battery management concepts

### Key Capabilities

✅ **Multi-Chemistry Support**: NMC, LFP, NCA, LMO, LTO batteries  
✅ **Advanced SOC Estimation**: Coulomb Counting, Kalman Filter, Adaptive Extended Kalman Filter (AEKF)  
✅ **Battery Pack Management**: Series-parallel configurations with cell-level monitoring  
✅ **Balancing Algorithms**: Passive and active (inductive/capacitive) balancing  
✅ **Fault Injection & Testing**: Comprehensive fault simulation for BMS validation  
✅ **Charging/Discharging Protocols**: CC-CV, fast charging, pulse charging, load profiles  
✅ **Thermal Modeling**: Temperature-dependent behavior and thermal runaway simulation  
✅ **Real-time Visualization**: Live monitoring with PyQt5 GUI  
✅ **High Scalability**: Parallel processing support for large battery packs  
✅ **Data Logging**: CSV/JSON logging with configurable intervals  

---

## 🏗️ Framework Architecture

### Core Components

#### 1. **Battery Model (`battery_model.py`)**
The foundation of GAIA, implementing PyBaMM-based battery cell models with support for:
- **Model Types**: Single Particle Model (SPM), Single Particle Model with electrolyte (SPMe), Doyle-Fuller-Newman (DFN)
- **Chemistries**: Multiple pre-configured parameter sets for different battery types
- **State Extraction**: Voltage, SOC, temperature, current extraction from simulations

#### 2. **Battery Pack (`battery_pack.py`)**
Manages series-parallel battery pack configurations:
- **Pack Configuration**: Flexible `NsPp` (e.g., 16s1p, 8s24p) configurations
- **Cell-Level Monitoring**: Individual cell state tracking
- **Imbalance Detection**: Real-time cell imbalance analysis
- **Faulty Cell Detection**: Automatic identification of problematic cells

#### 3. **SOC Estimation (`soc_estimation.py`)**
Three-tier SOC estimation system:
- **Coulomb Counting**: Simple integration-based method
- **Kalman Filter**: Extended Kalman Filter with voltage feedback
- **AEKF**: Adaptive Extended Kalman Filter with noise adaptation for maximum accuracy

#### 4. **Battery Balancing (`battery_balancing.py`)**
Cell balancing algorithms:
- **Passive Balancing**: Resistor-based dissipative balancing (simple, reliable)
- **Active Balancing**: Energy transfer between cells (efficient, complex)
  - Inductive balancing
  - Capacitive balancing

#### 5. **Fault Injection (`fault_injection.py`)**
Comprehensive fault simulation:
- **Fault Types**: Short circuit, open circuit, overvoltage, undervoltage, overcurrent, overtemperature, thermal runaway, capacity degradation
- **Fault Scenarios**: Pre-configured scenarios for testing
- **Realistic Modeling**: Severity-based fault injection

#### 6. **Charging/Discharging (`charging_discharging_simulation.py`)**
Advanced charge/discharge protocols:
- **Charging Modes**: CC, CV, CC-CV, fast charging, trickle charging, pulse charging
- **Discharging Modes**: Constant current, constant power, constant resistance, load profiles
- **Profile Management**: Customizable charging/discharging profiles

#### 7. **Simulation Manager (`simulation_manager.py`)**
Orchestrates all simulation components:
- **Simulation Control**: Start, stop, pause simulations
- **Experiment Mode**: Load custom PyBaMM experiments
- **Data Management**: Results storage and retrieval

#### 8. **Configuration Manager (`config_manager.py`)**
Centralized configuration:
- **JSON Configuration**: Human-readable configuration files
- **Validation**: Automatic configuration validation
- **Default Values**: Sensible defaults for all parameters

#### 9. **Data Logger (`gui/data_logger.py`)**
Comprehensive data logging:
- **Formats**: CSV and JSON support
- **Time-series Data**: Voltage, current, SOC, SOH, temperature, power, energy
- **Export Options**: Easy data export for analysis

#### 10. **GUI (`gui/main_window.py`, `gui/widget_class.py`)**
Modern graphical interface:
- **Real-time Plots**: Voltage, SOC, SOH, current, temperature, internal resistance
- **Interactive Controls**: Sliders, dropdowns, input fields
- **Configuration**: Easy parameter adjustment
- **Monitoring**: Live simulation status

---

## 📊 Key Concepts Explained

### State of Charge (SOC)
SOC represents the remaining charge in a battery as a percentage (0-100%). GAIA implements multiple estimation methods:

1. **Coulomb Counting**: Integrates current over time (simple but prone to drift)
2. **Kalman Filter**: Uses voltage measurements to correct coulomb counting (more accurate)
3. **AEKF**: Adapts to changing conditions for maximum accuracy in dynamic environments

### State of Health (SOH)
SOH represents the battery's capacity relative to its original capacity. GAIA tracks SOH through:
- Capacity fade modeling
- Internal resistance increase
- Cycle counting

### Battery Pack Configuration
GAIA supports flexible pack configurations:
- **Series Cells (`Ns`)**: Increase voltage (e.g., 16 cells = 16 × 3.7V = 59.2V)
- **Parallel Cells (`Pp`)**: Increase capacity (e.g., 24 parallel = 24 × 50Ah = 1200Ah)
- **Example**: `16s24p` = 16 series × 24 parallel = 384 total cells

### Cell Balancing
Essential for pack longevity:
- **Problem**: Cells age differently, causing SOC imbalance
- **Passive Solution**: Discharge high cells via resistors (simple, inefficient)
- **Active Solution**: Transfer energy from high to low cells (efficient, complex)

### Thermal Modeling
Critical for safety and performance:
- **Temperature Effects**: Capacity, resistance, and lifespan all depend on temperature
- **Thermal Runaway**: Exponential temperature rise that can cause catastrophic failure
- **Cooling Systems**: Active cooling simulation support

### Fault Types
GAIA can simulate various fault conditions:
- **Electrical Faults**: Short circuits, open circuits, connection failures
- **Voltage Faults**: Overvoltage, undervoltage
- **Current Faults**: Overcurrent conditions
- **Thermal Faults**: Overtemperature, thermal runaway
- **Aging Faults**: Capacity degradation, resistance increase

---

## 🚀 Getting Started

### Installation

1. **Check Python Version** (Must be 3.9-3.12)
```bash
python --version
```

2. **Clone the Repository**
```bash
git clone https://github.com/yourusername/GAIA.git
cd GAIA
```

3. **Create Virtual Environment (Recommended)**
```bash
python -m venv venv
# Activate: venv\Scripts\activate (Windows) or source venv/bin/activate (macOS/Linux)
```

4. **Install Dependencies**
```bash
pip install -r requirements.txt
```

5. **Install GAIA (Optional)**
```bash
pip install -e .
```

For detailed installation instructions, see [INSTALLATION.md](INSTALLATION.md).

### Quick Start

#### Command Line Usage

```python
from bms_core import BatteryModel, SimulatorManager

# Create a battery model
battery = BatteryModel(
    model_type="SPM",
    chemistry="NMC",
    initial_temperature=298.15
)

# Run simulation
solution = battery.run_simulation(duration=3600)  # 1 hour simulation
```

#### GUI Usage

```bash
python Scripts/gui/main_window.py
```

Or use the entry point:
```bash
gaia-simulator
```

#### Using Configuration Files

```python
from bms_core import ConfigManager, SimulatorManager

# Load configuration
config = ConfigManager("config.json")

# Create simulator with config
sim_manager = SimulatorManager(
    model_type=config.get("battery.model_type"),
    chemistry=config.get("battery.chemistry"),
    initial_temperature=config.get("battery.initial_temperature")
)

# Run simulation
sim_manager.run_battery_simulation(
    duration=config.get("simulation.duration")
)
```

---

## 📖 Detailed Usage Examples

### Example 1: Basic Battery Simulation

```python
from bms_core import BatteryModel

# Initialize battery model
battery = BatteryModel(
    model_type="SPMe",  # Single Particle Model with electrolyte
    chemistry="LFP",     # Lithium Iron Phosphate
    initial_temperature=298.15
)

# Run simulation
solution = battery.run_simulation(duration=7200)  # 2 hours

# Extract data
time = solution["Time [s]"].entries
voltage = battery.get_voltage(solution, time)
soc = battery.get_soc(solution, time)
temperature = battery.get_temperature(solution, time)
```

### Example 2: Battery Pack with Balancing

```python
from bms_core import BatteryPack, BatteryBalancer, BalancingMethod

# Create 16s1p pack (16 cells in series)
pack = BatteryPack(
    cells_in_series=16,
    cells_in_parallel=1,
    chemistry="NMC"
)

# Create balancer
balancer = BatteryBalancer(
    method=BalancingMethod.PASSIVE,
    balancing_threshold=0.02  # 2% SOC difference triggers balancing
)

# Check if balancing is needed
if balancer.is_balancing_needed(pack):
    # Perform balancing
    results = balancer.balance(pack, dt=1.0)
    print(f"Power dissipated: {results['power_dissipated']} W")
```

### Example 3: SOC Estimation with AEKF

```python
from bms_core import SOCEstimator, SOCEstimationMethod

# Create SOC estimator
soc_estimator = SOCEstimator(
    method=SOCEstimationMethod.AEKF,
    nominal_capacity=50.0,  # Ah
    initial_soc=100.0
)

# Update SOC with measurements
current = -2.0  # A (negative for charging)
voltage = 3.8   # V
dt = 1.0        # seconds

soc = soc_estimator.update(current, voltage, dt)
print(f"Current SOC: {soc:.2f}%")
```

### Example 4: Fault Injection Testing

```python
from bms_core import FaultInjector, FaultType, Fault

# Create fault injector
fault_injector = FaultInjector()

# Inject a cell short fault
fault = Fault(
    fault_type=FaultType.CELL_SHORT,
    cell_position=(0, 0),  # First cell
    severity=0.5,  # 50% severity
    start_time=10.0
)
fault_injector.inject_fault(fault)

# Apply faults to cell state
cell_state = {
    "voltage": 3.7,
    "current": 0.0,
    "temperature": 298.15
}

modified_state = fault_injector.apply_faults(cell_state, current_time=15.0)
print(f"Voltage after fault: {modified_state['voltage']} V")
```

### Example 5: Charging Simulation

```python
from bms_core import ChargeDischargeSimulator, ChargingMode, ChargingProfile

# Create charging profile (CC-CV charging)
profile = ChargingProfile(
    mode=ChargingMode.CONSTANT_CURRENT_CONSTANT_VOLTAGE,
    cc_current=1.0,  # 1C rate
    cv_voltage=4.2,  # V
    termination_current=0.05  # 0.05C termination
)

# Create simulator
simulator = ChargeDischargeSimulator(charging_profile=profile)

# Simulate charging step
results = simulator.simulate_charging_step(
    voltage=3.8,
    soc=50.0,
    temperature=298.15,
    dt=1.0,
    nominal_capacity=50.0
)

print(f"Charging current: {results['current']} A")
print(f"Energy added: {results['energy_added']} Wh")
```

---

## 🔧 Configuration

### Configuration File Structure

Create a `config.json` file:

```json
{
    "battery": {
        "chemistry": "NMC",
        "model_type": "SPM",
        "nominal_capacity": 50.0,
        "nominal_voltage": 3.7,
        "initial_temperature": 298.15,
        "initial_soc": 100.0
    },
    "pack": {
        "cells_in_series": 16,
        "cells_in_parallel": 1,
        "balancing_enabled": true,
        "balancing_method": "passive",
        "balancing_threshold": 0.02
    },
    "simulation": {
        "duration": 3600,
        "time_step": 1.0,
        "simulation_mode": "Manual Parameter Mode"
    },
    "soc_estimation": {
        "method": "aekf",
        "coulombic_efficiency": 0.98
    },
    "logging": {
        "enabled": true,
        "log_directory": "logs",
        "log_format": "csv"
    }
}
```

See `config_example.json` for a complete example.

---

## 🎛️ GUI Features

The GAIA GUI provides:

1. **Simulation Control**
   - Start/Stop/Reset buttons
   - Real-time status indicators

2. **Configuration Panel**
   - Simulation mode selection
   - Battery chemistry selection
   - Model type selection
   - Pack configuration
   - Charging/discharging mode

3. **Parameter Adjustment**
   - C-rate slider
   - Voltage slider
   - Simulation time input
   - Initial temperature input

4. **Real-time Visualization**
   - Voltage vs Time
   - SOC vs Time
   - SOH vs Time
   - Current vs Time
   - Temperature vs Time
   - Internal Resistance vs Time

---

## 📈 Scalability Features

GAIA is designed for large-scale applications:

### 1. **Parallel Processing Support**
```python
from joblib import Parallel, delayed
from bms_core import BatteryPack

# Simulate multiple packs in parallel
packs = [BatteryPack(16, 1) for _ in range(100)]

results = Parallel(n_jobs=4)(
    delayed(pack.get_pack_statistics)() for pack in packs
)
```

### 2. **Batch Simulation**
GAIA supports batch processing for parameter sweeps and optimization studies.

### 3. **Memory Optimization**
- Efficient data structures
- Optional data streaming for large datasets
- Configurable cache management

### 4. **Distributed Computing Ready**
Architecture supports distributed computing frameworks (Dask, Ray) for cluster-level simulations.

---

## 🧪 Testing and Validation

### Running Tests

```bash
pytest tests/
```

### Fault Scenario Testing

```python
from bms_core import FaultInjector

fault_injector = FaultInjector()

# Load predefined scenario
scenario = fault_injector.create_fault_scenario("thermal_event")

for fault in scenario:
    fault_injector.inject_fault(fault)
```

---

## 📚 Documentation

- **API Documentation**: See `docs/` directory
- **Usage Guide**: See `Scripts/docs/usage_guide.md`
- **Research Notes**: See `Scripts/docs/research_notes.md`
- **Installation Guide**: See [INSTALLATION.md](INSTALLATION.md)
- **Quick Start**: See [QUICKSTART.md](QUICKSTART.md)

---

## 🔬 Advanced Features

### Custom Experiments

Define custom PyBaMM experiments:

```json
{
    "experiment_steps": [
        "Discharge at C/10 for 10 hours or until 3.3 V",
        "Rest for 1 hour",
        "Charge at 1 A until 4.1 V",
        "Hold at 4.1 V until 50 mA",
        "Rest for 1 hour"
    ],
    "repeat": 3
}
```

### Machine Learning Integration

GAIA's architecture supports ML-based SOC estimation:

```python
# Future: ML-based SOC estimator
from bms_core import ML_SOCEstimator

ml_estimator = ML_SOCEstimator(model_path="trained_model.h5")
```

---

## 🛠️ Extending GAIA

### Adding Custom Battery Chemistries

```python
from bms_core import BatteryModel
import pybamm

# Add custom parameter set
custom_params = pybamm.ParameterValues("CustomChemistry")
BatteryModel.CHEMISTRY_PARAMETERS["Custom"] = custom_params
```

### Creating Custom Balancing Algorithms

Extend the `BatteryBalancer` class:

```python
from bms_core import BatteryBalancer, BatteryPack

class CustomBalancer(BatteryBalancer):
    def balance(self, pack, dt):
        # Your custom balancing logic
        pass
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## 🙏 Acknowledgments

- **PyBaMM**: Advanced battery modeling library
- **PyQt5**: GUI framework
- **NumPy/SciPy**: Scientific computing foundation

---

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/GAIA/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/GAIA/discussions)
- **Email**: gaia@example.com

---

## 🔮 Roadmap

Future enhancements:
- [ ] Hardware-in-the-Loop (HIL) support
- [ ] CAN bus integration
- [ ] Cloud-based simulation platform
- [ ] Advanced ML-based optimization
- [ ] Multi-physics coupling (electro-thermal-mechanical)
- [ ] Digital twin capabilities

---

## 🌟 Key Differentiators

What makes GAIA unique:

1. **Comprehensive**: Covers all aspects of BMS from cell to pack level
2. **Scalable**: Designed for both single-cell and large-scale pack simulations
3. **Accurate**: State-of-the-art algorithms (AEKF, active balancing)
4. **Extensible**: Modular architecture for easy customization
5. **User-Friendly**: Intuitive GUI and clear API
6. **Well-Documented**: Extensive documentation and examples

---

**GAIA - Empowering the Future of Battery Technology** 🔋⚡

---

*Version 1.0.0 | Last Updated: 2024*
