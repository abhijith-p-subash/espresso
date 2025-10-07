import time
import platform
import threading
import sys
import os
from pynput.keyboard import Key, Controller as KeyController
from pystray import Icon, Menu, MenuItem
from PIL import Image



# ---------------------------
# Helper function for PyInstaller
# ---------------------------
def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        # PyInstaller stores files in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    return os.path.join(base_path, "assets", relative_path)

class Espresso:
    def __init__(self, interval=60):
        self.running = False
        self.interval = interval
        self.keyboard = KeyController()
        self._stop_event = threading.Event()
        self.thread = None
        icon_image = Image.open(resource_path("c5.png"))
        self.icon = Icon(
            "Espresso",
            icon_image,
            title="Espresso",
            menu=self._menu())

    def _menu(self):
        return Menu(
            MenuItem(lambda item: f"Status: {'Running 😊' if self.running else 'Stopped 💀'}", None, enabled=False),
            MenuItem("Start", self.start),
            MenuItem("Stop", self.stop),
            MenuItem("Quit", self.quit)
        )

    def _check_sys(self):
        return platform.system()

    def simulate_activity(self):
        """Simulate user activity""" 
        try:
            self.keyboard.press(Key.f15)
            self.keyboard.release(Key.f15)
            print(f"☑️ Activity at {time.strftime('%a %b %d %H:%M:%S %Y')}")
        except Exception as e:
            print(f"☠️ Failed Error: {e}")


    def _run(self):
        while not self._stop_event.is_set():
            self.simulate_activity()

            if self._stop_event.wait(self.interval):
                break


    def start(self):
        if self.thread and self.thread.is_alive():
            print("⚠️ Already running...")
            return
        self._stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()
        self.running = True
        print(f"▶️ Espresso started - every {self.interval}s")

    def stop(self, icon=None, item=None):
        self._stop_event.set()
        if self.thread:
            self.thread.join(timeout=1)
        self.running = False
        print("⏹️ Espresso Stopped")

    def quit(self, icon=None, item=None):
        print("👋 Exiting...")
        self.stop()
        self.icon.stop() 

    def run(self):
        self.start()
        self.icon.run()


if __name__ == "__main__":
    Espresso(interval=30).run()