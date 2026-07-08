# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Finger Paint** — a Python project for IP camera motion tracking with ONVIF PTZ control. The main entry point is `tracker.py`.

## Running the Project

```powershell
pip install -r requirements.txt
python tracker.py
```

## Dependencies

Declared in `requirements.txt`:

- `opencv-python` (cv2) — video capture and image processing
- `numpy` — array operations
- `onvif-zeep` / `zeep` — ONVIF PTZ control
