/*
 * SweepRadar - Arduino side
 * Sweeps an HC-SR04 ultrasonic sensor on a servo and sends
 * "angle,distance." over USB serial at 9600 baud.
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

void loop() {
  for (int a = 0; a <= 180; a += STEP_DEG) {
    scanner.write(a);
    delay(STEP_DELAY);
    sendReading(a, readDistanceCm());
  }
  for (int a = 180; a >= 0; a -= STEP_DEG) {
    scanner.write(a);
    delay(STEP_DELAY);
    sendReading(a, readDistanceCm());
  }
}
