# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller onefile spec for EpitopeRank-Desktop-ESM2.exe (windowed, no console)."""

from PyInstaller.utils.hooks import collect_data_files, collect_submodules
import os

HERE = SPECPATH
ROOT = os.path.dirname(HERE)

_OPTIONAL_DATAS = [
    (os.path.join(ROOT, "config"), "config"),
    (os.path.join(ROOT, ".env.example"), "."),
    (os.path.join(ROOT, "epitoperank", "interface", "opencc-cn2t.js"), "epitoperank/interface"),
    (os.path.join(ROOT, "epitoperank", "interface", "OPENCC-JS-LICENSE.txt"), "epitoperank/interface"),
    (os.path.join(ROOT, "epitoperank", "interface", "OPENCC-DATA-LICENSE.txt"), "epitoperank/interface"),
    (os.path.join(ROOT, "epitoperank", "interface", "OPENCC-NOTICE.txt"), "epitoperank/interface"),
    (os.path.join(ROOT, "epitoperank", "peptide", "reference"), "epitoperank/peptide/reference"),
]
datas = [(src, dst) for src, dst in _OPTIONAL_DATAS if os.path.exists(src)]
datas += collect_data_files("matplotlib")
datas += collect_data_files("reportlab")

hiddenimports = []
for package in (
    "epitoperank",
    "autogen_agentchat",
    "autogen_agentchat.agents",
    "autogen_agentchat.teams",
    "autogen_core",
    "autogen_core.models",
    "autogen_ext",
    "autogen_ext.models",
    "autogen_ext.models.openai",
    "openai",
    "httpx",
    "httpcore",
    "jiter",
    "distro",
    "sniffio",
    "pymed",
    "uvicorn",
    "fastapi",
    "starlette",
    "python_multipart",
    "webview",
    "webview.platforms.winforms",
    "webview.platforms.edgechromium",
    "requests",
):
    try:
        hiddenimports += collect_submodules(package)
    except Exception:
        hiddenimports.append(package)

hiddenimports += [
    "matplotlib.backends.backend_agg",
    "matplotlib.backends.backend_svg",
    "matplotlib.backends.backend_pdf",
    "matplotlib.backends.backend_ps",
    "reportlab",
    "yaml",
    "httptools",
    "watchfiles",
    "websockets",
    "click",
    "dotenv",
    "multipart",
    "email",
    "mimetypes",
    "scipy",
    "scipy.stats",
    "openpyxl",
    "xlrd",
    "epitoperank.report",
    "epitoperank.report.generator",
    "epitoperank.splicing.orf_builder",
    "epitoperank.peptide.binding_tiers",
    "epitoperank.peptide.esm2_client",
    "epitoperank.web_fetch",
]

excludes = [
    "streamlit",
    "pytest",
    "pandas",
    "seaborn",
    "plotly",
    "sqlalchemy",
    "tkinter",
    "PyQt5",
    "PySide2",
    "IPython",
    "notebook",
    "playwright",
    "pyee",
]

block_cipher = None

a = Analysis(
    [os.path.join(ROOT, "desktop_ui.py")],
    pathex=[ROOT],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[os.path.join(HERE, "rthook_runtime.py")],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

_DROP_PREFIXES = ("playwright", "pyee")


def _drop(entries):
    return [
        entry
        for entry in entries
        if not any(
            str(entry[0]).replace("\\", "/").lower() == p
            or str(entry[0]).replace("\\", "/").lower().startswith(p + "/")
            for p in _DROP_PREFIXES
        )
    ]


_FONT_KEEP_EXACT = {
    "dejavusans.ttf", "dejavusans-bold.ttf", "dejavusans-oblique.ttf",
    "dejavusans-boldoblique.ttf", "dejavusansdisplay.ttf",
    "dejavusansmono.ttf", "dejavusansmono-bold.ttf",
}


def _keep_bundled_font(name):
    lowered = name.replace("\\", "/").lower()
    normalized = "/" + lowered.lstrip("/")
    if "/mpl-data/fonts/" not in normalized and "/reportlab/fonts/" not in normalized:
        return True
    base = lowered.rsplit("/", 1)[-1]
    if "/reportlab/fonts/" in normalized:
        return base.endswith(".afm") or base.endswith(".txt")
    if base.endswith((".afm", ".txt", ".map")):
        return True
    if base in _FONT_KEEP_EXACT:
        return True
    if base.startswith("dejavuserif"):
        return False
    return True


a.binaries = _drop(a.binaries)
a.datas = _drop(a.datas)
a.datas = [e for e in a.datas if _keep_bundled_font(str(e[0]))]

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="EpitopeRank-Desktop-ESM2",
    icon=os.path.join(HERE, "icon.ico"),
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
