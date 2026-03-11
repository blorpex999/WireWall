@echo off
setlocal
pushd "%~dp0.."

call scripts\build.bat
if errorlevel 1 (
  popd
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo Build incomplet: .venv\Scripts\python.exe introuvable.
  popd
  exit /b 1
)
set "VENV_PYTHON=%CD%\.venv\Scripts\python.exe"

"%VENV_PYTHON%" scripts\check_release_consistency.py
if errorlevel 1 (
  popd
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\fetch_ollama_installer.ps1
if errorlevel 1 (
  echo Echec du telechargement de l'installeur Ollama.
  popd
  exit /b 1
)

set /p WIREWALL_VERSION=<VERSION
set "WIREWALL_DIST_DIR=%CD%\dist\WireWall"
set "WIREWALL_RELEASE_DIR=%CD%\release"
set "OLLAMA_INSTALLER=%CD%\build\third_party\OllamaSetup.exe"

if not exist "%WIREWALL_RELEASE_DIR%" mkdir "%WIREWALL_RELEASE_DIR%"
if not exist "%WIREWALL_DIST_DIR%\WireWall.exe" (
  echo Build incomplet: %WIREWALL_DIST_DIR%\WireWall.exe introuvable.
  popd
  exit /b 1
)
if not exist "%OLLAMA_INSTALLER%" (
  echo Installeur Ollama introuvable: %OLLAMA_INSTALLER%
  popd
  exit /b 1
)

set "ISCC_BIN=%ISCC_EXE%"
if not defined ISCC_BIN if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_BIN=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_BIN if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_BIN=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if not defined ISCC_BIN if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC_BIN=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"

if not defined ISCC_BIN (
  echo Inno Setup 6 n'est pas installe sur ce poste.
  echo Installez ISCC.exe ou definissez la variable d'environnement ISCC_EXE.
  popd
  exit /b 1
)

"%ISCC_BIN%" ^
  /DAppVersion=%WIREWALL_VERSION% ^
  "/DSourceDist=%WIREWALL_DIST_DIR%" ^
  "/DReleaseDir=%WIREWALL_RELEASE_DIR%" ^
  /DBundleOllamaInstaller=1 ^
  "/DOllamaInstallerSource=%OLLAMA_INSTALLER%" ^
  installer\WireWall.iss
if errorlevel 1 (
  echo Echec de compilation de l'installateur full Inno Setup.
  popd
  exit /b 1
)

echo Installateur full genere dans %WIREWALL_RELEASE_DIR%
popd
exit /b 0
