#!/usr/bin/env python3
"""
SweepRadar web bridge - run this on the computer plugged into the Arduino,
then open its IP from any device on the same network (Mac, iPhone, Android).

    pip install pyserial
    python3 server.py            # optional: python3 server.py /dev/ttyUSB0

Serves a radar UI at http://<your-ip>:8080 with:
  - live sweep line + red blip (polled every 150 ms)
  - [Auto sweep] button  -> sends "m"  to the Arduino
  - angle slider         -> sends "a<deg>" to the Arduino
"""

import json
import socket
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import serial
from serial.tools import list_ports

BAUD = 9600
HTTP_PORT = 8080
MAX_CM = 40  # must match MAX_CM in RadarSensor.ino


def find_port():
    if len(sys.argv) > 1:
        return sys.argv[1]
    for p in list_ports.comports():  # Arduino VID 0x2341
        if p.vid == 0x2341:
            return p.device
    ports = list_ports.comports()
    if not ports:
        sys.exit("No serial ports found - is the Arduino plugged in?")
    return ports[0].device


port = find_port()
ser = serial.Serial(port, BAUD, timeout=1)
print(f"Serial connected: {port}")

latest = {"angle": 90, "distance": 0, "ts": 0.0}


def serial_reader():
    for raw in ser:
        line = raw.strip()
        if b"," not in line:
            continue
        a, _, d = line.rstrip(b".").partition(b",")
        try:
            latest.update(angle=int(float(a)), distance=int(float(d)), ts=time.time())
        except ValueError:
            pass  # garbled packet, keep last good values


threading.Thread(target=serial_reader, daemon=True).start()


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        s.close()


HTML = """<!doctype html>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>SweepRadar</title>
<style>
 body{background:#000;color:#62f51f;font-family:monospace;text-align:center;margin:0;padding:8px}
 canvas{max-width:100%;height:auto;border:1px solid #1a3}
 button,input{font-family:monospace;font-size:18px}
 button{background:#000;color:#62f51f;border:2px solid #62f51f;padding:10px 22px;border-radius:6px}
 button:active{background:#62f51f;color:#000}
 #wrap{margin-top:8px}
 #sl{width:50%;accent-color:#62f51f}
 #rd{display:block;margin-top:8px;font-size:18px}
</style>
<canvas id=c width=900 height=470></canvas>
<div id=wrap>
 <button onclick="cmd('auto')">Auto sweep</button>
 <input id=sl type=range min=0 max=180 value=90
        oninput="cmd('angle:'+this.value);lbl()"
        onchange="cmd('angle:'+this.value,1);lbl()">
 <span id=deg>90&deg;</span>
 <span id=rd>Waiting for data...</span>
</div>
<script>
const cv=document.getElementById('c'),x=cv.getContext('2d'),R=440;
let lastCmd=0;
function lbl(){document.getElementById('deg').textContent=sl.value+'&deg;'}
async function cmd(c,force){
  const now=Date.now();
  if(!force&&now-lastCmd<120)return; lastCmd=now;  // throttle slider spam
  await fetch('/cmd',{method:'POST',body:JSON.stringify({cmd:c})});
}
function draw(a,d,stale){
  x.fillStyle='rgba(0,0,0,.3)';x.fillRect(0,0,900,470);
  x.save();x.translate(450,455);
  x.strokeStyle='#62f51f';x.lineWidth=2;
  for(let i=1;i<=4;i++){x.beginPath();x.arc(0,0,R*i/4,Math.PI,2*Math.PI);x.stroke();}
  x.lineWidth=1;
  for(let ag=0;ag<=180;ag+=30){
    const rad=(180-ag)*Math.PI/180;
    x.beginPath();x.moveTo(0,0);
    x.lineTo(R*Math.cos(rad),-R*Math.sin(rad));x.stroke();
  }
  x.beginPath();x.moveTo(-R,0);x.lineTo(R,0);x.stroke();
  const rad=(180-a)*Math.PI/180;
  x.strokeStyle='rgba(30,250,60,.9)';x.lineWidth=3;   // sweep line
  x.beginPath();x.moveTo(0,0);x.lineTo(R*Math.cos(rad),-R*Math.sin(rad));x.stroke();
  if(!stale&&d<MAXCM){
    const rr=d/MAXCM*R;                                // red blip
    x.fillStyle='rgba(255,60,60,.95)';
    x.beginPath();x.arc(rr*Math.cos(rad),-rr*Math.sin(rad),6,0,7);x.fill();
    x.strokeStyle='rgba(255,100,100,.5)';x.lineWidth=1;
    x.beginPath();x.moveTo(0,0);x.lineTo(rr*Math.cos(rad),-rr*Math.sin(rad));x.stroke();
  }
  x.restore();
  x.fillStyle='#62f51f';x.font='16px monospace';
  for(let i=1;i<=4;i++)x.fillText(i*10+'cm',450+R*i/4+8,468);
  x.fillText('SweepRadar',10,20);
  const st=d<MAXCM?'In Range':'Out of Range';
  x.fillStyle=stale?'#ffcc00':(d<MAXCM?'#62f51f':'#ff6464');
  x.fillText(stale?'Waiting for data...':'Angle: '+a+'\u00B0  Distance: '
    +(stale?'---':d+' cm')+'  '+st,10,460);
}
let MAXCM=40;
async function tick(){
  try{
    const j=await(await fetch('/data')).json();
    draw(j.angle,j.distance,Date.now()/1000-j.ts>2);
  }catch(e){draw(90,0,true);}
  setTimeout(tick,150);
}
tick();
</script>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.end_headers()
        self.wfile.write(body if isinstance(body, bytes) else body.encode())

    def do_GET(self):
        if self.path == "/":
            self._send(200, HTML, "text/html; charset=utf-8")
        elif self.path == "/data":
            self._send(200, json.dumps(latest))
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/cmd":
            return self.send_error(404)
        try:
            n = int(self.headers.get("Content-Length", 0))
            cmd = json.loads(self.rfile.read(n))["cmd"]
            if cmd == "auto":
                ser.write(b"m\n")
            elif cmd.startswith("angle:"):
                deg = max(0, min(180, int(cmd[6:])))
                ser.write(f"a{deg}\n".encode())
            else:
                return self.send_error(400, "unknown command")
            self._send(204, b"")
        except (ValueError, KeyError, json.JSONDecodeError) as e:
            self.send_error(400, str(e))

    def log_message(self, *args):
        pass  # quiet server log


if __name__ == "__main__":
    ip = lan_ip()
    print(f"\n  SweepRadar running:  http://{ip}:{HTTP_PORT}")
    print("  Open that URL from any device on the same WiFi network.")
    print("  Ctrl+C to stop.\n")
    ThreadingHTTPServer(("0.0.0.0", HTTP_PORT), Handler).serve_forever()
