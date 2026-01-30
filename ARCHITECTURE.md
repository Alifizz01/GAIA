# GAIA BMS Framework - Architecture & Design

## 🏗️ System Architecture Overview

GAIA is built on a **modular, layered architecture** that separates concerns and enables both simulation and real hardware integration. The architecture follows a **BMS Controller-centric design** where all battery management functions are orchestrated by a central controller.

### Core Philosophy

1. **Simulation-First**: Complete simulation capabilities for development and testing
2. **Hardware-Ready**: Seamless transition from simulation to hardware via abstraction layer
3. **Scalable**: Support from single cell to large battery packs
4. **Real-time Capable**: Designed for both real-time simulation and hardware operation

---

## 📐 Architecture Layers

### Layer 1: Hardware Abstraction Layer (HAL)
**Purpose**: Abstract away the differences between simulation and real hardware

- **`HardwareInterface`**: Base class defining interface for data acquisition and control
- **`SimulationHardwareInterface`**: Implements interface using PyBaMM models
- **`RealHardwareInterface`**: Implements interface for actual hardware (CAN, I2C, SPI, etc.)

**Key Features**:
- Read cell voltages, currents, temperatures
- Write control commands (enable/disable, balancing, etc.)
- Hardware discovery and configuration
- Error handling and reconnection

### Layer 2: BMS Controller Core
**Purpose**: The "brain" of the BMS - all decision-making logic

**Components**:
- **`BMSController`**: Main controller orchestrating all functions
- **`ProtectionSystem`**: Safety functions (overvoltage, overcurrent, overtemperature protection)
- **`StateMachine`**: System state management (IDLE, CHARGING, DISCHARGING, FAULT, etc.)
- **`ControlLoop`**: Real-time control loop that runs all BMS functions

**Key Features**:
- Protection algorithms (OV, UV, OC, OT, SC protection)
- Balancing control (passive/active)
- Charge/discharge control
- Fault detection and handling
- State management

### Layer 3: Battery Management Functions
**Purpose**: Specialized algorithms and functions

**Components**:
- **`SOCEstimator`**: State of Charge estimation (Coulomb Counting, EKF, AEKF)
- **`SOHEstimator`**: State of Health estimation
- **`BatteryBalancer`**: Cell balancing algorithms
- **`ThermalManager`**: Thermal monitoring and cooling control
- **`AgingModel`**: Battery aging and degradation modeling

### Layer 4: Data Acquisition & Monitoring
**Purpose**: Collect, process, and store system data

**Components**:
- **`DataAcquisition`**: Unified data collection from HAL
- **`DataLogger`**: Logging to files/databases
- **`Monitor`**: Real-time monitoring and alerting
- **`Analytics`**: Data analysis and reporting

### Layer 5: Application Layer
**Purpose**: User interfaces and application logic

**Components**:
- **GUI**: PyQt5-based graphical interface
- **CLI**: Command-line interface
- **API**: REST/WebSocket API for remote access
- **Simulation Engine**: High-level simulation orchestration

---

## 🔄 System Operation Modes

### Mode 1: Pure Simulation
- All components run in simulation mode
- Uses PyBaMM for battery modeling
- Fast iteration and testing
- No hardware required

### Mode 2: Hardware-in-the-Loop (HIL)
- BMS Controller runs on real hardware
- Battery models run in simulation
- Testing BMS algorithms with simulated batteries

### Mode 3: Real Hardware
- All components interface with real hardware
- Production deployment
- Full hardware abstraction via HAL

### Mode 4: Hybrid
- Mix of simulated and real components
- Gradual migration path from simulation to hardware

---

## 🔋 BMS Controller State Machine

```
┌─────────┐
│  IDLE   │───[Start Charge]──>┌──────────┐
└─────────┘                     │ CHARGING │
   ↑                            └──────────┘
   │                                   │
   │                                   │
   │                                   ▼
┌──────────┐                    ┌──────────┐
│ FAULT    │<──[Protection]───  │DISCHARGING│
└──────────┘                    └──────────┘
   │                                   │
   │                                   │
   └───────[Reset/Clear]───────────────┘
```

**States**:
- **IDLE**: System ready, no active operations
- **CHARGING**: Charging operation active
- **DISCHARGING**: Discharging operation active
- **BALANCING**: Balancing operation active
- **FAULT**: Protection triggered, operation suspended
- **EMERGENCY**: Critical fault, immediate shutdown

---

## 🔌 Hardware Abstraction Layer (HAL) Design

### Interface Contract

```python
class HardwareInterface(ABC):
    """Abstract interface for hardware access"""
    
    @abstractmethod
    def initialize(self) -> bool:
        """Initialize hardware connection"""
        
    @abstractmethod
    def read_cell_voltage(self, cell_id: int) -> float:
        """Read voltage from cell"""
        
    @abstractmethod
    def read_cell_current(self) -> float:
        """Read pack current"""
        
    @abstractmethod
    def read_temperature(self, sensor_id: int) -> float:
        """Read temperature from sensor"""
        
    @abstractmethod
    def enable_charge(self, enable: bool):
        """Enable/disable charging"""
        
    @abstractmethod
    def enable_balance(self, cell_id: int, enable: bool):
        """Enable/disable balancing for cell"""
```

### Implementation Types

1. **SimulationHardwareInterface**
   - Uses PyBaMM BatteryModel for cell simulation
   - Simulates ADC readings, noise, sampling delays
   - Perfect for testing and development

2. **RealHardwareInterface**
   - Communicates via CAN bus, I2C, SPI, Modbus, etc.
   - Handles hardware-specific protocols
   - Error recovery and reconnection logic

3. **MockHardwareInterface**
   - Test stub with configurable responses
   - Useful for unit testing

---

## 🎯 Real-time Simulation Engine

### Control Loop Architecture

```
┌─────────────────────────────────────────┐
│     Real-time Simulation Loop           │
├─────────────────────────────────────────┤
│ 1. Read hardware state (via HAL)        │
│ 2. BMS Controller processing:            │
│    - Protection checks                  │
│    - SOC estimation                     │
│    - Balancing control                  │
│    - State machine updates              │
│ 3. Calculate control outputs            │
│ 4. Write control commands (via HAL)     │
│ 5. Update battery model (simulation)    │
│ 6. Data acquisition and logging         │
│ 7. Wait for next time step              │
└─────────────────────────────────────────┘
```

### Timing Considerations

- **Control Loop Frequency**: 10-100 Hz (configurable)
- **Protection Checks**: Every loop iteration
- **SOC Update**: Every loop iteration
- **Balancing Control**: Every loop iteration
- **Data Logging**: Configurable interval (1-10 Hz)
- **Thermal Updates**: 1 Hz

---

## 📊 Data Flow Architecture

```
Hardware/Simulation
    ↓ (via HAL)
Data Acquisition
    ↓
BMS Controller
    ↓
├──→ Protection System
├──→ SOC Estimator
├──→ Balancing Controller
├──→ State Machine
└──→ Control Outputs
    ↓ (via HAL)
Hardware/Simulation
    ↓
Data Logger
    ↓
GUI/Dashboard
```

---

## 🔐 Protection System Design

### Protection Levels

1. **Warning Level**: Log warning, continue operation
2. **Pre-Alarm Level**: Reduce power/current, log alert
3. **Alarm Level**: Stop operation, enter FAULT state
4. **Emergency Level**: Immediate shutdown, disconnect pack

### Protection Functions

- **Overvoltage Protection (OVP)**: Cell voltage > threshold
- **Undervoltage Protection (UVP)**: Cell voltage < threshold
- **Overcurrent Protection (OCP)**: Pack current > threshold
- **Overtemperature Protection (OTP)**: Temperature > threshold
- **Short Circuit Protection (SCP)**: Rapid current rise detection
- **Imbalance Protection**: Cell imbalance > threshold

---

## 🧪 Testing Strategy

### Unit Tests
- Individual components (SOC estimator, balancer, etc.)
- Hardware interface mocks

### Integration Tests
- BMS Controller with simulated hardware
- End-to-end simulation scenarios

### Hardware Tests
- HIL testing with real BMS controller
- Real hardware validation

---

## 🚀 Scalability Design

### Single Cell
- Minimal overhead
- Direct HAL connection

### Small Pack (1-16 cells)
- Standard BMS Controller
- Single-threaded operation

### Medium Pack (16-96 cells)
- Multi-threaded cell monitoring
- Hierarchical balancing

### Large Pack (96+ cells)
- Distributed architecture
- Module-level BMS controllers
- Master BMS coordinator

---

## 📝 Configuration System

### Configuration Hierarchy

1. **Hardware Configuration**: Hardware-specific settings
2. **BMS Configuration**: Protection thresholds, algorithms
3. **Simulation Configuration**: Model parameters, time steps
4. **Application Configuration**: GUI settings, logging

### Configuration Files

- **hardware_config.json**: Hardware interface settings
- **bms_config.json**: BMS controller parameters
- **simulation_config.json**: Simulation parameters
- **app_config.json**: Application settings

---

## 🔄 Migration Path: Simulation → Hardware

1. **Phase 1**: Develop in pure simulation
2. **Phase 2**: Replace HAL with hardware interface
3. **Phase 3**: Test with real hardware
4. **Phase 4**: Deploy to production

The architecture supports this migration with minimal code changes!

---

## 🎨 UI Architecture

### Main Dashboard
- Real-time plots (voltage, SOC, temperature, current)
- System status indicators
- Control buttons (start/stop/reset)
- Alert panel

### Configuration Panel
- Hardware selection (simulation/hardware)
- BMS parameters
- Protection thresholds
- Simulation parameters

### Monitoring Views
- Cell-level detail views
- Pack statistics
- Historical data
- Fault history

---

## 🔮 Future Extensions

### Planned Features
- **Cloud Integration**: Remote monitoring and control
- **Machine Learning**: Adaptive SOC estimation, fault prediction
- **Digital Twin**: Real-time synchronization with physical system
- **Edge Computing**: Deploy BMS Controller to edge devices
- **Multi-Protocol Support**: CAN, Modbus, Ethernet, wireless

---

## 📚 Key Design Principles

1. **Separation of Concerns**: Clear boundaries between layers
2. **Dependency Inversion**: High-level modules depend on abstractions
3. **Single Responsibility**: Each component has one clear purpose
4. **Open/Closed**: Open for extension, closed for modification
5. **Testability**: Easy to test with mocks and stubs

---

**Version**: 2.0.0  
**Last Updated**: 2024  
**Status**: Active Development

