@echo off
setlocal
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0check_target_prereqs.ps1" %*
set "EXIT_CODE=%ERRORLEVEL%"
echo.
pause
exit /b %EXIT_CODE%
