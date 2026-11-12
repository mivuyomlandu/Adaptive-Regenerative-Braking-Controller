"""
Generator + braking model for the RS PRO 12V DC motor.

When the motor is spun by external kinetic energy (the wheel), it acts as a
generator. The back-EMF voltage is proportional to speed.

Source labels:
    [EST]     estimated from nameplate / datasheet
    [ASSUMED] engineering assumption, justified but unverified
"""

import numpy as np


class GeneratorModel:
    def __init__(self):
        # --- Electrical parameters ---
        self.V_supply = 12.0                                     # [V]       [EST]
        
        # K_e (back-EMF constant) must match the motor's spin-up model
        # K_e = 12V / (98 RPM converted to rad/s)
        self.K_e = 12.0 / (98.0 * 2.0 * np.pi / 60.0)            # [V.s/rad] [EST]
        self.K_t = self.K_e                                      # [N.m/A]   [EST]
        
        # Internal resistance of the motor windings
        self.R_armature = 2.5                                    # [ohm]     [ASSUMED]

    def generated_voltage(self, omega):
        """Open-circuit voltage produced by the generator at a given speed."""
        return self.K_e * omega

    def current_to_load(self, omega, R_load):
        """Current flowing into a purely resistive load (like the 10 ohm test resistor)."""
        V_emf = self.generated_voltage(omega)
        I = V_emf / (self.R_armature + R_load)
        return I

    def braking_torque(self, omega, R_load):
        """The torque that opposes the rotation (slows the motor down)."""
        I = self.current_to_load(omega, R_load)
        T_brake = self.K_t * I
        return T_brake

    def electrical_power(self, omega, R_load):
        """Power dissipated in the load resistor (simulating recovered energy)."""
        I = self.current_to_load(omega, R_load)
        P_load = (I ** 2) * R_load
        return P_load