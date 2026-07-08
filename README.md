# Finger Paint

Motion-tracking PTZ control for IP cameras. Pulls an RTSP stream, detects moving objects, and steers the camera with ONVIF commands to keep the target centred.

Built for JOOAN A2R-U style cameras, but should work with any RTSP + ONVIF PTZ setup.

## Requirements

- Python 3.9+
- A network IP camera with RTSP and ONVIF PTZ support

## Setup

```powershell
pip install -r requirements.txt
```

Edit the `CONFIG` section at the top of `tracker.py` with your camera IP, username, and password.

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

- `CAM_IP`, `CAM_USER`, `CAM_PASS` — camera credentials
- `RTSP_URL` — stream path (try `/onvif1`, `/stream0`, `/ch0_0.264` if the default fails)
- `PAN_SPEED`, `TILT_SPEED` — PTZ movement speed (0.0–1.0)
- `DEAD_ZONE` — centre zone where the camera won't adjust (reduces jitter)
- `MIN_AREA` — minimum motion blob size in pixels²
