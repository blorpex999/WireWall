@echo off
setlocal
pushd "%~dp0.."

set /p WIREWALL_VERSION=<VERSION

if not exist "dist\WireWall\WireWall.exe" (
  echo Artefact manquant : dist\WireWall\WireWall.exe
  popd
  exit /b 1
)

where /r "dist\WireWall" libusb-1.0.dll >nul 2>nul
if errorlevel 1 (
  echo Artefact manquant : libusb-1.0.dll dans dist\WireWall
  popd
  exit /b 1
)

if not exist "release\WireWall-%WIREWALL_VERSION%-win64-portable.zip" (
  echo Artefact manquant : release\WireWall-%WIREWALL_VERSION%-win64-portable.zip
  popd
  exit /b 1
)

if not exist "release\WireWall-Setup-%WIREWALL_VERSION%.exe" (
  if not exist "release\WireWall-Setup-%WIREWALL_VERSION%-full.exe" (
    echo Artefact manquant : installeur release standard ou full.
    popd
    exit /b 1
  )
)

if not exist "release\WireWall-%WIREWALL_VERSION%-manifest.json" (
  echo Artefact manquant : manifest de release
  popd
  exit /b 1
)

if not exist "release\SHA256SUMS.txt" (
  echo Artefact manquant : release\SHA256SUMS.txt
  popd
  exit /b 1
)

echo Artefacts de release valides.
popd
exit /b 0
