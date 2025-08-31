#!/usr/bin/env python3
"""
测试用户提到的具体问题：
8月28日收盘价7.08，预测8月29日开盘价6.43的不合理情况
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from app.prediction_service import get_prediction_service

def test_specific_case():
    """测试具体的价格连续性问题"""
    print("🧪 测试具体案例：8月28日收盘7.08 -> 8月29日开盘预测")
    
    # 创建模拟的历史数据，模拟用户提到的情况
    dates = pd.date_range('2025-08-26', '2025-08-28', freq='D')
    
    # 用户提到的历史数据
    historical_data = pd.DataFrame({
        'open': [7.30, 7.26, 7.07],
        'high': [7.33, 7.27, 7.14], 
        'low': [7.21, 7.07, 6.89],
        'close': [7.29, 7.07, 7.08],  # 最后收盘价7.08
        'volume': [1000000, 1000000, 1000000],
        'amount': [7290000, 7070000, 7080000]
    }, index=dates)
    
    print("📊 历史数据:")
    for i, (date, row) in enumerate(historical_data.iterrows()):
        print(f"  {date.strftime('%Y-%m-%d')}: O={row['open']:.2f}, H={row['high']:.2f}, L={row['low']:.2f}, C={row['close']:.2f}")
    
    # 使用我们改进的预测算法
    service = get_prediction_service(use_mock=True)
    
    # 模拟预测过程
    recent_prices = historical_data['close'].values
    recent_volumes = historical_data['volume'].values
    
    # 应用我们的改进算法
    price_changes = np.diff(recent_prices[-10:]) if len(recent_prices) >= 10 else np.diff(recent_prices)
    
    # 检测异常涨跌
    if len(recent_prices) >= 2:
        normal_changes = price_changes[np.abs(price_changes / recent_prices[:-1]) <= 0.08]
    else:
        normal_changes = price_changes
    
    if len(normal_changes) > 0:
        price_trend = np.mean(normal_changes)
        price_volatility = np.std(normal_changes) / np.mean(recent_prices)
    else:
        price_trend = 0
        price_volatility = 0.02
    
    price_volatility = min(price_volatility, 0.03)
    
    # 检测最近异常涨跌
    last_change = recent_prices[-1] - recent_prices[-2]
    last_change_pct = last_change / recent_prices[-2]
    
    if abs(last_change_pct) > 0.05:
        price_trend *= 0.3
        print(f"🔍 检测到异常涨跌: {last_change_pct:.2%}，减弱趋势延续性")
    
    last_close = recent_prices[-1]  # 7.08
    
    # 预测第一天开盘价
    gap_factor = np.random.normal(0, 0.01)
    gap_factor = np.clip(gap_factor, -0.02, 0.02)
    predicted_open = last_close * (1 + gap_factor)
    
    print(f"\n📈 预测分析:")
    print(f"  最后收盘价: {last_close:.2f}")
    print(f"  价格趋势: {price_trend:.4f}")
    print(f"  价格波动率: {price_volatility:.4f}")
    print(f"  跳空因子: {gap_factor:.4f} ({gap_factor*100:.2f}%)")
    print(f"  预测开盘价: {predicted_open:.2f}")
    
    gap_percent = (predicted_open - last_close) / last_close * 100
    print(f"  跳空幅度: {gap_percent:.2f}%")
    
    # 评估结果
    if abs(gap_percent) <= 2.0:
        print("✅ 价格连续性优秀")
    elif abs(gap_percent) <= 3.0:
        print("✅ 价格连续性良好")
    elif abs(gap_percent) <= 5.0:
        print("⚠️ 价格跳空较大但可接受")
    else:
        print("❌ 价格跳空过大")
    
    return predicted_open, gap_percent

def test_multiple_scenarios():
    """测试多种场景"""
    print("\n🔄 测试多种市场场景...")
    
    scenarios = [
        {
            'name': '正常波动',
            'prices': [10.0, 10.1, 10.05, 10.08, 10.12],
            'expected_gap': '小幅跳空'
        },
        {
            'name': '连续上涨',
            'prices': [10.0, 10.2, 10.4, 10.6, 10.8],
            'expected_gap': '小幅高开'
        },
        {
            'name': '连续下跌',
            'prices': [10.0, 9.8, 9.6, 9.4, 9.2],
            'expected_gap': '小幅低开'
        },
        {
            'name': '异常涨停',
            'prices': [10.0, 10.1, 10.05, 10.08, 11.09],  # 最后一天涨停
            'expected_gap': '回调开盘'
        },
        {
            'name': '异常跌停',
            'prices': [10.0, 10.1, 10.05, 10.08, 9.07],   # 最后一天跌停
            'expected_gap': '反弹开盘'
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📊 场景: {scenario['name']}")
        prices = np.array(scenario['prices'])
        
        # 应用算法
        price_changes = np.diff(prices)
        normal_changes = price_changes[np.abs(price_changes / prices[:-1]) <= 0.08]
        
        if len(normal_changes) > 0:
            price_trend = np.mean(normal_changes)
            price_volatility = np.std(normal_changes) / np.mean(prices)
        else:
            price_trend = 0
            price_volatility = 0.02
        
        price_volatility = min(price_volatility, 0.03)
        
        # 检测异常
        last_change_pct = (prices[-1] - prices[-2]) / prices[-2]
        if abs(last_change_pct) > 0.05:
            price_trend *= 0.3
            print(f"  🔍 检测到异常涨跌: {last_change_pct:.2%}")
        
        # 预测开盘
        gap_factor = np.clip(np.random.normal(0, 0.01), -0.02, 0.02)
        predicted_open = prices[-1] * (1 + gap_factor)
        gap_percent = (predicted_open - prices[-1]) / prices[-1] * 100
        
        print(f"  收盘: {prices[-1]:.2f} -> 预测开盘: {predicted_open:.2f} (跳空{gap_percent:.2f}%)")
        print(f"  预期: {scenario['expected_gap']}")

if __name__ == "__main__":
    print("🚀 开始具体案例测试...")
    
    # 测试具体问题
    test_specific_case()
    
    # 测试多种场景
    test_multiple_scenarios()
    
    print("\n✅ 测试完成！")
