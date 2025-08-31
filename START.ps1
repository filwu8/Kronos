# G-Prophet 唯一启动脚本
# 这是您唯一需要的启动脚本，替代所有其他启动脚本

param(
    [string]$Mode = "auto"  # auto, restart, diagnose
)

Write-Host "🚀 G-Prophet 启动器" -ForegroundColor Green
Write-Host "==================" -ForegroundColor Green

# 设置环境变量
$env:DEVICE = 'auto'
$env:FAST_CPU_MODE = '0'
$env:CPU_THREADS = '24'

# 创建必要目录
New-Item -ItemType Directory -Force -Path 'volumes/logs' | Out-Null

# 检测Python环境
if (Test-Path .\.venv\Scripts\python.exe) {
    $py = ".\.venv\Scripts\python.exe"
    Write-Host "✅ 虚拟环境已找到" -ForegroundColor Green
} else {
    Write-Host "❌ 虚拟环境未找到" -ForegroundColor Red
    Write-Host "请运行以下命令创建虚拟环境:" -ForegroundColor Yellow
    Write-Host "python -m venv .venv" -ForegroundColor Gray
    Write-Host ".venv\Scripts\activate" -ForegroundColor Gray
    Write-Host "pip install -r app/requirements.txt" -ForegroundColor Gray
    exit 1
}

# 函数：停止所有服务
function Stop-AllServices {
    Write-Host "🛑 停止现有服务..." -ForegroundColor Yellow
    
    # 停止Python进程
    Get-Process | Where-Object {$_.ProcessName -like '*python*'} | ForEach-Object {
        try {
            Stop-Process -Id $_.Id -Force -ErrorAction SilentlyContinue
            Write-Host "  停止进程: $($_.ProcessName) (PID: $($_.Id))" -ForegroundColor Gray
        } catch {}
    }
    
    # 等待端口释放
    Start-Sleep 3
}

# 函数：检查服务健康
function Test-ServiceHealth {
    param($url, $name, $timeout = 10)
    
    try {
        $response = Invoke-WebRequest -Uri $url -TimeoutSec $timeout -ErrorAction SilentlyContinue
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $name 服务正常" -ForegroundColor Green
            return $true
        }
    } catch {}
    
    Write-Host "❌ $name 服务异常" -ForegroundColor Red
    return $false
}

# 函数：启动服务
function Start-Services {
    Write-Host "📡 启动API服务..." -ForegroundColor Cyan
    
    # 启动API服务
    $apiProcess = Start-Process -FilePath $py -ArgumentList '-m','uvicorn','app.api:app','--host','0.0.0.0','--port','8000','--log-level','info' -WindowStyle Hidden -PassThru
    
    # 等待API启动
    Write-Host "⏳ 等待API服务启动..." -ForegroundColor Yellow
    $apiStarted = $false
    for ($i = 1; $i -le 15; $i++) {
        if (Test-ServiceHealth -url "http://localhost:8000/health" -name "API" -timeout 5) {
            $apiStarted = $true
            break
        }
        Write-Host "  等待API启动... ($i/15)" -ForegroundColor Gray
        Start-Sleep 3
    }
    
    if (-not $apiStarted) {
        Write-Host "❌ API服务启动失败" -ForegroundColor Red
        return $false
    }
    
    Write-Host "🌐 启动Streamlit服务..." -ForegroundColor Cyan
    
    # 启动Streamlit服务
    $streamlitProcess = Start-Process -FilePath $py -ArgumentList '-m','streamlit','run','app/streamlit_app.py','--server.port=8501','--server.address=0.0.0.0','--server.headless=true' -WindowStyle Hidden -PassThru
    
    # 等待Streamlit启动
    Write-Host "⏳ 等待Streamlit服务启动..." -ForegroundColor Yellow
    $streamlitStarted = $false
    for ($i = 1; $i -le 10; $i++) {
        if (Test-ServiceHealth -url "http://localhost:8501" -name "Streamlit" -timeout 5) {
            $streamlitStarted = $true
            break
        }
        Write-Host "  等待Streamlit启动... ($i/10)" -ForegroundColor Gray
        Start-Sleep 4
    }
    
    if (-not $streamlitStarted) {
        Write-Host "❌ Streamlit服务启动失败" -ForegroundColor Red
        return $false
    }
    
    # 成功启动
    Write-Host "`n🎉 服务启动成功！" -ForegroundColor Green
    Write-Host "==================" -ForegroundColor Green
    Write-Host "API服务: http://localhost:8000" -ForegroundColor Cyan
    Write-Host "前端界面: http://localhost:8501" -ForegroundColor Cyan
    Write-Host "API文档: http://localhost:8000/docs" -ForegroundColor Cyan
    
    # 记录进程信息
    Write-Host "`n📋 进程信息:" -ForegroundColor Yellow
    Write-Host "API进程ID: $($apiProcess.Id)" -ForegroundColor Gray
    Write-Host "Streamlit进程ID: $($streamlitProcess.Id)" -ForegroundColor Gray
    
    # 打开浏览器
    Start-Sleep 2
    Start-Process 'http://localhost:8501'
    
    return $true
}

# 函数：诊断问题
function Start-Diagnosis {
    Write-Host "🔍 开始系统诊断..." -ForegroundColor Cyan
    
    # 检查Python环境
    Write-Host "`n1. Python环境检查" -ForegroundColor Yellow
    $version = & $py --version 2>&1
    Write-Host "  Python版本: $version" -ForegroundColor Gray
    
    # 检查依赖
    Write-Host "`n2. 关键依赖检查" -ForegroundColor Yellow
    $deps = @("uvicorn", "fastapi", "streamlit", "pandas", "numpy")
    foreach ($dep in $deps) {
        try {
            & $py -c "import $dep; print('✅ $dep')" 2>$null
            if ($LASTEXITCODE -eq 0) {
                Write-Host "  ✅ $dep" -ForegroundColor Green
            } else {
                Write-Host "  ❌ $dep" -ForegroundColor Red
            }
        } catch {
            Write-Host "  ❌ $dep" -ForegroundColor Red
        }
    }
    
    # 检查端口
    Write-Host "`n3. 端口检查" -ForegroundColor Yellow
    foreach ($port in 8000, 8501) {
        try {
            $connections = Get-NetTCPConnection -State Listen -LocalPort $port -ErrorAction SilentlyContinue
            if ($connections) {
                Write-Host "  ⚠️ 端口 $port 被占用" -ForegroundColor Yellow
            } else {
                Write-Host "  ✅ 端口 $port 可用" -ForegroundColor Green
            }
        } catch {
            Write-Host "  ✅ 端口 $port 可用" -ForegroundColor Green
        }
    }
    
    # 测试API
    Write-Host "`n4. API测试" -ForegroundColor Yellow
    if (Test-ServiceHealth -url "http://localhost:8000/health" -name "API" -timeout 5) {
        Write-Host "  ✅ API服务可访问" -ForegroundColor Green
        
        # 测试预测功能
        try {
            $testResult = & $py -c "
import requests
try:
    response = requests.post('http://localhost:8000/predict', 
                           json={'stock_code': '000001', 'pred_len': 1, 'sample_count': 1}, 
                           timeout=10)
    print(f'预测测试: {response.status_code}')
except Exception as e:
    print(f'预测测试失败: {e}')
"
            Write-Host "  $testResult" -ForegroundColor Gray
        } catch {
            Write-Host "  ⚠️ 预测功能测试失败" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  ❌ API服务不可访问" -ForegroundColor Red
    }
}

# 主逻辑
switch ($Mode) {
    "restart" {
        Write-Host "🔄 重启模式" -ForegroundColor Magenta
        Stop-AllServices
        Start-Services
    }
    
    "diagnose" {
        Write-Host "🔍 诊断模式" -ForegroundColor Magenta
        Start-Diagnosis
    }
    
    default {
        Write-Host "🚀 自动模式" -ForegroundColor Magenta
        
        # 检查是否已有服务运行
        $apiRunning = Test-ServiceHealth -url "http://localhost:8000/health" -name "API" -timeout 3
        $streamlitRunning = Test-ServiceHealth -url "http://localhost:8501" -name "Streamlit" -timeout 3
        
        if ($apiRunning -and $streamlitRunning) {
            Write-Host "✅ 服务已在运行" -ForegroundColor Green
            Write-Host "API服务: http://localhost:8000" -ForegroundColor Cyan
            Write-Host "前端界面: http://localhost:8501" -ForegroundColor Cyan
            Start-Process 'http://localhost:8501'
        } else {
            Write-Host "启动新服务..." -ForegroundColor Yellow
            Stop-AllServices
            $success = Start-Services
            
            if (-not $success) {
                Write-Host "`n❌ 启动失败，运行诊断..." -ForegroundColor Red
                Start-Diagnosis
            }
        }
    }
}

Write-Host "`n📋 使用说明:" -ForegroundColor Yellow
Write-Host "启动服务: .\START.ps1" -ForegroundColor Gray
Write-Host "重启服务: .\START.ps1 restart" -ForegroundColor Gray
Write-Host "诊断问题: .\START.ps1 diagnose" -ForegroundColor Gray
Write-Host "停止服务: taskkill /f /im python.exe" -ForegroundColor Gray

Write-Host "`n✅ 完成！" -ForegroundColor Green
