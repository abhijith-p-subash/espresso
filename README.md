# Espresso ☕️
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

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
```bash
Espresso/
├── assets/
├── src/
│ └── main.py # Main application code
├── dist/ # Build outputs
├── build/ # Temporary build files
├── venv/ # Virtual environment
├── requirements.txt # Python dependencies
└── .gitignore

```



---

## Prerequisites

- Python 3.13+  
- Pip  
- Virtual environment (recommended)

Install dependencies:

```bash
pip install -r requirements.txt

```

## Building From Source

1. Windows (.exe)
```bash
pyinstaller --onefile --windowed --add-data "assets\c5.png;assets" src\main.py --icon=assets\c5.ico --name Espresso
```
- Output: `dist/Espresso.exe`
- Tray icon is included automatically.

2. macOS (.app)
```bash
pyinstaller --onefile --windowed --add-data "assets/c5.png:assets" src/main.py --icon=assets/c5.icns --name Espresso
```
- Output: `dist/Espresso.app`
- Optional DMG installer:
```bash
create-dmg dist/Espresso.app --overwrite --dmg-title="Espresso"
```

3. Linux(Binary)
```bash
pyinstaller --onefile --windowed --add-data "assets/c5.png:assets" src/main.py --name espresso
```

- Output: `dist/espresso` (ELF binary)
- Can optionally package into .deb or .rpm.

---

## Usage
1. Launch the built executable (`.exe`, `.app`, or Linux binary).

2. The Espresso icon will appear in the system tray.

3. Right-click (or click) the tray icon to **Start**, **Stop**, or **Quit** the simulation.

---
## Download Pre-Built Binaries
Pre-built binaries can be distributed

| Platform  | File |
| ------------- |:-------------:|
| Windows     | [`Espresso.exe`](https://github.com/abhijith-p-subash/espresso/releases/latest/download/espresso.exe)     |
| MacOS      | [`Espresso.app` or `,dmg`](https://github.com/abhijith-p-subash/espresso/releases/latest/download/espresso.zip)   |
| Linux      | [`espresso` ](https://github.com/abhijith-p-subash/espresso/releases/latest/download/espresso-linux.zip)    |
 
 ---

 ## Open Source
 Espresso is **open source** under MIT License.

 Feel free to fork, contribute, or report issues!

 ### How to contribute
1. For the repository.
2. Clone locally:
```bash
https://github.com/abhijith-p-subash/espresso.git
```
3. create a virtual environment and install dependencies:
```bash
cd espresso
python -m venv venv
source venv/bin/activate   # macOS/Linux
venv\Scripts\activate      # Windows
pip install -r requirements.txt
```
4. Make your changes, test, and submit a pull request.

---
## License

This project is licensed under the [MIT License](LICENSE).

