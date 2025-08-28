@echo off
setlocal enableextensions enabledelayedexpansion

REM Visual Studio 2022 Build Tools environment
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\Common7\Tools\VsDevCmd.bat" -arch=amd64
if errorlevel 1 (
  echo [ERROR] Failed to initialize VS Dev environment
  exit /b 1
)

REM CUDA 13.0 Toolkit paths
set "CUDA_PATH=C:\Program Files\NVIDIA GPU Computing Toolkit\CUDA\v13.0"
set "PATH=%CUDA_PATH%\bin;%CUDA_PATH%\libnvvp;%PATH%"

REM PyTorch build config for RTX 5090 (sm_120)
set "TORCH_CUDA_ARCH_LIST=12.0"
set "USE_CUDA=1"
set "MAX_JOBS=16"

REM Use Ninja generator to avoid VS CUDA toolset dependency; point CMake to nvcc directly
set "CMAKE_GENERATOR=Ninja"
set "USE_NINJA=1"
set "CMAKE_CUDA_COMPILER=%CUDA_PATH%\bin\nvcc.exe"

cd /d %~dp0\..\

if not exist .deps\pytorch (
  echo [ERROR] .deps\pytorch not found. Clone repo first.
  exit /b 1
)

cd .deps\pytorch

REM Clean previous CMake caches to avoid generator conflicts
if exist CMakeCache.txt del /f /q CMakeCache.txt
if exist CMakeFiles rmdir /s /q CMakeFiles
if exist build rmdir /s /q build
if exist cmake_build rmdir /s /q cmake_build

REM Ensure repo is clean of cached CMake artifacts
git reset --hard HEAD
git clean -fdx

REM Use project venv python explicitly
set "PYTHON=..\..\.venv\Scripts\python.exe"

"%PYTHON%" --version || exit /b 1
"%PYTHON%" -m pip --version || exit /b 1
"%PYTHON%" -m pip install -q ninja packaging || exit /b 1

"%PYTHON%" setup.py clean

"%PYTHON%" setup.py develop
if errorlevel 1 (
  echo [ERROR] PyTorch develop build failed
  exit /b 1
)

endlocal
exit /b 0

