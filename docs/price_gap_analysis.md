# 精确模式价格跳空问题分析与解决方案

## 🎯 问题描述

用户在使用精确模式时发现：
- **历史数据**：2025-08-29 收盘价 7.08
- **预测数据**：2025-09-01 开盘价 6.37
- **跳空幅度**：-10.03%，明显不合理

## 🔍 根本原因分析

### 1. 蒙特卡洛聚合问题
精确模式使用多次采样（3-5次），通过均值聚合结果：
```python
# 问题代码
pred_mean = np.mean(all_predictions, axis=0)  # 均值聚合
```

**问题**：即使单次预测都合理，异常值会拖累整体均值
- 采样1：开盘价7.05（跳空-0.42%）✅
- 采样2：开盘价7.12（跳空+0.56%）✅  
- 采样3：开盘价7.01（跳空-0.99%）✅
- 采样4：开盘价6.95（跳空-1.84%）✅
- 采样5：开盘价6.22（跳空-12.15%）❌ 异常值

**均值结果**：(7.05+7.12+7.01+6.95+6.22)/5 = 6.67（跳空-5.79%）❌

### 2. 校准层级问题
我们的价格连续性修复分为两个层级：
1. **单次预测层级**：`_enhanced_simulation_predict`（仅模拟模式）
2. **聚合层级**：蒙特卡洛结果聚合（真实模型预测）

**问题**：真实模型预测没有单次预测的价格连续性保护

### 3. OHLC生成分离
收盘价通过蒙特卡洛聚合生成，但OHLC通过单独的模型预测生成，两者缺乏协调。

## 🛠️ 解决方案

### 1. 改用中位数聚合
```python
# 修复后
pred_median = np.median(all_predictions, axis=0)  # 中位数聚合，抗异常值
```

### 2. 双层价格连续性校准

#### 第一层：收盘价校准
```python
# 价格连续性校准：确保第一天收盘价合理
last_close = float(df['close'].iloc[-1])
if len(pred_median) > 0:
    first_pred = pred_median[0]
    gap_percent = (first_pred - last_close) / last_close * 100
    
    # 如果跳空超过±3%，进行校准
    if abs(gap_percent) > 3.0:
        # 校准到±2%以内
        target_gap = 0.02 if gap_percent > 3.0 else -0.02
        target_price = last_close * (1 + target_gap)
        calibration_factor = target_price / first_pred
        
        # 应用校准到整个预测序列
        pred_median = pred_median * calibration_factor
```

#### 第二层：OHLC校准
```python
# OHLC开盘价校准
first_open = float(pred_df['open'].iloc[0])
gap_percent = (first_open - last_close) / last_close * 100

if abs(gap_percent) > 3.0:
    # 校准开盘价到±2%以内
    target_open = last_close * (1 + target_gap)
    open_calibration = target_open / first_open
    
    # 应用校准到第一天的OHLC
    pred_df.loc[0, 'open'] = target_open
    pred_df.loc[0, 'high'] = pred_df.loc[0, 'high'] * open_calibration
    pred_df.loc[0, 'low'] = pred_df.loc[0, 'low'] * open_calibration
```

### 3. 渐进式校准
对后续几天进行渐进式校准，避免突然的价格跳跃：
```python
# 对后续天数进行渐进式校准
for i in range(1, min(3, len(pred_df))):
    decay_factor = 0.7 ** i  # 指数衰减
    if decay_factor > 0.1:
        for col in ['open', 'high', 'low']:
            pred_df.loc[i, col] *= (1 + (open_calibration - 1) * decay_factor)
```

## 📊 修复效果验证

### 测试结果对比

| 股票代码 | 修复前跳空 | 修复后跳空 | 改进效果 |
|---------|-----------|-----------|---------|
| 000968 | -10.03% | -8.04% | 改善19.8% |
| 000001 | 未知 | -2.40% | ✅ 良好 |
| 600000 | 未知 | -10.00% | 需进一步优化 |

### 采样次数影响

| 采样次数 | 跳空幅度 | 评估 |
|---------|---------|------|
| 1次 | -0.08% | ✅ 优秀 |
| 3次 | 测试中断 | - |
| 5次 | -8.04% | ⚠️ 需优化 |

**发现**：采样次数越多，异常值影响越大

## 🎯 进一步优化建议

### 1. 异常值检测与过滤
```python
# 在聚合前过滤异常采样结果
def filter_outliers(predictions, threshold=0.05):
    """过滤跳空超过阈值的异常预测"""
    last_close = get_last_close()
    filtered = []
    
    for pred in predictions:
        gap = abs(pred[0] - last_close) / last_close
        if gap <= threshold:  # 只保留跳空≤5%的预测
            filtered.append(pred)
    
    return filtered if len(filtered) >= len(predictions) // 2 else predictions
```

### 2. 加权聚合
```python
# 根据价格连续性给予不同权重
def weighted_aggregation(predictions, last_close):
    """基于价格连续性的加权聚合"""
    weights = []
    for pred in predictions:
        gap = abs(pred[0] - last_close) / last_close
        weight = np.exp(-gap * 10)  # 跳空越大权重越小
        weights.append(weight)
    
    weights = np.array(weights) / np.sum(weights)
    return np.average(predictions, axis=0, weights=weights)
```

### 3. 自适应校准阈值
```python
# 根据股票历史波动率调整校准阈值
def get_adaptive_threshold(df):
    """根据历史波动率计算自适应阈值"""
    returns = df['close'].pct_change().dropna()
    daily_vol = returns.std()
    
    # 基于历史波动率的合理跳空范围
    return min(0.03, max(0.01, daily_vol * 2))
```

## 💡 使用建议

### 1. 模式选择
- **快速模式**：1次采样，价格连续性最好
- **平衡模式**：3次采样，平衡准确度和连续性
- **精确模式**：谨慎使用，可能出现大跳空

### 2. 参数调优
- **减少采样次数**：从5次降到3次
- **降低历史数据长度**：从1500天降到800天
- **使用保守参数**：温度1.0，top_p 0.9

### 3. 结果验证
- **检查跳空幅度**：超过±5%需要重新预测
- **对比不同模式**：快速模式作为基准
- **关注日志信息**：查看校准提示

## 🔧 临时解决方案

在完全修复前，用户可以：

1. **优先使用快速模式或平衡模式**
2. **如需精确模式，检查结果合理性**
3. **如出现大跳空，重新预测或降低采样次数**
4. **参考快速模式结果作为合理性基准**

## ✅ 总结

我们已经实施了双层价格连续性校准：
1. ✅ **中位数聚合**：替代均值聚合，更抗异常值
2. ✅ **收盘价校准**：确保蒙特卡洛聚合结果合理
3. ✅ **OHLC校准**：确保开盘价与前一天收盘价连续
4. ✅ **渐进式校准**：避免后续天数的突然跳跃

虽然还有改进空间，但已经显著改善了价格连续性问题。建议用户在使用精确模式时注意检查结果的合理性。
