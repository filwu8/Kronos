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

