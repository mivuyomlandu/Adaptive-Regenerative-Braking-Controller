import serial
import time

# Set to COM7 based on your Arduino IDE
ARDUINO_PORT = 'COM7' 
BAUD_RATE = 9600

try:
    print(f"Connecting to {ARDUINO_PORT}...")
    ser = serial.Serial(ARDUINO_PORT, BAUD_RATE, timeout=1)
    time.sleep(2) # Wait for the Arduino to reset
    print("Connected! Waiting for data...")
    
    while True:
        # Read a line from the Arduino
        line = ser.readline().decode('utf-8').strip()
        
        # If the line has data, print it
        if line:
            print(f"Arduino says: {line}")

except serial.SerialException:
    print(f"ERROR: Could not open port {ARDUINO_PORT}.")
    print("Check that the Arduino is plugged in and the COM port is correct.")
    print("Also, make sure the Arduino IDE Serial Monitor is CLOSED.")
except KeyboardInterrupt:
    print("\nTest stopped.")
    ser.close()