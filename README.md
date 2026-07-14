# Finger Paint

Motion-tracking PTZ control for IP cameras. Finger Paint pulls a live RTSP stream, detects moving objects with OpenCV, and steers the camera in real time via ONVIF PTZ commands to keep the target centred in frame — turning any static PTZ camera into a self-tracking one.

Built and tested against JOOAN A2R-U style cameras, but should work with any camera that exposes an RTSP stream and ONVIF PTZ control.

## How it works

1. **Capture** — grabs frames from the camera's RTSP stream (low-latency buffering to avoid lag).
2. **Detect** — runs background subtraction (`MOG2`) on each frame to isolate moving objects, filters out noise below a minimum blob size, and picks the largest moving contour as the target.
3. **Track** — computes how far the target is from frame centre and, if it's outside a configurable dead zone, sends `ContinuousMove` ONVIF commands to pan/tilt the camera toward it. A short cooldown between commands keeps motion smooth instead of jittery.
4. **Display** — shows a live annotated preview (bounding box, centre crosshair, pan/tilt readout, tracking status) so you can tune settings visually.

If the camera can't be reached over ONVIF, the script still runs in display-only mode so you can verify motion detection before wiring up PTZ.

## Features

- Real-time motion detection and tracking using OpenCV
- Automatic PTZ steering over ONVIF, with smooth speed control and a dead zone to reduce jitter
- Auto-reconnect on dropped RTSP frames
- Live on-screen overlay: target box, centre crosshair, pan/tilt values, tracking status
- Runs in display-only mode if ONVIF isn't available, so detection can be tuned without a live camera

## Requirements

- Python 3.9+
- A network IP camera with RTSP streaming and ONVIF PTZ support

## Setup

```powershell
pip install -r requirements.txt
```

Edit the `CONFIG` section at the top of `tracker.py` with your camera's IP, username, and password.

## Run

```powershell
python tracker.py
```

| Key | Action |
|-----|--------|
| `q` | Quit |
| `p` | Pause / resume tracking |

## Configuration

Key settings in `tracker.py`:

| Setting | Description |
|---|---|
| `CAM_IP`, `CAM_USER`, `CAM_PASS` | Camera credentials |
| `RTSP_PORT`, `ONVIF_PORT` | Camera's RTSP and ONVIF ports |
| `RTSP_URL` | Stream path — try `/onvif1`, `/stream0`, `/ch0_0.264`, or `/live/ch00_0` if the default fails |
| `PAN_SPEED`, `TILT_SPEED` | PTZ movement speed (0.0–1.0). Lower = smoother, higher = snappier |
| `DEAD_ZONE` | Centre zone (as a fraction of the frame) where the camera won't adjust, to reduce jitter |
| `MIN_AREA` | Minimum motion blob size in pixels² — raise this to ignore small/noisy movement |

## Troubleshooting

- **Stream won't open** — double-check `CAM_IP`, credentials, and try the alternate RTSP paths listed above.
- **Camera doesn't move but video shows fine** — ONVIF connection likely failed; verify `ONVIF_PORT` and that ONVIF is enabled on the camera.
- **Camera jitters or over-corrects** — increase `DEAD_ZONE`, or lower `PAN_SPEED` / `TILT_SPEED`.
- **False triggers from small movements** — raise `MIN_AREA`.

## Tech stack

Python · OpenCV · NumPy · ONVIF (`onvif-zeep`, `zeep`) · multithreading
