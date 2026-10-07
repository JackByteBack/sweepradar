/*
 * SweepRadar - Arduino side
 * Sweeps an HC-SR04 ultrasonic sensor on a servo and sends
 * "angle,distance." over USB serial at 9600 baud.
 *
 * Also accepts commands from any connected client (web/app):
 *   a<angle>  hold servo at angle (manual mode)
 *   m         resume auto sweep
 *
 * Wiring (Arduino Uno):
 *   HC-SR04 TRIG -> D10
 *   HC-SR04 ECHO -> D11
 *   HC-SR04 VCC  -> 5V
 *   HC-SR04 GND  -> GND
 *   Servo signal -> D9
 *   Servo VCC    -> 5V (external 5V supply recommended for larger servos)
 *   Servo GND    -> GND (common ground with Arduino)
 */

#include <Servo.h>

const int TRIG_PIN   = 10;
const int ECHO_PIN   = 11;
const int SERVO_PIN  = 9;
const int MAX_CM     = 40;    // must match the Processing constrain() limit
const int STEP_DEG   = 2;     // sweep resolution
const int STEP_DELAY = 30;    // ms per step, lets the servo settle

Servo scanner;

bool autoMode = true;
int currentAngle = 0;
int sweepDir = STEP_DEG;
int targetAngle = 90;

long readDistanceCm() {
  digitalWrite(TRIG_PIN, LOW);
  delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);

  // 25000 us timeout ~= 4 m max; 0 means no echo
  long duration = pulseIn(ECHO_PIN, HIGH, 25000);
  if (duration == 0) return MAX_CM + 1;  // report as out of range
  return duration * 0.034 / 2;
}

void sendReading(int angle, long cm) {
  if (cm < 0)    cm = 0;
  if (cm > 400)  cm = 400;
  Serial.print(angle);
  Serial.print(",");
  Serial.print(cm);
  Serial.print(".");   // delimiter the Processing sketch buffers on
}

void setup() {
  pinMode(TRIG_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  Serial.begin(9600);
  scanner.attach(SERVO_PIN);
  scanner.write(90);
  delay(500);
}

// Incoming commands from any connected client (via server.py):
//   "a<angle>\n" -> hold servo at angle (manual mode), e.g. "a90\n"
//   "m\n"        -> resume auto sweep
void readCommands() {
  while (Serial.available()) {
    char c = Serial.read();
    if (c == 'a') {
      autoMode = false;
      targetAngle = constrain(Serial.parseInt(), 0, 180);
      scanner.write(targetAngle);
      sendReading(targetAngle, readDistanceCm());
    } else if (c == 'm') {
      autoMode = true;
      currentAngle = targetAngle;
    }
  }
}

void loop() {
  readCommands();
  if (!autoMode) {          // hold position but keep listening for commands
    delay(20);
    return;
  }

  currentAngle += sweepDir;
  if (currentAngle >= 180 || currentAngle <= 0) sweepDir = -sweepDir;
  scanner.write(currentAngle);
  delay(STEP_DELAY);
  sendReading(currentAngle, readDistanceCm());
}
