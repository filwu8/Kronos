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

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AStockDataFetcher:
    """A股数据获取器"""
    
    def __init__(self):
        self.data_sources = ['akshare', 'yfinance']
        
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
            
            # 获取历史数据
            if frequency == "daily":
                df = ak.stock_zh_a_hist(symbol=akshare_code, period="daily", 
                                       start_date=start_date, end_date=end_date)
            else:
                df = ak.stock_zh_a_hist(symbol=akshare_code, period=frequency,
                                       start_date=start_date, end_date=end_date)
            
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
            
            # 确保日期列为datetime类型
            df['date'] = pd.to_datetime(df['date'])
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
        
        # 首先尝试akshare
        df = self.fetch_data_akshare(stock_code, period, frequency)
        if df is not None and len(df) > 0:
            return df
        
        # 如果akshare失败，尝试yfinance
        logger.info(f"akshare失败，尝试yfinance: {stock_code}")
        df = self.fetch_data_yfinance(stock_code, period)
        if df is not None and len(df) > 0:
            return df
        
        logger.error(f"所有数据源都无法获取数据: {stock_code}")
        return None
    
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
