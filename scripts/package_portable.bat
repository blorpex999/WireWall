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
set "RELEASE_DIR=%CD%\release"
set "PORTABLE_NAME=WireWall-%WIREWALL_VERSION%-win64-portable"
set "PORTABLE_STAGE=%RELEASE_DIR%\%PORTABLE_NAME%"
set "PORTABLE_ZIP=%RELEASE_DIR%\%PORTABLE_NAME%.zip"

if not exist "%RELEASE_DIR%" mkdir "%RELEASE_DIR%"
if exist "%PORTABLE_ZIP%" del /f /q "%PORTABLE_ZIP%"
if exist "%PORTABLE_STAGE%" rmdir /s /q "%PORTABLE_STAGE%"
mkdir "%PORTABLE_STAGE%"

robocopy "dist\WireWall" "%PORTABLE_STAGE%" /E >nul
if errorlevel 8 (
  echo Echec de copie du bundle portable.
  popd
  exit /b 1
)

mkdir "%PORTABLE_STAGE%\docs" >nul 2>nul
mkdir "%PORTABLE_STAGE%\tools" >nul 2>nul
copy /y "README.md" "%PORTABLE_STAGE%\README.md" >nul
copy /y "CHANGELOG.md" "%PORTABLE_STAGE%\CHANGELOG.md" >nul
copy /y "config.example.json" "%PORTABLE_STAGE%\config.example.json" >nul
copy /y "VERSION" "%PORTABLE_STAGE%\VERSION" >nul
robocopy "docs" "%PORTABLE_STAGE%\docs" /E >nul
if errorlevel 8 (
  echo Echec de copie de la documentation portable.
  popd
  exit /b 1
)
copy /y "scripts\check_target_prereqs.bat" "%PORTABLE_STAGE%\tools\check_target_prereqs.bat" >nul
copy /y "scripts\check_target_prereqs.ps1" "%PORTABLE_STAGE%\tools\check_target_prereqs.ps1" >nul
copy /y "scripts\setup_ai.bat" "%PORTABLE_STAGE%\tools\setup_ai.bat" >nul
copy /y "scripts\check_ollama.ps1" "%PORTABLE_STAGE%\tools\check_ollama.ps1" >nul
copy /y "scripts\install_ollama.ps1" "%PORTABLE_STAGE%\tools\install_ollama.ps1" >nul
copy /y "scripts\install_ollama_model.ps1" "%PORTABLE_STAGE%\tools\install_ollama_model.ps1" >nul
copy /y "scripts\setup_ai.ps1" "%PORTABLE_STAGE%\tools\setup_ai.ps1" >nul

powershell -NoProfile -Command "Compress-Archive -Path '%PORTABLE_STAGE%\*' -DestinationPath '%PORTABLE_ZIP%' -Force"
if errorlevel 1 (
  echo Echec de creation de l'archive portable.
  popd
  exit /b 1
)

echo Package portable genere : %PORTABLE_ZIP%
popd
exit /b 0
