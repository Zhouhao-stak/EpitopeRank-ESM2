@echo off
cd /d "%~dp0..\.."
REM EpitopeRank ESM-2 Windowed Desktop Build Script - Outputs to dist/
REM Usage: scripts\windows\build.bat

setlocal enabledelayedexpansion

echo ========================================
echo   EpitopeRank ESM-2 Desktop Build
echo ========================================
echo.

set "PY_EXE="
if exist "venv\Scripts\python.exe" set "PY_EXE=venv\Scripts\python.exe"
if not defined PY_EXE if exist "..\SpliceGAIP\venv\Scripts\python.exe" set "PY_EXE=..\SpliceGAIP\venv\Scripts\python.exe"
if not defined PY_EXE (
    echo ERROR: Virtual environment with PyInstaller and pywebview not found!
    exit /b 1
)

echo [1/4] Cleaning previous builds...
if exist "packaging\build-temp" rmdir /s /q "packaging\build-temp"
for /d /r "epitoperank" %%D in (__pycache__) do @if exist "%%D" rmdir /s /q "%%D"
if exist "__pycache__" rmdir /s /q "__pycache__"
echo       Done.
echo.

echo [2/4] Building windowed EXE with PyInstaller (%PY_EXE%)...
"%PY_EXE%" -m PyInstaller packaging\EpitopeRank-Desktop-OneFile.spec ^
    --distpath dist ^
    --workpath packaging\build-temp ^
    --noconfirm
if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    exit /b 1
)
echo       Done.
echo.

echo [3/4] Copying configuration files...
if exist ".env.example" (
    copy /Y ".env.example" "dist\.env.example" >nul 2>&1
)
if exist ".env" (
    copy /Y ".env" "dist\.env" >nul 2>&1
    echo       Copied .env to dist\.env
)
echo       Done.
echo.

echo [4/4] Verifying output...
if exist "dist\EpitopeRank-Desktop-ESM2.exe" (
    for %%I in ("dist\EpitopeRank-Desktop-ESM2.exe") do set SIZE=%%~zI
    set /a SIZE_MB=!SIZE! / 1048576
    echo       SUCCESS!
    echo ========================================
    echo   Location: dist\EpitopeRank-Desktop-ESM2.exe
    echo   EXE Size: !SIZE_MB! MB
    echo ========================================
) else (
    echo ERROR: dist\EpitopeRank-Desktop-ESM2.exe not found!
    exit /b 1
)
