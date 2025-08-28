import os
from datetime import datetime, timedelta
from typing import Optional
import pandas as pd

class QlibDataAdapter:
    """
    轻量Qlib数据适配器（若系统安装了pyqlib且本地数据就绪，则可用）。
    provider_uri 默认指向 ./volumes/qlib_data/cn_data，便于持久化复用。
    """
    def __init__(self, provider_uri: Optional[str] = None):
        self.available = False
        self.provider_uri = provider_uri or os.getenv("QLIB_PROVIDER_URI", "./volumes/qlib_data/cn_data")
        try:
            import qlib
            from qlib.config import REG_CN
            qlib.init(provider_uri=self.provider_uri, region=REG_CN)
            self.available = True
        except Exception:
            self.available = False

    def get_stock_df(self, symbol: str, lookback: int = 100, predict_window: int = 10) -> Optional[pd.DataFrame]:
        """
        返回格式为 [open, high, low, close, volume, amount] 且以交易日为索引的DataFrame。
        """
        if not self.available:
            return None
        try:
            import pandas as pd
            from qlib.data import D

            end_date = datetime.now().strftime('%Y-%m-%d')
            # 预留额外缓冲，避免因交易日/节假日导致窗口不足
            start_date = (datetime.now() - timedelta(days=lookback + predict_window + 180)).strftime('%Y-%m-%d')
            fields = ['$open', '$high', '$low', '$close', '$volume']
            data = D.features([symbol], fields, start_time=start_date, end_time=end_date)
            if data is None or len(data) == 0:
                return None
            # 多级列 -> 单级，形如 (datetime, field)
            df = data.droplevel(1, axis=1)
            df = df.rename(columns={
                '$open': 'open', '$high': 'high', '$low': 'low', '$close': 'close', '$volume': 'volume'
            })
            # 构造 amount 列（简单用收盘价*成交量近似）
            df['amount'] = df['close'] * df['volume']
            # 去缺失
            df = df.dropna()
            # 仅保留必需列
            df = df[['open', 'high', 'low', 'close', 'volume', 'amount']]
            return df
        except Exception:
            return None



    @staticmethod
    def code_to_symbol(code: str) -> str:
        code = (code or '').strip()
        if code.endswith(('.SZ', '.SS')):
            return code
        if code.startswith(('00', '30')):
            return f"{code}.SZ"
        if code.startswith('60'):
            return f"{code}.SS"
        return code

    def export_symbol_csv_for_import(self, symbol: str, df: pd.DataFrame) -> str:
        """
        将传入的 df（必须包含列: open, high, low, close, volume, amount；索引为日期）
        合并现有 Qlib 数据后导出到 provider 的 _import 目录下，便于后续使用官方工具导入。
        返回导出文件路径字符串。
        """
        # 规范化索引与列
        out = df.copy()
        if not isinstance(out.index, pd.DatetimeIndex):
            if 'date' in out.columns:
                out = out.set_index(pd.to_datetime(out['date']))
            else:
                raise ValueError('df 需要日期索引或包含 date 列')
        out.index = pd.to_datetime(out.index).tz_localize(None)
        need = ['open', 'high', 'low', 'close', 'volume', 'amount']
        for c in need:
            if c not in out.columns:
                if c == 'amount':
                    out['amount'] = out.get('close', 0) * out.get('volume', 0)
                else:
                    out[c] = 0.0
        out = out[need]

        # 尝试读取现有数据并合并
        merged = out
        try:
            from qlib.data import D
            ex = D.features([symbol], ['$open', '$high', '$low', '$close', '$volume'])
            if ex is not None and len(ex) > 0:
                ex = ex.droplevel(1, axis=1)
                ex = ex.rename(columns={'$open':'open', '$high':'high', '$low':'low', '$close':'close', '$volume':'volume'})
                ex['amount'] = ex['close'] * ex['volume']
                ex = ex[['open', 'high', 'low', 'close', 'volume', 'amount']].dropna()
                merged = pd.concat([ex[~ex.index.isin(out.index)], out]).sort_index()
        except Exception:
            pass

        # 导出 CSV 到 _import 目录
        from pathlib import Path
        export_dir = Path(self.provider_uri).parent / '_import'
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / f"{symbol.replace('.', '_')}.csv"
        merged.reset_index().rename(columns={'index':'date'}).to_csv(export_path, index=False)
        return str(export_path)
