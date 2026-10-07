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
9. [Step 3 — Multi-device control (Mac, iPhone, Android)](#9-step-3--multi-device-control-mac-iphone-android)
10. [Testing tips](#10-testing-tips)
11. [Code walkthrough](#11-code-walkthrough)
12. [Tuning](#12-tuning)
13. [Troubleshooting](#13-troubleshooting)
14. [Project files](#14-project-files)

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
- **Arduino → PC (telemetry):** `angle,distance.`

  Example stream in Serial Monitor:

  ```
  0,180.2,175.4,170.,...,90,25,92,26,...,180,40.
  ```

  Values: `angle` = 0–180 (degrees), `distance` = 0–400 (cm, capped).
  Distance > 40 is treated as "out of range" by the displays.

- **PC → Arduino (commands, optional):**

  | Command | Effect |
  |---|---|
  | `m` (e.g. `m\n`) | Resume automatic 0→180→0 sweep |
  | `a<angle>` (e.g. `a90\n`) | Hold the servo at that angle (0–180) and take one reading |

  The Processing display is receive-only (no commands). Commands come from the
  web app in Step 3. The Arduino ignores the command stream gracefully if
  nothing ever sends one — it just sweeps.

---

## 6. Software prerequisites

| Software | Version | Get it |
|----------|---------|--------|
| Arduino IDE | 1.8.19 (you have this) | https://www.arduino.cc/en/software |
| Processing | 4.x (Mac/Windows/Linux) | https://processing.org/download |
| Serial library | bundled with Processing | Sketch → Import Library → Manage Libraries → search "Serial" |
| Python 3 + pyserial | only for Step 3 (web/multi-device) | https://python.org then `pip install pyserial` |

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

## 9. Step 3 — Multi-device control (Mac, iPhone, Android)

The Processing display in Step 2 is a desktop app. To let **any device — a Mac,
an iPhone, an Android phone, a tablet, a second PC — view and control** the
radar over WiFi, run the bundled web server on whichever computer is plugged
into the Arduino:

### One-time setup on the host computer (Mac / Windows / Linux)

1. Install Python 3 from https://python.org (skip — Macs usually have it).
2. Install the one dependency:

   ```bash
   pip install pyserial
   ```

   (Mac/Linux: `pip3 install pyserial`)

### Run the server

```bash
cd web
python3 server.py                    # auto-detects the Arduino
python3 server.py /dev/ttyUSB0       # or name the port explicitly
python3 server.py COM3               # Windows
```

Output:

```
Serial connected: /dev/tty.usbmodem14101

  SweepRadar running:  http://192.168.1.24:8080
  Open that URL from any device on the same WiFi network.
```

### Connect any device

Open that URL in a browser — same WiFi network, no app install:

| Device | How |
|---|---|
| **Mac** | Safari/Chrome → `http://192.168.1.24:8080` (or run the Processing app directly) |
| **iPhone** | Safari → same URL |
| **Android** | Chrome → same URL |
| Any other PC | Any browser → same URL |

### What each device can do

- **View** — live radar: sweep line, distance rings, red blip, angle/distance/
  status readout, refreshed every 150 ms. Multiple devices can watch at once.
- **Control** —
  - **[Auto sweep]** button → sends `m`, servo resumes its 0→180→0 sweep.
  - **Angle slider** → sends `a<deg>`, the servo stops and holds that exact
    angle while it takes a reading. Drag it to aim the sensor anywhere.

If the IP printed by the server is wrong or the devices can't reach it:
firewall allowing port 8080, and phone/host on the same network (guest WiFi
isolation blocks this).

> **Upgrade path:** swap the Uno for an ESP32 and move this same server code
> onto the chip — the radar then broadcasts its own WiFi with no PC attached.
> Not needed yet, but the serial protocol above stays identical.

---

## 10. Testing tips

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
5. **Web app not updating?** — confirm `server.py` prints `Serial connected:`,
   and that the Arduino's Serial Monitor is closed (only one app can hold the
   port).
6. **Phone can't reach the page?** — host and phone must be on the same WiFi
   (guest networks often block device-to-device traffic), and port 8080 must
   be allowed through the host firewall.

**Other keys:** none — `R` and `S` are the only shortcuts.

---

## 11. Code walkthrough

### Arduino — `RadarSensor.ino`

| Function / block | What it does |
|---|---|
| `#include <Servo.h>` | Servo control library (ships with Arduino) |
| `TRIG_PIN / ECHO_PIN / SERVO_PIN` | Pin assignments — change here only |
| `readDistanceCm()` | Fires a 10 µs trigger pulse, measures the echo with `pulseIn(..., 25000)` (25 ms timeout ≈ 4 m). No echo → reports out-of-range instead of hanging |
| `sendReading(angle, cm)` | Prints `angle,distance.` — the exact packet format |
| `setup()` | 9600 baud, attaches servo to D9, parks it at 90° for 500 ms |
| `readCommands()` | Reads incoming command bytes: `a<deg>` holds the servo at an angle (manual mode), `m` resumes auto sweep. Idle if nothing sends commands |
| `loop()` | Auto mode: sweeps 0→180→0 in 2° steps, 30 ms settle delay, sends one packet per step. Manual mode: holds position, keeps listening for commands |

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

### Web server — `web/server.py`

| Block | What it does |
|---|---|
| `find_port()` | Auto-detects the Arduino by USB vendor ID (0x2341), falls back to the first port; `python3 server.py <port>` to override |
| `serial_reader()` (thread) | Continuously parses `angle,distance.` packets into the `latest` dict — keeps running while requests are served |
| `GET /` | Serves the embedded radar UI (one HTML file, canvas drawing, 150 ms polling) |
| `GET /data` | Returns `latest` as JSON: `{"angle", "distance", "ts"}` |
| `POST /cmd` | Forwards control commands to the Arduino: `auto` → `m`, `angle:<n>` → `a<n>` (clamped 0–180) |
| `lan_ip()` / `__main__` | Detects the machine's LAN IP and prints the URL to open from other devices |

---

## 12. Tuning

| Want to… | Change |
|---|---|
| Different range (e.g. 100 cm sensor) | `MAX_RANGE_CM` in `.pde`, `MAX_CM` in `.ino`, and the ring markers `i * 10` in `drawText()` |
| Faster sweep | Lower `STEP_DELAY` (settle time) or raise `STEP_DEG` (coarser resolution) in `.ino` |
| Smoother display | Lower `STEP_DEG` to 1 (slower, finer) |
| Different serial port | `String portName` in `setup()` of the `.pde` |
| Different baud rate | `Serial.begin(...)` in `.ino` **and** `new Serial(this, portName, ...)` in `.pde` |
| Different window size | `size(w, h)` in `.pde` — all drawing scales off `width`/`height` |
| Different pins | The `const int` block at the top of `.ino` |
| Different web port | `HTTP_PORT` in `server.py` (default 8080) |
| Faster/slower UI refresh | `setTimeout(tick, 150)` in `server.py` HTML (milliseconds) |

---

## 13. Troubleshooting

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
| `ModuleNotFoundError: No module named 'serial'` | pyserial missing | `pip install pyserial` (Mac/Linux: `pip3`) |
| `server.py` says `Permission denied` on port | Port busy | Serial Monitor open, or another `server.py` running — close it |
| Phone shows "Waiting for data..." but host works | Network isolation / stale timestamp | Same WiFi (not guest), firewall allows 8080, restart `server.py` |

---

## 14. Project files

```
sweepradar/
├── README.md                      ← this file
├── RadarSensor/
│   └── RadarSensor.ino            ← upload to Arduino Uno (Arduino IDE)
├── RadarDisplay/
│   └── RadarDisplay.pde           ← desktop radar UI (Processing IDE, Mac/Win)
└── web/
    └── server.py                  ← web radar + remote control for any device
                                      (Mac, iPhone, Android browser)
```

**License:** free to use, modify, and share. Change the name in `drawText()`
if you ship it as your own.
