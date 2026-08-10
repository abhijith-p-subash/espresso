import time

from espresso.config import Config
from espresso.service import KeepAwakeService


def wait_for(predicate, timeout=5.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


def make_service(backend, simulator, **kwargs):
    # Most of these tests assert on both mechanisms, so ask for both explicitly
    # rather than inheriting whatever the app default happens to be.
    kwargs.setdefault("mode", "both")
    config = Config(interval=kwargs.pop("interval", 5), **kwargs)
    return KeepAwakeService(config, backend=backend, simulator=simulator)


def test_starts_and_stops(backend, simulator):
    service = make_service(backend, simulator)
    assert service.start() is True
    assert service.is_active
    assert wait_for(lambda: simulator.pulses >= 1)
    assert service.stop() is True
    assert not service.is_active


def test_backend_acquired_once_and_released(backend, simulator):
    service = make_service(backend, simulator)
    service.start()
    assert wait_for(lambda: backend.acquired == 1)
    service.stop()
    assert backend.released == 1


def test_double_start_is_a_no_op(backend, simulator):
    service = make_service(backend, simulator)
    assert service.start() is True
    assert service.start() is False
    service.stop()
    assert backend.acquired == 1


def test_stop_when_never_started(backend, simulator):
    service = make_service(backend, simulator)
    assert service.stop() is False
    assert backend.released == 0


def test_repeated_stop_does_not_double_release(backend, simulator):
    service = make_service(backend, simulator)
    service.start()
    assert wait_for(lambda: backend.acquired == 1)
    service.stop()
    service.stop()
    assert backend.released == 1


def test_system_mode_skips_keystrokes(backend, simulator):
    service = make_service(backend, simulator, mode="system")
    service.start()
    assert wait_for(lambda: backend.acquired == 1)
    service.stop()
    assert simulator.pulses == 0


def test_activity_mode_skips_the_inhibitor(backend, simulator):
    service = make_service(backend, simulator, mode="activity")
    service.start()
    assert wait_for(lambda: simulator.pulses >= 1)
    service.stop()
    assert backend.acquired == 0
    assert backend.released == 0


def test_stop_is_prompt_even_with_a_long_interval(backend, simulator):
    service = make_service(backend, simulator, interval=3600)
    service.start()
    assert wait_for(lambda: simulator.pulses >= 1)
    started = time.monotonic()
    service.stop()
    assert time.monotonic() - started < 2.0
    assert not service.is_active


def test_setting_interval_recycles_a_running_worker(backend, simulator):
    service = make_service(backend, simulator)
    service.start()
    assert wait_for(lambda: backend.acquired == 1)
    service.set_interval(120)
    assert service.config.interval == 120
    assert service.is_active
    assert wait_for(lambda: backend.acquired == 2 and backend.released == 1)
    service.stop()


def test_setting_interval_while_paused_does_not_start_it(backend, simulator):
    service = make_service(backend, simulator)
    service.set_interval(300)
    assert service.config.interval == 300
    assert not service.is_active
    assert backend.acquired == 0


def test_invalid_interval_is_clamped(backend, simulator):
    service = make_service(backend, simulator)
    service.set_interval(-1)
    assert service.config.interval >= 1


def test_toggle_flips_state(backend, simulator):
    service = make_service(backend, simulator)
    assert service.toggle() is True
    assert service.toggle() is False
    assert backend.acquired == 1
    assert backend.released == 1


def test_on_change_fires_for_start_and_stop(backend, simulator):
    calls = []
    service = make_service(backend, simulator)
    service.on_change = lambda: calls.append(service.is_active)
    service.start()
    service.stop()
    assert calls == [True, False]


def test_broken_on_change_does_not_break_the_service(backend, simulator):
    service = make_service(backend, simulator)
    service.on_change = lambda: 1 / 0
    service.start()
    assert service.is_active
    service.stop()
    assert backend.released == 1


def test_failing_simulator_does_not_stop_the_loop(backend, simulator):
    simulator.works = False
    service = make_service(backend, simulator)
    service.start()
    assert wait_for(lambda: simulator.pulses >= 1)
    assert service.is_active
    service.stop()
    assert service.pulse_count == 0


def test_crashing_backend_release_is_contained(backend, simulator):
    def boom():
        raise RuntimeError("release failed")

    service = make_service(backend, simulator)
    service.start()
    assert wait_for(lambda: backend.acquired == 1)
    backend.release = boom
    service.stop()
    assert not service.is_active
