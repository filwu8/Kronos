# Kronos股票预测应用 - 部署指南

## 📋 项目概述

基于Kronos模型的A股股票价格预测Web应用，支持容器化一键部署。

### 🎯 主要功能
- 🔍 A股股票代码查询和信息获取
- 📈 基于Kronos模型的股票价格预测
- 📊 交互式图表展示历史数据和预测结果
- 🌐 用户友好的Web界面
- 🚀 容器化部署，开箱即用

### 🏗️ 技术架构
- **前端**: Streamlit (端口8501)
- **后端**: FastAPI (端口8000)
- **模型**: Kronos深度学习模型
- **数据源**: akshare + yfinance
- **容器**: Docker + Docker Compose

## 🚀 快速开始

### 方式一：Docker Compose 一键部署（推荐）

1. **克隆项目**
```bash
git clone <repository-url>
cd Kronos
```

2. **启动应用**
```bash
docker-compose up -d
```

3. **访问应用**
- 前端界面: http://localhost:8501
- API文档: http://localhost:8000/docs
- API健康检查: http://localhost:8000/health

### 方式二：单容器部署

1. **构建镜像**
```bash
docker build -t kronos-stock-app .
```

2. **运行容器**
```bash
docker run -d \
  --name kronos-app \
  -p 8000:8000 \
  -p 8501:8501 \
  -e USE_MOCK_MODEL=true \
  -e DEVICE=cpu \
  kronos-stock-app
```

### 方式三：本地开发部署

1. **安装依赖**
```bash
cd app
pip install -r requirements.txt
```

2. **启动后端服务**
```bash
python api.py
# 或者
uvicorn api:app --host 0.0.0.0 --port 8000 --reload
```

3. **启动前端服务**（新终端）
```bash
streamlit run streamlit_app.py --server.port 8501
```

## ⚙️ 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `USE_MOCK_MODEL` | `true` | 是否使用模拟模型（true/false） |
| `DEVICE` | `cpu` | 计算设备（cpu/cuda） |
| `PYTHONPATH` | `/app` | Python路径 |

### 模型配置

- **模拟模式** (`USE_MOCK_MODEL=true`): 使用随机生成的预测数据，适合演示和测试
- **真实模式** (`USE_MOCK_MODEL=false`): 使用Kronos预训练模型，需要下载模型文件

## 📊 使用指南

### 1. 访问Web界面
打开浏览器访问 http://localhost:8501

### 2. 输入股票代码
- 支持6位数字代码：`000001`、`600000`
- 支持带交易所后缀：`000001.SZ`、`600000.SS`

### 3. 配置预测参数
- **预测天数**: 1-60天
- **历史数据周期**: 6个月、1年、2年
- **高级参数**: 采样温度、核采样概率等

### 4. 查看预测结果
- 📊 关键指标：当前价格、预测价格、变化幅度
- 📈 交互式图表：价格走势和成交量
- 📋 详细数据：预测数据表格

### 5. API接口使用

#### 预测单只股票
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "period": "1y",
    "pred_len": 30
  }'
```

#### 获取股票信息
```bash
curl "http://localhost:8000/stocks/000001/info"
```

#### 批量预测
```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001", "600000"],
    "pred_len": 30
  }'
```

## 🔧 故障排除

### 常见问题

1. **API服务无法启动**
   - 检查端口8000是否被占用
   - 查看容器日志：`docker logs kronos-api`

2. **前端无法连接API**
   - 确认API服务健康：`curl http://localhost:8000/health`
   - 检查防火墙设置

3. **股票数据获取失败**
   - 检查网络连接
   - 验证股票代码格式
   - 查看API日志了解具体错误

4. **模型加载失败**
   - 确认`USE_MOCK_MODEL=true`使用模拟模式
   - 检查CUDA环境（如使用GPU）

### 日志查看

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f api
docker-compose logs -f frontend

# 查看容器内日志
docker exec -it kronos-api cat /app/logs/api.log
```

### 性能优化

1. **启用GPU加速**（如有NVIDIA GPU）
```yaml
# docker-compose.yml
environment:
  - USE_MOCK_MODEL=false
  - DEVICE=cuda
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

2. **调整内存限制**
```yaml
# docker-compose.yml
deploy:
  resources:
    limits:
      memory: 4G
    reservations:
      memory: 2G
```

## 🛡️ 安全注意事项

1. **生产环境部署**
   - 修改默认端口
   - 配置HTTPS
   - 设置访问控制
   - 定期更新依赖

2. **API安全**
   - 添加认证机制
   - 限制请求频率
   - 输入验证和过滤

3. **数据安全**
   - 不存储敏感信息
   - 定期清理日志
   - 备份重要配置

## 📈 扩展功能

### 添加新的数据源
1. 在`data_fetcher.py`中添加新的获取方法
2. 更新`fetch_stock_data`方法的逻辑
3. 测试数据格式兼容性

### 集成真实Kronos模型
1. 下载预训练模型文件
2. 设置`USE_MOCK_MODEL=false`
3. 配置模型路径和参数

### 部署到云平台
- **AWS**: 使用ECS或EKS
- **Azure**: 使用Container Instances
- **Google Cloud**: 使用Cloud Run
- **阿里云**: 使用容器服务ACK

## 📞 技术支持

如遇到问题，请：
1. 查看本文档的故障排除部分
2. 检查GitHub Issues
3. 提交新的Issue并附上详细日志

## 📄 许可证

本项目基于MIT许可证开源。
