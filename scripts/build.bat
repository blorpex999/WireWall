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
python scripts\check_runtime.py --require-python 3.11 --require-tk
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

python -m PyInstaller --clean --noconfirm wirewall.spec
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
