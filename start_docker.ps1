# Kronos Docker 启动脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kronos股票预测应用启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 检查Docker Desktop是否运行
Write-Host "`n[1/6] 检查Docker状态..." -ForegroundColor Yellow
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "SUCCESS: Docker Desktop已运行" -ForegroundColor Green
    } else {
        throw "Docker Desktop未运行"
    }
} catch {
    Write-Host "WARNING: Docker Desktop未运行，尝试启动..." -ForegroundColor Yellow
    
    # 尝试启动Docker Desktop
    $dockerPath = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $dockerPath) {
        Start-Process $dockerPath
        Write-Host "正在启动Docker Desktop，请等待..." -ForegroundColor Yellow
        
        # 等待Docker Desktop启动
        $timeout = 60
        $count = 0
        do {
            Start-Sleep 2
            $count += 2
            Write-Host "等待中... ($count/$timeout 秒)" -ForegroundColor Yellow
            try {
                docker info 2>$null | Out-Null
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "SUCCESS: Docker Desktop已启动" -ForegroundColor Green
                    break
                }
            } catch {}
        } while ($count -lt $timeout)
        
        if ($count -ge $timeout) {
            Write-Host "ERROR: Docker Desktop启动超时" -ForegroundColor Red
            Write-Host "请手动启动Docker Desktop后重新运行此脚本" -ForegroundColor Red
            Read-Host "按Enter键退出"
            exit 1
        }
    } else {
        Write-Host "ERROR: 未找到Docker Desktop，请先安装Docker Desktop" -ForegroundColor Red
        Read-Host "按Enter键退出"
        exit 1
    }
}

# 检查volumes目录
Write-Host "`n[2/6] 检查volumes目录..." -ForegroundColor Yellow
if (!(Test-Path "volumes\app\api.py")) {
    Write-Host "初始化volumes目录..." -ForegroundColor Yellow
    
    # 创建目录结构
    @("app", "model", "examples", "finetune", "logs", "nginx_logs") | ForEach-Object {
        $dir = "volumes\$_"
        if (!(Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }
    
    # 复制文件
    if (Test-Path "app") { Copy-Item "app\*" "volumes\app\" -Recurse -Force }
    if (Test-Path "model") { Copy-Item "model\*" "volumes\model\" -Recurse -Force }
    if (Test-Path "examples") { Copy-Item "examples\*" "volumes\examples\" -Recurse -Force }
    if (Test-Path "finetune") { Copy-Item "finetune\*" "volumes\finetune\" -Recurse -Force }
}
Write-Host "SUCCESS: volumes目录已准备就绪" -ForegroundColor Green

# 创建.env文件
Write-Host "`n[3/6] 检查环境配置..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Copy-Item ".env.example" ".env"
        Write-Host "SUCCESS: 已创建.env配置文件" -ForegroundColor Green
    }
} else {
    Write-Host "SUCCESS: .env配置文件已存在" -ForegroundColor Green
}

# 构建和启动服务
Write-Host "`n[4/6] 构建Docker镜像..." -ForegroundColor Yellow
docker-compose build
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Docker镜像构建失败" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host "SUCCESS: Docker镜像构建完成" -ForegroundColor Green

Write-Host "`n[5/6] 启动服务..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: 服务启动失败" -ForegroundColor Red
    Read-Host "按Enter键退出"
    exit 1
}
Write-Host "SUCCESS: 服务启动完成" -ForegroundColor Green

# 等待服务就绪
Write-Host "`n[6/6] 等待服务就绪..." -ForegroundColor Yellow
Start-Sleep 15

# 检查服务状态
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "服务状态" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
docker-compose ps

# 健康检查
Write-Host "`n检查服务健康状态..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://localhost/health" -TimeoutSec 10 -UseBasicParsing
    if ($response.StatusCode -eq 200) {
        Write-Host "SUCCESS: 应用健康检查通过" -ForegroundColor Green
    }
} catch {
    Write-Host "WARNING: 健康检查失败，服务可能还在启动中" -ForegroundColor Yellow
}

# 显示访问信息
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "访问信息" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "主界面: http://localhost" -ForegroundColor White
Write-Host "API文档: http://localhost/direct-api/docs" -ForegroundColor White
Write-Host "健康检查: http://localhost/health" -ForegroundColor White

Write-Host "`n是否打开浏览器访问应用? (Y/N): " -ForegroundColor Yellow -NoNewline
$choice = Read-Host
if ($choice -eq "Y" -or $choice -eq "y" -or $choice -eq "") {
    Start-Process "http://localhost"
}

Write-Host "`n应用已启动完成！" -ForegroundColor Green
Write-Host "按Enter键退出..." -ForegroundColor Gray
Read-Host
