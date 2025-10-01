pyinstaller --onefile --windowed main.py --icon=my_icon.ico


2. Check build command

For Windows, you must use ; in --add-data:

pyinstaller --onefile --windowed --add-data "c5.png;." main.py --icon=c5.ico


For Mac/Linux, use : instead:

pyinstaller --onefile --windowed --add-data "c5.png:." main.py --icon=c5.ico


⚠️ If you’re on Windows and use :, PyInstaller will silently skip including the file → causing your exact error.


build msi file using cx_freeze: python setup.py bdist_msi

--------------------------------------------
1. windows (.exe)

pyinstaller --onefile --windowed --add-data "assets\c5.png;assets" src\main.py --icon=assets\c5.ico --name Espresso


* --add-data "assets\\c5.png;assets" → includes assets in bundle

* Output: dist/Espresso.exe

2. mac (.app)

pyinstaller --onefile --windowed --add-data "assets/c5.png:assets" src/main.py --icon=assets/c5.icns --name Espresso


  * --add-data "assets/c5.png:assets" (use : on macOS/Linux)
  * Output: dist/Espresso.app
  * Optional .dmg:  create-dmg dist/Espresso.app --overwrite --dmg-title="Espresso" .

3. Linux (binary)
pyinstaller --onefile --windowed \
  --add-data "assets/c5.png:assets" \
  src/main.py --name espresso

* Output: dist/espresso (executable ELF binary)

* You can wrap into .deb or .rpm later if needed.
