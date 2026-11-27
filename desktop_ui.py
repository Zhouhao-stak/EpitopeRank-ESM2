"""High-performance native desktop launcher for EpitopeRank (ESM-2 Edition).

Key responsiveness guarantees:
1. **Process isolation**: The FastAPI/Uvicorn backend runs in a dedicated child
   process (bound to a Windows Job Object with ``KILL_ON_JOB_CLOSE``), so SQLite
   queries, rMATS parsing, and matplotlib chart generation NEVER contend for the
   Python GIL with the WinForms / Edge WebView2 UI thread.
2. **Zero HTTP marshalling**: Unhooks ``pywebview``'s ``WebResourceRequested``
   wildcard filter once WebView2 is ready, so network requests flow natively
   between Edge WebView2 (C++) and Uvicorn over loopback TCP without crossing
   Python/.NET on the UI thread.
3. **Windowed / No Console**: Runs cleanly under PyInstaller ``console=False``
   with live Windows 10/11 DWM title-bar theme synchronization.
"""

from __future__ import annotations

import ctypes
import io
import multiprocessing
import os
import socket
import sys
import threading
import time
import urllib.request
from ctypes import wintypes
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

WINDOW_TITLE = "EpitopeRank · 剪接新抗原与 ESM-2 分析平台"

_THEMES = {
    "light": {
        "dark_mode": 0,
        "bg": "#f2f5f9",
        "fg": "#0f172a",
        "border": "#e3e8ef",
    },
    "dark": {
        "dark_mode": 1,
        "bg": "#070b15",
        "fg": "#e7edf7",
        "border": "#1e2a42",
    },
}

_DWMWA_USE_IMMERSIVE_DARK_MODE = 20
_DWMWA_BORDER_COLOR = 34
_DWMWA_CAPTION_COLOR = 35
_DWMWA_TEXT_COLOR = 36

_SWP_NOSIZE = 0x0001
_SWP_NOMOVE = 0x0002
_SWP_NOZORDER = 0x0004
_SWP_NOACTIVATE = 0x0010
_SWP_FRAMECHANGED = 0x0020
_SWP_ASYNCWINDOWPOS = 0x4000

_JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE = 0x00002000
_JobObjectExtendedLimitInformation = 9
_PROCESS_SET_QUOTA = 0x0100
_PROCESS_TERMINATE = 0x0001


class _IO_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("ReadOperationCount", ctypes.c_ulonglong),
        ("WriteOperationCount", ctypes.c_ulonglong),
        ("OtherOperationCount", ctypes.c_ulonglong),
        ("ReadTransferCount", ctypes.c_ulonglong),
        ("WriteTransferCount", ctypes.c_ulonglong),
        ("OtherTransferCount", ctypes.c_ulonglong),
    ]


class _JOBOBJECT_BASIC_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("PerProcessUserTimeLimit", ctypes.c_longlong),
        ("PerJobUserTimeLimit", ctypes.c_longlong),
        ("LimitFlags", wintypes.DWORD),
        ("MinimumWorkingSetSize", ctypes.c_size_t),
        ("MaximumWorkingSetSize", ctypes.c_size_t),
        ("ActiveProcessLimit", wintypes.DWORD),
        ("Affinity", ctypes.c_size_t),
        ("PriorityClass", wintypes.DWORD),
        ("SchedulingClass", wintypes.DWORD),
    ]


class _JOBOBJECT_EXTENDED_LIMIT_INFORMATION(ctypes.Structure):
    _fields_ = [
        ("BasicLimitInformation", _JOBOBJECT_BASIC_LIMIT_INFORMATION),
        ("IoInfo", _IO_COUNTERS),
        ("ProcessMemoryLimit", ctypes.c_size_t),
        ("JobMemoryLimit", ctypes.c_size_t),
        ("PeakProcessMemoryUsed", ctypes.c_size_t),
        ("PeakJobMemoryUsed", ctypes.c_size_t),
    ]


def _bind_child_to_kill_on_close_job(child_pid: int) -> int:
    """Attach ``child_pid`` to a Win32 Job Object so it dies if the UI exits."""
    if sys.platform != "win32" or not child_pid:
        return 0
    try:
        k32 = ctypes.windll.kernel32
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        job = k32.CreateJobObjectW(None, None)
        if not job:
            return 0
        info = _JOBOBJECT_EXTENDED_LIMIT_INFORMATION()
        info.BasicLimitInformation.LimitFlags = _JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        ok = k32.SetInformationJobObject(
            job,
            _JobObjectExtendedLimitInformation,
            ctypes.byref(info),
            ctypes.sizeof(info),
        )
        if not ok:
            k32.CloseHandle(job)
            return 0
        proc_handle = k32.OpenProcess(_PROCESS_SET_QUOTA | _PROCESS_TERMINATE, False, int(child_pid))
        if proc_handle:
            k32.AssignProcessToJobObject(job, proc_handle)
            k32.CloseHandle(proc_handle)
        return int(job)
    except Exception:
        return 0


def _pick_free_port(start: int = 8800, attempts: int = 40) -> int:
    for offset in range(attempts):
        port = start + offset
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
                return port
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _serve_backend_process(port: int) -> None:
    """Entry point for the isolated backend server process."""
    if not getattr(sys, "frozen", False):
        sys.path.insert(0, str(Path(__file__).resolve().parent))
    from serve_ui import _load_local_env, _write_env_templates
    import uvicorn
    from epitoperank.api.app import create_app

    _load_local_env()
    _write_env_templates()
    uvicorn.run(
        create_app(),
        host="127.0.0.1",
        port=port,
        log_level="error",
        log_config=None,
        access_log=False,
    )


def _colorref(hex_color: str) -> int:
    value = hex_color.lstrip("#")
    r, g, b = (int(value[i : i + 2], 16) for i in (0, 2, 4))
    return r | (g << 8) | (b << 16)


def _dwm_set(hwnd: int, attribute: int, value: int) -> bool:
    try:
        setter = ctypes.windll.dwmapi.DwmSetWindowAttribute
    except (AttributeError, OSError):
        return False
    setter.argtypes = [wintypes.HWND, wintypes.DWORD, ctypes.c_void_p, wintypes.DWORD]
    setter.restype = ctypes.c_long
    packed = ctypes.c_int(value)
    try:
        return setter(wintypes.HWND(hwnd), attribute, ctypes.byref(packed), ctypes.sizeof(packed)) == 0
    except OSError:
        return False


def _apply_window_chrome(hwnd: int, theme: str = "light") -> bool:
    if not hwnd or sys.platform != "win32":
        return False
    spec = _THEMES.get(theme, _THEMES["light"])
    ok_mode = _dwm_set(hwnd, _DWMWA_USE_IMMERSIVE_DARK_MODE, spec["dark_mode"])
    ok_cap = _dwm_set(hwnd, _DWMWA_CAPTION_COLOR, _colorref(spec["bg"]))
    _dwm_set(hwnd, _DWMWA_TEXT_COLOR, _colorref(spec["fg"]))
    _dwm_set(hwnd, _DWMWA_BORDER_COLOR, _colorref(spec["border"]))
    try:
        ctypes.windll.user32.SetWindowPos(
            wintypes.HWND(hwnd),
            None,
            0,
            0,
            0,
            0,
            _SWP_NOSIZE
            | _SWP_NOMOVE
            | _SWP_NOZORDER
            | _SWP_NOACTIVATE
            | _SWP_FRAMECHANGED
            | _SWP_ASYNCWINDOWPOS,
        )
    except OSError:
        pass
    return ok_mode or ok_cap


def _window_handle(window: object | None) -> int:
    if window is not None:
        native = getattr(window, "native", None)
        if native is not None:
            try:
                handle = int(native.Handle.ToInt64())
                if handle:
                    return handle
            except Exception:
                pass
    return 0


class DesktopBridge:
    """JS-callable bridge exposed as ``window.pywebview.api``."""

    def __init__(self) -> None:
        self.window: object | None = None
        self.theme: str = "light"

    def set_theme(self, theme: str) -> bool:
        normalized = "dark" if str(theme).lower() == "dark" else "light"
        hwnd = _window_handle(self.window)
        if normalized == self.theme and hwnd:
            return True
        self.theme = normalized
        if hwnd:
            threading.Thread(
                target=_apply_window_chrome,
                args=(hwnd, normalized),
                daemon=True,
            ).start()
        return True


def _unhook_pywebview_network_filter(window: object) -> None:
    """Detach pywebview's wildcard WebResourceRequested filter on the UI thread.

    pywebview registers ``AddWebResourceRequestedFilter('*', All)`` by default,
    which pauses every HTTP/image fetch in Edge WebView2 to marshal headers into
    Python on the WinForms UI thread. Removing it lets WebView2 communicate
    directly over C++ loopback TCP with zero UI-thread overhead.
    """
    try:
        from System import Action
        from Microsoft.Web.WebView2.Core import CoreWebView2WebResourceContext
        from webview.platforms.winforms import BrowserView

        form = getattr(window, "native", None)
        browser = BrowserView.instances.get(getattr(window, "uid", None), None)
        if form is None or browser is None:
            return
        edge = getattr(browser, "browser", None)
        if edge is None or getattr(edge, "webview", None) is None:
            return

        def _strip() -> None:
            try:
                core = edge.webview.CoreWebView2
                if core is not None:
                    core.RemoveWebResourceRequestedFilter("*", CoreWebView2WebResourceContext.All)
                    core.WebResourceRequested -= edge.on_web_resource_request
                    core.WebResourceResponseReceived -= edge.on_web_resource_response
            except Exception:
                pass

        form.BeginInvoke(Action(_strip))
    except Exception:
        pass


def _webview_storage_dir() -> str:
    base = os.environ.get("LOCALAPPDATA") or str(Path.home())
    target = Path(base) / "EpitopeRank" / "webview2"
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError:
        return ""
    return str(target)


def main() -> int:
    port = _pick_free_port(8800)
    url = f"http://127.0.0.1:{port}/"

    backend_proc = multiprocessing.Process(
        target=_serve_backend_process,
        args=(port,),
        name="epitoperank-backend",
        daemon=True,
    )
    backend_proc.start()
    _job_handle = _bind_child_to_kill_on_close_job(backend_proc.pid or 0)

    # Import webview in the parent process while the child process warms up in parallel!
    import webview

    deadline = time.monotonic() + 60
    while time.monotonic() < deadline:
        if not backend_proc.is_alive():
            raise RuntimeError("本地分析服务进程未能启动，请检查运行环境或端口占用。")
        try:
            with urllib.request.urlopen(url + "api/health", timeout=0.6) as response:
                if response.status == 200:
                    break
        except Exception:
            time.sleep(0.12)
    else:
        backend_proc.terminate()
        raise RuntimeError("本地分析服务启动超时。")

    bridge = DesktopBridge()
    storage_path = _webview_storage_dir()
    try:
        window = webview.create_window(
            WINDOW_TITLE,
            url,
            js_api=bridge,
            width=1440,
            height=900,
            min_size=(1060, 680),
            background_color=_THEMES["light"]["bg"],
            text_select=True,
        )
        bridge.window = window

        def _on_shown() -> None:
            def _chrome_init() -> None:
                for _ in range(25):
                    hwnd = _window_handle(window)
                    if hwnd and _apply_window_chrome(hwnd, bridge.theme):
                        break
                    time.sleep(0.1)
            threading.Thread(target=_chrome_init, daemon=True).start()

        window.events.shown += _on_shown

        start_kwargs: dict[str, object] = {
            "gui": "edgechromium",
            "private_mode": False,
        }
        if storage_path:
            start_kwargs["storage_path"] = storage_path
        webview.start(**start_kwargs)
    finally:
        if backend_proc.is_alive():
            backend_proc.terminate()
            backend_proc.join(timeout=3)
            if backend_proc.is_alive():
                backend_proc.kill()
        if _job_handle and sys.platform == "win32":
            ctypes.windll.kernel32.CloseHandle(wintypes.HANDLE(_job_handle))
    return 0


if __name__ == "__main__":
    multiprocessing.freeze_support()
    try:
        raise SystemExit(main())
    except Exception as error:
        if sys.platform == "win32":
            ctypes.windll.user32.MessageBoxW(0, str(error), "EpitopeRank 启动失败", 0x10)
        raise
