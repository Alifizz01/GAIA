"""
Data Logging Module for GAIA BMS Framework
Handles logging of simulation data to CSV files and databases.

NOTE: DataLogger has been moved to bms_core.data_logger.
This file provides backward compatibility by re-exporting it.
"""

# Backward compatibility: re-export from bms_core
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from bms_core.data_logger import DataLogger

__all__ = ["DataLogger"]
