#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方向回测工具（供测试脚本与前端 UI 复用）
- 核心方法：run_direction_backtest(...)
- 产物：summary_df（方向准确率汇总）、details_df（逐条记录，可选）、保存 CSV/图
- 外部依赖：AStockDataFetcher、get_prediction_service（真实模型）
"""
from __future__ import annotations

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from .data_fetcher import AStockDataFetcher
from .prediction_service import get_prediction_service


def _ensure_period_cache(fetcher: AStockDataFetcher, stock: str, period: str) -> pd.DataFrame:
    info = fetcher.refresh_stock_cache(stock, period=period)
    if not info:
        raise RuntimeError(f"无法刷新 {stock} 数据缓存（period={period}）")
    df = fetcher._load_from_cache(stock)
    if df is None or len(df) == 0:
        raise RuntimeError("缓存读取失败或为空")
    df = df.sort_index()
    # 校验跨度是否满足期望
    expected_days = {"6mo": 6*30, "1y": 365, "2y": 2*365, "5y": 5*365}.get(period, 365)
    actual_days = (df.index.max() - df.index.min()).days
    if actual_days < expected_days * 0.8:
        full = fetcher.fetch_stock_data(stock, period=period)
        if full is not None and len(full) > 0:
            df = full.sort_index()
    return df


def _predict_one(service,
                 df_hist: pd.DataFrame,
                 lookback: int,
                 pred_len: int,
                 T: float,
                 top_p: float,
                 sample_count: int) -> pd.DataFrame:
    # 保护：lookback 不超过可用历史
    if len(df_hist) < lookback:
        lookback = len(df_hist)
    x_df = df_hist.iloc[-lookback:][['open','high','low','close','volume','amount']].copy()
    x_ts = pd.Series(x_df.index)
    last_date = pd.to_datetime(df_hist.index[-1])
    y_ts = pd.Series(pd.bdate_range(start=last_date + pd.Timedelta(days=1), periods=pred_len))

    preds_close = []
    pred_df_ref = None
    for _ in range(max(1, sample_count)):
        pred_df = service.predictor.predict(
            df=x_df,
            x_timestamp=x_ts,
            y_timestamp=y_ts,
            pred_len=pred_len,
            T=T,
            top_p=top_p,
            top_k=0,
            sample_count=1,
            verbose=False,
        )
        pred_df_ref = pred_df
        preds_close.append(pd.to_numeric(pred_df['close'], errors='coerce').values)
    preds_close = np.vstack(preds_close)
    close_med = np.nanmedian(preds_close, axis=0)
    out = pred_df_ref.copy()
    out['close'] = close_med
    return out


def run_direction_backtest(stock: str,
                           period: str = "5y",
                           lookback: int = 1024,
                           pred_len: int = 10,
                           horizons: List[int] = [1,5,10],
                           temperature: float = 0.6,
                           top_p: float = 0.8,
                           sample_count: int = 3,
                           step: int = 5,
                           eps: float = 0.005,
                           save_dir: Optional[Path] = None) -> Tuple[pd.DataFrame, Path, Path]:
    """
    执行方向回测，返回 (summary_df, summary_csv_path, fig_path)
    - 会写入 details CSV（与 summary 同目录）
    """
    save_dir = save_dir or Path(f"volumes/backtest/{stock}")
    save_dir.mkdir(parents=True, exist_ok=True)

    fetcher = AStockDataFetcher()
    service = get_prediction_service()
    if not getattr(service, 'model_loaded', False):
        raise RuntimeError("模型未加载成功；请检查依赖/设备")

    df = _ensure_period_cache(fetcher, stock, period)

    max_h = max(horizons + [pred_len])
    pred_len = max(pred_len, max_h)

    start_idx = max(lookback, 50)
    end_idx = len(df) - max_h
    if end_idx <= start_idx:
        raise RuntimeError(f"样本不足：len(df)={len(df)}, lookback={lookback}, max_h={max_h}")

    totals = {h: 0 for h in horizons}
    hits = {h: 0 for h in horizons}
    totals_filt = {h: 0 for h in horizons}
    hits_filt = {h: 0 for h in horizons}

    rows_detail = []

    for i in range(start_idx, end_idx + 1, max(1, step)):
        df_hist = df.iloc[:i]
        cur_close = float(df_hist['close'].iloc[-1])
        pred_df = _predict_one(service, df_hist, lookback, pred_len, temperature, top_p, sample_count)
        for h in horizons:
            true_close = float(df['close'].iloc[i - 1 + h])
            pred_close = float(pred_df['close'].iloc[h - 1])
            true_ret = (true_close - cur_close) / cur_close
            pred_ret = (pred_close - cur_close) / cur_close
            ok = 1 if np.sign(true_ret) == np.sign(pred_ret) else 0
            totals[h] += 1
            hits[h] += ok
            if abs(true_ret) >= eps:
                totals_filt[h] += 1
                hits_filt[h] += ok
            rows_detail.append({
                'idx': i,
                'date_cur': df_hist.index[-1].strftime('%Y-%m-%d'),
                'h': h,
                'cur_close': cur_close,
                'pred_close': pred_close,
                'true_close': true_close,
                'pred_ret': pred_ret,
                'true_ret': true_ret,
                'hit': ok,
                'hit_filt': ok if abs(true_ret) >= eps else np.nan,
            })

    summary = []
    for h in horizons:
        acc = hits[h] / totals[h] if totals[h] > 0 else np.nan
        acc_f = hits_filt[h] / totals_filt[h] if totals_filt[h] > 0 else np.nan
        summary.append({'horizon': h, 'total': totals[h], 'hits': hits[h], 'accuracy': acc,
                        'total_filtered': totals_filt[h], 'hits_filtered': hits_filt[h], 'accuracy_filtered': acc_f,
                        'eps': eps})
    summary_df = pd.DataFrame(summary).sort_values('horizon')

    # 写出 CSV
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    sum_csv = save_dir / f"direction_summary_{ts}.csv"
    det_csv = save_dir / f"direction_details_{ts}.csv"
    summary_df.to_csv(sum_csv, index=False)
    pd.DataFrame(rows_detail).to_csv(det_csv, index=False)

    # 画图
    try:
        fig, ax = plt.subplots(figsize=(6,4))
        ax.plot(summary_df['horizon'], summary_df['accuracy']*100, marker='o', label='All')
        if summary_df['accuracy_filtered'].notna().any():
            ax.plot(summary_df['horizon'], summary_df['accuracy_filtered']*100, marker='s', label='Filtered')
        ax.set_xlabel('预测步长 h (交易日)')
        ax.set_ylabel('方向准确率 (%)')
        ax.set_title(f'{stock} 方向回测 (period={period}, lookback={lookback})')
        ax.grid(True, ls='--', alpha=0.4)
        ax.legend()
        fig.tight_layout()
        fig_path = save_dir / f"direction_accuracy_{ts}.png"
        fig.savefig(fig_path, dpi=150)
    except Exception:
        fig_path = save_dir / f"direction_accuracy_{ts}.png"

    return summary_df, sum_csv, fig_path

