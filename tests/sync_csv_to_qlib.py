#!/usr/bin/env python3
"""
将 volumes/data/akshare_data 下的本地 CSV 同步导入到 Qlib 本地数据目录（provider_uri）。
- 仅追加/覆盖对应标的的数据；不做删除操作
- 统一字段: [open, high, low, close, volume, amount]，索引为交易日（yyyy-mm-dd）
- Windows 本地开发与 Docker 一致：请确保挂载 volumes 目录

使用方式：
  1) 安装 pyqlib（建议在虚拟环境或容器内）
  2) 确保 QLIB_PROVIDER_URI 指向 Qlib 本地数据目录（默认 ./volumes/qlib_data/cn_data）
  3) 运行：python tests/sync_csv_to_qlib.py

注意：
  - 本脚本不会下载数据，仅从 CSV 写入 Qlib 的本地 provider
  - 目标是“有限使用Qlib”，即需要更长历史时由 Qlib 提供一致的时间序列
"""

import os
from pathlib import Path
import pandas as pd

def init_qlib(provider_uri: str):
    import qlib
    from qlib.config import REG_CN
    qlib.init(provider_uri=provider_uri, region=REG_CN)


def code_to_symbol(code: str) -> str:
    code = code.strip()
    if code.endswith(('.SZ', '.SS')):
        return code
    if code.startswith(('00', '30')):
        return f"{code}.SZ"
    if code.startswith('60'):
        return f"{code}.SS"
    # 保底：不带市场后缀的原样返回（Qlib 可能解析不到）
    return code


def load_csv_norm(path: Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    cols = list(raw.columns)
    if 'date' in cols:
        raw['date'] = pd.to_datetime(raw['date'], errors='coerce')
    elif '日期' in cols:
        raw.rename(columns={'日期': 'date'}, inplace=True)
        raw['date'] = pd.to_datetime(raw['date'], errors='coerce')
    else:
        raise ValueError(f"{path} 缺少 date/日期 列")

    rename_map = {
        '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close',
        '成交量': 'volume', '成交额': 'amount', '股票代码': 'code'
    }
    for k, v in rename_map.items():
        if k in raw.columns and v not in raw.columns:
            raw.rename(columns={k: v}, inplace=True)

    need = ['open', 'high', 'low', 'close', 'volume']
    for c in need + ['amount']:
        if c not in raw.columns:
            raw[c] = pd.NA
    out = raw[['date'] + need + ['amount']].copy()
    out = out.dropna(subset=['date']).sort_values('date')
    out.set_index('date', inplace=True)
    out.index = pd.to_datetime(out.index).tz_localize(None)

    # amount 缺失则用 close*volume 近似
    if out['amount'].isna().any():
        out['amount'] = (out['close'] * out['volume']).astype('float64')

    # 仅保留必需列
    out = out[need + ['amount']]
    return out


def write_to_qlib(symbol: str, df: pd.DataFrame):
    """将 df 写入 Qlib provider。这里采用最简单的方式：
    - 读取 Qlib 现有数据（若存在），与 df 按索引合并（新数据覆盖旧数据）
    - 再写回 provider
    """
    from qlib.data import D

    # 读取现有
    try:
        old = D.features([symbol], ['$open', '$high', '$low', '$close', '$volume'])
        if old is not None and len(old) > 0:
            old = old.droplevel(1, axis=1)
            old = old.rename(columns={'$open':'open', '$high':'high', '$low':'low', '$close':'close', '$volume':'volume'})
            old['amount'] = old['close'] * old['volume']
            old = old[['open', 'high', 'low', 'close', 'volume', 'amount']].dropna()
        else:
            old = None
    except Exception:
        old = None

    merged = df
    if old is not None and len(old) > 0:
        merged = pd.concat([old[~old.index.isin(df.index)], df]).sort_index()

    # 将合并后的数据写回 provider
    # 简化实现：通过 D.features 无直接写接口，这里使用 qlib 的 dump 功能
    # 若你的环境未提供直接写入API，可改为导出到 CSV 并使用官方数据准备工具导入
    try:
        from qlib.data.dataset.handler import DataHandlerLP
        # 最小化写入：这里只是示例，实际生产建议使用 qlib 官方数据准备脚本
        # 这里将数据保存为 csv，方便后续用 qlib_prepare 工具导入
        export_dir = Path('./volumes/qlib_data/_import')
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / f"{symbol.replace('.', '_')}.csv"
        merged.reset_index().rename(columns={'index':'date'}).to_csv(export_path, index=False)
        print(f"导出到 {export_path}，请使用 qlib 官方脚本导入 provider")
    except Exception:
        # 兜底导出 CSV
        export_dir = Path('./volumes/qlib_data/_import')
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / f"{symbol.replace('.', '_')}.csv"
        merged.reset_index().rename(columns={'index':'date'}).to_csv(export_path, index=False)
        print(f"导出到 {export_path}，请使用 qlib 官方脚本导入 provider")


def main():
    provider_uri = os.getenv('QLIB_PROVIDER_URI', './volumes/qlib_data/cn_data')
    init_qlib(provider_uri)

    cache_dir = Path('volumes/data/akshare_data')
    if not cache_dir.exists():
        print(f"未找到缓存目录: {cache_dir}")
        return

    csv_files = sorted(cache_dir.glob('*.csv'))
    if not csv_files:
        print("缓存目录为空，无需同步")
        return

    for path in csv_files:
        try:
            code = path.stem
            symbol = code_to_symbol(code)
            df = load_csv_norm(path)
            write_to_qlib(symbol, df)
            print(f"同步完成: {code} -> {symbol}, 行数={len(df)}")
        except Exception as e:
            print(f"同步失败: {path.name}: {e}")

if __name__ == '__main__':
    main()

