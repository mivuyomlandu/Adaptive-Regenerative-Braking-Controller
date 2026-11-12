#include <SPI.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

// --- OLED Screen dimensions ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_DC     8
#define OLED_RESET  9
#define OLED_CS     10

// Initialize the OLED display using SPI
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &SPI, OLED_DC, OLED_RESET, OLED_CS);

// --- Motor Driver Pins ---
const int IN1 = 4;
const int IN2 = 5;
const int ENA = 6;

// --- Sensor Pin ---
const int sensorPin = 2;

// --- System States ---
// 0 = IDLE (motor off)
// 1 = RAMP UP (increasing speed)
// 2 = MEASURING (counting pulses)
// 3 = BRAKING (decreasing speed)
int systemState = 0; 
int currentSpeed = 0;

const int MAX_SPEED = 150;  // Max PWM speed (safe for sensor reading)
const int STEP_SIZE = 15;   // How much to increase/decrease speed per step
unsigned long lastStepTime = 0;

// --- Variables for RPM calculation ---
int eventCount = 0;
unsigned long lastEventTime = 0;
unsigned long intervals[4]; // We measure 4 time intervals (between 5 touches)
float latched_rpm = 0.0;
bool measurementComplete = false;

void setup() {
  // Start serial communication with the laptop (Python dashboard)
  Serial.begin(9600);
  
  // Set pin modes
  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);
  pinMode(sensorPin, INPUT); 

  // Ensure the motor is off at startup for safety
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  analogWrite(ENA, 0);

  // Initialize the OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC)) {
    for(;;); // Stop if OLED fails
  }
  
  // Show startup message on OLED
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0,0);
  display.println("System Ready");
  display.println("Mode: IDLE");
  display.display();
  delay(1000);
}

void loop() {
  // --- 1. LISTEN FOR COMMANDS FROM PYTHON DASHBOARD ---
  if (Serial.available() > 0) {
    String command = Serial.readStringUntil('\n');
    command.trim();
    
    // If Python sends "DRIVE" and we are IDLE, start ramping up
    if (command == "DRIVE" && systemState == 0) {
      systemState = 1; 
      currentSpeed = 0;
      eventCount = 0;
      latched_rpm = 0.0;
      measurementComplete = false;
      lastStepTime = millis();
    } 
    // If Python sends "BRAKE" and we are MEASURING, start braking
    else if (command == "BRAKE" && systemState == 2) {
      systemState = 3; 
      lastStepTime = millis();
    }
  }

  // --- 2. SYSTEM STATE MACHINE ---
  
  // STATE 0: IDLE (Motor off)
  if (systemState == 0) {
    digitalWrite(IN1, LOW);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, 0);
  } 
  
  // STATE 1: RAMP UP (Gradually increase speed)
  else if (systemState == 1) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    
    // Increase speed every 500ms
    if (millis() - lastStepTime > 500) {
      lastStepTime = millis();
      currentSpeed += STEP_SIZE;
      
      // If we hit max speed, switch to measuring state
      if (currentSpeed >= MAX_SPEED) {
        currentSpeed = MAX_SPEED;
        systemState = 2; 
        lastEventTime = millis(); 
      }
      analogWrite(ENA, currentSpeed);
    }
  }
  
  // STATE 2: MEASURING (Motor running at max speed, waiting for 5 pulses)
  else if (systemState == 2) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    analogWrite(ENA, currentSpeed);
    
    if (!measurementComplete) {
      // Read the sensor (LOW means the magnet is touching the wires)
      if (digitalRead(sensorPin) == LOW) {
        unsigned long currentTime = millis();
        
        // Record the time between touches (ignore the very first touch)
        if (eventCount > 0 && eventCount < 5) { 
          intervals[eventCount - 1] = currentTime - lastEventTime;
        }
        
        lastEventTime = currentTime;
        eventCount++;
        
        // Once we have 5 touches, calculate the average RPM
        if (eventCount == 5) { 
          unsigned long totalTime = 0;
          for (int i = 0; i < 4; i++) {
            totalTime += intervals[i];
          }
          float avgTime = totalTime / 4.0;
          
          if (avgTime > 0) {
            // RPM = 60000 milliseconds / average time per revolution
            latched_rpm = 60000.0 / avgTime;
            
            // Cap at 200 to prevent crazy numbers from bouncing
            if (latched_rpm > 200.0) latched_rpm = 200.0;
          }
          measurementComplete = true; 
        }
        
        // Wait for the magnet to separate before looking for the next pulse
        while(digitalRead(sensorPin) == LOW) { }
      }
    }
  }
  
  // STATE 3: BRAKING (Gradually decrease speed)
  else if (systemState == 3) {
    digitalWrite(IN1, HIGH);
    digitalWrite(IN2, LOW);
    
    // Decrease speed every 500ms
    if (millis() - lastStepTime > 500) {
      lastStepTime = millis();
      currentSpeed -= STEP_SIZE;
      
      // Once stopped, go back to IDLE
      if (currentSpeed <= 0) {
        currentSpeed = 0;
        systemState = 0; 
        digitalWrite(IN1, LOW);
        digitalWrite(IN2, LOW);
      }
      analogWrite(ENA, currentSpeed);
    }
  }

  // --- 3. SEND DATA TO PYTHON DASHBOARD ---
  // Format: STATE:0,EVENTS:0,RPM:0.0
  Serial.print("STATE:");
  Serial.print(systemState);
  Serial.print(",EVENTS:");
  Serial.print(eventCount);
  Serial.print(",RPM:");
  Serial.println(latched_rpm);

  // --- 4. UPDATE OLED DISPLAY ---
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("ADAPTIVE BRAKING");
  display.drawLine(0, 12, 127, 12, SSD1306_WHITE);

  display.setCursor(0, 25);
  
  // Show current state on the screen
  if (systemState == 0) display.println("Mode: IDLE");
  if (systemState == 1) display.println("Mode: RAMP UP");
  if (systemState == 2) {
    display.print("Mode: DRIVING ");
    display.print(eventCount);
    display.println("/5");
  }
  if (systemState == 3) display.println("Mode: BRAKING");
  
  // Show current speed and RPM
  display.print("Speed: ");
  display.print(currentSpeed);
  display.println(" PWM");
  
  display.print("RPM: ");
  display.println(latched_rpm, 1);
  
  display.display();
  delay(50); 
}