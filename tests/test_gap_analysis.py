#!/usr/bin/env python3
"""
分析多个股票的跳空问题
"""

import requests
import json

def test_stock_gaps():
    """测试多个股票的跳空情况"""
    stocks = ['000968', '000001', '000002', '600000', '600036']
    
    print("🔍 分析多个股票的跳空情况...")
    print(f"{'股票代码':<8} {'历史收盘':<8} {'预测开盘':<8} {'跳空幅度':<10} {'评估'}")
    print("-" * 50)
    
    for stock_code in stocks:
        try:
            response = requests.post(
                'http://localhost:8000/predict',
                json={
                    'stock_code': stock_code,
                    'pred_len': 3,
                    'sample_count': 1,
                    'lookback': 200
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    historical = result['data']['historical_data']
                    predictions = result['data']['predictions']
                    
                    last_close = historical[-1]['close']
                    first_open = predictions[0]['open']
                    gap_percent = (first_open - last_close) / last_close * 100
                    
                    # 评估跳空程度
                    if abs(gap_percent) <= 2.0:
                        assessment = "✅ 优秀"
                    elif abs(gap_percent) <= 5.0:
                        assessment = "⚠️ 可接受"
                    elif abs(gap_percent) <= 10.0:
                        assessment = "❌ 较大"
                    else:
                        assessment = "❌ 异常"
                    
                    print(f"{stock_code:<8} {last_close:<8.2f} {first_open:<8.2f} {gap_percent:<10.2f}% {assessment}")
                else:
                    print(f"{stock_code:<8} 预测失败: {result.get('error', '未知')}")
            else:
                print(f"{stock_code:<8} API错误: {response.status_code}")
                
        except Exception as e:
            print(f"{stock_code:<8} 异常: {str(e)}")

def test_different_modes():
    """测试不同模式下的跳空情况"""
    print("\n🔄 测试不同模式下的跳空情况...")
    
    modes = [
        {'name': '快速模式', 'sample_count': 1, 'lookback': 100},
        {'name': '平衡模式', 'sample_count': 3, 'lookback': 400},
        {'name': '精确模式', 'sample_count': 5, 'lookback': 800}
    ]
    
    stock_code = '000968'
    
    print(f"{'模式':<10} {'跳空幅度':<10} {'评估'}")
    print("-" * 30)
    
    for mode in modes:
        try:
            response = requests.post(
                'http://localhost:8000/predict',
                json={
                    'stock_code': stock_code,
                    'pred_len': 3,
                    'sample_count': mode['sample_count'],
                    'lookback': mode['lookback']
                },
                timeout=45
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    historical = result['data']['historical_data']
                    predictions = result['data']['predictions']
                    
                    last_close = historical[-1]['close']
                    first_open = predictions[0]['open']
                    gap_percent = (first_open - last_close) / last_close * 100
                    
                    if abs(gap_percent) <= 3.0:
                        assessment = "✅ 良好"
                    elif abs(gap_percent) <= 8.0:
                        assessment = "⚠️ 一般"
                    else:
                        assessment = "❌ 较差"
                    
                    print(f"{mode['name']:<10} {gap_percent:<10.2f}% {assessment}")
                else:
                    print(f"{mode['name']:<10} 失败: {result.get('error', '未知')}")
            else:
                print(f"{mode['name']:<10} API错误: {response.status_code}")
                
        except Exception as e:
            print(f"{mode['name']:<10} 异常: {str(e)}")

if __name__ == "__main__":
    test_stock_gaps()
    test_different_modes()
    
    print("\n💡 跳空问题分析:")
    print("• 如果多数股票都有大跳空，说明是系统性问题")
    print("• 如果不同模式跳空差异很大，说明参数影响显著")
    print("• 需要在模型输出后进行价格连续性校准")
