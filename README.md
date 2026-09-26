# Finger Paint

An OpenCV motion tracker that connects an IP camera's RTSP video stream to its ONVIF pan-and-tilt controls. It follows the largest moving region in the frame and shows an annotated desktop preview for tuning the tracking behaviour.

The project is a compact Python experiment in computer vision and camera control. Its configuration targets JOOAN A2R-U-style cameras; other cameras need compatible RTSP and ONVIF PTZ support and device-specific configuration.

## What it does

- Detects motion with MOG2 background subtraction, Gaussian blur, thresholding, and contour filtering.
- Selects the largest contour above a configurable minimum area.
- Sends ONVIF `ContinuousMove` commands when the target moves outside a central dead zone.
- Uses fixed pan/tilt speeds and a 0.3-second command cooldown to limit frequent adjustments.
- Displays the target box, centre guides, movement commands, and tracking state.
- Attempts to reopen the RTSP stream after a failed frame read.
- Continues with video and motion detection if the initial ONVIF connection fails.

This is motion tracking, not object recognition: it does not identify people, remember a target, or distinguish camera movement from movement in the scene.

## Requirements

- Python 3.9 or newer and the packages in [requirements.txt](requirements.txt).
- A desktop environment that can display an OpenCV window.
- A reachable RTSP video stream; motor control additionally requires an ONVIF PTZ camera.
- The camera's IP address, credentials, RTSP path, and ONVIF port.

## Getting started

```bash
git clone https://github.com/m1-k-k/finger-paint.git
cd finger-paint
python -m venv .venv
```

Activate the environment with `.venv/Scripts/Activate.ps1` in Windows PowerShell, or `source .venv/bin/activate` on macOS/Linux, then install dependencies:

```bash
python -m pip install -r requirements.txt
```

Edit the `CONFIG` section in [tracker.py](tracker.py), then run:

```bash
python tracker.py
```

Keep the preview window focused when using the keyboard controls.

| Key | Action |
| --- | --- |
| `p` | Pause or resume tracking; pausing sends a motor stop command |
| `q` | Stop the camera, close the stream, and exit |

## Camera configuration

| Setting | Default | Purpose |
| --- | --- | --- |
| `CAM_IP`, `CAM_USER`, `CAM_PASS` | Placeholder camera details | Address and credentials for RTSP and ONVIF |
| `RTSP_PORT` | `554` | Video-stream port |
| `ONVIF_PORT` | `8899` | ONVIF service port; varies by camera |
| `RTSP_URL` | `/onvif1` stream path | Full RTSP URL assembled from the camera settings |
| `PAN_SPEED` | `0.15` | Horizontal movement speed |
| `TILT_SPEED` | `0.12` | Vertical movement speed |
| `DEAD_ZONE` | `0.12` | No-movement zone extending 12% of the frame dimension to each side of centre |
| `MIN_AREA` | `1500` | Minimum contour area in pixels squared |

The source also lists `/stream0`, `/ch0_0.264`, and `/live/ch00_0` as alternative stream paths to try. Use the path and port supported by your camera. `MOVE_COOLDOWN` is defined inside `main()` if you need to adjust the interval between movement commands.

Camera credentials are currently edited directly in the source, and the full RTSP URL is printed at startup. Keep those local edits and logs private when sharing code or troubleshooting output.

## How the tracking loop works

1. Open the RTSP stream and attempt an ONVIF connection using the camera's first media profile.
2. Blur each frame, subtract the background, and expand the detected foreground regions.
3. Find the largest qualifying contour and normalise its centre relative to the frame.
4. Pan or tilt towards the target when it lies outside the dead zone; stop when it is centred or no qualifying motion remains.
5. Draw the preview and process pause/quit input.

## Troubleshooting and limitations

| Symptom | What to check |
| --- | --- |
| Stream does not open | Camera address, credentials, RTSP port, stream path, and network reachability |
| Video works but motors do not move | ONVIF availability, service port, credentials, and PTZ support on the selected media profile |
| Camera oscillates or over-corrects | Reduce pan/tilt speeds or increase the dead zone and command cooldown |
| Small movements trigger tracking | Increase `MIN_AREA` and test under steadier lighting |
| Tracking changes target unexpectedly | The algorithm always chooses the largest moving contour; it does not maintain an object identity |

Camera movement, shadows, lighting changes, and multiple moving subjects can confuse background subtraction. Display-only operation still requires a working RTSP stream. The repository contains a single synchronous tracking script and no automated tests or packaged application.

## Repository layout

- [tracker.py](tracker.py) — camera configuration, motion detection, PTZ commands, and preview loop.
- [requirements.txt](requirements.txt) — OpenCV, NumPy, `onvif-zeep`, and `zeep` dependencies.
