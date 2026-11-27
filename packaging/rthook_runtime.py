"""PyInstaller runtime hook for EpitopeRank (ESM-2 Desktop).

In ``console=False`` (windowed ``runw.exe``) builds on Windows, ``sys.stdout``
and ``sys.stderr`` are ``None`` when launched from Explorer, which crashes
libraries that call ``sys.stderr.isatty()`` or ``print()`` (such as Uvicorn's
default logging formatter and ``multiprocessing``). Redirect missing standard
streams to ``os.devnull`` before any application or child-process code runs.
"""

import io
import os
import sys
from pathlib import Path

if sys.stdout is None:
    try:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    except OSError:
        sys.stdout = io.StringIO()

if sys.stderr is None:
    try:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")
    except OSError:
        sys.stderr = io.StringIO()

if getattr(sys, "frozen", False):
    try:
        exe_dir = Path(sys.executable).resolve().parent
        os.environ.setdefault(
            "MPLCONFIGDIR", str(exe_dir / "epitoperank_runtime" / ".mplcache")
        )
    except Exception:  # noqa: BLE001
        pass
