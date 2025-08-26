@echo off
echo ========================================
echo Kronos股票预测应用启动测试
echo ========================================

echo.
echo [1/5] 检查Docker状态...
docker --version
if errorlevel 1 (
    echo ERROR: Docker未安装或不可用
    pause
    exit /b 1
)

echo.
echo [2/5] 等待Docker Desktop启动...
:wait_docker
docker ps >nul 2>&1
if errorlevel 1 (
    echo 等待Docker Desktop启动中...
    timeout /t 5 /nobreak >nul
    goto wait_docker
)
echo SUCCESS: Docker Desktop已启动

echo.
echo [3/5] 检查volumes目录...
if not exist volumes\app\api.py (
    echo ERROR: volumes目录未正确初始化
    echo 请运行: xcopy app volumes\app /E /I /Y
    pause
    exit /b 1
)
echo SUCCESS: volumes目录已准备就绪

echo.
echo [4/5] 启动Docker Compose服务...
docker-compose up -d
if errorlevel 1 (
    echo ERROR: Docker Compose启动失败
    pause
    exit /b 1
)

echo.
echo [5/5] 等待服务启动...
timeout /t 15 /nobreak >nul

echo.
echo ========================================
echo 检查服务状态
echo ========================================
docker-compose ps

echo.
echo ========================================
echo 访问信息
echo ========================================
echo 主界面: http://localhost
echo API文档: http://localhost/direct-api/docs
echo 健康检查: http://localhost/health
echo.
echo 按任意键打开浏览器...
pause >nul

start http://localhost

echo.
echo 按任意键退出...
pause >nul
