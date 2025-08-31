#!/usr/bin/env python3
"""
测试价格连续性修复效果
验证预测的开盘价是否合理地接近前一天收盘价
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from app.prediction_service import get_prediction_service

def test_price_continuity():
    """测试价格连续性"""
    print("🧪 测试价格连续性修复效果...")
    
    # 使用模拟模式进行测试
    service = get_prediction_service(use_mock=True)
    
    # 测试参数
    test_params = {
        'lookback': 30,
        'pred_len': 5,
        'T': 1.0,
        'top_p': 0.9,
        'sample_count': 1
    }
    
    # 测试多只股票
    test_stocks = ['000001', '600000', '000002']
    
    for stock_code in test_stocks:
        print(f"\n📊 测试股票: {stock_code}")
        
        try:
            # 进行预测
            result = service.predict_stock(stock_code, **test_params)
            
            if not result['success']:
                print(f"❌ 预测失败: {result.get('error', '未知错误')}")
                continue
            
            # 获取数据
            historical_data = result['data']['historical_data']
            predictions = result['data']['predictions']
            
            if not historical_data or not predictions:
                print("❌ 数据为空")
                continue
            
            # 分析价格连续性
            last_close = historical_data[-1]['close']
            first_pred_open = predictions[0]['open']
            
            # 计算跳空幅度
            gap_percent = (first_pred_open - last_close) / last_close * 100
            
            print(f"📈 历史最后收盘价: {last_close:.2f}")
            print(f"📈 预测首日开盘价: {first_pred_open:.2f}")
            print(f"📈 跳空幅度: {gap_percent:.2f}%")
            
            # 验证合理性
            if abs(gap_percent) <= 3.0:  # 跳空在3%以内认为合理
                print("✅ 价格连续性良好")
            elif abs(gap_percent) <= 5.0:
                print("⚠️ 价格跳空较大但可接受")
            else:
                print("❌ 价格跳空过大，需要进一步优化")
            
            # 验证OHLC关系
            print("\n🔍 验证OHLC关系:")
            for i, pred in enumerate(predictions[:3]):  # 检查前3天
                open_p = pred['open']
                high_p = pred['high']
                low_p = pred['low']
                close_p = pred['close']
                
                # 检查价格关系
                if low_p <= min(open_p, close_p) and max(open_p, close_p) <= high_p:
                    status = "✅"
                else:
                    status = "❌"
                
                print(f"  第{i+1}天 {status}: O={open_p:.2f}, H={high_p:.2f}, L={low_p:.2f}, C={close_p:.2f}")
                
                # 检查日内波动
                daily_range = (high_p - low_p) / open_p * 100
                if daily_range <= 10:  # 日内波动在10%以内
                    range_status = "✅"
                else:
                    range_status = "⚠️"
                print(f"    日内波动: {daily_range:.2f}% {range_status}")
            
            # 检查连续性
            print("\n🔗 检查日间连续性:")
            for i in range(1, min(3, len(predictions))):
                prev_close = predictions[i-1]['close']
                curr_open = predictions[i]['open']
                gap = (curr_open - prev_close) / prev_close * 100
                
                if abs(gap) <= 2.0:
                    gap_status = "✅"
                elif abs(gap) <= 4.0:
                    gap_status = "⚠️"
                else:
                    gap_status = "❌"
                
                print(f"  第{i}天->第{i+1}天: 收盘{prev_close:.2f} -> 开盘{curr_open:.2f}, 跳空{gap:.2f}% {gap_status}")
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

def test_multiple_runs():
    """测试多次运行的一致性"""
    print("\n🔄 测试多次运行的稳定性...")
    
    service = get_prediction_service(use_mock=True)
    stock_code = '000001'
    
    gaps = []
    
    for run in range(5):
        try:
            result = service.predict_stock(stock_code, lookback=30, pred_len=3)
            
            if result['success']:
                historical_data = result['data']['historical_data']
                predictions = result['data']['predictions']
                
                last_close = historical_data[-1]['close']
                first_pred_open = predictions[0]['open']
                gap_percent = (first_pred_open - last_close) / last_close * 100
                gaps.append(gap_percent)
                
                print(f"  运行{run+1}: 跳空{gap_percent:.2f}%")
            
        except Exception as e:
            print(f"  运行{run+1}: 失败 - {str(e)}")
    
    if gaps:
        avg_gap = np.mean(gaps)
        std_gap = np.std(gaps)
        print(f"\n📊 跳空统计: 平均{avg_gap:.2f}%, 标准差{std_gap:.2f}%")
        
        if std_gap <= 1.0:
            print("✅ 预测稳定性良好")
        elif std_gap <= 2.0:
            print("⚠️ 预测稳定性一般")
        else:
            print("❌ 预测稳定性较差")

if __name__ == "__main__":
    print("🚀 开始价格连续性测试...")
    
    # 基本连续性测试
    test_price_continuity()
    
    # 稳定性测试
    test_multiple_runs()
    
    print("\n✅ 测试完成！")
