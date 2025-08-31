
# G-Prophet 启动指南

## 🚀 推荐启动方式（已修复并行启动问题）

### 方案1：快速启动脚本（推荐）✅
```powershell
.\quick_start.ps1
```

**特点**：
- ✅ 自动检测环境和依赖
- ✅ 智能端口清理
- ✅ 健康检查和错误诊断
- ✅ 自动打开浏览器
- ✅ 解决了原并行启动的窗口关闭问题

### 方案2：诊断模式
如果遇到问题，先运行诊断：
```powershell
.\diagnose.ps1
```

### 方案3：原并行启动（已知问题）⚠️
```powershell
# 此方案可能遇到 "forrtl: error (200): program aborting due to window-CLOSE event" 错误
# 建议使用方案1替代
```

### 方案2：API优先启动
$env:DEVICE='auto'; $env:FAST_CPU_MODE='0'; $env:CPU_THREADS='24'; New-Item -ItemType Directory -Force -Path 'volumes/logs' | Out-Null; if (Test-Path .\.venv\Scripts\python.exe) { $py = ".\.venv\Scripts\python.exe" } else { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }; if (-not $py) { Write-Error 'python not found'; exit }; foreach ($p in 8000,8501) { $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { try { Stop-Process -Id $c.OwningProcess -Force } catch {} } }; Write-Host "启动 API 服务（前台）..." -ForegroundColor Green; & $py -m uvicorn app.api:app --host 0.0.0.0 --port 8000 2>&1 | Tee-Object -FilePath volumes\logs\api.log

### 方案3：Streamlit优先启动
$env:DEVICE='auto'; $env:FAST_CPU_MODE='0'; $env:CPU_THREADS='24'; New-Item -ItemType Directory -Force -Path 'volumes/logs' | Out-Null; if (Test-Path .\.venv\Scripts\python.exe) { $py = ".\.venv\Scripts\python.exe" } else { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }; if (-not $py) { Write-Error 'python not found'; exit }; foreach ($p in 8000,8501) { $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { try { Stop-Process -Id $c.OwningProcess -Force } catch {} } }; Write-Host "启动 Streamlit 服务（前台）..." -ForegroundColor Green; & $py -m streamlit run app/streamlit_app.py --server.port=8501 --server.address=0.0.0.0 2>&1 | Tee-Object -FilePath volumes\logs\streamlit.log


# 一键启动（自动落盘日志）

说明：以下两段命令将自动终止 8000/8501 上的旧进程，最小化启动 API 与前端，并将日志写入 volumes\logs\。

- API 日志：volumes\logs\api.log
- 前端日志：volumes\logs\streamlit.log 

确保已激活 .venv 并安装依赖：
- python -m venv .venv
- .venv\Scripts\activate
- pip install -r app/requirements.txt

## GPU 优先启动
$env:DEVICE='auto'; $env:FAST_CPU_MODE='0'; $env:CPU_THREADS='24'; New-Item -ItemType Directory -Force -Path 'volumes/logs' | Out-Null; if (Test-Path .\.venv\Scripts\python.exe) { $py = ".\.venv\Scripts\python.exe" } else { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }; if (-not $py) { Write-Error 'python not found'; exit }; foreach ($p in 8000,8501) { $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { try { Stop-Process -Id $c.OwningProcess -Force } catch {} } }; Start-Process -FilePath $py -ArgumentList '-m','uvicorn','app.api:app','--host','0.0.0.0','--port','8000' -RedirectStandardOutput 'volumes/logs/api.log' -RedirectStandardError 'volumes/logs/api.err.log' -WindowStyle Minimized; Start-Process -FilePath $py -ArgumentList '-m','streamlit','run','app/streamlit_app.py','--server.port=8501','--server.address=0.0.0.0' -RedirectStandardOutput 'volumes/logs/streamlit.log' -RedirectStandardError 'volumes/logs/streamlit.err.log' -WindowStyle Minimized; Start-Process 'http://localhost:8501'

## CPU 启动
$env:DEVICE='cpu'; $env:FAST_CPU_MODE='0'; $env:CPU_THREADS='24'; New-Item -ItemType Directory -Force -Path 'volumes/logs' | Out-Null; if (Test-Path .\.venv\Scripts\python.exe) { $py = ".\.venv\Scripts\python.exe" } else { $py = (Get-Command python -ErrorAction SilentlyContinue).Source }; if (-not $py) { Write-Error 'python not found'; exit }; foreach ($p in 8000,8501) { $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { try { Stop-Process -Id $c.OwningProcess -Force } catch {} } }; Start-Process -FilePath $py -ArgumentList '-m','uvicorn','app.api:app','--host','0.0.0.0','--port','8000' -RedirectStandardOutput 'volumes/logs/api.log' -RedirectStandardError 'volumes/logs/api.err.log' -WindowStyle Minimized; Start-Process -FilePath $py -ArgumentList '-m','streamlit','run','app/streamlit_app.py','--server.port=8501','--server.address=0.0.0.0' -RedirectStandardOutput 'volumes/logs/streamlit.log' -RedirectStandardError 'volumes/logs/streamlit.err.log' -WindowStyle Minimized; Start-Process 'http://localhost:8501'



## 实用命令

### 查看后台任务状态
Get-Job

### 查看实时日志输出
Get-Job | Receive-Job -Keep

### 停止所有后台服务
Get-Job | Stop-Job; Get-Job | Remove-Job

### 单独查看日志文件
Get-Content volumes\logs\api.log -Tail 20 -Wait
Get-Content volumes\logs\streamlit.log -Tail 20 -Wait
