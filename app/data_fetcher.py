"""
A股数据获取模块
支持通过股票代码获取历史K线数据
"""

import pandas as pd
import numpy as np
import yfinance as yf
import akshare as ak
from datetime import datetime, timedelta
import logging
from typing import Optional, Tuple
import time
from pathlib import Path

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AStockDataFetcher:
    """A股数据获取器，带本地磁盘缓存（volumes/data/akshare_data）"""

    def __init__(self, cache_dir: str = None, cache_ttl_days: int = 0):
        self.data_sources = ['akshare', 'yfinance']
        self.cache_dir = Path(cache_dir) if cache_dir else Path("volumes/data/akshare_data")
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        # 默认TTL=0：不依赖mtime判新鲜度，转为按“最后交易日”判断
        self.cache_ttl_days = cache_ttl_days
        # 最近一次获取的状态
        self.last_source: Optional[str] = None  # 'cache'|'akshare'|'yfinance'
        self.last_cache_status: Optional[str] = None  # 'hit'|'miss'|'stale'
        self.cache_written: bool = False
        # 最近一次刷新动作信息（供前端展示刷新来源与是否写入）
        self.last_refresh_source: Optional[str] = None  # 'akshare'|'yfinance'|'cache'|'unknown'
        self.last_refresh_written: bool = False
        self.last_refresh_time: Optional[datetime] = None

    def normalize_stock_code(self, stock_code: str) -> Tuple[str, str]:
        """
        标准化股票代码
        Args:
            stock_code: 输入的股票代码，支持多种格式
        Returns:
            (akshare_code, yfinance_code): 标准化后的代码
        """
        # 移除空格和转换为大写
        code = stock_code.strip().upper()

        # 如果只有6位数字，需要添加交易所后缀
        if code.isdigit() and len(code) == 6:
            if code.startswith(('60', '68')):  # 上交所
                akshare_code = code
                yfinance_code = f"{code}.SS"
            elif code.startswith(('00', '30')):  # 深交所
                akshare_code = code
                yfinance_code = f"{code}.SZ"
            else:
                raise ValueError(f"无法识别的股票代码: {code}")

        # 如果已经包含交易所后缀
        elif '.' in code:
            parts = code.split('.')
            if len(parts) == 2:
                stock_num, exchange = parts
                akshare_code = stock_num
                if exchange in ['SS', 'SH']:
                    yfinance_code = f"{stock_num}.SS"
                elif exchange == 'SZ':
                    yfinance_code = f"{stock_num}.SZ"
                else:
                    yfinance_code = code
            else:
                raise ValueError(f"股票代码格式错误: {code}")

        else:
            # 其他格式，直接使用
            akshare_code = code
            yfinance_code = code

        return akshare_code, yfinance_code

    def fetch_data_akshare(self, stock_code: str, period: str = "1y",
                          frequency: str = "daily") -> Optional[pd.DataFrame]:
        """
        使用akshare获取股票数据
        Args:
            stock_code: 股票代码
            period: 时间周期 (1y, 2y, 5y等)
            frequency: 数据频率 (daily, weekly, monthly)
        Returns:
            DataFrame: 包含OHLCV数据
        """
        try:
            akshare_code, _ = self.normalize_stock_code(stock_code)

            # 计算开始日期
            end_date = datetime.now().strftime('%Y%m%d')
            if period == "1y":
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
            elif period == "2y":
                start_date = (datetime.now() - timedelta(days=730)).strftime('%Y%m%d')
            elif period == "5y":
                start_date = (datetime.now() - timedelta(days=1825)).strftime('%Y%m%d')
            else:
                start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')

            # 获取历史数据（使用前复权 qfq）
            if frequency == "daily":
                df = ak.stock_zh_a_hist(symbol=akshare_code, period="daily",
                                       start_date=start_date, end_date=end_date, adjust="qfq")
            else:
                df = ak.stock_zh_a_hist(symbol=akshare_code, period=frequency,
                                       start_date=start_date, end_date=end_date, adjust="qfq")

            if df is None or df.empty:
                logger.warning(f"akshare未获取到数据: {stock_code}")
                return None

            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            })

            # 确保日期列为datetime类型（统一为无时区，避免 tz-naive/aware 比较错误）
            df['date'] = pd.to_datetime(df['date'], utc=False).dt.tz_localize(None)
            df = df.set_index('date')

            # 选择需要的列
            required_cols = ['open', 'high', 'low', 'close', 'volume']
            if 'amount' in df.columns:
                required_cols.append('amount')
            else:
                df['amount'] = df['volume'] * df['close']  # 估算成交额
                required_cols.append('amount')

            df = df[required_cols]

            # 数据类型转换
            for col in required_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            # 移除空值
            df = df.dropna()

            logger.info(f"akshare成功获取数据: {stock_code}, 数据量: {len(df)}")
            return df

        except Exception as e:
            logger.error(f"akshare获取数据失败 {stock_code}: {str(e)}")
            return None

    def fetch_data_yfinance(self, stock_code: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        使用yfinance获取股票数据
        Args:
            stock_code: 股票代码
            period: 时间周期
        Returns:
            DataFrame: 包含OHLCV数据
        """
        try:
            _, yfinance_code = self.normalize_stock_code(stock_code)

            # 创建ticker对象
            ticker = yf.Ticker(yfinance_code)

            # 获取历史数据
            df = ticker.history(period=period)

            if df is None or df.empty:
                logger.warning(f"yfinance未获取到数据: {stock_code}")
                return None

            # 统一索引为无时区（tz-naive），避免与 akshare/缓存比较时报 tz 冲突
            if isinstance(df.index, pd.DatetimeIndex) and getattr(df.index, 'tz', None) is not None:
                df.index = df.index.tz_localize(None)

            # 标准化列名
            df.columns = df.columns.str.lower()
            df = df.rename(columns={'adj close': 'adj_close'})

            # 添加amount列（估算）
            if 'amount' not in df.columns:
                df['amount'] = df['volume'] * df['close']

            # 选择需要的列
            required_cols = ['open', 'high', 'low', 'close', 'volume', 'amount']
            df = df[required_cols]

            # 移除空值
            df = df.dropna()

            logger.info(f"yfinance成功获取数据: {stock_code}, 数据量: {len(df)}")
            return df
        except Exception as e:
            logger.error(f"yfinance获取数据失败 {stock_code}: {str(e)}")
            return None
    def _cache_path(self, stock_code: str) -> Path:
        code = stock_code.split('.')[0]
        return self.cache_dir / f"{code}.csv"

    def _load_from_cache(self, stock_code: str) -> Optional[pd.DataFrame]:
        path = self._cache_path(stock_code)
        if not path.exists():
            self.last_cache_status = 'miss'
            return None
        try:
            # 兼容两种缓存格式：英文列名(date, open, ...) 与 中文列名(日期, 开盘, ...)
            raw = pd.read_csv(path)
            cols = list(raw.columns)
            # 日期列兼容
            if 'date' in cols:
                raw['date'] = pd.to_datetime(raw['date'], errors='coerce', utc=False).dt.tz_localize(None)
            elif '日期' in cols:
                raw.rename(columns={'日期': 'date'}, inplace=True)
                raw['date'] = pd.to_datetime(raw['date'], errors='coerce', utc=False).dt.tz_localize(None)
            else:
                raise ValueError('cache missing date column')
            # 其余列兼容
            rename_map = {
                '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close',
                '成交量': 'volume', '成交额': 'amount', '股票代码': 'code'
            }
            raw.rename(columns=rename_map, inplace=True)
            df = raw.set_index('date')
            # 仅保留所需列
            need = ['open','high','low','close','volume']
            if 'amount' not in df.columns:
                df['amount'] = df['close'] * df['volume']
            df = df[need + ['amount']]
            # 数值类型
            for c in need + ['amount']:
                df[c] = pd.to_numeric(df[c], errors='coerce')
            # 去空、排序
            df = df.dropna().sort_index()
            logger.info(f"缓存命中: {path}")
            self.last_cache_status = 'hit'
            return df
        except Exception as e:
            logger.warning(f"读取缓存失败 {path}: {e}")
            self.last_cache_status = 'miss'
            return None
    def refresh_stock_cache(self, stock_code: str, period: str = "1y", frequency: str = "daily") -> Optional[dict]:
        """增量刷新缓存：
        - 若已存在缓存：仅获取“最后一行日期+1”到今天的增量数据并合并（不截断历史）
        - 若不存在缓存：按 period 获取并写入
        返回：数据源、最后日期、总行数
        """
        # 先尝试读取旧缓存
        old = self._load_from_cache(stock_code)
        if old is not None and len(old) > 0:
            # 统一旧数据索引为 tz-naive，避免与后续增量数据比较时报 tz 冲突
            if isinstance(old.index, pd.DatetimeIndex) and getattr(old.index, 'tz', None) is not None:
                old.index = old.index.tz_localize(None)
            # 计算增量起始日期
            last_dt = pd.Timestamp(old.index.max()).normalize()
            start_dt = (last_dt + pd.Timedelta(days=1))
            today = datetime.now()
            if start_dt.normalize() > pd.Timestamp(today.date()):
                # 已是最新，无需拉取
                self.last_source = 'cache'
                self.last_cache_status = 'hit'
                return {
                    'source': self.last_source,
                    'last_date': last_dt.strftime('%Y-%m-%d'),
                    'rows': int(len(old))
                }

            # 优先 akshare 增量
            try:
                akshare_code, _ = self.normalize_stock_code(stock_code)
                inc = ak.stock_zh_a_hist(
                    symbol=akshare_code,
                    period=frequency,
                    start_date=start_dt.strftime('%Y%m%d'),
                    end_date=today.strftime('%Y%m%d'),
                    adjust="qfq",
                )
                if inc is not None and not inc.empty:
                    inc = inc.rename(columns={
                        '日期': 'date', '开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount'
                    })
                    inc['date'] = pd.to_datetime(inc['date'], utc=False).dt.tz_localize(None)
                    inc = inc.set_index('date')
                    for c in ['open','high','low','close','volume']:
                        inc[c] = pd.to_numeric(inc[c], errors='coerce')
                    if 'amount' not in inc.columns:
                        inc['amount'] = inc['close'] * inc['volume']
                    inc = inc.dropna().sort_index()
                else:
                    inc = None
                src = 'akshare' if inc is not None and len(inc) > 0 else None
            except Exception:
                inc = None
                src = None

            # 如果 akshare 无增量，尝试 yfinance 增量
            if inc is None or len(inc) == 0:
                try:
                    _, y_code = self.normalize_stock_code(stock_code)
                    import yfinance as yf
                    ticker = yf.Ticker(y_code)
                    ydf = ticker.history(start=start_dt.strftime('%Y-%m-%d'))
                    if ydf is not None and not ydf.empty:
                        # 统一索引为无时区（tz-naive）
                        if isinstance(ydf.index, pd.DatetimeIndex) and getattr(ydf.index, 'tz', None) is not None:
                            ydf.index = ydf.index.tz_localize(None)
                        ydf.columns = ydf.columns.str.lower()
                        if 'amount' not in ydf.columns:
                            ydf['amount'] = ydf['close'] * ydf['volume']
                        need = ['open','high','low','close','volume','amount']
                        inc = ydf[need].dropna().sort_index()
                        src = 'yfinance'
                except Exception:
                    inc = None

            # 合并并写缓存
            merged = old
            $added_count_placeholder
            if inc is not None and len(inc) > 0:
                added_count = int(len(inc))
                merged = pd.concat([old[~old.index.isin(inc.index)], inc]).sort_index()
                self._save_to_cache(stock_code, merged)
                self.last_source = src or 'unknown'
                self.last_cache_status = 'written'
                # 记录刷新信息
                self.last_refresh_source = self.last_source
                self.last_refresh_written = True
                self.last_refresh_time = datetime.now()
            else:
                added_count = 0
                # 没有可用增量，保持原样
                self.last_source = 'cache'
                self.last_cache_status = 'hit'
                # 记录刷新信息（无写入）
                self.last_refresh_source = self.last_source
                self.last_refresh_written = False
                self.last_refresh_time = datetime.now()

            # 确保合并后的索引为 tz-naive
            if isinstance(merged.index, pd.DatetimeIndex) and getattr(merged.index, 'tz', None) is not None:
                merged.index = merged.index.tz_localize(None)
            final_last = pd.Timestamp(merged.index.max())
            return {
                'source': self.last_source,
                'last_date': final_last.strftime('%Y-%m-%d'),
                'rows': int(len(merged)),
                'rows_added': int(added_count)
            }

        # 若无旧缓存：按 period 获取并写入（内部已做合并与写入）
        df = self.fetch_stock_data(stock_code, period=period, frequency=frequency)
        if df is None or len(df) == 0:
            return None
        # fetch_stock_data 已保存缓存并设置 last_source
        self.last_cache_status = 'written'
        # 确保新数据索引为 tz-naive
        if isinstance(df.index, pd.DatetimeIndex) and getattr(df.index, 'tz', None) is not None:
            df.index = df.index.tz_localize(None)
        last_dt = pd.Timestamp(df.index.max())
        return {
            'source': getattr(self, 'last_source', 'unknown'),
            'last_date': last_dt.strftime('%Y-%m-%d'),
            'rows': int(len(df))
        }


    def _save_to_cache(self, stock_code: str, df: pd.DataFrame) -> None:
        try:
            path = self._cache_path(stock_code)
            out = df.copy()
            # 确保有 date 列
            if isinstance(out.index, pd.DatetimeIndex):
                out = out.reset_index().rename(columns={'index':'date'})
            elif 'date' not in out.columns:
                out['date'] = out.index
                out = out.reset_index(drop=True)
            # 统一列顺序
            cols = ['date','open','high','low','close','volume','amount']
            for c in cols:
                if c not in out.columns:
                    if c == 'amount':
                        out[c] = out['close'] * out['volume']
                    else:
                        out[c] = np.nan
            out = out[cols]
            out['date'] = pd.to_datetime(out['date'], utc=False).dt.tz_localize(None).dt.strftime('%Y-%m-%d')
            out.to_csv(path, index=False)

            self.cache_written = True
            logger.info(f"缓存写入: {path} ({len(out)} 行)")
        except Exception as e:
            logger.warning(f"写入缓存失败: {e}")

    def _is_cache_fresh(self, stock_code: str) -> bool:
        """基于最后交易日判断新鲜度：如果CSV的最后一行日期 < 今天最近一个交易日，则认为过期"""
        path = self._cache_path(stock_code)
        if not path.exists():
            return False
        try:
            tail = pd.read_csv(path, usecols=['日期','date']).tail(1)
        except Exception:
            tail = pd.read_csv(path).tail(1)
        # 解析最后日期
        last_str = None
        for col in ['日期','date']:
            if col in tail.columns:
                last_str = str(tail.iloc[0][col])
                break
        if not last_str:
            return False
        last_dt = pd.to_datetime(last_str, errors='coerce', utc=False).tz_localize(None)
        if pd.isna(last_dt):
            return False
        # 计算最近一个交易日（东八区）
        now = datetime.now()
        today = pd.Timestamp(now.date())
        # 若今天是周末，回退到上一个工作日
        recent_trading = today
        while recent_trading.weekday() >= 5:
            recent_trading -= pd.Timedelta(days=1)
        return last_dt.normalize() >= recent_trading



    def fetch_stock_data(self, stock_code: str, period: str = "1y",
                        frequency: str = "daily") -> Optional[pd.DataFrame]:
        """
        获取股票数据（尝试多个数据源）
        Args:
            stock_code: 股票代码
            period: 时间周期
            frequency: 数据频率
        Returns:
            DataFrame: 股票数据
        """
        logger.info(f"开始获取股票数据: {stock_code}")
        # 不在此处重置 last_source/cache_written，以便在刷新后的一次预测中保留“已写入”状态

        # 1) 优先读缓存（新鲜缓存直接返回）
        if self._is_cache_fresh(stock_code):
            cached = self._load_from_cache(stock_code)
            if cached is not None and len(cached) > 0:
                self.last_source = 'cache'
                return cached

        # 2) 尝试在线获取（akshare -> yfinance）
        df = self.fetch_data_akshare(stock_code, period, frequency)
        src = None
        if df is not None and len(df) > 0:
            src = 'akshare'
        else:
            logger.info(f"akshare失败，尝试yfinance: {stock_code}")
            df = self.fetch_data_yfinance(stock_code, period)
            if df is not None and len(df) > 0:
                src = 'yfinance'

        if df is None or len(df) == 0:
            # 3) 如果在线也失败，但旧缓存存在，返回旧缓存（降级）
            cached = self._load_from_cache(stock_code)
            if cached is not None and len(cached) > 0:
                logger.warning("在线获取失败，使用旧缓存")
                self.last_source = 'cache'
                return cached
            logger.error(f"所有数据源都无法获取数据: {stock_code}")
            return None

        # 3) 合并增量并写缓存
        old = self._load_from_cache(stock_code)
        if old is not None and len(old) > 0:
            # 按索引合并，优先新数据
            merged = pd.concat([old[~old.index.isin(df.index)], df]).sort_index()
            df = merged
        # 写缓存
        self._save_to_cache(stock_code, df)
        self.last_source = src or 'unknown'
        return df

    def validate_data(self, df: pd.DataFrame, min_days: int = 100) -> bool:
        """
        验证数据质量
        Args:
            df: 股票数据
            min_days: 最少天数要求
        Returns:
            bool: 数据是否有效
        """
        if df is None or df.empty:
            return False

        # 检查数据量
        if len(df) < min_days:
            logger.warning(f"数据量不足: {len(df)} < {min_days}")
            return False

        # 检查必要列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        if not all(col in df.columns for col in required_cols):
            logger.warning("缺少必要的数据列")
            return False

        # 检查数据完整性
        if df[required_cols].isnull().any().any():
            logger.warning("数据包含空值")
            return False

        # 检查价格数据的合理性
        if (df['high'] < df['low']).any():
            logger.warning("数据包含不合理的价格")
            return False

        if (df['high'] < df['open']).any() or (df['high'] < df['close']).any():
            logger.warning("最高价小于开盘价或收盘价")
            return False

        if (df['low'] > df['open']).any() or (df['low'] > df['close']).any():
            logger.warning("最低价大于开盘价或收盘价")
            return False

        return True

    def get_stock_info(self, stock_code: str) -> dict:
        """
        获取股票基本信息
        Args:
            stock_code: 股票代码
        Returns:
            dict: 股票信息
        """
        try:
            akshare_code, yfinance_code = self.normalize_stock_code(stock_code)

            # 尝试获取股票信息
            try:
                # 使用akshare获取股票信息
                info = ak.stock_individual_info_em(symbol=akshare_code)
                if info is not None and not info.empty:
                    stock_info = {
                        'code': stock_code,
                        'name': info.loc[info['item'] == '股票简称', 'value'].iloc[0] if len(info.loc[info['item'] == '股票简称']) > 0 else 'Unknown',
                        'market': '上交所' if akshare_code.startswith(('60', '68')) else '深交所',
                        'source': 'akshare'
                    }
                    return stock_info
            except:
                pass

            # 如果akshare失败，尝试yfinance
            try:
                ticker = yf.Ticker(yfinance_code)
                info = ticker.info
                stock_info = {
                    'code': stock_code,
                    'name': info.get('longName', info.get('shortName', 'Unknown')),
                    'market': '上交所' if stock_code.endswith('.SS') else '深交所',
                    'source': 'yfinance'
                }
                return stock_info
            except:
                pass

            # 如果都失败，返回基本信息
            return {
                'code': stock_code,
                'name': 'Unknown',
                'market': '上交所' if akshare_code.startswith(('60', '68')) else '深交所',
                'source': 'unknown'
            }

        except Exception as e:
            logger.error(f"获取股票信息失败 {stock_code}: {str(e)}")
            return {
                'code': stock_code,
                'name': 'Unknown',
                'market': 'Unknown',
                'source': 'error'
            }


# 测试函数
def test_data_fetcher():
    """测试数据获取功能"""
    fetcher = AStockDataFetcher()

    # 测试股票代码
    test_codes = ['000001', '600000', '000001.SZ', '600000.SS']

    for code in test_codes:
        print(f"\n测试股票代码: {code}")

        # 获取股票信息
        info = fetcher.get_stock_info(code)
        print(f"股票信息: {info}")

        # 获取股票数据
        df = fetcher.fetch_stock_data(code, period="6mo")
        if df is not None:
            print(f"数据形状: {df.shape}")
            print(f"数据范围: {df.index[0]} 到 {df.index[-1]}")
            print(f"最新收盘价: {df['close'].iloc[-1]:.2f}")

            # 验证数据
            is_valid = fetcher.validate_data(df)
            print(f"数据有效性: {is_valid}")
        else:
            print("获取数据失败")


if __name__ == "__main__":
    test_data_fetcher()
