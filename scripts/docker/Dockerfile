# RTX 5090 GPU加速股票预测系统 - Docker版本
FROM nvidia/cuda:12.8-devel-ubuntu22.04

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV DOCKER_ENV=1
ENV CUDA_VISIBLE_DEVICES=0

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    build-essential \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# 创建工作目录
WORKDIR /app

# 创建volumes挂载点
RUN mkdir -p /volumes/data/akshare_data \
             /volumes/models \
             /volumes/logs \
             /volumes/config

# 复制requirements文件
COPY requirements.txt .

# 安装Python依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 安装PyTorch nightly版本 (支持RTX 5090)
RUN pip3 install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# 安装akshare和其他依赖
RUN pip3 install akshare streamlit plotly pandas numpy

# 复制应用代码
COPY app/ ./app/
COPY volumes/config/ /volumes/config/

# 设置Python路径
ENV PYTHONPATH=/app:/volumes

# 暴露端口
EXPOSE 8000 8501

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# 启动命令
CMD ["python3", "-m", "uvicorn", "app.api:app", "--host", "0.0.0.0", "--port", "8000"]
