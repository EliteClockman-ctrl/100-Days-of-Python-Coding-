# Day 03 — QR Code Generator

Build a polished desktop QR code generator in Python. The app supports multiple payload types, styling options, logo embedding, and export to PNG (SVG optional).

## Features
- Clean GUI with live preview.
- Payload presets: Plain text, URL, WiFi, Email, SMS, vCard.
- Error correction, size, border, colors.
- Optional center logo overlay.
- History list with quick reload.
- Save to PNG (and SVG if optional dependency is available).

## Setup
1. `cd Day-03_QR-Code-Generator`
2. Install dependencies:
   `pip install -r requirements.txt`
3. Run:
   `python qr_generator.py`

## Notes
- Tkinter ships with Python on Windows, so no extra UI dependency is needed.
- SVG export is enabled if `qrcode` has SVG support (it usually does). If not, the button is disabled.