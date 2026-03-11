@echo off
setlocal
set "WIREWALL_PYTHON="

where py >nul 2>nul
if not errorlevel 1 (
  py -3.11 -c "import sys; print(sys.version)" >nul 2>nul
  if not errorlevel 1 (
    set "WIREWALL_PYTHON=py -3.11"
  )
)

if not defined WIREWALL_PYTHON (
  python scripts\check_runtime.py --require-python 3.11 >nul 2>nul
  if errorlevel 1 (
    echo Python 3.11 est requis pour WireWall. Installez Python 3.11 puis relancez le script.
    exit /b 1
  )
  set "WIREWALL_PYTHON=python"
)

endlocal & set "WIREWALL_PYTHON=%WIREWALL_PYTHON%"
exit /b 0
