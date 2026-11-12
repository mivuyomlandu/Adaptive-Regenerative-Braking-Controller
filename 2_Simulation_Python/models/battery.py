"""
Battery model (12V, 7Ah Sealed Lead Acid).

Simulates the State of Charge (SoC) and voltage.
Enforces charging limits (max charging current, max voltage).
"""

import numpy as np

class BatteryModel:
    def __init__(self):
        # --- Nameplate Data ---
        self.capacity_Ah = 7.0             # [Ah] 7 Amp-hours
        self.nominal_voltage = 12.0        # [V]
        
        # --- Charging Limits (SLA Battery safety) ---
        # SLA batteries should not be charged faster than C/5 (1.4A) or C/10 (0.7A)
        self.max_charge_current = 1.4      # [A] Max safe charging current
        self.max_voltage = 14.4            # [V] Bulk charge voltage limit
        
        # --- Internal Resistance ---
        self.R_internal = 0.05             # [ohm] [ASSUMED]
        
        # --- State ---
        # Start at 50% SoC for the simulation
        self.soc = 0.5                     # [0.0 to 1.0]
        
    def get_open_circuit_voltage(self):
        """Estimate Open Circuit Voltage based on State of Charge."""
        # Simple linear approximation for SLA:
        # 11.8V at 0%, 12.7V at 100%
        return 11.8 + (self.soc * (12.7 - 11.8))

    def is_accepting_charge(self, charge_current):
        """Check if the battery can safely accept this current."""
        if self.soc >= 0.98: # Don't charge if full
            return False
        if charge_current > self.max_charge_current:
            return False
        return True

    def update_state(self, charge_current, dt):
        """Update the State of Charge based on current flowing IN."""
        # If current is negative, it means discharging. If positive, charging.
        if charge_current > 0:
            # Limit current to max safe value
            actual_current = min(charge_current, self.max_charge_current)
            
            # Convert Amps to Amp-seconds, then to Amp-hours (Ah)
            Ah_added = (actual_current * dt) / 3600.0
            
            # Update SoC (Capacity is 7Ah, so 1 hour of 7A = 100% increase)
            self.soc += (Ah_added / self.capacity_Ah)
            
            # Cap at 100%
            if self.soc > 1.0:
                self.soc = 1.0