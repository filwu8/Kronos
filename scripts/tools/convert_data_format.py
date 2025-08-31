#!/usr/bin/env python3
"""
数据格式转换脚本
将akshare/tushare数据转换为Qlib格式
"""

import pandas as pd
from pathlib import Path
import qlib
from qlib.config import REG_CN

def convert_akshare_to_qlib():
    """将akshare数据转换为Qlib格式"""
    print("🔄 转换akshare数据到Qlib格式...")
    
    akshare_dir = Path("data/akshare_data")
    if not akshare_dir.exists():
        print("❌ akshare数据目录不存在")
        return
    
    # 初始化Qlib
    qlib_data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    qlib.init(provider_uri=str(qlib_data_dir), region=REG_CN)
    
    csv_files = list(akshare_dir.glob("*.csv"))
    print(f"找到 {len(csv_files)} 个数据文件")
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            # 重命名列以匹配Qlib格式
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
            df['date'] = pd.to_datetime(df['date'])
            df = df.set_index('date')
            
            # 计算vwap
            if 'amount' in df.columns and 'volume' in df.columns:
                df['vwap'] = df['amount'] / df['volume']
            
            print(f"✅ 转换 {csv_file.name}: {len(df)} 条记录")
            
        except Exception as e:
            print(f"❌ 转换 {csv_file.name} 失败: {str(e)}")

if __name__ == "__main__":
    convert_akshare_to_qlib()
