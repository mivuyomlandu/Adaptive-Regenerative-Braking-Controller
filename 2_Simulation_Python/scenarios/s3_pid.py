"""
Scenario 3: Adaptive PID Braking.
The motor spins at 98 RPM. The PID controller tries to brake it down to 20 RPM.
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
from models.battery import BatteryModel
from control.pid import PIDController

def run():
    # --- Setup models ---
    m = MotorWheelModel()
    g = GeneratorModel()
    b = BatteryModel()
    
    # --- PID Tuning ---
    # Target: 20 RPM
    target_rpm = 20.0
    target_omega = target_rpm * 2.0 * np.pi / 60.0
    
    # We tune the PID to control the Braking Torque directly
    pid = PIDController(Kp=1.5, Ki=2.0, Kd=0.1, out_min=0.0, out_max=1.0)
    
    # --- Simulation setup ---
    m.omega = 98.0 * 2.0 * np.pi / 60.0  # Start at 98 RPM
    dt = 1e-3
    t_end = 10.0  # 10 seconds
    n = int(t_end / dt)
    
    R_load = 10.0 # 10 Ohm resistor
    
    t_log = np.zeros(n)
    rpm_log = np.zeros(n)
    target_log = np.zeros(n) + target_rpm
    duty_log = np.zeros(n)
    torque_log = np.zeros(n)
    
    for i in range(n):
        # 1. The error is (target - actual). 
        # Note: The PID outputs 0.0 to 1.0, representing 0% to 100% braking force.
        duty = pid.compute(setpoint=m.omega, measured_value=target_omega, dt=dt)
        
        # 2. Calculate physical braking torque.
        # Maximum braking torque is 0.5 N.m when duty is 100%.
        T_brake_max = 0.5
        T_brake = T_brake_max * duty
        
        # 3. Physics step
        # Friction drag
        T_drag = m.B_viscous * m.omega
        
        # Net torque is Negative because we are braking
        T_net = -T_brake - T_drag
        
        # Update angular velocity: domega = (T_net / J) * dt
        m.omega += (T_net / m.J) * dt
        
        # Prevent negative speeds
        if m.omega < 0.0:
            m.omega = 0.0
            
        # 4. Logging
        t_log[i] = i * dt
        rpm_log[i] = m.rpm()
        duty_log[i] = duty * 100 # Convert to percentage
        torque_log[i] = T_brake
        
    print(f"Initial Speed: 98.0 RPM")
    print(f"Target Speed : {target_rpm} RPM")
    print(f"Final Speed  : {rpm_log[-1]:.1f} RPM")
    print(f"Final Braking Duty Cycle: {duty_log[-1]:.1f}%")
    
    # Plot Speed and Duty Cycle
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 8))
    
    ax1.plot(t_log, rpm_log, color='blue', linewidth=2, label="Actual Speed")
    ax1.plot(t_log, target_log, color='black', linestyle='--', label="Target Speed (20 RPM)")
    ax1.set_ylabel("Speed [RPM]")
    ax1.set_title("PID Adaptive Braking: Speed Tracking")
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    ax2.plot(t_log, duty_log, color='orange', linewidth=2, label="Braking Force (Duty Cycle %)")
    ax2.set_ylabel("Duty Cycle [%]")
    ax2.set_xlabel("Time [s]")
    ax2.grid(True, alpha=0.3)
    
    fig.tight_layout()
    out = os.path.join(HERE, "s3_pid_speed.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print(f"Saved {out}")

if __name__ == "__main__":
    run()