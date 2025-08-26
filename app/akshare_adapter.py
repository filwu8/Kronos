#!/usr/bin/env python3
"""
akshare数据适配器 - 将akshare数据转换为Kronos格式
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Tuple, Optional

class AkshareDataAdapter:
    """akshare数据适配器"""
    
    def __init__(self, data_dir: str = None):
        # 使用统一配置管理
        if data_dir is None:
            try:
                import sys
                sys.path.append("volumes")
                from config.settings import DATA_DIR
                self.data_dir = Path(DATA_DIR)
            except ImportError:
                # 兼容性回退
                self.data_dir = Path("volumes/data/akshare_data")
        else:
            self.data_dir = Path(data_dir)
        
    def get_stock_data(self, stock_code: str, lookback: int = 100, period: str = "1y") -> Optional[pd.DataFrame]:
        """
        获取股票数据

        Args:
            stock_code: 股票代码 (如 "000001")
            lookback: 历史数据长度
            period: 历史数据周期 ("6mo", "1y", "2y", "5y")

        Returns:
            DataFrame with columns: [open, high, low, close, volume, amount]
        """
        # 查找数据文件
        csv_file = self.data_dir / f"{stock_code}.csv"
        
        # 确保数据可用（如果不存在则自动下载）
        if not self.ensure_data_available(stock_code):
            print(f"❌ 无法获取股票 {stock_code} 的数据")
            return None
        
        try:
            # 读取数据
            df = pd.read_csv(csv_file)
            
            # 重命名列以匹配Kronos格式
            column_mapping = {
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close', 
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount'
            }
            
            df = df.rename(columns=column_mapping)
            
            # 确保数据类型正确
            df['date'] = pd.to_datetime(df['date'])
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 按日期排序
            df = df.sort_values('date')
            
            # 移除缺失值
            df = df.dropna()

            # 根据period参数过滤时间范围
            end_date = df['date'].max()

            # 计算开始日期
            period_mapping = {
                "6mo": 6 * 30,      # 6个月
                "1y": 365,          # 1年
                "2y": 2 * 365,      # 2年
                "5y": 5 * 365       # 5年
            }

            days_back = period_mapping.get(period, 365)  # 默认1年
            start_date = end_date - pd.Timedelta(days=days_back)

            # 过滤时间范围
            df = df[df['date'] >= start_date]

            print(f"📊 股票 {stock_code} 数据范围: {df['date'].min().strftime('%Y-%m-%d')} 到 {df['date'].max().strftime('%Y-%m-%d')} ({len(df)} 条记录)")

            # 优先保证用户选择的period时间范围
            # RTX 5090性能强劲，支持大数据量处理
            if len(df) > lookback:
                df = df.tail(lookback)
                print(f"📊 根据用户设置限制为最近 {lookback} 条记录: {df['date'].min().strftime('%Y-%m-%d')} 到 {df['date'].max().strftime('%Y-%m-%d')}")
            else:
                print(f"📊 保持period({period})范围内的所有数据: {len(df)} 条记录 (RTX 5090性能充足)")
            
            # 重置索引
            df = df.reset_index(drop=True)
            
            # 返回Kronos需要的格式 [open, high, low, close, volume, amount]
            result = df[['open', 'high', 'low', 'close', 'volume', 'amount']].copy()
            
            print(f"✅ 获取 {stock_code} 数据: {len(result)} 条记录")
            return result
            
        except Exception as e:
            print(f"❌ 读取 {stock_code} 数据失败: {str(e)}")
            return None
    
    def get_stock_info(self, stock_code: str) -> dict:
        """获取股票基本信息"""
        # 股票名称映射 (简化版)
        stock_names = {
            "000001": "平安银行",
            "000002": "万科A", 
            "000004": "*ST国华",
            "000005": "世纪星源",
            "000006": "深振业A",
            "000007": "全新好",
            "000008": "神州高铁",
            "000009": "中国宝安",
            "000010": "美丽生态"
        }
        
        return {
            "code": stock_code,
            "name": stock_names.get(stock_code, f"股票{stock_code}"),
            "market": "深圳" if stock_code.startswith("00") else "上海"
        }
    
    def prepare_kronos_input(self, stock_code: str, lookback: int = 90, period: str = "1y") -> Tuple[Optional[np.ndarray], Optional[dict]]:
        """
        准备Kronos模型输入

        Args:
            stock_code: 股票代码
            lookback: 历史数据长度
            period: 历史数据周期

        Returns:
            (input_data, stock_info): 输入数据和股票信息
        """
        # 获取数据
        df = self.get_stock_data(stock_code, lookback, period)
        if df is None:
            return None, None
        
        # 转换为numpy数组
        input_data = df.values.astype(np.float32)
        
        # 获取股票信息
        stock_info = self.get_stock_info(stock_code)
        
        return input_data, stock_info
    
    def list_available_stocks(self) -> list:
        """列出可用的股票代码"""
        if not self.data_dir.exists():
            return []
        
        csv_files = list(self.data_dir.glob("*.csv"))
        stock_codes = [f.stem for f in csv_files]
        
        return sorted(stock_codes)

    def auto_download_missing_data(self, stock_code: str) -> bool:
        """自动下载缺失的股票数据"""
        try:
            import akshare as ak
            import time

            print(f"正在下载股票 {stock_code} 的数据...")

            # 获取股票历史数据 (5年)
            end_date = datetime.now().strftime('%Y%m%d')
            start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')

            # 使用akshare获取数据
            df = ak.stock_zh_a_hist(
                symbol=stock_code,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"
            )

            if df is not None and not df.empty:
                # 重命名列以匹配我们的格式
                df = df.rename(columns={
                    '开盘': 'open',
                    '最高': 'high',
                    '最低': 'low',
                    '收盘': 'close',
                    '成交量': 'volume',
                    '成交额': 'amount'
                })

                # 确保目录存在
                self.data_dir.mkdir(parents=True, exist_ok=True)

                # 保存数据
                file_path = self.data_dir / f"{stock_code}.csv"
                df.to_csv(file_path, index=False)

                print(f"✅ 股票 {stock_code} 数据下载完成: {len(df)} 条记录")
                return True
            else:
                print(f"❌ 无法获取股票 {stock_code} 的数据")
                return False

        except Exception as e:
            print(f"❌ 下载股票 {stock_code} 数据失败: {str(e)}")
            return False

    def ensure_data_available(self, stock_code: str) -> bool:
        """确保股票数据可用，如果不存在则自动下载"""
        file_path = self.data_dir / f"{stock_code}.csv"

        if file_path.exists():
            return True

        print(f"股票 {stock_code} 数据不存在，尝试自动下载...")
        return self.auto_download_missing_data(stock_code)
