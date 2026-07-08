"""
JOOAN A2R-U Motion Tracking Webcam
====================================
Pulls RTSP stream, detects moving objects, and steers the camera
using ONVIF PTZ commands to keep the target centred.

REQUIREMENTS:
    pip install opencv-python onvif-zeep zeep numpy

USAGE:
    1. Edit CONFIG below with your camera's IP, username, password
    2. python jooan_tracker.py
    3. Press 'q' to quit, 'p' to pause tracking
"""

import cv2
import numpy as np
import time
import threading

# ─── CONFIG ──────────────────────────────────────────────────────────────────
CAM_IP       = "192.168.1.100"   # your camera's local IP (check router DHCP)
CAM_USER     = "admin"           # default JOOAN username
CAM_PASS     = "your_password"   # password you set in cam720 app
RTSP_PORT    = 554
ONVIF_PORT   = 8899              # JOOAN ONVIF port

# RTSP stream URL — try these in order:
RTSP_URL = f"rtsp://{CAM_USER}:{CAM_PASS}@{CAM_IP}:{RTSP_PORT}/onvif1"
# fallbacks: /stream0  /ch0_0.264  /live/ch00_0

# PTZ speed (0.0 – 1.0). Lower = smoother, Higher = snappier
PAN_SPEED    = 0.15
TILT_SPEED   = 0.12

# Dead zone: fraction of frame where we DON'T move (avoids jitter)
DEAD_ZONE    = 0.12   # 12% either side of centre = 24% total

# Minimum contour area to count as a "real" moving object (tune to reduce noise)
MIN_AREA     = 1500   # pixels²
# ─────────────────────────────────────────────────────────────────────────────


def connect_ptz():
    """Connect to camera via ONVIF and return PTZ service + profile token."""
    try:
        from onvif import ONVIFCamera
        cam = ONVIFCamera(CAM_IP, ONVIF_PORT, CAM_USER, CAM_PASS)
        media  = cam.create_media_service()
        ptz    = cam.create_ptz_service()
        profiles = media.GetProfiles()
        token  = profiles[0].token
        print(f"[ONVIF] Connected. Profile token: {token}")
        return ptz, token
    except Exception as e:
        print(f"[ONVIF] Connection failed: {e}")
        print("  → Tracking will run WITHOUT motor control (display only)")
        return None, None


def stop_camera(ptz, token):
    """Send a stop command to halt any ongoing PTZ movement."""
    if not ptz:
        return
    try:
        req = ptz.create_type("Stop")
        req.ProfileToken = token
        req.PanTilt  = True
        req.Zoom     = False
        ptz.Stop(req)
    except Exception:
        pass


def move_camera(ptz, token, pan_vel, tilt_vel):
    """
    Send a continuous-move PTZ command.
    pan_vel  : -1.0 (left) to +1.0 (right)
    tilt_vel : -1.0 (down) to +1.0 (up)
    """
    if not ptz:
        return
    try:
        req = ptz.create_type("ContinuousMove")
        req.ProfileToken = token
        req.Velocity = {
            "PanTilt": {"x": pan_vel,  "y": tilt_vel},
            "Zoom":    {"x": 0}
        }
        ptz.ContinuousMove(req)
    except Exception as e:
        print(f"[PTZ] Move error: {e}")


def get_motion_centre(frame, bg_subtractor):
    """
    Returns (cx_norm, cy_norm) of the largest moving blob,
    both normalised to [-0.5, +0.5] from frame centre.
    Returns (None, None) if nothing detected.
    """
    blurred = cv2.GaussianBlur(frame, (21, 21), 0)
    fg_mask = bg_subtractor.apply(blurred)

    # Threshold + dilate to fill holes
    _, thresh = cv2.threshold(fg_mask, 25, 255, cv2.THRESH_BINARY)
    thresh = cv2.dilate(thresh, None, iterations=3)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        return None, None, thresh

    # Pick the largest contour
    largest = max(contours, key=cv2.contourArea)
    if cv2.contourArea(largest) < MIN_AREA:
        return None, None, thresh

    x, y, w, h = cv2.boundingRect(largest)
    cx = x + w // 2
    cy = y + h // 2

    H, W = frame.shape[:2]
    cx_norm = (cx - W / 2) / W   # -0.5 left … +0.5 right
    cy_norm = (cy - H / 2) / H   # -0.5 top  … +0.5 bottom

    return cx_norm, cy_norm, thresh, (x, y, w, h)


def main():
    print(f"[STREAM] Connecting to {RTSP_URL} …")
    cap = cv2.VideoCapture(RTSP_URL)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)   # reduce latency

    if not cap.isOpened():
        print("[ERROR] Cannot open RTSP stream. Check IP, credentials, and URL.")
        print("  Tried:", RTSP_URL)
        return

    print("[STREAM] Connected ✓")

    ptz, token = connect_ptz()

    bg_sub      = cv2.createBackgroundSubtractorMOG2(history=300, varThreshold=40, detectShadows=False)
    tracking    = True
    last_move   = 0
    MOVE_COOLDOWN = 0.3   # seconds between PTZ commands

    print("\nControls: [q] quit  [p] pause/resume tracking\n")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Frame drop — reconnecting…")
            time.sleep(0.5)
            cap.release()
            cap = cv2.VideoCapture(RTSP_URL)
            continue

        H, W = frame.shape[:2]
        display = frame.copy()

        result = get_motion_centre(frame, bg_sub)
        if len(result) == 4:
            cx_norm, cy_norm, mask, bbox = result
        else:
            cx_norm, cy_norm, mask = result[0], result[1], result[2]
            bbox = None

        now = time.time()

        if tracking and cx_norm is not None:
            # Draw target
            if bbox:
                x, y, w, h = bbox
                cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
            # Draw centre cross
            cx_px = int((cx_norm + 0.5) * W)
            cy_px = int((cy_norm + 0.5) * H)
            cv2.circle(display, (cx_px, cy_px), 8, (0, 255, 0), -1)
            cv2.line(display, (W//2, 0), (W//2, H), (0, 200, 255), 1)
            cv2.line(display, (0, H//2), (W, H//2), (0, 200, 255), 1)

            # Only move if outside dead zone and cooldown elapsed
            if now - last_move > MOVE_COOLDOWN:
                pan_vel  = 0.0
                tilt_vel = 0.0

                if abs(cx_norm) > DEAD_ZONE:
                    pan_vel = PAN_SPEED * np.sign(cx_norm)   # positive = right

                if abs(cy_norm) > DEAD_ZONE:
                    # positive cy_norm = object below centre → tilt DOWN (negative y in ONVIF)
                    tilt_vel = -TILT_SPEED * np.sign(cy_norm)

                if pan_vel != 0 or tilt_vel != 0:
                    move_camera(ptz, token, pan_vel, tilt_vel)
                    last_move = now
                    cv2.putText(display, f"PAN {pan_vel:+.2f}  TILT {tilt_vel:+.2f}",
                                (10, H-20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
                else:
                    stop_camera(ptz, token)
                    cv2.putText(display, "ON TARGET", (10, H-20),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        else:
            if tracking:
                stop_camera(ptz, token)

        status = "TRACKING" if tracking else "PAUSED"
        colour = (0, 255, 0) if tracking else (0, 100, 255)
        cv2.putText(display, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1.0, colour, 2)

        cv2.imshow("JOOAN Tracker", display)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            stop_camera(ptz, token)
            break
        elif key == ord('p'):
            tracking = not tracking
            if not tracking:
                stop_camera(ptz, token)
            print(f"[INFO] Tracking {'resumed' if tracking else 'paused'}")

    cap.release()
    cv2.destroyAllWindows()
    print("[INFO] Exited cleanly.")


if __name__ == "__main__":
    main()