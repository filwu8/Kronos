@echo off
REM Kronos股票预测应用管理脚本 (Windows版本)

setlocal enabledelayedexpansion

REM 颜色定义 (Windows CMD不支持颜色，使用echo)
set "INFO=[INFO]"
set "SUCCESS=[SUCCESS]"
set "WARNING=[WARNING]"
set "ERROR=[ERROR]"

REM 显示帮助信息
:show_help
echo Kronos股票预测应用管理脚本
echo.
echo 用法: %0 [命令]
echo.
echo 命令:
echo   start     启动所有服务
echo   stop      停止所有服务
echo   restart   重启所有服务
echo   status    查看服务状态
echo   logs      查看服务日志
echo   clean     清理容器和卷
echo   build     重新构建镜像
echo   test      运行测试
echo   help      显示此帮助信息
echo.
echo 示例:
echo   %0 start          # 启动应用
echo   %0 logs api       # 查看API服务日志
echo   %0 clean --all    # 清理所有数据
goto :eof

REM 检查Docker和Docker Compose
:check_requirements
docker --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Docker未安装，请先安装Docker
    exit /b 1
)

docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo %ERROR% Docker Compose未安装，请先安装Docker Compose
    exit /b 1
)
goto :eof

REM 启动服务
:start_services
echo %INFO% 启动Kronos股票预测应用...

REM 创建.env文件（如果不存在）
if not exist .env (
    echo %INFO% 创建环境配置文件...
    copy .env.example .env >nul
)

REM 创建volumes目录结构
echo %INFO% 创建volumes目录结构...
if not exist volumes mkdir volumes
if not exist volumes\app mkdir volumes\app
if not exist volumes\model mkdir volumes\model
if not exist volumes\examples mkdir volumes\examples
if not exist volumes\finetune mkdir volumes\finetune
if not exist volumes\logs mkdir volumes\logs
if not exist volumes\nginx_logs mkdir volumes\nginx_logs

REM 复制初始代码到volumes目录（如果为空）
if not exist volumes\app\api.py (
    echo %INFO% 复制应用代码到volumes目录...
    xcopy app volumes\app /E /I /Q >nul 2>&1
)

if not exist volumes\model\__init__.py (
    echo %INFO% 复制模型文件到volumes目录...
    xcopy model volumes\model /E /I /Q >nul 2>&1
)

if not exist volumes\examples\prediction_example.py (
    echo %INFO% 复制示例文件到volumes目录...
    xcopy examples volumes\examples /E /I /Q >nul 2>&1
)

if not exist volumes\finetune\config.py (
    echo %INFO% 复制微调文件到volumes目录...
    xcopy finetune volumes\finetune /E /I /Q >nul 2>&1
)

docker-compose up -d
if errorlevel 1 (
    echo %ERROR% 服务启动失败
    exit /b 1
)

echo %SUCCESS% 服务启动完成！
echo %INFO% 访问地址:
echo %INFO%   主界面: http://localhost
echo %INFO%   API文档: http://localhost/direct-api/docs
echo %INFO%   健康检查: http://localhost/health

echo %INFO% 等待服务启动...
timeout /t 10 /nobreak >nul

REM 检查服务状态
call :check_health
goto :eof

REM 停止服务
:stop_services
echo %INFO% 停止服务...
docker-compose down
echo %SUCCESS% 服务已停止
goto :eof

REM 重启服务
:restart_services
echo %INFO% 重启服务...
docker-compose restart
echo %SUCCESS% 服务已重启

timeout /t 5 /nobreak >nul
call :check_health
goto :eof

REM 查看服务状态
:show_status
echo %INFO% 服务状态:
docker-compose ps
echo.
echo %INFO% 容器资源使用:
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" 2>nul
goto :eof

REM 查看日志
:show_logs
if "%~2"=="" (
    echo %INFO% 显示所有服务日志...
    docker-compose logs --tail=100
) else (
    echo %INFO% 显示 %~2 服务日志...
    docker-compose logs --tail=100 %~2
)
goto :eof

REM 清理资源
:clean_resources
echo %WARNING% 这将删除容器和相关资源

if "%~2"=="--all" (
    echo %WARNING% 包括数据卷也将被删除！
    set /p confirm="确认继续？(y/N): "
    if /i "!confirm!"=="y" (
        echo %INFO% 清理所有资源...
        docker-compose down -v --remove-orphans
        docker system prune -f
        echo %SUCCESS% 清理完成
    ) else (
        echo %INFO% 取消清理
    )
) else (
    set /p confirm="确认继续？(y/N): "
    if /i "!confirm!"=="y" (
        echo %INFO% 清理容器...
        docker-compose down --remove-orphans
        echo %SUCCESS% 清理完成
    ) else (
        echo %INFO% 取消清理
    )
)
goto :eof

REM 重新构建镜像
:build_images
echo %INFO% 重新构建镜像...
docker-compose build --no-cache
echo %SUCCESS% 镜像构建完成
goto :eof

REM 运行测试
:run_tests
echo %INFO% 运行应用测试...

REM 确保服务正在运行
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo %INFO% 启动服务进行测试...
    docker-compose up -d
    timeout /t 15 /nobreak >nul
)

REM 运行测试
python test_app.py
goto :eof

REM 检查健康状态
:check_health
echo %INFO% 检查服务健康状态...

curl -f http://localhost/health >nul 2>&1
if errorlevel 1 (
    echo %ERROR% 应用健康检查失败
    echo %INFO% 查看服务状态:
    docker-compose ps
) else (
    echo %SUCCESS% 应用健康检查通过
)
goto :eof

REM 主函数
:main
call :check_requirements

REM 解析命令
if "%~1"=="start" (
    call :start_services
) else if "%~1"=="stop" (
    call :stop_services
) else if "%~1"=="restart" (
    call :restart_services
) else if "%~1"=="status" (
    call :show_status
) else if "%~1"=="logs" (
    call :show_logs %*
) else if "%~1"=="clean" (
    call :clean_resources %*
) else if "%~1"=="build" (
    call :build_images
) else if "%~1"=="test" (
    call :run_tests
) else if "%~1"=="health" (
    call :check_health
) else if "%~1"=="help" (
    call :show_help
) else if "%~1"=="--help" (
    call :show_help
) else if "%~1"=="-h" (
    call :show_help
) else if "%~1"=="" (
    call :show_help
) else (
    echo %ERROR% 未知命令: %~1
    echo.
    call :show_help
    exit /b 1
)

goto :eof

REM 调用主函数
call :main %*
