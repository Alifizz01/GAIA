"""
Battery Balancing Module for GAIA BMS Framework
Implements passive and active balancing algorithms for battery pack management.
"""

import numpy as np
from typing import List, Tuple, Dict, Optional
from enum import Enum
from .battery_pack import BatteryPack, CellState


class BalancingMethod(Enum):
    """Available balancing methods."""
    PASSIVE = "passive"  # Resistor-based dissipative balancing
    ACTIVE_INDUCTIVE = "active_inductive"  # Inductor-based active balancing
    ACTIVE_CAPACITIVE = "active_capacitive"  # Capacitor-based active balancing


class PassiveBalancing:
    """
    Passive (Dissipative) Balancing using resistors.
    Discharges cells with higher SOC to match lower cells.
    """
    
    def __init__(self, balancing_current: float = 0.1, balancing_threshold: float = 0.02,
                 resistor_value: float = 10.0):
        """
        Initialize passive balancing.
        
        Args:
            balancing_current: Balancing current in Amperes
            balancing_threshold: SOC difference threshold to trigger balancing (%)
            resistor_value: Balancing resistor value in Ohms
        """
        self.balancing_current = balancing_current  # A
        self.balancing_threshold = balancing_threshold  # 2% = 0.02
        self.resistor_value = resistor_value  # Ohms
        self.active_cells = set()  # Cells currently being balanced
        
    def calculate_balancing_action(self, pack: BatteryPack) -> Dict[Tuple[int, int], float]:
        """
        Calculate which cells need balancing and required current.
        
        Args:
            pack: BatteryPack instance
            
        Returns:
            Dictionary mapping (series_idx, parallel_idx) to balancing current
        """
        balancing_actions = {}
        
        # Calculate average SOC for each series group
        series_avg_soc = []
        for series_group in pack.cells:
            avg_soc = np.mean([cell.soc for cell in series_group])
            series_avg_soc.append(avg_soc)
        
        overall_avg = np.mean(series_avg_soc)
        
        # Find cells that need balancing
        for s_idx, series_group in enumerate(pack.cells):
            series_avg = series_avg_soc[s_idx]
            
            # Only balance if series group is significantly above average
            if series_avg > overall_avg + self.balancing_threshold * 100:
                for p_idx, cell in enumerate(series_group):
                    # Balance cells above the series average
                    if cell.soc > series_avg:
                        balancing_actions[(s_idx, p_idx)] = self.balancing_current
        
        return balancing_actions
    
    def apply_balancing(self, pack: BatteryPack, dt: float) -> float:
        """
        Apply passive balancing to the pack.
        
        Args:
            pack: BatteryPack instance
            dt: Time step in seconds
            
        Returns:
            Total power dissipated during balancing (Watts)
        """
        balancing_actions = self.calculate_balancing_action(pack)
        total_power = 0.0
        dt_hours = dt / 3600.0
        
        for (s_idx, p_idx), balance_current in balancing_actions.items():
            cell = pack.cells[s_idx][p_idx]
            
            # Estimate capacity change (simplified)
            # Assuming nominal voltage for power calculation
            power_dissipated = cell.voltage * balance_current
            total_power += power_dissipated
            
            # Update cell SOC (discharging)
            capacity_change = balance_current * dt_hours  # Ah
            nominal_capacity = 50.0  # Ah (should come from pack configuration)
            soc_change = (capacity_change / nominal_capacity) * 100.0
            
            # Update cell SOC
            cell.soc = max(0.0, cell.soc - abs(soc_change))
            
            self.active_cells.add((s_idx, p_idx))
        
        # Remove cells that no longer need balancing
        cells_to_remove = []
        for cell_pos in self.active_cells:
            if cell_pos not in balancing_actions:
                cells_to_remove.append(cell_pos)
        for cell_pos in cells_to_remove:
            self.active_cells.remove(cell_pos)
        
        return total_power


class ActiveBalancing:
    """
    Active balancing using energy transfer between cells.
    More efficient than passive balancing but more complex.
    """
    
    def __init__(self, balancing_efficiency: float = 0.85, balancing_threshold: float = 0.02,
                 max_balancing_current: float = 2.0):
        """
        Initialize active balancing.
        
        Args:
            balancing_efficiency: Efficiency of energy transfer (0-1)
            balancing_threshold: SOC difference threshold to trigger balancing (%)
            max_balancing_current: Maximum balancing current in Amperes
        """
        self.balancing_efficiency = balancing_efficiency
        self.balancing_threshold = balancing_threshold
        self.max_balancing_current = max_balancing_current
        self.active_transfers = {}  # Current active energy transfers
        
    def calculate_balancing_action(self, pack: BatteryPack) -> List[Tuple[Tuple, Tuple, float]]:
        """
        Calculate energy transfers needed for balancing.
        
        Returns:
            List of (source_cell, target_cell, current) tuples
        """
        transfers = []
        
        # Find cells with highest and lowest SOC
        all_cells = []
        for s_idx, series_group in enumerate(pack.cells):
            for p_idx, cell in enumerate(series_group):
                all_cells.append(((s_idx, p_idx), cell.soc, cell))
        
        if len(all_cells) < 2:
            return transfers
        
        # Sort by SOC
        all_cells.sort(key=lambda x: x[1], reverse=True)
        
        # Calculate average SOC
        avg_soc = np.mean([soc for _, soc, _ in all_cells])
        
        # Transfer energy from high SOC cells to low SOC cells
        high_cells = [(pos, cell) for (pos, soc, cell) in all_cells 
                     if soc > avg_soc + self.balancing_threshold * 100]
        low_cells = [(pos, cell) for (pos, soc, cell) in all_cells 
                    if soc < avg_soc - self.balancing_threshold * 100]
        
        # Match high cells with low cells
        for high_pos, high_cell in high_cells:
            if not low_cells:
                break
            
            low_pos, low_cell = low_cells[0]
            
            # Calculate required current based on SOC difference
            soc_diff = high_cell.soc - low_cell.soc
            balance_current = min(self.max_balancing_current, soc_diff * 0.1)
            
            if balance_current > 0.01:  # Minimum threshold
                transfers.append((high_pos, low_pos, balance_current))
                low_cells.pop(0)
        
        return transfers
    
    def apply_balancing(self, pack: BatteryPack, dt: float) -> float:
        """
        Apply active balancing to the pack.
        
        Args:
            pack: BatteryPack instance
            dt: Time step in seconds
            
        Returns:
            Total energy transferred (Ah)
        """
        transfers = self.calculate_balancing_action(pack)
        total_energy = 0.0
        dt_hours = dt / 3600.0
        
        for source_pos, target_pos, current in transfers:
            source_cell = pack.cells[source_pos[0]][source_pos[1]]
            target_cell = pack.cells[target_pos[0]][target_pos[1]]
            
            # Calculate energy transfer
            energy_transfer = current * dt_hours  # Ah
            effective_energy = energy_transfer * self.balancing_efficiency
            
            # Update cell states
            nominal_capacity = 50.0  # Ah (should come from configuration)
            
            # Source cell loses energy
            soc_change_source = (energy_transfer / nominal_capacity) * 100.0
            source_cell.soc = max(0.0, source_cell.soc - soc_change_source)
            
            # Target cell gains energy (with efficiency loss)
            soc_change_target = (effective_energy / nominal_capacity) * 100.0
            target_cell.soc = min(100.0, target_cell.soc + soc_change_target)
            
            total_energy += effective_energy
        
        return total_energy


class BatteryBalancer:
    """
    Unified battery balancing interface supporting multiple methods.
    """
    
    def __init__(self, method: BalancingMethod = BalancingMethod.PASSIVE,
                 balancing_threshold: float = 0.02):
        """
        Initialize battery balancer.
        
        Args:
            method: Balancing method to use
            balancing_threshold: SOC difference threshold to trigger balancing
        """
        self.method = method
        self.balancing_threshold = balancing_threshold
        
        if method == BalancingMethod.PASSIVE:
            self.balancer = PassiveBalancing(balancing_threshold=balancing_threshold)
        elif method == BalancingMethod.ACTIVE_INDUCTIVE:
            self.balancer = ActiveBalancing(balancing_threshold=balancing_threshold)
        elif method == BalancingMethod.ACTIVE_CAPACITIVE:
            self.balancer = ActiveBalancing(balancing_threshold=balancing_threshold)
        else:
            raise ValueError(f"Unknown balancing method: {method}")
    
    def balance(self, pack: BatteryPack, dt: float) -> Dict:
        """
        Perform balancing on the battery pack.
        
        Args:
            pack: BatteryPack instance
            dt: Time step in seconds
            
        Returns:
            Dictionary with balancing statistics
        """
        imbalance_before = pack.get_cell_imbalance()
        
        if self.method == BalancingMethod.PASSIVE:
            power_dissipated = self.balancer.apply_balancing(pack, dt)
            return {
                "method": "passive",
                "power_dissipated": power_dissipated,
                "imbalance_before": imbalance_before,
                "imbalance_after": pack.get_cell_imbalance(),
                "active_cells": len(self.balancer.active_cells)
            }
        else:
            energy_transferred = self.balancer.apply_balancing(pack, dt)
            return {
                "method": "active",
                "energy_transferred": energy_transferred,
                "imbalance_before": imbalance_before,
                "imbalance_after": pack.get_cell_imbalance()
            }
    
    def is_balancing_needed(self, pack: BatteryPack) -> bool:
        """Check if balancing is needed based on cell imbalance."""
        imbalance = pack.get_cell_imbalance()
        return imbalance["max_soc_diff"] > self.balancing_threshold * 100

