"""
Example: Using the New GAIA BMS Architecture
Demonstrates the new architecture with Hardware Abstraction Layer,
BMS Controller, and Real-time Simulation Engine.
"""

import sys
import os
import time

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from bms_core import (
    SimulationHardwareInterface,
    BMSController,
    SimulationEngine,
    ChargingProfile,
    ChargingMode
)


def main():
    """Main example demonstrating new architecture."""
    
    print("=" * 70)
    print("GAIA BMS Framework - New Architecture Example")
    print("=" * 70)
    print()
    
    # ========================================================================
    # Step 1: Configure the System
    # ========================================================================
    print("Step 1: Configuring system...")
    
    pack_config = {
        "cells_in_series": 16,
        "cells_in_parallel": 1,
        "chemistry": "NMC",
        "nominal_capacity": 50.0,  # Ah
        "initial_soc": 80.0  # Start at 80% SOC
    }
    
    battery_model_config = {
        "chemistry": "NMC",
        "model_type": "SPM",
        "initial_temperature": 298.15,  # 25°C
        "nominal_voltage": 3.7
    }
    
    bms_config = {
        "protection": {
            "overvoltage_threshold": 4.25,  # V
            "undervoltage_threshold": 2.5,   # V
            "overcurrent_threshold": 100.0,  # A
            "overtemperature_threshold": 60.0,  # °C
            "imbalance_threshold": 0.2  # V
        },
        "soc_estimation": {
            "method": "aekf"
        },
        "balancing": {
            "enabled": True,
            "method": "passive",
            "threshold": 0.02  # 2% SOC difference
        },
        "control_loop_frequency": 10.0  # 10 Hz
    }
    
    simulation_config = {
        "control_loop_frequency": 10.0,  # Hz
        "logging": {
            "enabled": True,
            "log_directory": "logs",
            "log_format": "csv",
            "log_interval": 1.0  # seconds
        }
    }
    
    print(f"  Pack: {pack_config['cells_in_series']}s{pack_config['cells_in_parallel']}p")
    print(f"  Chemistry: {pack_config['chemistry']}")
    print(f"  Initial SOC: {pack_config['initial_soc']}%")
    print()
    
    # ========================================================================
    # Step 2: Create Hardware Interface (Simulation)
    # ========================================================================
    print("Step 2: Creating hardware interface (simulation mode)...")
    
    hardware = SimulationHardwareInterface(
        pack_config=pack_config,
        battery_model_config=battery_model_config
    )
    
    if not hardware.initialize():
        print("ERROR: Failed to initialize hardware interface")
        return
    
    print("  ✓ Hardware interface initialized (simulation mode)")
    print(f"  Total cells: {hardware.total_cells}")
    print()
    
    # ========================================================================
    # Step 3: Create BMS Controller
    # ========================================================================
    print("Step 3: Creating BMS controller...")
    
    bms_controller = BMSController(
        hardware_interface=hardware,
        pack_config=pack_config,
        bms_config=bms_config
    )
    
    if not bms_controller.initialize():
        print("ERROR: Failed to initialize BMS controller")
        return
    
    print("  ✓ BMS controller initialized")
    print(f"  Initial state: {bms_controller.state.value}")
    print()
    
    # ========================================================================
    # Step 4: Create Simulation Engine
    # ========================================================================
    print("Step 4: Creating simulation engine...")
    
    engine = SimulationEngine(
        hardware_interface=hardware,
        pack_config=pack_config,
        bms_config=bms_config,
        simulation_config=simulation_config
    )
    
    # Register status callback for monitoring
    def status_callback(bms_status):
        """Callback for status updates."""
        pass  # Could print status here
    
    engine.register_status_callback(status_callback)
    
    if not engine.initialize():
        print("ERROR: Failed to initialize simulation engine")
        return
    
    print("  ✓ Simulation engine initialized")
    print()
    
    # ========================================================================
    # Step 5: Start Simulation
    # ========================================================================
    print("Step 5: Starting simulation...")
    print()
    
    engine.start_simulation()
    
    # Wait for engine to start
    time.sleep(0.5)
    
    print("  ✓ Simulation started")
    print("  Running control loop at 10 Hz...")
    print()
    
    # ========================================================================
    # Step 6: Run Charging Scenario
    # ========================================================================
    print("Step 6: Running charging scenario...")
    print()
    
    # Set up charging profile
    charging_profile = ChargingProfile(
        mode=ChargingMode.CONSTANT_CURRENT_CONSTANT_VOLTAGE,
        cc_current=1.0,  # 1C rate
        cv_voltage=4.2,  # V
        termination_current=0.05  # 0.05C termination
    )
    
    engine.set_charging_profile(charging_profile)
    engine.bms_controller.enable_charging(True)
    
    print("  Charging at 1C rate (50A)...")
    print()
    
    # Monitor simulation for 10 seconds
    print("Monitoring simulation (10 seconds)...")
    print("-" * 70)
    print(f"{'Time':<8} {'State':<12} {'Pack V':<10} {'Pack I':<10} {'SOC':<8} {'Temp':<8}")
    print("-" * 70)
    
    start_time = time.time()
    last_print_time = 0.0
    
    while time.time() - start_time < 10.0:
        status = engine.get_status()
        bms_status = status.get("bms_status")
        
        if bms_status and (time.time() - last_print_time) >= 1.0:
            print(f"{status['simulation_time']:>6.1f}s  "
                  f"{bms_status.state.value:<12} "
                  f"{bms_status.pack_voltage:>6.2f}V  "
                  f"{bms_status.pack_current:>7.2f}A  "
                  f"{bms_status.pack_soc:>5.1f}%  "
                  f"{bms_status.pack_temperature-273.15:>5.1f}°C")
            last_print_time = time.time()
        
        time.sleep(0.1)
    
    print("-" * 70)
    print()
    
    # ========================================================================
    # Step 7: Display Final Status
    # ========================================================================
    print("Step 7: Final status...")
    print()
    
    final_status = engine.get_status()
    bms_status = final_status["bms_status"]
    
    print(f"  Simulation time: {final_status['simulation_time']:.1f} seconds")
    print(f"  BMS state: {bms_status.state.value}")
    print(f"  Pack voltage: {bms_status.pack_voltage:.2f} V")
    print(f"  Pack current: {bms_status.pack_current:.2f} A")
    print(f"  Pack SOC: {bms_status.pack_soc:.1f} %")
    print(f"  Pack temperature: {bms_status.pack_temperature - 273.15:.1f} °C")
    print(f"  Active faults: {len(bms_status.active_faults)}")
    print(f"  Balancing active: {bms_status.balancing_active}")
    print()
    
    # ========================================================================
    # Step 8: Cleanup
    # ========================================================================
    print("Step 8: Stopping simulation...")
    
    engine.stop_simulation()
    engine.close()
    
    print("  ✓ Simulation stopped")
    print()
    
    print("=" * 70)
    print("Example completed successfully!")
    print("=" * 70)
    print()
    print("Next steps:")
    print("  - Try different pack configurations")
    print("  - Experiment with different charging profiles")
    print("  - Test protection functions by injecting faults")
    print("  - Integrate with real hardware using RealHardwareInterface")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nSimulation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

