@echo off
setlocal
set PYEXE=d:\Docker-Devops\Aigc\Kronos\.venv-gpu\Scripts\python.exe
if not exist "%PYEXE%" (
  echo [FAIL] Python not found at %PYEXE%
  exit /b 1
)
"%PYEXE%" tests\tmp_check.py > out_gpu_check.txt 2>&1
 type out_gpu_check.txt
endlocal

