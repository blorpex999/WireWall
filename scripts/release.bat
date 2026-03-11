@echo off
setlocal
pushd "%~dp0.."

call scripts\test.bat
if errorlevel 1 (
  popd
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Environnement Python introuvable apres les tests.
  popd
  exit /b 1
)
set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"

"%VENV_PYTHON%" scripts\check_release_consistency.py
if errorlevel 1 (
  popd
  exit /b 1
)

call scripts\package_portable.bat
if errorlevel 1 (
  popd
  exit /b 1
)

call scripts\build_installer.bat
if errorlevel 1 (
  popd
  exit /b 1
)

"%VENV_PYTHON%" scripts\write_release_manifest.py
if errorlevel 1 (
  popd
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\write_release_hashes.ps1
if errorlevel 1 (
  popd
  exit /b 1
)

call scripts\validate_artifacts.bat
if errorlevel 1 (
  popd
  exit /b 1
)

echo Release WireWall complete.
popd
exit /b 0
