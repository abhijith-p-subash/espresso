pyinstaller --onefile --windowed main.py --icon=my_icon.ico


2. Check build command

For Windows, you must use ; in --add-data:

pyinstaller --onefile --windowed --add-data "c5.png;." main.py --icon=c5.ico


For Mac/Linux, use : instead:

pyinstaller --onefile --windowed --add-data "c5.png:." main.py --icon=c5.ico


⚠️ If you’re on Windows and use :, PyInstaller will silently skip including the file → causing your exact error.


build msi file using cx_freeze: python setup.py bdist_msi
