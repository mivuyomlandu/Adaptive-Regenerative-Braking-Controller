"""
Scenario 1: Spin-up of the motor-wheel system under constant 12 V drive.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SIM_ROOT = os.path.dirname(HERE)
sys.path.insert(0, SIM_ROOT)

import numpy as np
import matplotlib
matplotlib.use("Agg")            # headless backend
import matplotlib.pyplot as plt

from models.motor import MotorWheelModel


def run():
    m = MotorWheelModel()
    dt = 1e-3                    # [s]   1 ms step
    t_end = 3.0                  # [s]   simulate 3 seconds
    n = int(t_end / dt)

    t_log = np.zeros(n)
    rpm_log = np.zeros(n)
    T_log = np.zeros(n)

    for i in range(n):
        m.step(dt, m.V_supply)
        t_log[i] = m.t
        rpm_log[i] = m.rpm()
        
        # Calculate torque directly for logging (based on current speed)
        if m.omega < m.omega_no_load:
            T_now = m.stall_torque * (1.0 - (m.omega / m.omega_no_load))
        else:
            T_now = 0.0
        T_log[i] = T_now

    print(f"Final speed : {rpm_log[-1]:.1f} RPM")
    print(f"Nameplate   : 98 RPM no-load [EST]")
    print(f"Final torque: {T_log[-1]*100:.2f} N.cm")

    # ---- speed plot --------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(t_log, rpm_log, linewidth=2, label="simulated speed [SIM]")
    ax.axhline(98, color="red", linestyle="--", linewidth=1, label="nameplate 98 RPM [EST]")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Speed [RPM]")
    ax.set_title("Motor spin-up under 12 V drive (Simulation A)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out1 = os.path.join(HERE, "s1_spinup_speed.png")
    fig.savefig(out1, dpi=120)
    plt.close(fig)
    print(f"Saved {out1}")

    # ---- torque plot -------------------------------------------------
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(t_log, T_log * 100, linewidth=2, label="motor torque [SIM]")
    ax.axhline(59, color="red", linestyle="--", linewidth=1, label="nameplate stall 59 N.cm [EST]")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Torque [N.cm]")
    ax.set_title("Motor torque during spin-up (Simulation A)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    out2 = os.path.join(HERE, "s1_spinup_torque.png")
    fig.savefig(out2, dpi=120)
    plt.close(fig)
    print(f"Saved {out2}")


if __name__ == "__main__":
    run()