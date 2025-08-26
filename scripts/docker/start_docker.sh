#!/bin/bash
# RTX 5090 GPU加速股票预测系统 - Docker启动脚本

echo "🚀 启动RTX 5090 GPU加速股票预测系统 (Docker版本)"
echo "=" * 60

# 检查Docker和nvidia-docker
echo "🔍 检查Docker环境..."

if ! command -v docker &> /dev/null; then
    echo "❌ Docker未安装，请先安装Docker"
    exit 1
fi

if ! command -v nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA驱动未安装，请先安装NVIDIA驱动"
    exit 1
fi

# 检查GPU
echo "📊 GPU信息:"
nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader

# 检查Docker Compose
if ! command -v docker-compose &> /dev/null; then
    echo "⚠️ docker-compose未找到，使用docker compose"
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD="docker-compose"
fi

# 进入脚本目录
cd "$(dirname "$0")"

# 停止现有容器
echo "🛑 停止现有容器..."
$COMPOSE_CMD down

# 构建并启动服务
echo "🔨 构建并启动服务..."
$COMPOSE_CMD up --build -d

# 等待服务启动
echo "⏳ 等待服务启动..."
sleep 10

# 检查服务状态
echo "🔍 检查服务状态..."
$COMPOSE_CMD ps

# 显示日志
echo "📋 服务日志:"
$COMPOSE_CMD logs --tail=20

echo ""
echo "✅ 服务启动完成!"
echo "🌐 访问地址:"
echo "   前端界面: http://localhost:8501"
echo "   API文档: http://localhost:8000/docs"
echo "   健康检查: http://localhost:8000/health"
echo ""
echo "📊 查看日志: $COMPOSE_CMD logs -f"
echo "🛑 停止服务: $COMPOSE_CMD down"
