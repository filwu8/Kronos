# RTX 5090 GPU加速股票预测系统 - 部署指南

## 🚀 系统概述

本系统支持两种完全一致的部署模式：
- **Docker容器化部署**: 适合服务器环境和云部署
- **本地exe运行**: 适合个人电脑和离线使用

两种模式使用相同的代码库，确保功能完全一致。

## 📁 项目结构

```
Kronos/
├── app/                          # 应用核心代码
│   ├── api.py                   # FastAPI后端服务
│   ├── streamlit_app.py         # Streamlit前端界面
│   ├── prediction_service.py    # 预测服务核心
│   └── akshare_adapter.py       # 数据适配器
├── volumes/                      # 外部数据目录
│   ├── data/akshare_data/       # 股票历史数据 (100只股票5年数据)
│   ├── models/                  # 模型文件
│   ├── logs/                    # 日志文件
│   └── config/                  # 配置文件
├── tests/                        # 测试文件
│   ├── unit/                    # 单元测试
│   ├── integration/             # 集成测试
│   └── performance/             # 性能测试
├── scripts/                      # 部署脚本
│   ├── docker/                  # Docker相关脚本
│   └── local/                   # 本地部署脚本
└── requirements.txt             # Python依赖
```

## 🐳 Docker容器化部署

### 前置要求

1. **硬件要求**:
   - NVIDIA RTX 5090 GPU
   - 16GB+ 系统内存
   - 50GB+ 可用磁盘空间

2. **软件要求**:
   - Docker 20.10+
   - Docker Compose 2.0+
   - NVIDIA Container Toolkit
   - NVIDIA驱动 580.97+

### 快速启动

```bash
# 1. 克隆项目
git clone <repository-url>
cd Kronos

# 2. 启动Docker服务
cd scripts/docker
chmod +x start_docker.sh
./start_docker.sh
```

### 手动部署

```bash
# 1. 构建镜像
docker build -f scripts/docker/Dockerfile -t kronos-gpu:latest .

# 2. 启动容器
docker run -d \
  --name kronos-rtx5090 \
  --gpus all \
  -p 8000:8000 \
  -p 8501:8501 \
  -v $(pwd)/volumes:/volumes \
  kronos-gpu:latest

# 3. 查看日志
docker logs -f kronos-rtx5090
```

### Docker Compose部署

```bash
# 启动所有服务
docker-compose -f scripts/docker/docker-compose.yml up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 💻 本地exe运行

### 前置要求

1. **硬件要求**:
   - NVIDIA RTX 5090 GPU
   - 16GB+ 系统内存
   - 20GB+ 可用磁盘空间

2. **软件要求**:
   - Python 3.8+
   - NVIDIA驱动 580.97+
   - CUDA 12.8+

### 开发模式启动

```bash
# 1. 安装依赖
pip install -r requirements.txt
pip install --pre torch torchvision torchaudio --index-url https://download.pytorch.org/whl/nightly/cu128

# 2. 启动服务
python scripts/local/start_local.py
```

### 构建exe文件

```bash
# 1. 运行构建脚本
python scripts/local/build_exe.py

# 2. 运行生成的exe
dist/KronosGPU/KronosGPU.exe
```

## 🔧 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `DEVICE` | auto | 计算设备 (auto/cpu/cuda) |
| `USE_MOCK` | false | 是否使用模拟数据 |
| `API_HOST` | 0.0.0.0 | API服务地址 |
| `API_PORT` | 8000 | API服务端口 |
| `STREAMLIT_PORT` | 8501 | 前端服务端口 |
| `AUTO_DOWNLOAD_DATA` | true | 自动下载缺失数据 |
| `LOG_LEVEL` | INFO | 日志级别 |

### 数据配置

- **股票数据**: `volumes/data/akshare_data/`
- **支持股票**: 100只A股 (000001-000516)
- **数据周期**: 5年历史数据
- **自动更新**: 支持缺失数据自动下载

## 🌐 访问地址

启动成功后，可通过以下地址访问：

- **前端界面**: http://localhost:8501
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health

## 🧪 功能测试

### 基础功能测试

```bash
# 运行集成测试
python tests/integration/test_dual_deployment.py

# 运行性能测试
python tests/performance/test_gpu_performance.py

# 运行单元测试
python -m pytest tests/unit/
```

### 手动测试

1. **访问前端**: http://localhost:8501
2. **输入股票代码**: 000001 (平安银行)
3. **设置预测参数**: 预测天数、历史周期等
4. **查看预测结果**: 价格走势图、趋势分析

## 🔍 故障排除

### 常见问题

1. **GPU不可用**:
   ```bash
   # 检查NVIDIA驱动
   nvidia-smi
   
   # 检查CUDA
   nvcc --version
   
   # 检查PyTorch GPU支持
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **端口冲突**:
   ```bash
   # 检查端口占用
   netstat -ano | findstr :8000
   netstat -ano | findstr :8501
   
   # 修改端口配置
   export API_PORT=8002
   export STREAMLIT_PORT=8502
   ```

3. **数据缺失**:
   ```bash
   # 检查数据目录
   ls volumes/data/akshare_data/
   
   # 手动下载数据
   python -c "from app.akshare_adapter import AkshareDataAdapter; adapter = AkshareDataAdapter(); adapter.auto_download_missing_data('000001')"
   ```

### 日志查看

- **Docker模式**: `docker logs kronos-rtx5090`
- **本地模式**: `volumes/logs/app.log`

## 📊 性能优化

### GPU优化

- **RTX 5090**: 自动启用GPU加速
- **内存管理**: 自动清理GPU缓存
- **批处理**: 支持批量预测优化

### 系统优化

- **CPU线程**: 自动配置最优线程数
- **内存缓存**: 智能数据缓存策略
- **网络优化**: 异步请求处理

## 🔄 版本一致性

两种部署模式保证：

- ✅ **功能完全一致**: 相同的预测算法和数据处理
- ✅ **配置统一**: 使用相同的配置管理系统
- ✅ **数据共享**: 使用相同的数据格式和存储
- ✅ **API兼容**: 完全相同的API接口

## 📞 技术支持

如遇到问题，请：

1. 查看日志文件获取详细错误信息
2. 运行诊断脚本检查系统状态
3. 参考故障排除章节解决常见问题
4. 提交Issue并附上系统信息和错误日志

---

**系统特性总结**:
- 🚀 RTX 5090 GPU加速
- 📊 100只A股5年真实数据
- 🎨 中文化交互界面
- 🐳 Docker容器化支持
- 💻 本地exe独立运行
- 🔧 自动化部署脚本
