# Zhaolun Zou 05/06/2024
import atexit
import sys
import time
import logging
from threading import Event, Thread, Lock
from dataclasses import dataclass
from queue import Queue, Empty
from typing import Optional, List, Tuple

__all__ = [
    'wicked_print',
    'wicked_print_flush',
    'configure_wicked_print',
]

_ANSI_RESET = '\033[0m'
_NAMED_COLORS = {
    'black': (0, 0, 0),
    'red': (255, 0, 0),
    'green': (0, 255, 0),
    'yellow': (255, 255, 0),
    'blue': (0, 0, 255),
    'magenta': (255, 0, 255),
    'cyan': (0, 255, 255),
    'white': (255, 255, 255),
}


@dataclass
class PrintMsg:
    text: str
    end: str
    perform_logging: bool
    print_interval: float
    color_code: Optional[str]


class WickedPrinter:
    def __init__(self) -> None:
        self._ingress: Queue = Queue()
        self._file = sys.stdout
        self._is_tty = hasattr(self._file, 'isatty') and self._file.isatty()
        self._worker: Optional[Thread] = None
        self._stop = Event()
        self._max_queue: Optional[int] = None
        self._lock = Lock()

    def enqueue(self, msg: PrintMsg) -> None:
        overflow: List[PrintMsg] = []
        with self._lock:
            self._refresh_output_target()
            self._ensure_worker()
            overflow = self._collect_overflow_locked()
            self._ingress.put_nowait(msg)
        for old_msg in overflow:
            self._print_sync(old_msg)

    def flush(self, timeout: Optional[float] = None) -> None:
        if timeout is None:
            self._ingress.join()
            return
        deadline = time.perf_counter() + timeout
        while True:
            if self._ingress.unfinished_tasks == 0:
                return
            remaining = deadline - time.perf_counter()
            if remaining <= 0:
                return
            time.sleep(min(0.005, remaining))

    def _print_sync(self, msg: PrintMsg) -> None:
        if self._is_tty:
            self._print_tty(msg)
        else:
            self._print_line(msg)
        if msg.perform_logging:
            logging.info(msg.text)

    def _refresh_output_target(self) -> None:
        self._file = sys.stdout
        self._is_tty = hasattr(self._file, 'isatty') and self._file.isatty()

    def _ensure_worker(self) -> None:
        if self._worker and self._worker.is_alive():
            return
        self._stop.clear()
        self._worker = Thread(target=self._run, name='WickedPrinterWorker')
        self._worker.daemon = True
        self._worker.start()

    def _run(self) -> None:
        while True:
            msg = self._ingress.get()
            if msg is None:
                self._ingress.task_done()
                break
            try:
                self._print_sync(msg)
            finally:
                self._ingress.task_done()

    def stop(self) -> None:
        drained: List[PrintMsg] = []
        with self._lock:
            worker = self._worker
            if worker and not worker.is_alive():
                worker = None
            if worker:
                self._stop.set()
                self._ingress.put_nowait(None)
                self._ingress.join()
                worker.join()
            while True:
                try:
                    msg = self._ingress.get_nowait()
                except Empty:
                    break
                if msg is None:
                    self._ingress.task_done()
                    continue
                drained.append(msg)
                self._ingress.task_done()
            self._worker = None
            self._stop.clear()
        for msg in drained:
            self._print_sync(msg)

    def _collect_overflow_locked(self) -> List[PrintMsg]:
        if self._max_queue is None:
            return []
        trimmed: List[PrintMsg] = []
        while self._ingress.qsize() >= self._max_queue:
            try:
                queued = self._ingress.get_nowait()
            except Empty:
                break
            if queued is None:
                self._ingress.task_done()
                continue
            trimmed.append(queued)
            self._ingress.task_done()
        return trimmed

    def _print_line(self, msg: PrintMsg) -> None:
        self._file.write(msg.text)
        self._file.write(msg.end)
        self._file.flush()

    def _print_tty(self, msg: PrintMsg) -> None:
        if msg.color_code:
            self._file.write(msg.color_code)
            self._file.flush()
        next_t = time.perf_counter()
        for ch in msg.text:
            self._file.write(ch)
            self._file.flush()
            if msg.print_interval > 0:
                next_t += msg.print_interval
                remain = next_t - time.perf_counter()
                if remain > 0:
                    time.sleep(remain)
        if msg.color_code:
            self._file.write(_ANSI_RESET)
        self._file.write(msg.end)
        self._file.flush()


_GLOBAL_WICKED_PRINTER: Optional[WickedPrinter] = None
_SHUTDOWN_REGISTERED = False


def _get_printer() -> WickedPrinter:
    global _GLOBAL_WICKED_PRINTER, _SHUTDOWN_REGISTERED
    if _GLOBAL_WICKED_PRINTER is None:
        _GLOBAL_WICKED_PRINTER = WickedPrinter()
        if not _SHUTDOWN_REGISTERED:
            atexit.register(_shutdown_printer)
            _SHUTDOWN_REGISTERED = True
    return _GLOBAL_WICKED_PRINTER


def _shutdown_printer() -> None:
    if _GLOBAL_WICKED_PRINTER is None:
        return
    _GLOBAL_WICKED_PRINTER.stop()


def wicked_print(
    *objects: object,
    end: str = '\n',
    sep: str = ' ',
    perform_logging: bool = False,
    print_interval: float = 0.015,
    color: Optional[str] = None,
) -> None:
    if _should_print_directly(print_interval):
        message = sep.join(str(obj) for obj in objects)
        print(message, end=end)
        if perform_logging:
            logging.info(message)
        return
    if not isinstance(end, str):
        raise TypeError(f'Parameter end should be str but got {type(end)}')
    if not isinstance(sep, str):
        raise TypeError(f'Parameter sep should be str but got {type(sep)}')
    if not isinstance(perform_logging, bool):
        raise TypeError(
            f'Parameter perform_logging should be boolean: {perform_logging}'
        )
    if not isinstance(print_interval, (int, float)):
        raise TypeError(
            f'Parameter print_interval must be numeric: {print_interval}'
        )
    if print_interval < 0:
        raise ValueError(
            f'Parameter print_interval must be non-negative: {print_interval}'
        )
    color_code = _resolve_color(color)

    text = sep.join(str(obj) for obj in objects) if objects else ''

    msg = PrintMsg(
        text=text,
        end=end,
        perform_logging=perform_logging,
        print_interval=print_interval,
        color_code=color_code,
    )

    printer = _get_printer()
    printer.enqueue(msg)


def wicked_print_flush(timeout: Optional[float] = None) -> None:
    printer = _GLOBAL_WICKED_PRINTER
    if printer is None:
        return
    printer.flush(timeout)


def configure_wicked_print(*, max_queue: Optional[int] = None) -> None:
    printer = _get_printer()
    if max_queue is not None and max_queue <= 0:
        raise ValueError('max_queue must be positive when provided')
    with printer._lock:
        printer._max_queue = max_queue


def _resolve_color(color: Optional[str]) -> Optional[str]:
    if color is None:
        return None
    if not isinstance(color, str):
        raise TypeError(f'Parameter color should be str but got {type(color)}')
    spec = color.strip()
    if not spec:
        return None
    lower = spec.lower()
    rgb: Optional[Tuple[int, int, int]]
    if lower in _NAMED_COLORS:
        rgb = _NAMED_COLORS[lower]
    else:
        rgb = _parse_hex_color(spec)
    if rgb is None:
        return None
    return f'\033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m'


def _parse_hex_color(spec: str) -> Tuple[int, int, int]:
    token = spec[1:] if spec.startswith('#') else spec
    if len(token) != 6:
        raise ValueError(
            f"Hex color must be 6 characters like '#RRGGBB': {spec}"
        )
    try:
        value = int(token, 16)
    except ValueError as exc:
        raise ValueError(
            f"Hex color must be 6 characters like '#RRGGBB': {spec}"
        ) from exc
    r = (value >> 16) & 0xFF
    g = (value >> 8) & 0xFF
    b = value & 0xFF
    return r, g, b


def _should_print_directly(print_interval: float) -> bool:
    if print_interval != 0:
        return False
    if getattr(sys, 'ps1', None):
        return True
    return bool(getattr(sys, 'flags', None) and sys.flags.interactive)


def main():
    def demo_print(test_code: str) -> None:
        wicked_print(f'Testing {test_code}......', end='')
        time.sleep(0.5)
        wicked_print(' Complete.', color='#FF0000')
    for _ in range(3):
        demo_print('A')
        demo_print('B')
        demo_print('C')
        wicked_print('Test Session Completed.', color='white',
                     print_interval=0.05)
        wicked_print('-' * 32, print_interval=0, color='#808080')
        wicked_print_flush()
    wicked_print('\n\n' + '-' * 32, print_interval=0, color='#005800')


if __name__ == '__main__':
    main()
