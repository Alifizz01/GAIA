"""
Data Logging Module for GAIA BMS Framework
Handles logging of simulation data to CSV files and databases.
"""

import csv
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np


class DataLogger:
    """
    Handles data logging for BMS simulations.
    Supports CSV and JSON formats with configurable logging intervals.
    """
    
    def __init__(self, log_directory: str = "logs", log_format: str = "csv"):
        """
        Initialize data logger.
        
        Args:
            log_directory: Directory to save log files
            log_format: Log format ("csv" or "json")
        """
        self.log_directory = log_directory
        self.log_format = log_format.lower()
        os.makedirs(log_directory, exist_ok=True)
        
        # Create timestamped log file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_filename = os.path.join(
            log_directory, 
            f"bms_simulation_{timestamp}.{log_format}"
        )
        
        self.log_data = []
        self.fieldnames = [
            "timestamp", "time", "voltage", "current", "soc", "soh", 
            "temperature", "power", "energy"
        ]
        
        # Initialize log file
        if self.log_format == "csv":
            self._initialize_csv_file()
    
    def _initialize_csv_file(self):
        """Initialize CSV file with headers."""
        with open(self.log_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
    
    def log(self, data: Dict, timestamp: Optional[float] = None):
        """
        Log a data point.
        
        Args:
            data: Dictionary with simulation data
            timestamp: Optional timestamp (uses current time if None)
        """
        if timestamp is None:
            timestamp = datetime.now().timestamp()
        
        log_entry = {
            "timestamp": timestamp,
            "time": data.get("time", 0.0),
            "voltage": data.get("voltage", 0.0),
            "current": data.get("current", 0.0),
            "soc": data.get("soc", 0.0),
            "soh": data.get("soh", 100.0),
            "temperature": data.get("temperature", 298.15),
            "power": data.get("power", 0.0),
            "energy": data.get("energy", 0.0)
        }
        
        self.log_data.append(log_entry)
        
        # Write to file immediately
        if self.log_format == "csv":
            self._write_csv_row(log_entry)
        elif self.log_format == "json":
            self._write_json_data()
    
    def _write_csv_row(self, row: Dict):
        """Write a single row to CSV file."""
        with open(self.log_filename, 'a', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writerow(row)
    
    def _write_json_data(self):
        """Write all data to JSON file."""
        with open(self.log_filename, 'w') as jsonfile:
            json.dump(self.log_data, jsonfile, indent=2)
    
    def log_batch(self, data_list: List[Dict]):
        """
        Log multiple data points at once.
        
        Args:
            data_list: List of data dictionaries
        """
        for data in data_list:
            self.log(data)
    
    def log_pack_data(self, pack_statistics: Dict, time: float):
        """
        Log battery pack statistics.
        
        Args:
            pack_statistics: Dictionary from BatteryPack.get_pack_statistics()
            time: Current simulation time
        """
        data = {
            "time": time,
            "voltage": pack_statistics.get("pack_voltage", 0.0),
            "current": pack_statistics.get("pack_current", 0.0),
            "soc": pack_statistics.get("pack_soc", 0.0),
            "soh": pack_statistics.get("pack_soh", 100.0),
            "power": pack_statistics.get("pack_power", 0.0),
            "temperature": pack_statistics.get("imbalance", {}).get("max_temperature", 298.15)
        }
        self.log(data)
    
    def get_log_data(self) -> List[Dict]:
        """Get all logged data."""
        return self.log_data.copy()
    
    def export_to_csv(self, filename: Optional[str] = None):
        """Export all logged data to CSV."""
        export_filename = filename or self.log_filename.replace(
            f".{self.log_format}", ".csv"
        )
        
        with open(export_filename, 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.fieldnames)
            writer.writeheader()
            writer.writerows(self.log_data)
    
    def export_to_json(self, filename: Optional[str] = None):
        """Export all logged data to JSON."""
        export_filename = filename or self.log_filename.replace(
            f".{self.log_format}", ".json"
        )
        
        with open(export_filename, 'w') as jsonfile:
            json.dump(self.log_data, jsonfile, indent=2)
    
    def clear(self):
        """Clear all logged data."""
        self.log_data.clear()
        if self.log_format == "csv":
            self._initialize_csv_file()
    
    def close(self):
        """Close the logger and finalize log file."""
        if self.log_format == "json":
            self._write_json_data()

