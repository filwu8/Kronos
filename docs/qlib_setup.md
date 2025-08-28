# Qlib 本地数据使用与同步

本项目支持“有限使用 Qlib”：当需要较长历史窗口（如 lookback≥1200 或 period ∈ {2y,5y}）时，优先从 Qlib 的本地 provider 读取历史数据，否则使用在线数据源（akshare→yfinance）。

- 相关环境变量
  - QLIB_PROVIDER_URI: Qlib provider 路径（默认 ./volumes/qlib_data/cn_data）
  - QLIB_LOOKBACK_THRESHOLD: 触发 Qlib 优先的 lookback 阈值，默认 1200（≈5年交易日）

## 一、初始化 Qlib 本地 provider（简要）

1. 安装 pyqlib（建议在虚拟环境或容器内）
2. 准备数据（任选其一）：
   - 使用 qlib 提供的数据准备脚本构建 cn_data
   - 或按下文将已有 CSV 缓存导出为 csv，随后导入到 provider

## 二、将本地 CSV 同步到 Qlib（推荐）

- 本地 CSV 缓存路径：volumes/data/akshare_data
- 同步脚本：tests/sync_csv_to_qlib.py
- 用法：
  1. 设置 QLIB_PROVIDER_URI（若使用默认则无需设置）
  2. 运行：

     python tests/sync_csv_to_qlib.py

- 脚本行为：
  - 读取缓存 CSV（兼容中文/英文字段名），标准化为 [open, high, low, close, volume, amount]，索引为 date（yyyy-mm-dd）
  - 与 Qlib 现有数据按索引合并（新覆盖旧）
  - 导出到 volumes/qlib_data/_import/{SYMBOL}.csv，供 qlib 官方工具导入 provider

提示：不同环境下直接向 provider 写入的 API 支持可能有限，所以采用“导出 CSV + 官方导入”的方式更稳健。

## 三、与项目的交互

- prediction_service 中：
  - 当 lookback≥QLIB_LOOKBACK_THRESHOLD 或 period∈{2y,5y}，优先调用 QlibDataAdapter.get_stock_df
  - 失败时回退在线源；最终 historical_data 仍按 lookback 截取

## 四、Windows 与 Docker 一致性

- volumes 目录为持久化数据目录；本地与容器内均挂载到相同路径，确保 CSV 与 Qlib 数据可复用
- 建议在 Windows 开发环境中也保持默认路径，以减少配置差异

