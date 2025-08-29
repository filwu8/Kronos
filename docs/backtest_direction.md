# 方向回测（Direction Accuracy Backtest）

本脚本评估未来 h 个交易日涨跌方向的命中率，支持滚动起点回测与“微幅过滤”。

- 脚本：tests/backtest_direction.py
- 数据：volumes/data/akshare_data/<code>.csv（自动刷新写入）
- 输出：volumes/backtest/<code>/direction_summary_*.csv、direction_details_*.csv、direction_accuracy_*.png

## 参数说明
- stock: 股票代码，例 000968
- period: 历史数据周期（6mo/1y/2y/5y）。建议 5y 获得更多起点
- lookback: 模型有效历史窗口（建议 1024；>512 边际收益有限）
- pred-len: 单次预测长度（必须 ≥ 最大 horizon）
- horizons: 评估步长，逗号分隔，例 1,5,10
- temperature: 采样温度（0.5–0.7 更利于方向稳定）
- top-p: 核采样概率（0.7–0.85 收敛更稳）
- sample-count: 每起点采样次数（取中位数聚合方向），UI 默认 1–3，命令行可设 3–5
- step: 滚动步长（每 step 个交易日取一个起点）
- eps: 微幅过滤阈值，真实涨跌幅 < eps 的样本不计入过滤版统计（例如 0.005=0.5%）

## 运行（Windows + .venv）
1. 创建并激活虚拟环境（如尚未创建）
   - python -m venv .venv
   - .venv\Scripts\activate
2. 安装依赖（已在 app/requirements.txt 声明）
   - pip install -r app/requirements.txt
3. 执行回测
   - python tests/backtest_direction.py --stock 000968 --period 5y --lookback 1024 \
     --pred-len 10 --horizons 1,5,10 --temperature 0.6 --top-p 0.8 --sample-count 3 --step 5 --eps 0.005

## 输出解读
- direction_summary_*.csv
  - horizon: 预测步长（交易日）
  - accuracy: 全样本方向准确率
  - accuracy_filtered: 过滤微幅后的方向准确率
  - total/hits 与 total_filtered/hits_filtered：分子分母
- direction_details_*.csv
  - 每个起点/步长的逐条记录，可定位典型成功/失败样例
- direction_accuracy_*.png
  - 准确率随步长变化曲线，通常 h 越大准确率越低

## 建议参数组合（以方向为主）
- period=5y, lookback=1024, horizons=1,5,10, pred-len≥10
- temperature: 0.5/0.6/0.7 对比；top-p: 0.7/0.8/0.85 对比
- sample-count: 3（或 5，经由 API 路径），方向采用“中位数路径”或“多数投票”

## 注意
- 刷新逻辑当前按指定 period 写缓存；若手动点击前端“刷新该股票数据”使用默认 1y，会将缓存截短。
- 预测服务的模型有效上下文约 512；lookback>512 边际效益有限，但可改善稳态估计与展示。
- 回测严格使用“当时可见”历史，避免未来信息泄漏；脚本内部不做任何兜底模拟。

