import os
import signal
import threading
import time

import pytest

from espresso.signals import SignalWatcher

pytestmark = pytest.mark.skipif(not hasattr(signal, "SIGUSR1"), reason="needs POSIX signals")


def test_signal_reaches_the_callback():
    received = []
    done = threading.Event()

    def on_signal(signum):
        received.append(signum)
        done.set()

    watcher = SignalWatcher(on_signal, signal_names=("SIGUSR1",))
    assert watcher.install() is True
    try:
        os.kill(os.getpid(), signal.SIGUSR1)
        assert done.wait(5), "signal never reached the watcher thread"
        assert received == [signal.SIGUSR1]
    finally:
        watcher.uninstall()


def test_signal_arrives_while_the_main_thread_is_blocked():
    """The whole point: delivery must not depend on the main thread running Python.

    A native GUI loop parks the main thread inside C code, where CPython never
    gets to dispatch a normal handler. Blocking on a lock reproduces that.
    """
    done = threading.Event()
    watcher = SignalWatcher(lambda _s: done.set(), signal_names=("SIGUSR1",))
    assert watcher.install() is True
    try:
        blocker = threading.Lock()
        blocker.acquire()

        def fire():
            time.sleep(0.2)
            os.kill(os.getpid(), signal.SIGUSR1)
            time.sleep(0.2)
            blocker.release()

        threading.Thread(target=fire, daemon=True).start()
        blocker.acquire()  # main thread parked, as in NSApplication.run()
        assert done.is_set()
    finally:
        watcher.uninstall()


def test_uninstall_restores_the_previous_handler():
    original = signal.getsignal(signal.SIGUSR1)
    watcher = SignalWatcher(lambda _s: None, signal_names=("SIGUSR1",))
    watcher.install()
    assert signal.getsignal(signal.SIGUSR1) is not original
    watcher.uninstall()
    assert signal.getsignal(signal.SIGUSR1) is original


def test_uninstall_restores_the_previous_wakeup_fd():
    watcher = SignalWatcher(lambda _s: None, signal_names=("SIGUSR1",))
    watcher.install()
    watcher.uninstall()
    # Reclaiming it must yield -1: nobody else's fd was left installed.
    assert signal.set_wakeup_fd(-1) == -1


def test_uninstall_is_idempotent():
    watcher = SignalWatcher(lambda _s: None, signal_names=("SIGUSR1",))
    watcher.install()
    watcher.uninstall()
    watcher.uninstall()


def test_context_manager_cleans_up():
    original = signal.getsignal(signal.SIGUSR1)
    with SignalWatcher(lambda _s: None, signal_names=("SIGUSR1",)):
        pass
    assert signal.getsignal(signal.SIGUSR1) is original


def test_unknown_signal_names_are_skipped():
    watcher = SignalWatcher(lambda _s: None, signal_names=("SIGNOPE",))
    assert watcher.install() is False


def test_install_off_the_main_thread_declines():
    result = {}

    def attempt():
        watcher = SignalWatcher(lambda _s: None, signal_names=("SIGUSR1",))
        result["installed"] = watcher.install()
        watcher.uninstall()

    thread = threading.Thread(target=attempt)
    thread.start()
    thread.join(5)
    assert result["installed"] is False


def test_a_raising_callback_does_not_kill_the_thread():
    watcher = SignalWatcher(lambda _s: 1 / 0, signal_names=("SIGUSR1",))
    watcher.install()
    try:
        os.kill(os.getpid(), signal.SIGUSR1)
        time.sleep(0.3)
    finally:
        watcher.uninstall()


@pytest.fixture(autouse=True)
def _restore_default_sigusr1():
    yield
    signal.signal(signal.SIGUSR1, signal.SIG_DFL)
    signal.set_wakeup_fd(-1)
