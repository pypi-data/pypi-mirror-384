import importlib
import io
import logging
import sys
import time
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
for name in ['wicked_print.wicked_print', 'wicked_print']:
    if name in sys.modules:
        del sys.modules[name]

import pytest

wicked_module = importlib.import_module(
    'wicked_print.wicked_print'
)  # type: ignore

from wicked_print import (
    wicked_print,
    wicked_print_flush,
    configure_wicked_print,
)  # type: ignore  # noqa: E402


@pytest.fixture(autouse=True)
def reset_printer_state():
    printer = wicked_module._GLOBAL_WICKED_PRINTER
    if printer is not None:
        wicked_module.wicked_print_flush()
        printer.stop()
    wicked_module._GLOBAL_WICKED_PRINTER = None
    yield
    printer = wicked_module._GLOBAL_WICKED_PRINTER
    if printer is not None:
        wicked_module.wicked_print_flush()
        printer.stop()
    wicked_module._GLOBAL_WICKED_PRINTER = None


def test_wicked_print_writes_output(capsys, monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buffer)
    wicked_print('hello', end='', print_interval=0)
    wicked_module.wicked_print_flush()
    assert buffer.getvalue() == 'hello'


def test_wicked_print_logs_when_requested(caplog, monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buffer)
    with caplog.at_level(logging.INFO):
        wicked_print('log me', perform_logging=True, print_interval=0)
        wicked_module.wicked_print_flush()
    assert 'log me' in caplog.text


def test_wicked_print_handles_arbitrary_objects(monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buffer)
    wicked_print('value:', 123, {'a': 1}, sep='|', end='', print_interval=0)
    wicked_module.wicked_print_flush()
    assert buffer.getvalue() == "value:|123|{'a': 1}"


def test_wicked_print_rejects_non_bool_logging():
    with pytest.raises(TypeError):
        wicked_print('hello', perform_logging='yes')  # type: ignore[arg-type]


def test_wicked_print_rejects_non_str_end():
    with pytest.raises(TypeError):
        wicked_print('hello', end=123)  # type: ignore[arg-type]


def test_wicked_print_rejects_non_str_sep():
    with pytest.raises(TypeError):
        wicked_print('hello', sep=123)  # type: ignore[arg-type]


def test_wicked_print_rejects_non_numeric_interval():
    with pytest.raises(TypeError):
        wicked_print('hello', print_interval='fast')  # type: ignore[arg-type]


def test_wicked_print_rejects_negative_interval():
    with pytest.raises(ValueError):
        wicked_print('hello', print_interval=-0.1)


def test_wicked_print_non_blocking(monkeypatch):
    class FakeTTY(io.StringIO):
        def isatty(self) -> bool:
            return True

    buffer = FakeTTY()
    monkeypatch.setattr(sys, 'stdout', buffer)
    start = time.perf_counter()
    wicked_print('slowwwwwwwwwww', end='', print_interval=0.02)
    duration = time.perf_counter() - start
    assert duration < 0.01


def test_configure_max_queue_flushes_oldest(monkeypatch):
    class FakeTTY(io.StringIO):
        def isatty(self) -> bool:
            return True

    buffer = FakeTTY()
    monkeypatch.setattr(sys, 'stdout', buffer)

    orig_print_tty = wicked_module.WickedPrinter._print_tty
    start_event = threading.Event()
    release_event = threading.Event()

    def controlled_print_tty(self, msg):
        if msg.text == 'slow':
            start_event.set()
            release_event.wait()
        orig_print_tty(self, msg)

    monkeypatch.setattr(
        wicked_module.WickedPrinter,
        '_print_tty',
        controlled_print_tty,
        raising=False,
    )

    configure_wicked_print(max_queue=1)

    wicked_print('slow', end='', print_interval=0.01)
    assert start_event.wait(0.5)

    wicked_print('second', end='', print_interval=0)
    wicked_print('third', end='', print_interval=0)

    assert 'second' in buffer.getvalue()
    assert 'third' not in buffer.getvalue()

    release_event.set()
    wicked_print_flush()

    final = buffer.getvalue()
    assert 'third' in final
    assert final.index('second') < final.index('third')


def test_configure_max_queue_rejects_non_positive():
    with pytest.raises(ValueError):
        configure_wicked_print(max_queue=0)


def test_wicked_print_hex_color_on_tty(monkeypatch):
    class FakeTTY(io.StringIO):
        def isatty(self) -> bool:
            return True

    buffer = FakeTTY()
    monkeypatch.setattr(sys, 'stdout', buffer)
    wicked_print('colorful', color='#00ff00', print_interval=0)
    wicked_module.wicked_print_flush()
    output = buffer.getvalue()
    assert '\033[38;2;0;255;0m' in output
    assert output.endswith('\033[0m\n')


def test_wicked_print_color_skipped_for_non_tty(monkeypatch):
    buffer = io.StringIO()
    monkeypatch.setattr(sys, 'stdout', buffer)
    wicked_print('plain', color='red', print_interval=0)
    wicked_module.wicked_print_flush()
    assert '\033' not in buffer.getvalue()


def test_wicked_print_rejects_bad_color():
    with pytest.raises(ValueError):
        wicked_print('oops', color='not-a-color')


def test_wicked_print_prints_directly_in_interactive(monkeypatch, caplog):
    class DummyFlags:
        interactive = True

    outputs = []

    def fake_print(msg, end='\n'):
        outputs.append((msg, end))

    monkeypatch.setattr(sys, 'ps1', '>>> ', raising=False)
    monkeypatch.setattr(sys, 'flags', DummyFlags(), raising=False)
    monkeypatch.setattr('builtins.print', fake_print)

    with caplog.at_level(logging.INFO):
        wicked_print('direct', print_interval=0, perform_logging=True)

    assert outputs == [('direct', '\n')]
    assert 'direct' in caplog.text


def test_shutdown_waits_for_slow_tty(monkeypatch):
    class FakeTTY(io.StringIO):
        def isatty(self) -> bool:
            return True

    buffer = FakeTTY()
    monkeypatch.setattr(sys, 'stdout', buffer)

    orig_print_tty = wicked_module.WickedPrinter._print_tty
    start_event = threading.Event()
    release_event = threading.Event()

    def blocking_print(self, msg):
        start_event.set()
        release_event.wait()
        orig_print_tty(self, msg)

    monkeypatch.setattr(
        wicked_module.WickedPrinter,
        '_print_tty',
        blocking_print,
        raising=False,
    )

    wicked_print('slow shutdown', end='', print_interval=0.01)
    assert start_event.wait(0.5)

    shutdown_thread = threading.Thread(
        target=wicked_module._shutdown_printer
    )
    shutdown_thread.start()

    time.sleep(0.2)
    assert shutdown_thread.is_alive()

    time.sleep(1.05)
    assert shutdown_thread.is_alive()

    release_event.set()
    shutdown_thread.join(timeout=1)
    assert not shutdown_thread.is_alive()
