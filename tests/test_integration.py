#!/usr/bin/env python3
"""测试真实模型集成"""

import sys
sys.path.append('app')

from akshare_adapter import AkshareDataAdapter

def test_data_adapter():
    """测试数据适配器"""
    print("🔍 测试数据适配器...")
    
    adapter = AkshareDataAdapter()
    
    # 列出可用股票
    stocks = adapter.list_available_stocks()
    print(f"✅ 可用股票数量: {len(stocks)}")
    print(f"样本股票: {stocks[:5]}")
    
    # 测试获取数据
    if stocks:
        test_stock = stocks[0]
        data, info = adapter.prepare_kronos_input(test_stock, lookback=50)
        
        if data is not None:
            print(f"✅ 数据获取成功: {test_stock}")
            print(f"   数据形状: {data.shape}")
            print(f"   股票信息: {info}")
            print(f"   最新价格: {data[-1, 3]:.2f}")
            return True
        else:
            print(f"❌ 数据获取失败: {test_stock}")
            return False
    else:
        print("❌ 没有可用的股票数据")
        return False

if __name__ == "__main__":
    test_data_adapter()
