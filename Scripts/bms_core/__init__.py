<<<<<<< HEAD
"""
GAIA BMS Core Module
Generalized Advanced Intelligent Analytics for Battery Management Systems
"""

from .battery_model import BatteryModel
from .simulation_manager import SimulatorManager
from .battery_pack import BatteryPack, CellState
from .soc_estimation import (
    SOCEstimator,
    SOCEstimationMethod,
    CoulombCountingSOC,
    KalmanFilterSOC,
    AdaptiveExtendedKalmanFilterSOC
)
from .battery_balancing import (
    BatteryBalancer,
    BalancingMethod,
    PassiveBalancing,
    ActiveBalancing
)
from .fault_injection import (
    FaultInjector,
    FaultType,
    Fault
)
from .charging_discharging_simulation import (
    ChargingController,
    DischargingController,
    ChargeDischargeSimulator,
    ChargingMode,
    DischargingMode,
    ChargingProfile,
    DischargingProfile
)
from .config_manager import ConfigManager

# New architecture components
from .hardware_interface import (
    HardwareInterface,
    SimulationHardwareInterface,
    RealHardwareInterface
)
from .bms_controller import (
    BMSController,
    BMSState,
    BMSStatus
)
from .protection_system import (
    ProtectionSystem,
    ProtectionLevel,
    ProtectionFaultType,
    ProtectionResult
)
from .simulation_engine import SimulationEngine

__version__ = "2.0.0"
__all__ = [
    # Legacy components (backward compatibility)
    "BatteryModel",
    "SimulatorManager",
    "BatteryPack",
    "CellState",
    "SOCEstimator",
    "SOCEstimationMethod",
    "CoulombCountingSOC",
    "KalmanFilterSOC",
    "AdaptiveExtendedKalmanFilterSOC",
    "BatteryBalancer",
    "BalancingMethod",
    "PassiveBalancing",
    "ActiveBalancing",
    "FaultInjector",
    "FaultType",
    "Fault",
    "ChargingController",
    "DischargingController",
    "ChargeDischargeSimulator",
    "ChargingMode",
    "DischargingMode",
    "ChargingProfile",
    "DischargingProfile",
    "ConfigManager",
    # New architecture components
    "HardwareInterface",
    "SimulationHardwareInterface",
    "RealHardwareInterface",
    "BMSController",
    "BMSState",
    "BMSStatus",
    "ProtectionSystem",
    "ProtectionLevel",
    "ProtectionFaultType",
    "ProtectionResult",
    "SimulationEngine",
]

=======
"""
GAIA BMS Core Module
Generalized Advanced Intelligent Analytics for Battery Management Systems
"""

from .battery_model import BatteryModel
from .simulation_manager import SimulatorManager
from .battery_pack import BatteryPack, CellState
from .soc_estimation import (
    SOCEstimator,
    SOCEstimationMethod,
    CoulombCountingSOC,
    KalmanFilterSOC,
    AdaptiveExtendedKalmanFilterSOC
)
from .battery_balancing import (
    BatteryBalancer,
    BalancingMethod,
    PassiveBalancing,
    ActiveBalancing
)
from .fault_injection import (
    FaultInjector,
    FaultType,
    Fault
)
from .charging_discharging_simulation import (
    ChargingController,
    DischargingController,
    ChargeDischargeSimulator,
    ChargingMode,
    DischargingMode,
    ChargingProfile,
    DischargingProfile
)
from .config_manager import ConfigManager

# New architecture components
from .hardware_interface import (
    HardwareInterface,
    SimulationHardwareInterface,
    RealHardwareInterface
)
from .bms_controller import (
    BMSController,
    BMSState,
    BMSStatus
)
from .protection_system import (
    ProtectionSystem,
    ProtectionLevel,
    ProtectionFaultType,
    ProtectionResult
)
from .simulation_engine import SimulationEngine

__version__ = "2.0.0"
__all__ = [
    # Legacy components (backward compatibility)
    "BatteryModel",
    "SimulatorManager",
    "BatteryPack",
    "CellState",
    "SOCEstimator",
    "SOCEstimationMethod",
    "CoulombCountingSOC",
    "KalmanFilterSOC",
    "AdaptiveExtendedKalmanFilterSOC",
    "BatteryBalancer",
    "BalancingMethod",
    "PassiveBalancing",
    "ActiveBalancing",
    "FaultInjector",
    "FaultType",
    "Fault",
    "ChargingController",
    "DischargingController",
    "ChargeDischargeSimulator",
    "ChargingMode",
    "DischargingMode",
    "ChargingProfile",
    "DischargingProfile",
    "ConfigManager",
    # New architecture components
    "HardwareInterface",
    "SimulationHardwareInterface",
    "RealHardwareInterface",
    "BMSController",
    "BMSState",
    "BMSStatus",
    "ProtectionSystem",
    "ProtectionLevel",
    "ProtectionFaultType",
    "ProtectionResult",
    "SimulationEngine",
]

>>>>>>> e25e88bc9d309c3e29a000420b6d5c43e3c84787
