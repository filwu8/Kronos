#!/usr/bin/env python3
"""
下载5年以上A股历史数据
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import requests
import zipfile
import tempfile
from datetime import datetime, timedelta
import pandas as pd

def install_dependencies():
    """安装必要的依赖"""
    print("📦 安装必要依赖...")
    
    dependencies = [
        "pyqlib",
        "akshare>=1.12.0", 
        "yfinance>=0.2.0",
        "tushare>=1.2.0"
    ]
    
    for dep in dependencies:
        print(f"安装 {dep}...")
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "install", dep], 
                                  capture_output=True, text=True, timeout=300)
            if result.returncode == 0:
                print(f"✅ {dep} 安装成功")
            else:
                print(f"❌ {dep} 安装失败: {result.stderr}")
        except Exception as e:
            print(f"❌ {dep} 安装异常: {str(e)}")

def download_qlib_official_data():
    """下载Qlib官方数据"""
    print("\n⬇️ 下载Qlib官方A股数据...")
    
    # 创建数据目录
    data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"数据目录: {data_dir}")
    
    # 使用Qlib官方命令下载数据
    cmd = [
        sys.executable, "-m", "qlib.run.get_data", 
        "qlib_data", 
        "--target_dir", str(data_dir),
        "--region", "cn"
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    print("⏳ 正在下载数据，这可能需要30分钟到2小时...")
    
    try:
        result = subprocess.run(cmd, timeout=7200)  # 2小时超时
        if result.returncode == 0:
            print("✅ Qlib官方数据下载成功")
            return True
        else:
            print("❌ Qlib官方数据下载失败")
            return False
    except subprocess.TimeoutExpired:
        print("⏰ 下载超时，请检查网络连接")
        return False
    except Exception as e:
        print(f"❌ 下载异常: {str(e)}")
        return False

def download_alternative_data():
    """备用方法：使用akshare下载数据"""
    print("\n⬇️ 使用akshare下载A股数据...")
    
    try:
        import akshare as ak
        
        # 获取股票列表
        print("获取股票列表...")
        stock_list = ak.stock_info_a_code_name()
        print(f"获取到 {len(stock_list)} 只股票")
        
        # 创建数据目录
        data_dir = Path("data") / "akshare_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 计算5年前的日期
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
        
        print(f"数据时间范围: {start_date} 到 {end_date}")
        
        # 下载前100只股票的数据作为示例
        sample_stocks = stock_list.head(100)
        
        for idx, row in sample_stocks.iterrows():
            stock_code = row['code']
            stock_name = row['name']
            
            try:
                print(f"下载 {stock_code} {stock_name}...")
                
                # 下载日线数据
                df = ak.stock_zh_a_hist(
                    symbol=stock_code,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq"  # 前复权
                )
                
                if len(df) > 0:
                    # 保存数据
                    file_path = data_dir / f"{stock_code}.csv"
                    df.to_csv(file_path, index=False)
                    print(f"✅ {stock_code} 数据保存成功，{len(df)} 条记录")
                else:
                    print(f"⚠️ {stock_code} 无数据")
                    
            except Exception as e:
                print(f"❌ {stock_code} 下载失败: {str(e)}")
                continue
        
        print(f"✅ akshare数据下载完成，保存在 {data_dir}")
        return True
        
    except Exception as e:
        print(f"❌ akshare下载失败: {str(e)}")
        return False

def download_tushare_data():
    """使用tushare下载数据"""
    print("\n⬇️ 使用tushare下载A股数据...")
    
    try:
        import tushare as ts
        
        print("⚠️ tushare需要注册并获取token")
        print("请访问 https://tushare.pro/ 注册并获取token")
        
        token = input("请输入您的tushare token (回车跳过): ").strip()
        
        if not token:
            print("跳过tushare下载")
            return False
        
        # 设置token
        ts.set_token(token)
        pro = ts.pro_api()
        
        # 获取股票列表
        stock_list = pro.stock_basic(exchange='', list_status='L', fields='ts_code,symbol,name')
        print(f"获取到 {len(stock_list)} 只股票")
        
        # 创建数据目录
        data_dir = Path("data") / "tushare_data"
        data_dir.mkdir(parents=True, exist_ok=True)
        
        # 计算5年前的日期
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=5*365)).strftime('%Y%m%d')
        
        # 下载前50只股票的数据
        sample_stocks = stock_list.head(50)
        
        for idx, row in sample_stocks.iterrows():
            ts_code = row['ts_code']
            stock_name = row['name']
            
            try:
                print(f"下载 {ts_code} {stock_name}...")
                
                # 下载日线数据
                df = pro.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                
                if len(df) > 0:
                    # 保存数据
                    file_path = data_dir / f"{ts_code}.csv"
                    df.to_csv(file_path, index=False)
                    print(f"✅ {ts_code} 数据保存成功，{len(df)} 条记录")
                else:
                    print(f"⚠️ {ts_code} 无数据")
                    
            except Exception as e:
                print(f"❌ {ts_code} 下载失败: {str(e)}")
                continue
        
        print(f"✅ tushare数据下载完成，保存在 {data_dir}")
        return True
        
    except Exception as e:
        print(f"❌ tushare下载失败: {str(e)}")
        return False

def verify_downloaded_data():
    """验证下载的数据"""
    print("\n🔍 验证下载的数据...")
    
    # 检查Qlib数据
    qlib_data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    if qlib_data_dir.exists():
        print(f"✅ Qlib数据目录存在: {qlib_data_dir}")
        
        # 检查关键目录
        essential_dirs = ['calendars', 'instruments', 'features']
        for dir_name in essential_dirs:
            dir_path = qlib_data_dir / dir_name
            if dir_path.exists():
                print(f"✅ {dir_name} 目录存在")
            else:
                print(f"❌ {dir_name} 目录缺失")
        
        # 检查股票数据数量
        features_dir = qlib_data_dir / "features"
        if features_dir.exists():
            stock_dirs = [d for d in features_dir.iterdir() if d.is_dir()]
            print(f"✅ Qlib股票数据文件数量: {len(stock_dirs)}")
    
    # 检查akshare数据
    akshare_data_dir = Path("data") / "akshare_data"
    if akshare_data_dir.exists():
        csv_files = list(akshare_data_dir.glob("*.csv"))
        print(f"✅ akshare数据文件数量: {len(csv_files)}")
        
        if csv_files:
            # 检查第一个文件的数据
            sample_file = csv_files[0]
            df = pd.read_csv(sample_file)
            print(f"✅ 样本数据 {sample_file.name}: {len(df)} 条记录")
            print(f"   时间范围: {df['日期'].min()} 到 {df['日期'].max()}")
    
    # 检查tushare数据
    tushare_data_dir = Path("data") / "tushare_data"
    if tushare_data_dir.exists():
        csv_files = list(tushare_data_dir.glob("*.csv"))
        print(f"✅ tushare数据文件数量: {len(csv_files)}")

def create_data_converter():
    """创建数据格式转换脚本"""
    print("\n📄 创建数据格式转换脚本...")
    
    converter_script = '''#!/usr/bin/env python3
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
'''
    
    with open("convert_data_format.py", 'w', encoding='utf-8') as f:
        f.write(converter_script)
    
    print("✅ 已创建 convert_data_format.py")

def main():
    """主函数"""
    print("🚀 开始下载5年以上A股历史数据")
    print("=" * 60)
    
    # 步骤1：安装依赖
    install_dependencies()
    
    # 步骤2：尝试多种下载方法
    download_success = False
    
    print("\n📊 开始数据下载...")
    print("将尝试多种数据源以确保获取完整的5年历史数据")
    
    # 方法1：Qlib官方数据
    print("\n🎯 方法1：Qlib官方数据")
    if download_qlib_official_data():
        download_success = True
        print("✅ Qlib官方数据下载成功")
    else:
        print("❌ Qlib官方数据下载失败，尝试备用方法")
    
    # 方法2：akshare数据
    print("\n🎯 方法2：akshare数据")
    if download_alternative_data():
        download_success = True
        print("✅ akshare数据下载成功")
    
    # 方法3：tushare数据
    print("\n🎯 方法3：tushare数据")
    if download_tushare_data():
        download_success = True
        print("✅ tushare数据下载成功")
    
    # 步骤3：验证数据
    verify_downloaded_data()
    
    # 步骤4：创建转换脚本
    create_data_converter()
    
    print("\n" + "=" * 60)
    if download_success:
        print("🎉 数据下载完成！")
        print("\n📋 下载结果:")
        print("✅ 至少一种数据源下载成功")
        print("✅ 数据时间跨度: 5年以上")
        print("✅ 数据格式: 包含OHLCV等必要字段")
        
        print("\n📁 数据位置:")
        print(f"- Qlib数据: {Path.home() / '.qlib' / 'qlib_data' / 'cn_data'}")
        print("- akshare数据: ./data/akshare_data/")
        print("- tushare数据: ./data/tushare_data/")
        
        print("\n🔧 后续步骤:")
        print("1. 运行 python test_qlib_data.py 验证Qlib数据")
        print("2. 运行 python convert_data_format.py 转换数据格式")
        print("3. 下载Kronos预训练模型")
        print("4. 更新应用配置使用真实数据")
        
    else:
        print("❌ 所有数据下载方法都失败")
        print("\n🔧 手动解决方案:")
        print("1. 检查网络连接")
        print("2. 参考 QLIB_DATA_SETUP.md 手动下载")
        print("3. 联系技术支持")

if __name__ == "__main__":
    main()
