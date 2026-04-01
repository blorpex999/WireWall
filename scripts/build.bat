@echo off
setlocal
pushd "%~dp0.."

call scripts\common_env.bat
if errorlevel 1 (
  popd
  exit /b 1
)

if not exist .venv (
  %WIREWALL_PYTHON% -m venv .venv
)

call .venv\Scripts\activate
python scripts\check_runtime.py --require-python 3.11 --require-qt
if errorlevel 1 (
  popd
  exit /b 1
)

python -m pip install -r requirements-dev.txt
if errorlevel 1 (
  popd
  exit /b 1
)

python scripts\build_version_info.py
if errorlevel 1 (
  popd
  exit /b 1
)

set "WIREWALL_BUILD_ROOT=%LOCALAPPDATA%\WireWallBuilder"
if not defined LOCALAPPDATA set "WIREWALL_BUILD_ROOT=%TEMP%\WireWallBuilder"
set "PYI_WORKPATH=%WIREWALL_BUILD_ROOT%\pyinstaller-work"
if not exist "%WIREWALL_BUILD_ROOT%" mkdir "%WIREWALL_BUILD_ROOT%" >nul 2>nul

python -m PyInstaller --clean --noconfirm --workpath "%PYI_WORKPATH%" wirewall.spec
if errorlevel 1 (
  popd
  exit /b 1
)

if not exist "dist\WireWall\WireWall.exe" (
  echo Build incomplet: dist\WireWall\WireWall.exe introuvable.
  popd
  exit /b 1
)

echo Build WireWall termine: dist\WireWall\WireWall.exe
popd
exit /b 0
