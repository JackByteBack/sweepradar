# SweepRadar

Real-time ultrasonic radar: an Arduino Uno sweeps an HC-SR04 sensor on a servo
through 180°, streams `angle,distance` packets over USB serial, and a
Processing app renders them as a live radar screen — green sweep line, distance
rings, and a red blip on anything detected within 40 cm.

---

## Table of Contents

1. [Why your original build failed](#1-why-your-original-build-failed)
2. [How it works](#2-how-it-works)
3. [Parts list](#3-parts-list)
4. [Wiring](#4-wiring)
5. [Serial protocol](#5-serial-protocol)
6. [Software prerequisites](#6-software-prerequisites)
7. [Step 1 — Flash the Arduino](#7-step-1--flash-the-arduino)
8. [Step 2 — Run the Processing display](#8-step-2--run-the-processing-display)
9. [Testing tips](#9-testing-tips)
10. [Code walkthrough](#10-code-walkthrough)
11. [Tuning](#11-tuning)
12. [Troubleshooting](#12-troubleshooting)
13. [Project files](#13-project-files)

---

## 1. Why your original build failed

You pasted the **Processing** sketch into the **Arduino IDE**. That code is
Java (Processing), not C++ — so the compiler reported:

```
'import' does not name a type
'size' was not declared in this scope
redefinition of 'void setup()'
```

These errors are not bugs in the radar code. **It is simply the wrong IDE.**
This project is two programs that talk to each other:

| File | IDE | Runs on | Purpose |
|------|-----|---------|---------|
| `RadarSensor/RadarSensor.ino` | Arduino IDE | Arduino Uno | Sweeps servo, reads sensor, sends serial data |
| `RadarDisplay/RadarDisplay.pde` | Processing IDE | Your PC | Receives serial data, draws the radar screen |

---

## 2. How it works

```
┌─────────────┐   servo sweep    ┌──────────────┐
│  Arduino    │ ───────────────► │ Servo +      │
│  Uno        │   0° → 180°      │ HC-SR04      │
│             │ ◄─────────────── │ sensor       │
└──────┬──────┘   echo distance  └──────────────┘
       │ USB serial, 9600 baud
       │ sends "90,25." (angle,distance)
       ▼
┌─────────────┐
│ Processing  │  parses packet →
│ RadarDisplay│  draws sweep line at angle,
└─────────────┘  red blip at distance if < 40 cm
```

Every sensor reading is one packet: **`angle,distance.`** — angle 0–180°,
distance in centimeters, `.` as the terminator. The Processing sketch buffers
until it sees the `.`, so partial reads never corrupt the display.

---

## 3. Parts list

| Qty | Part | Notes |
|-----|------|-------|
| 1 | Arduino Uno | Any Arduino with a hardware serial port works |
| 1 | HC-SR04 ultrasonic sensor | 2–400 cm range, 4-pin |
| 1 | Micro servo | SG90 (small) or MG996R (metal gear) |
| 4–6 | Jumper wires (M-F) | |
| 1 | External 5V power supply | Recommended for MG996R; SG90 often runs fine from USB |
| 1 | USB cable (A–B) | Uno's programming cable doubles as power + data |

---

## 4. Wiring

### Pin connections

| Component | Pin | Connects to Arduino |
|-----------|-----|---------------------|
| HC-SR04 | VCC | **5V** |
| HC-SR04 | GND | **GND** |
| HC-SR04 | TRIG | **D10** |
| HC-SR04 | ECHO | **D11** |
| Servo | Signal (orange/yellow) | **D9** |
| Servo | VCC (red) | **5V** — *or external 5V+* |
| Servo | GND (brown/black) | **GND** |

### Two rules that prevent 90% of problems

1. **Common ground** — if the servo uses an external supply, its GND must
   still connect to the Arduino GND. No common ground = random sensor readings.
2. **Servo power** — a servo spinning the sensor draws spikes the Uno's 5V
   regulator can't supply. Symptoms of under-powering: the Uno resets mid-sweep,
   serial garbles, radar display freezes. Fix: external 5V supply for the servo,
   or keep the small SG90 and don't stall the horn.

---

## 5. Serial protocol

- **Baud rate:** 9600 (must match both sides — default in both sketches)
- **Format:** `angle,distance.`

Example stream in Serial Monitor:

```
0,180,2,175,4,170,...,90,25,92,26,...,180,40.
```

Values: `angle` = 0–180 (degrees), `distance` = 0–400 (cm, capped).
Distance > 40 is treated as "out of range" by the display.

---

## 6. Software prerequisites

| Software | Version | Get it |
|----------|---------|--------|
| Arduino IDE | 1.8.19 (you have this) | https://www.arduino.cc/en/software |
| Processing | 4.x (Windows) | https://processing.org/download |
| Serial library | bundled with Processing | Sketch → Import Library → Manage Libraries → search "Serial" |

If Processing flags `Serial` as unrecognized: open **Sketch → Import Library →
Manage Libraries**, search `Serial`, install, restart Processing.

> **Note:** a Processing sketch's folder name must match its `.pde` filename.
> Keep `RadarDisplay/RadarDisplay.pde` as-is.

---

## 7. Step 1 — Flash the Arduino

1. Open `RadarSensor/RadarSensor.ino` in the Arduino IDE.
2. Select **Tools → Board → Arduino Uno**.
3. Select **Tools → Port → COMx** (your Uno's port).
4. Click **Verify (✓)** then **Upload (→)**.
5. Open **Tools → Serial Monitor**, set line ending baud to **9600**.
6. You should see a stream of readings:

   ```
   0,180.
   2,175.
   4,170.
   ```

   (one `angle,distance.` packet per line as the servo steps)

7. **Close the Serial Monitor when you're done.** Only one program can hold a
   serial port — if the Monitor stays open, Processing will get
   `Error opening serial port`.

**No hardware yet?** Skip to Step 2 and press `R` — the display runs without
an Arduino, it just shows a simulated detection.

---

## 8. Step 2 — Run the Processing display

1. Install and open Processing 4.
2. **File → Open** → navigate to `RadarDisplay/RadarDisplay.pde`.
3. (First run only) **Sketch → Import Library → Manage Libraries** → install
   `Serial` if prompted.
4. Check the port line in the code:

   ```java
   String portName = "COM5";
   ```

   Change `COM5` to your Uno's port if different. Wrong port is fine — the
   sketch prints every available port and falls back to the first one.
5. Click **Run (▶)**.

**Expected result:** a black window with a green half-circle radar grid,
a sweeping green line following the servo angle, distance markers
`10cm 20cm 30cm 40cm`, and a status bar reading angle / distance /
`In Range` or `Out of Range`. Hold your hand ~15 cm in front of the sensor and
a **red dot** appears where the sweep points.

The Processing console shows:

```
Available serial ports:
[COM1, COM3, COM5]
Connected to: COM5
```

---

## 9. Testing tips

1. **Open the Serial Monitor first** to verify the Arduino sends
   `angle,distance.` at 9600 baud. If the format is wrong there, Processing
   can't fix it — fix the Arduino side.
2. **Check the Processing console for available ports** if `COM5` fails.
   It prints the full port list on startup; set `portName` to the right one
   (often `COM3` on Windows, `/dev/ttyUSB0` on Linux, `/dev/tty.usbmodem*` on
   macOS).
3. **Press `R`** to simulate a detection (90°, 25 cm) — tests the drawing and
   status UI with no hardware attached. Press `S` to print the current
   angle/distance to the Processing console.
4. **Adjust the `constrain()` limits** if your sensor has a different range —
   in `serialEvent()`:

   ```java
   iAngle    = int(constrain(float(angle),    0, 180));
   iDistance = int(constrain(float(distance),  0, MAX_RANGE_CM));
   ```

   Change `MAX_RANGE_CM` (`.pde`) **and** `MAX_CM` (`.ino`) together so both
   sides agree on the range.

**Other keys:** none — `R` and `S` are the only shortcuts.

---

## 10. Code walkthrough

### Arduino — `RadarSensor.ino`

| Function / block | What it does |
|---|---|
| `#include <Servo.h>` | Servo control library (ships with Arduino) |
| `TRIG_PIN / ECHO_PIN / SERVO_PIN` | Pin assignments — change here only |
| `readDistanceCm()` | Fires a 10 µs trigger pulse, measures the echo with `pulseIn(..., 25000)` (25 ms timeout ≈ 4 m). No echo → reports out-of-range instead of hanging |
| `sendReading(angle, cm)` | Prints `angle,distance.` — the exact packet format |
| `setup()` | 9600 baud, attaches servo to D9, parks it at 90° for 500 ms |
| `loop()` | Sweeps 0→180→0 in 2° steps, 30 ms settle delay per step, sends one packet per step |

### Processing — `RadarDisplay.pde`

| Function | What it does |
|---|---|
| `setup()` | 1366×768 window, loads font, lists serial ports, connects (tries `COM5`, falls back to first port), buffers until `.` |
| `draw()` | Clears with `background(0, 20)` — low alpha gives the fading trail effect — then calls the four draw functions |
| `serialEvent()` | Fires per packet: strips `.`, splits on `,`, validates, `constrain()`s, stores `iAngle` / `iDistance`. Malformed packets are dropped; the previous valid values are kept |
| `drawRadar()` | 4 concentric arcs (10–40 cm rings), angle lines every 30°, baseline. Translated to the bottom-center origin |
| `drawLine()` | The green sweep line from center to the outer ring at `iAngle` |
| `drawObject()` | If distance < 40 cm: red dot at the mapped position + faint red line from center. Uses `map(distance, 0, 40, 0, maxRadius)` and polar→cartesian conversion |
| `drawText()` | Status bar: distance markers, project name, angle, distance, in/out-of-range status, yellow `Waiting for data...` until the first packet |
| `keyPressed()` | `R` simulates a detection, `S` dumps current values to console |

---

## 11. Tuning

| Want to… | Change |
|---|---|
| Different range (e.g. 100 cm sensor) | `MAX_RANGE_CM` in `.pde`, `MAX_CM` in `.ino`, and the ring markers `i * 10` in `drawText()` |
| Faster sweep | Lower `STEP_DELAY` (settle time) or raise `STEP_DEG` (coarser resolution) in `.ino` |
| Smoother display | Lower `STEP_DEG` to 1 (slower, finer) |
| Different serial port | `String portName` in `setup()` of the `.pde` |
| Different baud rate | `Serial.begin(...)` in `.ino` **and** `new Serial(this, portName, ...)` in `.pde` |
| Different window size | `size(w, h)` in `.pde` — all drawing scales off `width`/`height` |
| Different pins | The `const int` block at the top of `.ino` |

---

## 12. Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `'import' does not name a type` in Arduino IDE | Processing code in the Arduino IDE | Open the `.pde` in Processing instead |
| `Waiting for data...` forever | Port busy or wrong port | Close Serial Monitor, check console port list, set `portName` |
| `Error opening serial port` in console | Another app holds the port | Close Serial Monitor/other serial tools, rerun Processing |
| Console shows `Serial parsing error` occasionally | Garbled packet | Harmless — sketch keeps last valid values; persists? check wiring/baud |
| Radar freezes mid-sweep | Servo brown-out resets the Uno | External 5V for servo, common ground |
| Distance always `---` / `Out of Range` | No echo | Check TRIG=D10, ECHO=D11; sensor needs a solid target within 4 m (hand works) |
| Red dot jitters wildly | Electrical noise on servo supply | Separate servo power, common ground, decoupling cap across servo VCC/GND |
| Wrong COM port listed | Multiple serial devices | Unplug Uno, rerun (list shrinks), replug to identify it |
| `Serial` library not found in Processing | Library missing | Sketch → Import Library → Manage Libraries → install "Serial" |

---

## 13. Project files

```
sweepradar/
├── README.md                      ← this file
├── RadarSensor/
│   └── RadarSensor.ino            ← upload to Arduino Uno (Arduino IDE)
└── RadarDisplay/
    └── RadarDisplay.pde           ← run on PC (Processing IDE)
```

**License:** free to use, modify, and share. Change the name in `drawText()`
if you ship it as your own.
