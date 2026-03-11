@echo off
setlocal
pushd "%~dp0.."

for %%D in (
  build
  dist
  release
  .pytest_cache
  .wirewall-runtime
  .wirewall-pytest-tmp
  wirewall_pytest_tmp
  wirewall_test_artifacts
) do (
  if exist "%%D" rmdir /s /q "%%D"
)

for /d /r %%D in (__pycache__) do (
  if exist "%%D" rmdir /s /q "%%D"
)

if exist ".coverage" del /f /q ".coverage"

popd
exit /b 0
