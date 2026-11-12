import tkinter as tk
import threading
import time
import serial

class Dashboard:
    def __init__(self, root):
        self.root = root
        self.root.title("DES371S - Adaptive Regenerative Braking System")
        self.root.geometry("1000x650") 
        self.root.configure(bg="#000000") 
        
        self.grid_frame = tk.Frame(root, bg="#000000")
        self.grid_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.grid_frame.grid_rowconfigure(0, weight=1)
        self.grid_frame.grid_rowconfigure(1, weight=1)
        self.grid_frame.grid_columnconfigure(0, weight=1)
        self.grid_frame.grid_columnconfigure(1, weight=1)

        self.build_top_left()
        self.build_top_right()
        self.build_bottom_left()
        self.build_bottom_right()

        self.data_points = []
        self.current_rpm = 0.0
        self.target_rpm = 0.0
        self.total_energy = 0.0
        
        self.running = True
        self.ser = None
        threading.Thread(target=self.read_serial, daemon=True).start()

    def build_top_left(self):
        frame = tk.Frame(self.grid_frame, bg="#0a0a0a", highlightbackground="#00f0ff", highlightthickness=2)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        tk.Label(frame, text="MOTOR SPEED (RPM)", font=("Arial", 18, "bold"), fg="white", bg="#0a0a0a").pack(pady=10)
        self.rpm_display = tk.Label(frame, text="0.0", font=("Arial", 80, "bold"), fg="#00f0ff", bg="#0a0a0a")
        self.rpm_display.pack(expand=True)
        tk.Label(frame, text="RPM", font=("Arial", 20, "bold"), fg="#00f0ff", bg="#0a0a0a").pack(pady=10)

    def build_top_right(self):
        frame = tk.Frame(self.grid_frame, bg="#0a0a0a", highlightbackground="#00f0ff", highlightthickness=2)
        frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        tk.Label(frame, text="LIVE BRAKING TELEMETRY", font=("Arial", 18, "bold"), fg="white", bg="#0a0a0a").pack(pady=10)
        self.canvas = tk.Canvas(frame, bg="#0a0a0a", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=10, pady=10)

    def build_bottom_left(self):
        frame = tk.Frame(self.grid_frame, bg="#0a0a0a", highlightbackground="#00f0ff", highlightthickness=2)
        frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        tk.Label(frame, text="TOTAL ENERGY RECOVERED", font=("Arial", 18, "bold"), fg="white", bg="#0a0a0a").pack(pady=10)
        self.energy_display = tk.Label(frame, text="0.0 Joules", font=("Arial", 40, "bold"), fg="#00ff00", bg="#0a0a0a")
        self.energy_display.pack(expand=True)
        tk.Label(frame, text="(Simulated based on live RPM)", font=("Arial", 12), fg="#aaaaaa", bg="#0a0a0a").pack(pady=5)

    def build_bottom_right(self):
        frame = tk.Frame(self.grid_frame, bg="#0a0a0a", highlightbackground="#00f0ff", highlightthickness=2)
        frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        tk.Label(frame, text="SYSTEM CONTROL", font=("Arial", 18, "bold"), fg="white", bg="#0a0a0a").pack(pady=10)
        self.mode_display = tk.Label(frame, text="IDLE", font=("Arial", 24, "bold"), fg="#00f0ff", bg="#0a0a0a")
        self.mode_display.pack(pady=20) # Increased spacing since power label is gone
        
        btn_frame = tk.Frame(frame, bg="#0a0a0a")
        btn_frame.pack(pady=20)
        tk.Button(btn_frame, text="START", font=("Arial", 16, "bold"), bg="#00ff00", fg="black", command=self.trigger_driving, width=10).pack(side="left", padx=10, ipady=10)
        tk.Button(btn_frame, text="BRAKE", font=("Arial", 16, "bold"), bg="#ff4444", fg="white", command=self.trigger_braking, width=10).pack(side="left", padx=10, ipady=10)

    def read_serial(self):
        try:
            self.ser = serial.Serial('COM7', 9600, timeout=1)
            time.sleep(2)
            
            while self.running:
                line = self.ser.readline().decode('utf-8').strip()
                if not line:
                    continue
                
                if "STATE:" in line:
                    try:
                        parts = line.split(',')
                        state = int(parts[0].split(':')[1])
                        events = int(parts[1].split(':')[1])
                        rpm = float(parts[2].split(':')[1])
                        
                        self.root.after(0, self.update_ui, state, events, rpm)
                    except Exception as e:
                        pass
                        
        except Exception as e:
            self.root.after(0, lambda: self.mode_display.config(text="COM ERROR", fg="#ff4444"))

    def trigger_driving(self):
        if self.ser is not None:
            self.ser.write(b"DRIVE\n")
            self.data_points = []
            self.total_energy = 0.0
            self.current_rpm = 0.0
            self.target_rpm = 0.0
            self.energy_display.config(text="0.0 Joules")
            self.rpm_display.config(text="0.0")
            self.animate_spinup()

    def trigger_braking(self):
        if self.ser is not None:
            self.ser.write(b"BRAKE\n")

    def update_ui(self, state, events, rpm):
        if state == 0:
            self.mode_display.config(text="IDLE", fg="#aaaaaa")
        elif state == 1:
            self.mode_display.config(text="RAMPING UP", fg="#ffaa00")
        elif state == 2:
            self.mode_display.config(text=f"MEASURING ({events}/5)", fg="#00ff00")
            if rpm > 0:
                self.target_rpm = rpm 
                
                # Keep the graph moving horizontally while measuring
                if self.current_rpm >= self.target_rpm:
                    self.data_points.append(self.target_rpm)
                    if len(self.data_points) > 100:
                        self.data_points.pop(0)
                    self.draw_graph()
                    
        elif state == 3:
            self.mode_display.config(text="BRAKING", fg="#ff4444")
            self.animate_braking()

    def animate_spinup(self):
        if self.target_rpm == 0:
            self.root.after(500, self.animate_spinup)
            return
            
        if self.current_rpm < self.target_rpm:
            self.current_rpm += 5.0
            if self.current_rpm > self.target_rpm:
                self.current_rpm = self.target_rpm
            
            self.rpm_display.config(text=f"{self.current_rpm:.1f}")
            self.data_points.append(self.current_rpm)
            self.draw_graph()
            self.root.after(100, self.animate_spinup)

    def animate_braking(self):
        if self.current_rpm > 0:
            self.current_rpm -= 2.0
            if self.current_rpm < 0: self.current_rpm = 0
            
            # Energy calculation (Instantaneous power removed)
            instant_power = ((self.current_rpm * 0.1) ** 2) / 10.0
            self.total_energy += instant_power * 0.2 
            self.energy_display.config(text=f"{self.total_energy:.1f} Joules")
            
            self.data_points.append(self.current_rpm)
            self.draw_graph()
            self.root.after(200, self.animate_braking)

    def draw_graph(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        if w < 10 or h < 10:
            return
            
        for i in range(0, 6):
            y = h - (i / 5) * (h - 20) - 20 
            self.canvas.create_line(30, y, w, y, fill="#1c2b42")
            self.canvas.create_text(15, y, text=str(i*16), fill="#aaaaaa", font=("Arial", 10))
            
        for i in range(0, 11):
            x = 30 + (i / 10) * (w - 30)
            self.canvas.create_line(x, 20, x, h-20, fill="#1c2b42")
            if i % 2 == 0:
                self.canvas.create_text(x, h-10, text=f"{i*5}s", fill="#aaaaaa", font=("Arial", 10))

        self.canvas.create_text(w/2, 10, text="Time (s)", fill="white", font=("Arial", 12, "bold"))
        self.canvas.create_text(10, h/2, text="RPM", fill="white", font=("Arial", 12, "bold"), angle=90)

        if len(self.data_points) > 1:
            points = []
            for i, val in enumerate(self.data_points):
                x = 30 + (i / len(self.data_points)) * (w - 30)
                y = (h - 20) - (val / 80.0) * (h - 40)
                points.append(x)
                points.append(y)
            
            self.canvas.create_line(points, fill="#ff4444", width=3, smooth=True)

if __name__ == "__main__":
    root = tk.Tk()
    app = Dashboard(root)
    root.mainloop()