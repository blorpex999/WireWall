@echo off
setlocal
pushd "%~dp0.."

call scripts\test.bat
if errorlevel 1 (
  popd
  exit /b 1
)

call scripts\build.bat
if errorlevel 1 (
  popd
  exit /b 1
)

if not exist "dist\WireWall\WireWall.exe" (
  echo Release check en echec: dist\WireWall\WireWall.exe introuvable.
  popd
  exit /b 1
)

where /r "dist\WireWall" libusb-1.0.dll >nul 2>nul
if errorlevel 1 (
  echo Release check en echec: libusb-1.0.dll introuvable dans dist\WireWall.
  popd
  exit /b 1
)

echo Release check OK.
popd
exit /b 0
