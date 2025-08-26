# 📊 Qlib数据准备完整指南

## 🎯 概述

根据Kronos项目要求，需要使用Qlib数据进行模型训练和预测。当前应用使用的是模拟数据，需要按照以下步骤准备真实的Qlib数据。

## ⚠️ 当前问题

1. **缺少Qlib安装**：项目依赖Qlib但未安装
2. **数据源不匹配**：使用akshare/yfinance而非Qlib数据
3. **数据量不足**：只有100天数据，模型需要多年历史数据
4. **模型未下载**：使用模拟模式而非真实Kronos模型

## 🚀 完整解决方案

### 步骤1：安装Qlib

```bash
# 安装Qlib
pip install pyqlib

# 验证安装
python -c "import qlib; print('Qlib安装成功')"
```

### 步骤2：下载中国A股数据

```bash
# 方法1：使用Qlib官方脚本下载
python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn

# 方法2：手动下载（如果上述方法失败）
# 从以下链接下载预处理的数据：
# https://github.com/microsoft/qlib/blob/main/scripts/data_collector/yahoo/README.md
```

### 步骤3：验证数据下载

```python
import qlib
from qlib.config import REG_CN

# 初始化Qlib
qlib.init(provider_uri="~/.qlib/qlib_data/cn_data", region=REG_CN)

# 测试数据访问
from qlib.data import D
instruments = D.instruments('csi300')
print(f"CSI300成分股数量: {len(instruments)}")

# 获取单只股票数据
data = D.features(['000001.SZ'], ['$close', '$volume'], start_time='2020-01-01', end_time='2023-12-31')
print(f"平安银行数据形状: {data.shape}")
```

### 步骤4：下载Kronos预训练模型

```bash
# 从Hugging Face下载Kronos模型
# 需要先安装git-lfs
git lfs install

# 下载Tokenizer模型
git clone https://huggingface.co/Kronos/Kronos-Tokenizer-base ./models/Kronos-Tokenizer-base

# 下载Predictor模型
git clone https://huggingface.co/Kronos/Kronos-small ./models/Kronos-small
```

### 步骤5：更新配置文件

```python
# 修改 finetune/config.py
class Config:
    def __init__(self):
        # 更新Qlib数据路径
        self.qlib_data_path = "~/.qlib/qlib_data/cn_data"
        
        # 更新模型路径
        self.pretrained_tokenizer_path = "./models/Kronos-Tokenizer-base"
        self.pretrained_predictor_path = "./models/Kronos-small"
        
        # 其他配置保持不变...
```

### 步骤6：预处理数据

```bash
# 运行数据预处理脚本
cd finetune
python qlib_data_preprocess.py
```

### 步骤7：更新应用以使用真实模型

需要修改以下文件：

1. **app/requirements.txt** - 添加Qlib依赖
2. **app/prediction_service.py** - 集成真实Kronos模型
3. **app/data_fetcher.py** - 使用Qlib数据源

## 📋 数据需求详解

### 对于单只股票预测：

1. **历史数据长度**：
   - 最少需要 `lookback_window + predict_window + 1` 天
   - 默认配置：90 + 10 + 1 = 101天最少
   - 建议：至少2-3年历史数据以获得更好效果

2. **数据字段**：
   - `open`, `high`, `low`, `close`: 价格数据
   - `volume`: 成交量
   - `vwap`: 成交量加权平均价格
   - `amount`: 成交金额（计算得出）

3. **数据质量**：
   - 无缺失值
   - 价格数据经过复权处理
   - 成交量数据完整

### 数据存储结构：

```
~/.qlib/qlib_data/cn_data/
├── calendars/
├── instruments/
├── features/
│   ├── 000001.SZ/
│   ├── 000002.SZ/
│   └── ...
└── meta.json
```

## 🔧 集成到当前应用

### 1. 创建Qlib数据适配器

```python
# app/qlib_adapter.py
import qlib
from qlib.config import REG_CN
from qlib.data import D

class QlibDataAdapter:
    def __init__(self, data_path="~/.qlib/qlib_data/cn_data"):
        qlib.init(provider_uri=data_path, region=REG_CN)
    
    def get_stock_data(self, symbol, start_date, end_date):
        """获取股票数据"""
        fields = ['$open', '$high', '$low', '$close', '$volume', '$vwap']
        data = D.features([symbol], fields, start_time=start_date, end_time=end_date)
        return data.droplevel(1, axis=1)  # 移除多级列索引
```

### 2. 更新预测服务

```python
# 在 app/prediction_service.py 中
class RealKronosPredictor:
    def __init__(self, tokenizer_path, predictor_path):
        # 加载真实的Kronos模型
        self.tokenizer = load_tokenizer(tokenizer_path)
        self.predictor = load_predictor(predictor_path)
        self.qlib_adapter = QlibDataAdapter()
    
    def predict(self, symbol, lookback=90, pred_len=10):
        # 使用Qlib获取历史数据
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=lookback+30)).strftime('%Y-%m-%d')
        
        data = self.qlib_adapter.get_stock_data(symbol, start_date, end_date)
        
        # 使用真实模型进行预测
        predictions = self.predictor.predict(data, pred_len)
        return predictions
```

## 📊 数据量建议

### 最小需求：
- **单股票预测**：101天历史数据
- **模型训练**：2-3年数据
- **回测验证**：5年以上数据

### 推荐配置：
- **历史数据**：10年以上（2014-2024）
- **股票池**：CSI300或CSI500成分股
- **更新频率**：每日更新
- **数据质量**：经过清洗和复权

## 🎯 实施优先级

### 阶段1：基础数据准备（必需）
1. 安装Qlib
2. 下载A股数据
3. 验证数据完整性

### 阶段2：模型集成（重要）
1. 下载Kronos预训练模型
2. 更新配置文件
3. 测试模型加载

### 阶段3：应用集成（优化）
1. 创建Qlib适配器
2. 更新预测服务
3. 集成到Web应用

## ⚠️ 注意事项

1. **数据大小**：完整的A股数据可能有几GB大小
2. **下载时间**：首次下载可能需要几小时
3. **存储空间**：确保有足够的磁盘空间
4. **网络要求**：需要稳定的网络连接
5. **计算资源**：真实模型需要更多内存和计算资源

## 🔗 相关资源

- [Qlib官方文档](https://github.com/microsoft/qlib)
- [Kronos模型Hub](https://huggingface.co/Kronos)
- [数据下载指南](https://qlib.readthedocs.io/en/latest/component/data.html)
- [A股数据说明](https://github.com/microsoft/qlib/blob/main/scripts/data_collector/yahoo/README.md)
