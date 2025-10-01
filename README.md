# Espresso ☕️

**Espresso** is a lightweight, cross-platform tray application that keeps your computer awake by simulating key activity at regular intervals. Perfect for preventing your system from going to sleep or locking automatically.  

It supports **Windows, macOS, and Linux**, and runs silently in the system tray with a simple Start/Stop/Quit menu.

---

## Features

- Runs in the **system tray** (Windows/Mac/Linux)  
- **Start/Stop** simulation with menu  
- **Custom tray icon** support  
- Lightweight, minimal CPU usage  
- Cross-platform (Windows `.exe`, macOS `.app`, Linux binary)  

---

## Folder Structure

Espresso/
├── assets/
│ ├── c5.png # Tray icon
│ ├── c5.ico # Windows icon
│ └── c5.icns # macOS icon
├── src/
│ └── main.py # Main application code
├── dist/ # Build outputs
├── build/ # Temporary build files
├── venv/ # Virtual environment
├── requirements.txt # Python dependencies
└── .gitignore



---

## Prerequisites

- Python 3.13+  
- Pip  
- Virtual environment (recommended)

Install dependencies:

```bash
pip install -r requirements.txt


