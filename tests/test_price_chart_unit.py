#!/usr/bin/env python3
"""
最小单元测试：直接调用 create_price_chart，验证图表可生成
不依赖后端API，避免环境影响
"""

import sys
from pathlib import Path

# 允许直接导入 app/streamlit_app.py
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT / 'app'))

from streamlit_app import create_price_chart  # type: ignore


def run():
    historical_data = [
        {"open": 10, "high": 11, "low": 9.5, "close": 10.5, "volume": 12000, "amount": 126000},
        {"open": 10.6, "high": 11.2, "low": 10.3, "close": 11.0, "volume": 15000, "amount": 165000},
    ]
    # 预测数据可以带 date；若无 date 也应能生成（前端已做兜底）
    predictions = [
        {"date": "2025-09-01", "close": 11.2, "open": 11.1, "high": 11.3, "low": 11.0, "volume": 13000, "amount": 145600},
        {"date": "2025-09-02", "close": 11.4, "open": 11.3, "high": 11.6, "low": 11.2, "volume": 14000, "amount": 159600},
    ]
    stock_info = {"name": "测试股票", "code": "TST"}

    fig = create_price_chart(historical_data, predictions, stock_info)
    ok = fig is not None and len(fig.data) > 0
    print("FIG_OK:", ok)
    if not ok:
        raise SystemExit(1)


if __name__ == '__main__':
    run()

