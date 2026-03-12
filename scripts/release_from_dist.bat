@echo off
setlocal
pushd "%~dp0.."

powershell -NoProfile -ExecutionPolicy Bypass -File scripts\release_from_dist.ps1 %*
set "EXITCODE=%ERRORLEVEL%"

popd
exit /b %EXITCODE%
