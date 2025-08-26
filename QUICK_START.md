# 🚀 Kronos股票预测应用 - 快速开始

## 📋 简介

这是一个基于Kronos深度学习模型的A股股票价格预测Web应用。您可以通过简单的网页界面输入任意A股股票代码，获取未来价格预测。

## ⚡ 一分钟快速启动

### 方法一：Docker一键部署（推荐）

```bash
# 1. 启动应用（自动创建volumes目录）
./manage.sh start
# 或直接使用docker-compose
docker-compose up -d

# 2. 访问应用（只需一个端口）
# 主界面: http://localhost
# API文档: http://localhost/direct-api/docs
# 健康检查: http://localhost/health
```

### 方法二：Python本地运行

```bash
# 1. 安装依赖
pip install -r app/requirements.txt

# 2. 启动应用
python run.py

# 3. 访问应用
# 前端: http://localhost:8501
# API: http://localhost:8000/docs
```

## 🎯 使用步骤

1. **打开浏览器**，访问 http://localhost

2. **输入股票代码**
   - 支持格式：`000001`、`600000`、`000001.SZ`、`600000.SS`
   - 常见股票：
     - 平安银行：`000001`
     - 浦发银行：`600000`
     - 万科A：`000002`
     - 招商银行：`600036`

3. **设置预测参数**
   - 预测天数：1-60天
   - 历史数据周期：6个月/1年/2年

4. **点击"开始预测"**

5. **查看结果**
   - 📊 关键指标：当前价格、预测价格、变化幅度
   - 📈 图表：价格走势和成交量预测
   - 📋 详细数据表格

## 🔧 故障排除

### 常见问题

**Q: 页面显示"API服务不可用"**
```bash
# 检查API服务状态
curl http://localhost:8000/health

# 如果失败，重启服务
docker-compose restart api
# 或
python run.py
```

**Q: 股票数据获取失败**
- 检查股票代码格式是否正确
- 确认网络连接正常
- 尝试其他股票代码

**Q: 预测速度很慢**
- 当前使用模拟模式，预测速度应该很快
- 如果使用真实模型，首次加载会较慢

### 查看日志

```bash
# Docker方式
docker-compose logs -f

# 本地方式
tail -f logs/api.log
tail -f logs/frontend.log
```

## 📊 API使用

### 预测股票价格

```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_code": "000001",
    "pred_len": 30
  }'
```

### 获取股票信息

```bash
curl "http://localhost:8000/stocks/000001/info"
```

### 批量预测

```bash
curl -X POST "http://localhost:8000/predict/batch" \
  -H "Content-Type: application/json" \
  -d '{
    "stock_codes": ["000001", "600000"],
    "pred_len": 10
  }'
```

## ⚙️ 配置选项

### 环境变量

```bash
# 使用模拟模型（默认）
export USE_MOCK_MODEL=true

# 使用真实模型（需要下载模型文件）
export USE_MOCK_MODEL=false

# 设置计算设备
export DEVICE=cpu        # CPU
export DEVICE=cuda       # GPU
```

### 预测参数

- **预测天数** (`pred_len`): 1-120天
- **历史数据长度** (`lookback`): 50-1000天
- **采样温度** (`temperature`): 0.1-2.0
- **核采样概率** (`top_p`): 0.1-1.0

## 🎨 界面功能

### 主要区域

1. **侧边栏**：参数配置和示例股票
2. **主区域**：预测结果展示
3. **图表区**：交互式价格和成交量图表
4. **数据区**：详细预测数据表格

### 交互功能

- 📊 **实时指标**：价格变化、趋势方向
- 📈 **缩放图表**：支持放大、缩小、平移
- 📋 **数据导出**：可复制预测数据
- 🔄 **参数调整**：实时修改预测参数

## 🛡️ 免责声明

⚠️ **重要提示**

- 本应用仅供学习和研究使用
- 预测结果不构成投资建议
- 股票投资存在风险，请谨慎决策
- 当前使用模拟数据，仅作演示用途

## 📞 技术支持

如遇问题：

1. 查看 [详细部署文档](README_DEPLOYMENT.md)
2. 运行测试脚本：`python test_app.py`
3. 检查日志文件
4. 提交GitHub Issue

## 🎯 下一步

- 🔧 集成真实Kronos模型
- 📊 添加更多技术指标
- 🌐 支持港股、美股
- 📱 移动端适配
- 🔔 价格预警功能

---

**🎉 开始您的股票预测之旅吧！**
