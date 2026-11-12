"""
Scenario 2: Regenerative braking simulation.
Motor spins at 98 RPM, then brakes by dumping energy into a 10 Ohm resistor.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_ROOT = os.path.dirname(HERE)
sys.path.insert(0, SIM_ROOT)

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from models.motor import MotorWheelModel
from models.generator import GeneratorModel

def run():
    m = MotorWheelModel()
    g = GeneratorModel()
    
    # Start at max speed (98 RPM = 10.26 rad/s)
    m.omega = 10.26
    dt = 1e-3 # 1 ms
    t_end = 2.0 # 2 seconds of braking
    n = int(t_end / dt)
    
    R_load = 10.0 # 10 Ohm resistor
    
    t_log = np.zeros(n)
    rpm_log = np.zeros(n)
    volt_log = np.zeros(n)
    power_log = np.zeros(n)
    
    for i in range(n):
        # 1. Calculate braking torque from the generator
        T_brake = g.braking_torque(m.omega, R_load)
        
        # 2. Apply physics (no motor voltage, just braking friction and generator torque)
        # domega = (T_net / J) * dt
        T_drag = m.B_viscous * m.omega
        T_net = -T_brake - T_drag
        
        m.omega += (T_net / m.J) * dt
        if m.omega < 0:
            m.omega = 0.0
            
        # 3. Log data
        t_log[i] = i * dt
        rpm_log[i] = m.rpm()
        volt_log[i] = g.generated_voltage(m.omega)
        power_log[i] = g.electrical_power(m.omega, R_load)
        
    print(f"Initial Speed: 98.0 RPM")
    print(f"Final Speed: {rpm_log[-1]:.1f} RPM")
    print(f"Peak Power Recovered: {np.max(power_log):.2f} Watts")
    
    # Plot Voltage and Power
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
    
    ax1.plot(t_log, volt_log, color='blue', linewidth=2)
    ax1.set_ylabel("Generated Voltage [V]")
    ax1.set_title("Regenerative Braking: Voltage & Power (10 Ohm Load)")
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(t_log, power_log, color='red', linewidth=2)
    ax2.set_ylabel("Power to Load [W]")
    ax2.set_xlabel("Time [s]")
    ax2.grid(True, alpha=0.3)
    
    fig.tight_layout()
    out = os.path.join(HERE, "s2_regen_power.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"Saved {out}")

if __name__ == "__main__":
    run()