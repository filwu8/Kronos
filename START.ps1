# G-Prophet Start Script (Stable ASCII Version)
# Modes: auto (default), restart, diagnose
# Usage examples:
#   .\START.ps1
#   .\START.ps1 -Mode restart -Debug -LogLevel DEBUG

param(
    [ValidateSet("auto","restart","diagnose")]
    [string]$Mode = "auto",
    [switch]$Debug,
    [ValidateSet("DEBUG","INFO","WARNING","ERROR","CRITICAL")]
    [string]$LogLevel = "INFO"
)

Write-Host "G-Prophet Starter" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green

# Environment
$env:DEVICE = 'auto'
$env:FAST_CPU_MODE = '0'
$env:CPU_THREADS = '24'
$env:APP_DEBUG = if ($Debug) { '1' } else { '0' }
$env:LOG_LEVEL = $LogLevel.ToUpper()

# Ensure log dir
New-Item -ItemType Directory -Force -Path 'volumes/logs' | Out-Null

# Resolve Python
if (Test-Path .\.venv\Scripts\python.exe) {
    $py = ".\.venv\Scripts\python.exe"
    Write-Host "Virtualenv found" -ForegroundColor Green
} else {
    Write-Host "Virtualenv not found" -ForegroundColor Red
    Write-Host "Create it then install deps:" -ForegroundColor Yellow
    Write-Host "python -m venv .venv" -ForegroundColor Gray
    Write-Host ".venv\Scripts\activate" -ForegroundColor Gray
    Write-Host "pip install -r app/requirements.txt" -ForegroundColor Gray
    exit 1
}

function Stop-AllServices {
    Write-Host "Stopping existing uvicorn/streamlit processes..." -ForegroundColor Yellow
    try {
        $procs = Get-CimInstance Win32_Process | Where-Object {
            $_.Name -like 'python*.exe' -and (
                $_.CommandLine -match 'uvicorn' -or $_.CommandLine -match 'streamlit' -or $_.CommandLine -match 'app.api:app' -or $_.CommandLine -match 'app/streamlit_app.py'
            )
        }
        foreach ($p in $procs) {
            try { Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue; Write-Host ("  Killed PID {0}: {1}" -f $p.ProcessId, $p.CommandLine) -ForegroundColor Gray } catch {}
        }
    } catch {
        # Fallback: kill any python (last resort)
        Get-Process | Where-Object { $_.ProcessName -like '*python*' } | ForEach-Object { try { Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue } catch {} }
    }
    Start-Sleep -Seconds 2
}

function Free-Ports {
    param([int[]]$Ports)
    foreach ($port in $Ports) {
        try {
            $conns = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
            if ($conns) {
                $pids = $conns | Select-Object -ExpandProperty OwningProcess -Unique
                foreach ($ownPid in $pids) {
                    try { Stop-Process -Id $ownPid -Force -ErrorAction SilentlyContinue } catch {}
                }
                Write-Host ("Freed port {0}" -f $port) -ForegroundColor Gray
            }
        } catch {}
    }
}

function Test-ServiceHealth {
    param([string]$Url,[string]$Name,[int]$TimeoutSec = 10)
    try {
        $response = Invoke-WebRequest -Uri $Url -TimeoutSec $TimeoutSec -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host ("{0} healthy" -f $Name) -ForegroundColor Green
            return $true
        }
    } catch {}
    Write-Host ("{0} not healthy" -f $Name) -ForegroundColor Red
    return $false
}

function Start-Services {
    # Always clean first
    Stop-AllServices
    Free-Ports -Ports @(8000,8501)

    Write-Host "Starting API..." -ForegroundColor Cyan
    $apiArgs = @('-m','uvicorn','app.api:app','--host','0.0.0.0','--port','8000','--log-level', $LogLevel.ToLower())
    if ($Debug) { $apiArgs += '--reload' }
    $api = Start-Process -FilePath $py -ArgumentList $apiArgs -WindowStyle Hidden -RedirectStandardOutput 'volumes/logs/api.stdout.log' -RedirectStandardError 'volumes/logs/api.stderr.log' -PassThru

    Write-Host "Waiting API..." -ForegroundColor Yellow
    $ok = $false
    for ($i=1; $i -le 20; $i++) {
        if (Test-ServiceHealth -Url 'http://localhost:8000/health' -Name 'API' -TimeoutSec 5) { $ok=$true; break }
        Start-Sleep -Seconds 2
    }
    if (-not $ok) { Write-Host "API failed to start" -ForegroundColor Red; return $false }

    Write-Host "Starting Streamlit..." -ForegroundColor Cyan
    $stArgs = @('-m','streamlit','run','app/streamlit_app.py','--server.port=8501','--server.address=0.0.0.0','--server.headless=true',"--logger.level=$($LogLevel.ToUpper())")
    $st = Start-Process -FilePath $py -ArgumentList $stArgs -WindowStyle Hidden -RedirectStandardOutput 'volumes/logs/frontend.stdout.log' -RedirectStandardError 'volumes/logs/frontend.stderr.log' -PassThru

    Write-Host "Waiting Streamlit..." -ForegroundColor Yellow
    $ok = $false
    for ($i=1; $i -le 15; $i++) {
        if (Test-ServiceHealth -Url 'http://localhost:8501' -Name 'Streamlit' -TimeoutSec 5) { $ok=$true; break }
        Start-Sleep -Seconds 3
    }
    if (-not $ok) { Write-Host "Streamlit failed to start" -ForegroundColor Red; return $false }

    Write-Host "\nServices started" -ForegroundColor Green
    Write-Host "==================" -ForegroundColor Green
    Write-Host "API: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "Frontend: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "Docs: http://localhost:8000/docs" -ForegroundColor Cyan

    Start-Sleep -Seconds 2
    Start-Process 'http://localhost:8501'
    return $true
}

function Start-Diagnosis {
    Write-Host "Diagnostics..." -ForegroundColor Cyan
    $version = & $py --version 2>&1
    Write-Host ("Python: {0}" -f $version) -ForegroundColor Gray

    Write-Host "\nCheck deps" -ForegroundColor Yellow
    $deps = @('uvicorn','fastapi','streamlit','pandas','numpy')
    foreach ($dep in $deps) {
        try { & $py -c "import $dep; print('OK')" 2>$null; if ($LASTEXITCODE -eq 0) { Write-Host ("{0}: OK" -f $dep) -ForegroundColor Green } else { Write-Host ("{0}: FAILED" -f $dep) -ForegroundColor Red } } catch { Write-Host ("{0}: FAILED" -f $dep) -ForegroundColor Red }
    }

    Write-Host "\nPorts" -ForegroundColor Yellow
    foreach ($p in 8000,8501) {
        try { $c=Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue; if ($c) { Write-Host ("Port {0} BUSY" -f $p) -ForegroundColor Yellow } else { Write-Host ("Port {0} FREE" -f $p) -ForegroundColor Green } } catch { Write-Host ("Port {0} FREE" -f $p) -ForegroundColor Green }
    }
}

switch ($Mode) {
    'restart' {
        Write-Host 'Mode: restart' -ForegroundColor Magenta
        $ok = Start-Services
        if (-not $ok) { Start-Diagnosis }
    }
    'diagnose' {
        Write-Host 'Mode: diagnose' -ForegroundColor Magenta
        Start-Diagnosis
    }
    default {
        Write-Host 'Mode: auto' -ForegroundColor Magenta
        $ok = Start-Services
        if (-not $ok) { Start-Diagnosis }
    }
}

Write-Host "\nUsage:" -ForegroundColor Yellow
Write-Host "Start: .\START.ps1" -ForegroundColor Gray
Write-Host "Restart: .\START.ps1 -Mode restart" -ForegroundColor Gray
Write-Host "Diagnose: .\START.ps1 -Mode diagnose" -ForegroundColor Gray
Write-Host "Stop all python: taskkill /f /im python.exe" -ForegroundColor Gray

Write-Host "\nDone" -ForegroundColor Green

