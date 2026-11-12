"""
PID Controller with Anti-Windup and Output Saturation.
"""

class PIDController:
    def __init__(self, Kp, Ki, Kd, out_min=0.0, out_max=1.0):
        # Tuning parameters
        self.Kp = Kp
        self.Ki = Ki
        self.Kd = Kd
        
        # Output limits (0.0 = no brake, 1.0 = full brake)
        self.out_min = out_min
        self.out_max = out_max
        
        # Internal state
        self.integral = 0.0
        self.prev_error = 0.0
        
    def compute(self, setpoint, measured_value, dt):
        """
        Calculate the control output (braking force 0.0 to 1.0).
        setpoint = desired speed
        measured_value = current speed
        """
        error = setpoint - measured_value
        
        # --- Proportional term ---
        P = self.Kp * error
        
        # --- Integral term (with anti-windup) ---
        # Only integrate if we aren't saturated
        if self.out_min < (P + self.integral) < self.out_max:
            self.integral += self.Ki * error * dt
        
        I = self.integral
        
        # --- Derivative term ---
        D = self.Kd * (error - self.prev_error) / dt
        self.prev_error = error
        
        # --- Calculate total output ---
        output = P + I + D
        
        # --- Apply saturation limits ---
        if output > self.out_max:
            output = self.out_max
        elif output < self.out_min:
            output = self.out_min
            
        return output

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0