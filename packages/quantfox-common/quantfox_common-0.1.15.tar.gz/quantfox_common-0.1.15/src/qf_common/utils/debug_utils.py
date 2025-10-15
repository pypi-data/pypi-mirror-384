# quant_debug.py
import logging, sys, os, io, json, time, textwrap
from contextlib import contextmanager
from typing import Any

try:
    import pandas as pd
except ImportError:
    pd = None

try:
    import numpy as np
except ImportError:
    np = None


def setup_quant_logging(level=logging.INFO, file_path="/tmp/quant_debug.log", use_emoji=True):
    """Configure le logger quant-friendly"""
    log = logging.getLogger()
    log.setLevel(level)
    for h in list(log.handlers):
        log.removeHandler(h)

    fmt = "%(asctime)s | %(levelname)-8s | %(message)s"
    datefmt = "%H:%M:%S"
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(fmt, datefmt))
    log.addHandler(handler)

    # fichier brut
    fh = logging.FileHandler(file_path, mode="w")
    fh.setFormatter(logging.Formatter(fmt, datefmt))
    log.addHandler(fh)

    log._USE_COLOR = sys.stdout.isatty()
    log._USE_EMOJI = use_emoji
    return log


def _stylize(txt, color):
    colors = {
        "cyan": "\033[36m", "magenta": "\033[35m",
        "yellow": "\033[33m", "bold": "\033[1m", "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{txt}{colors['reset']}"


def _fmt(obj, width=120, head=5):
    if pd and isinstance(obj, pd.DataFrame):
        buf = io.StringIO()
        print(f"DataFrame shape={obj.shape}, cols={list(obj.columns[:8])}", file=buf)
        with pd.option_context("display.max_columns", 10, "display.width", width):
            print(obj.head(head), file=buf)
        return buf.getvalue().rstrip()
    if np and isinstance(obj, np.ndarray):
        return f"array shape={obj.shape}, dtype={obj.dtype}, sample={obj.flatten()[:5]}"
    if isinstance(obj, (dict, list, tuple)):
        return json.dumps(obj, indent=2, ensure_ascii=False)[:width]
    return textwrap.fill(str(obj), width)


def dbg(*args, title=None, level=logging.INFO, logger=None, head=5, width=120, **kwargs):
    """debug élégant multi-objets et kwargs"""
    log = logger or logging.getLogger()
    emoji = "🔍" if getattr(log, "_USE_EMOJI", False) else ""
    banner = f"\n{_stylize('═'*10, 'magenta')} {_stylize(title or 'DEBUG', 'bold')} {emoji} {_stylize('═'*10, 'magenta')}"
    log.log(level, banner)

    # positional args
    for i, obj in enumerate(args, 1):
        log.log(level, f"{_stylize(f'[{i}]', 'cyan')} {_fmt(obj, width, head)}")

    # keyword args (nommés)
    for k, v in kwargs.items():
        log.log(level, f"{_stylize(k + ':', 'yellow')} {_fmt(v, width, head)}")

    log.log(level, _stylize("═"*40, "magenta"))


@contextmanager
def dbg_section(name: str, level=logging.INFO, logger=None):
    log = logger or logging.getLogger()
    emoji = "⏱" if getattr(log, "_USE_EMOJI", False) else ""
    start = time.perf_counter()
    log.log(level, f"{_stylize('▶', 'magenta')} {name} {emoji} start")
    try:
        yield
    finally:
        dt = (time.perf_counter() - start) * 1000
        log.log(level, f"{_stylize('◀', 'magenta')} {name} done in {dt:.1f} ms")


def timeit(level=logging.INFO):
    """Décorateur pour log de perf"""
    def deco(f):
        def wrap(*a, **kw):
            t0 = time.perf_counter()
            try:
                return f(*a, **kw)
            finally:
                dt = (time.perf_counter() - t0) * 1000
                logging.log(level, f"⚙️ {f.__name__} took {dt:.1f} ms")
        return wrap
    return deco
