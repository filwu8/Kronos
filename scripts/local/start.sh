#!/bin/bash

# 启动脚本 - 初始化挂载卷并运行服务

echo "🚀 启动Kronos股票预测应用..."

# 初始化绑定挂载目录
echo "🔧 初始化绑定挂载目录..."
/app/init-volumes.sh

# 检查环境变量
echo "📋 环境配置:"
echo "  - USE_MOCK_MODEL: ${USE_MOCK_MODEL:-true}"
echo "  - DEVICE: ${DEVICE:-cpu}"
echo "  - PYTHONPATH: ${PYTHONPATH:-/app}"

# 确保日志目录存在
mkdir -p /app/logs

# 检查关键文件是否存在
if [ ! -f /app/app/api.py ]; then
    echo "❌ 应用文件未找到，请检查绑定挂载配置"
    exit 1
fi

# 根据容器角色启动不同服务
SERVICE_TYPE=${SERVICE_TYPE:-"all"}

case $SERVICE_TYPE in
    "api")
        echo "🔧 启动API服务..."
        cd /app
        exec uvicorn app.api:app --host 0.0.0.0 --port 8000
        ;;
    "frontend")
        echo "🌐 启动前端服务..."
        cd /app
        exec streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501
        ;;
    "all"|*)
        echo "🔧 启动API服务（后台）..."
        cd /app
        uvicorn app.api:app --host 0.0.0.0 --port 8000 > /app/logs/api.log 2>&1 &
        API_PID=$!

        # 等待API服务启动
        echo "⏳ 等待API服务启动..."
        for i in {1..30}; do
            if curl -f http://localhost:8000/health > /dev/null 2>&1; then
                echo "✅ API服务启动成功"
                break
            fi
            if [ $i -eq 30 ]; then
                echo "❌ API服务启动超时"
                cat /app/logs/api.log
                exit 1
            fi
            sleep 1
        done

        echo "🌐 启动前端服务（后台）..."
        streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501 > /app/logs/streamlit.log 2>&1 &
        STREAMLIT_PID=$!

        # 等待前端服务启动
        echo "⏳ 等待前端服务启动..."
        for i in {1..20}; do
            if curl -f http://localhost:8501 > /dev/null 2>&1; then
                echo "✅ 前端服务启动成功"
                break
            fi
            if [ $i -eq 20 ]; then
                echo "⚠️ 前端服务启动可能失败，但继续运行"
                cat /app/logs/streamlit.log
            fi
            sleep 1
        done

        echo "🎉 应用启动完成!"
        echo "📊 内部服务地址:"
        echo "  - API服务: http://api:8000"
        echo "  - 前端服务: http://frontend:8501"
        echo "  - 外部访问: http://localhost (通过Nginx代理)"

        # 保持容器运行
        wait $API_PID $STREAMLIT_PID
        ;;
esac
