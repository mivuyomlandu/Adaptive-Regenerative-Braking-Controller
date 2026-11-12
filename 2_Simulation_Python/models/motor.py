import numpy as np

class MotorWheelModel:
    def __init__(self):
        # --- Nameplate Data (RS PRO 12V Motor) ---
        self.V_supply = 12.0                  # [V]
        self.no_load_rpm = 98.0               # [RPM]
        self.stall_torque = 59.0 / 100.0      # [N.m] (converted from 59 N.cm)
        
        # --- Calculated Constants ---
        self.omega_no_load = self.no_load_rpm * 2.0 * np.pi / 60.0 # [rad/s]
        
        # --- Inertia & Losses (Assumed) ---
        # We assume a slightly larger inertia so the spin-up is visible on a graph.
        self.J = 5.0e-2                       # [kg.m^2] [ASSUMED]
        self.B_viscous = 0.001                # [N.m.s/rad] [ASSUMED]

        # --- State ---
        self.omega = 0.0                      # [rad/s]
        self.t = 0.0

    def step(self, dt, V_applied):
        """Advance one time step. V_applied = voltage across motor terminals."""
        
        # Calculate torque based on the linear torque-speed curve
        # T = T_stall * (1 - (omega / omega_no_load))
        if self.omega < self.omega_no_load:
            T_motor = self.stall_torque * (1.0 - (self.omega / self.omega_no_load))
        else:
            T_motor = 0.0
            
        # Adjust for supply voltage (if V_applied is less than 12V, max speed drops)
        voltage_ratio = V_applied / self.V_supply
        T_motor = T_motor * voltage_ratio

        # Add friction/drag
        T_drag = self.B_viscous * self.omega
        T_net = T_motor - T_drag

        # Physics: T = J * alpha -> alpha = T / J
        domega = (T_net / self.J) * dt
        self.omega += domega
        
        if self.omega < 0:
            self.omega = 0.0
            
        self.t += dt
        return self.omega

    def rpm(self):
        return self.omega * 60.0 / (2.0 * np.pi)