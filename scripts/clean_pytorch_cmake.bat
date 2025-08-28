@echo off
setlocal enableextensions
cd /d %~dp0\..\
if not exist .deps\pytorch (
  echo [.cleanup] .deps\pytorch not found
  exit /b 0
)
echo [.cleanup] Removing CMake cache and build dirs under .deps\pytorch ...
pushd .deps\pytorch
for /r %%F in (CMakeCache.txt) do (
  echo Deleting %%F
  del /f /q "%%F"
)
for /r %%D in (CMakeFiles) do (
  if exist "%%D" (
    echo Removing dir %%D
    rmdir /s /q "%%D"
  )
)
if exist build rmdir /s /q build
if exist cmake_build rmdir /s /q cmake_build
popd
echo [.cleanup] Done
endlocal
exit /b 0

