#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方向回测脚本（滚动回测，评估不同预测步长的方向命中率）
- 复用 app/backtesting.py，避免重复代码
"""
from __future__ import annotations

import argparse
from pathlib import Path
from typing import List

from app.backtesting import run_direction_backtest


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser("方向回测（滚动评估方向命中率）")
    p.add_argument("--stock", type=str, default="000968", help="股票代码，如 000968")
    p.add_argument("--period", type=str, default="5y", choices=["6mo","1y","2y","5y"], help="历史数据周期")
    p.add_argument("--lookback", type=int, default=1024, help="模型使用的历史窗口长度")
    p.add_argument("--pred-len", type=int, default=10, help="单次预测未来步长（将至少覆盖最大 horizon）")
    p.add_argument("--horizons", type=str, default="1,5,10", help="逗号分隔的评估步长列表，例如 1,5,10")
    p.add_argument("--temperature", type=float, default=0.6, help="采样温度 T")
    p.add_argument("--top-p", type=float, default=0.8, help="核采样 top_p")
    p.add_argument("--sample-count", type=int, default=3, help="每个起点的采样次数（取中位数聚合方向）")
    p.add_argument("--step", type=int, default=5, help="滚动步长（每多少个交易日作为一个起点）")
    p.add_argument("--eps", type=float, default=0.005, help="微幅过滤阈值（真实涨跌幅<eps则不计入过滤版统计）")
    return p.parse_args()


def main():
    args = parse_args()
    horizons: List[int] = [int(x) for x in args.horizons.split(',') if x.strip()]
    summary_df, sum_csv, fig_path = run_direction_backtest(
        stock=args.stock,
        period=args.period,
        lookback=args.lookback,
        pred_len=max(args.pred_len, max(horizons)),
        horizons=horizons,
        temperature=args.temperature,
        top_p=args.top_p,
        sample_count=args.sample_count,
        step=args.step,
        eps=args.eps,
    )
    print("\n===== 方向回测摘要 =====")
    print(summary_df.to_string(index=False, formatters={'accuracy': '{:.3f}'.format, 'accuracy_filtered': '{:.3f}'.format}))
    print(f"\n结果文件: \n  摘要: {sum_csv}\n  曲线: {fig_path}")


if __name__ == "__main__":
    main()

