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

set "WIREWALL_PYTHON_EXE=%CD%\.venv\Scripts\python.exe"
set "WIREWALL_PYTHONW_EXE=%CD%\.venv\Scripts\pythonw.exe"
if exist "%WIREWALL_PYTHONW_EXE%" set "WIREWALL_PYTHON_EXE=%WIREWALL_PYTHONW_EXE%"
set "WIREWALL_ENTRY=%CD%\main.py"
set "WIREWALL_ARGS=\"%WIREWALL_ENTRY%\" %*"
set "WIREWALL_WORKDIR=%CD%"

powershell -NoProfile -Command "Start-Process -FilePath $env:WIREWALL_PYTHON_EXE -ArgumentList $env:WIREWALL_ARGS -WorkingDirectory $env:WIREWALL_WORKDIR -Verb RunAs"
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
