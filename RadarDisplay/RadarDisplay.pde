/*
 * SweepRadar - Processing side (run THIS in the Processing IDE, not Arduino)
 *
 * Reads "angle,distance." from the Arduino over USB serial and draws
 * a green radar sweep with a red blip for objects inside 40 cm.
 *
 * Keys:
 *   R - fake a detection (90 deg, 25 cm) so you can test the UI with no hardware
 *   S - print the current angle/distance to the Processing console
 */

import processing.serial.*;

Serial myPort;

String data = "";
String noObject = "Out of Range";

float pixsDistance;
int iAngle = 90, iDistance = 0;
int index1 = 0;

PFont orcFont;
boolean dataReceived = false;

final int MAX_RANGE_CM = 40;  // must match MAX_CM in RadarSensor.ino

void setup() {
  size(1366, 768);
  smooth();

  orcFont = createFont("Arial", 25, true);
  textFont(orcFont);

  // List ports so you can spot the right one if COM5 fails
  println("Available serial ports:");
  printArray(Serial.list());

  String portName = "COM5";                  // change to your port if needed
  String[] ports = Serial.list();

  if (ports.length > 0) {
    boolean found = false;
    for (String p : ports) {
      if (p.equals(portName)) { found = true; break; }
    }
    if (!found) {
      portName = ports[0];
      println("COM5 not found, using: " + portName);
    }
  } else {
    println("No serial ports found - is the Arduino plugged in?");
  }

  try {
    myPort = new Serial(this, portName, 9600);
    myPort.bufferUntil('.');                 // fire serialEvent on each complete packet
    println("Connected to: " + portName);
  } catch (Exception e) {
    println("Error opening serial port: " + e.getMessage());
    noObject = "Serial Error";
  }
}

void draw() {
  background(0, 20);                         // low alpha = fading trail effect

  drawRadar();
  drawLine();
  drawObject();
  drawText();
}

void serialEvent(Serial myPort) {
  try {
    data = myPort.readStringUntil('.');
    if (data == null || data.length() == 0) return;

    data = data.trim();
    if (data.endsWith(".")) data = data.substring(0, data.length() - 1);

    index1 = data.indexOf(",");
    if (index1 <= 0 || index1 >= data.length() - 1) return;   // malformed packet, drop it

    String angle = data.substring(0, index1).trim();
    String distance = data.substring(index1 + 1).trim();

    // constrain() also guards against a sensor glitching huge values
    iAngle = int(constrain(float(angle), 0, 180));
    iDistance = int(constrain(float(distance), 0, MAX_RANGE_CM));
    dataReceived = true;
  } catch (Exception e) {
    println("Serial parsing error: " + e.getMessage());       // keep last valid values
  }
}

void drawRadar() {
  pushMatrix();
  translate(width / 2, height - height * 0.074);

  noFill();
  strokeWeight(2);
  stroke(98, 245, 31);

  float maxRadius = width * 0.47;
  for (int i = 1; i <= 4; i++) {
    float r = maxRadius * i / 4;
    arc(0, 0, r * 2, r * 2, PI, TWO_PI);
  }

  strokeWeight(1);
  for (int a = 0; a <= 180; a += 30) {
    float x = maxRadius * cos(radians(180 - a));
    float y = maxRadius * sin(radians(180 - a));
    line(0, 0, -x, -y);
  }
  line(-maxRadius, 0, maxRadius, 0);

  popMatrix();
}

void drawLine() {
  pushMatrix();
  translate(width / 2, height - height * 0.074);

  strokeWeight(3);
  stroke(30, 250, 60, 150);

  float maxRadius = width * 0.47;
  float x = maxRadius * cos(radians(180 - iAngle));
  float y = -maxRadius * sin(radians(180 - iAngle));

  line(0, 0, x, y);
  popMatrix();
}

void drawObject() {
  if (!dataReceived || iDistance >= MAX_RANGE_CM) return;

  pushMatrix();
  translate(width / 2, height - height * 0.074);

  float maxRadius = width * 0.47;
  pixsDistance = map(iDistance, 0, MAX_RANGE_CM, 0, maxRadius);

  float x = pixsDistance * cos(radians(180 - iAngle));
  float y = -pixsDistance * sin(radians(180 - iAngle));

  stroke(255, 100, 100, 100);
  strokeWeight(1);
  line(0, 0, x, y);

  noStroke();
  fill(255, 50, 50, 200);
  ellipse(x, y, 8, 8);

  popMatrix();
}

void drawText() {
  // Status bar
  noStroke();
  fill(0, 200);
  rect(0, height - height * 0.065, width, height * 0.065);

  fill(98, 245, 31);
  textSize(20);
  textFont(orcFont);

  // Distance markers along the base line
  float maxRadius = width * 0.47;
  for (int i = 1; i <= 4; i++) {
    float markerX = width / 2 + (maxRadius * i / 4) * cos(radians(180 - 90));
    text((i * 10) + "cm", markerX - 15, height - height * 0.074 + 20);
  }

  boolean inRange = dataReceived && iDistance < MAX_RANGE_CM;
  noObject = inRange ? "In Range" : "Out of Range";

  textSize(25);
  fill(98, 245, 31);
  text("SweepRadar", 20, height - 10);

  textSize(22);
  fill(98, 245, 31);
  text("Angle: " + iAngle + "\u00B0", width / 2 - 80, height - 10);
  text("Distance: " + (inRange ? iDistance + " cm" : "---"),
       width / 2 + 60, height - 10);

  fill(inRange ? color(98, 245, 31) : color(255, 100, 100));
  text("Status: " + noObject, width - 220, height - 10);

  if (!dataReceived) {
    fill(255, 200, 0);
    textSize(18);
    text("Waiting for data...", 20, height - 35);
  }
}

void keyPressed() {
  if (key == 'r' || key == 'R') {
    iAngle = 90;
    iDistance = 25;
    dataReceived = true;
  }
  if (key == 's' || key == 'S') {
    println("Angle: " + iAngle + ", Distance: " + iDistance);
  }
}
