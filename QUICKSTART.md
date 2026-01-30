# GAIA Quick Start Guide

## Installation

```bash
# Clone repository
git clone https://github.com/yourusername/GAIA.git
cd GAIA

# Install dependencies
pip install -r requirements.txt

# Optional: Install GAIA package
pip install -e .
```

## Running the GUI

```bash
python Scripts/gui/main_window.py
```

Or use the command:
```bash
gaia-simulator
```

## Basic Usage

### Simple Battery Simulation

```python
from bms_core import BatteryModel

# Create battery model
battery = BatteryModel(
    model_type="SPM",
    chemistry="NMC",
    initial_temperature=298.15
)

# Run 1-hour simulation
solution = battery.run_simulation(duration=3600)

# Extract results
time = solution["Time [s]"].entries
voltage = battery.get_voltage(solution, time)
soc = battery.get_soc(solution, time)
```

### Battery Pack Simulation

```python
from bms_core import BatteryPack, BatteryBalancer, BalancingMethod

# Create 16s1p pack
pack = BatteryPack(16, 1, chemistry="NMC")

# Create balancer
balancer = BatteryBalancer(method=BalancingMethod.PASSIVE)

# Check imbalance
imbalance = pack.get_cell_imbalance()
print(f"Max SOC difference: {imbalance['max_soc_diff']}%")

# Balance if needed
if balancer.is_balancing_needed(pack):
    results = balancer.balance(pack, dt=1.0)
    print(f"Balancing complete. Power dissipated: {results['power_dissipated']} W")
```

### SOC Estimation

```python
from bms_core import SOCEstimator, SOCEstimationMethod

# Create AEKF estimator
estimator = SOCEstimator(
    method=SOCEstimationMethod.AEKF,
    nominal_capacity=50.0,
    initial_soc=100.0
)

# Update with measurements
soc = estimator.update(
    current=-2.0,  # A (charging)
    voltage=3.8,   # V
    dt=1.0         # seconds
)
print(f"SOC: {soc:.2f}%")
```

### Using Configuration Files

```python
from bms_core import ConfigManager, SimulatorManager

# Load configuration
config = ConfigManager("config_example.json")

# Create simulator
sim_manager = SimulatorManager(
    model_type=config.get("battery.model_type"),
    chemistry=config.get("battery.chemistry"),
    initial_temperature=config.get("battery.initial_temperature")
)

# Run simulation
sim_manager.run_battery_simulation(
    duration=config.get("simulation.duration")
)

# Get results
time, voltage, soc, temp, current = sim_manager.get_simulation_results()
```

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check [Scripts/docs/usage_guide.md](Scripts/docs/usage_guide.md) for advanced usage
- Explore examples in the [tests/](Scripts/tests/) directory

