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

set "WIREWALL_PYTHONW=%CD%\.venv\Scripts\pythonw.exe"
if exist "%WIREWALL_PYTHONW%" (
  "%WIREWALL_PYTHONW%" main.py --replace-existing
) else (
  python main.py --replace-existing
)
set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
