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

set /p WIREWALL_VERSION=<VERSION
set "WIREWALL_DIST_DIR=%CD%\dist\WireWall"
set "WIREWALL_RELEASE_DIR=%CD%\release"

if not exist "%WIREWALL_RELEASE_DIR%" mkdir "%WIREWALL_RELEASE_DIR%"
if not exist "%WIREWALL_DIST_DIR%\WireWall.exe" (
  echo Build incomplet: %WIREWALL_DIST_DIR%\WireWall.exe introuvable.
  popd
  exit /b 1
)

set "ISCC_BIN=%ISCC_EXE%"
if not defined ISCC_BIN if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC_BIN=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if not defined ISCC_BIN if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC_BIN=%ProgramFiles%\Inno Setup 6\ISCC.exe"

if not defined ISCC_BIN (
  echo Inno Setup 6 n'est pas installe sur ce poste.
  echo Installez ISCC.exe ou definissez la variable d'environnement ISCC_EXE.
  popd
  exit /b 1
)

"%ISCC_BIN%" ^
  /DAppVersion=%WIREWALL_VERSION% ^
  /DSourceDist=%WIREWALL_DIST_DIR% ^
  /DReleaseDir=%WIREWALL_RELEASE_DIR% ^
  installer\WireWall.iss
if errorlevel 1 (
  echo Echec de compilation de l'installateur Inno Setup.
  popd
  exit /b 1
)

echo Installateur genere dans %WIREWALL_RELEASE_DIR%
popd
exit /b 0
