#!/usr/bin/env python3
"""
测试价格连续性修复效果（针对精确模式的大跳空问题）
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from app.prediction_service import get_prediction_service

def test_precise_mode_continuity():
    """测试精确模式下的价格连续性"""
    print("🧪 测试精确模式价格连续性修复...")
    
    service = get_prediction_service(use_mock=True)
    
    # 精确模式参数
    precise_params = {
        'lookback': 1500,  # 精确模式：大历史数据
        'pred_len': 10,
        'sample_count': 5,  # 精确模式：多次采样
        'T': 1.0,
        'top_p': 0.9
    }
    
    test_stocks = ['000968', '000001', '600000']
    
    for stock_code in test_stocks:
        print(f"\n📊 测试股票: {stock_code} (精确模式)")
        
        try:
            result = service.predict_stock(stock_code, **precise_params)
            
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
            first_pred_close = predictions[0]['close']
            
            # 计算跳空幅度
            gap_percent = (first_pred_open - last_close) / last_close * 100
            
            print(f"📈 历史最后收盘价: {last_close:.2f}")
            print(f"📈 预测首日开盘价: {first_pred_open:.2f}")
            print(f"📈 预测首日收盘价: {first_pred_close:.2f}")
            print(f"📈 跳空幅度: {gap_percent:.2f}%")
            
            # 验证修复效果
            if abs(gap_percent) <= 2.0:
                print("✅ 价格连续性优秀 (≤2%)")
            elif abs(gap_percent) <= 3.0:
                print("✅ 价格连续性良好 (≤3%)")
            elif abs(gap_percent) <= 5.0:
                print("⚠️ 价格跳空较大但可接受 (≤5%)")
            else:
                print("❌ 价格跳空过大，需要进一步优化")
            
            # 检查性能信息
            if 'performance' in result['data']:
                perf = result['data']['performance']
                print(f"⏱️ 预测耗时: {perf['elapsed_time']}秒")
                print(f"📊 参数: lookback={perf['parameters']['lookback']}, samples={perf['parameters']['sample_count']}")
            
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

def test_different_sample_counts():
    """测试不同采样次数的影响"""
    print("\n🔄 测试不同采样次数的价格连续性...")
    
    service = get_prediction_service(use_mock=True)
    stock_code = '000968'
    
    sample_counts = [1, 3, 5, 10]
    results = {}
    
    for sample_count in sample_counts:
        print(f"\n📊 测试采样次数: {sample_count}")
        
        try:
            result = service.predict_stock(
                stock_code,
                lookback=800,
                pred_len=5,
                sample_count=sample_count
            )
            
            if result['success']:
                historical_data = result['data']['historical_data']
                predictions = result['data']['predictions']
                
                last_close = historical_data[-1]['close']
                first_pred_open = predictions[0]['open']
                gap_percent = (first_pred_open - last_close) / last_close * 100
                
                results[sample_count] = gap_percent
                print(f"  跳空幅度: {gap_percent:.2f}%")
                
                # 检查是否有校准日志
                if 'performance' in result['data']:
                    print(f"  耗时: {result['data']['performance']['elapsed_time']}秒")
            else:
                print(f"  失败: {result.get('error', '未知错误')}")
                
        except Exception as e:
            print(f"  异常: {str(e)}")
    
    # 分析结果
    if results:
        print(f"\n📈 采样次数影响分析:")
        print(f"{'采样次数':<8} {'跳空幅度':<10} {'评估'}")
        print("-" * 30)
        
        for sample_count, gap in results.items():
            if abs(gap) <= 2.0:
                assessment = "优秀"
            elif abs(gap) <= 3.0:
                assessment = "良好"
            elif abs(gap) <= 5.0:
                assessment = "可接受"
            else:
                assessment = "需优化"
            
            print(f"{sample_count:<8} {gap:<10.2f}% {assessment}")

def test_calibration_effectiveness():
    """测试校准机制的有效性"""
    print("\n🎯 测试价格连续性校准机制...")
    
    # 模拟一个会产生大跳空的场景
    service = get_prediction_service(use_mock=True)
    
    # 使用可能产生异常的参数
    test_params = {
        'lookback': 2000,  # 很大的历史数据
        'pred_len': 15,    # 较长的预测期
        'sample_count': 8, # 较多的采样次数
        'T': 1.2,         # 较高的温度
        'top_p': 0.85     # 较低的top_p
    }
    
    print("📊 使用可能产生异常跳空的参数组合...")
    print(f"参数: {test_params}")
    
    try:
        result = service.predict_stock('000968', **test_params)
        
        if result['success']:
            historical_data = result['data']['historical_data']
            predictions = result['data']['predictions']
            
            last_close = historical_data[-1]['close']
            first_pred_open = predictions[0]['open']
            gap_percent = (first_pred_open - last_close) / last_close * 100
            
            print(f"\n📈 校准后结果:")
            print(f"历史收盘价: {last_close:.2f}")
            print(f"预测开盘价: {first_pred_open:.2f}")
            print(f"跳空幅度: {gap_percent:.2f}%")
            
            if abs(gap_percent) <= 3.0:
                print("✅ 校准机制有效，跳空控制在合理范围内")
            else:
                print("⚠️ 校准机制可能需要进一步调整")
                
            # 检查预测序列的合理性
            print(f"\n📊 预测序列检查 (前5天):")
            for i, pred in enumerate(predictions[:5]):
                date_str = f"第{i+1}天"
                print(f"  {date_str}: O={pred['open']:.2f}, H={pred['high']:.2f}, L={pred['low']:.2f}, C={pred['close']:.2f}")
                
                # 检查OHLC关系
                if pred['low'] <= min(pred['open'], pred['close']) <= max(pred['open'], pred['close']) <= pred['high']:
                    ohlc_status = "✅"
                else:
                    ohlc_status = "❌"
                print(f"    OHLC关系: {ohlc_status}")
        else:
            print(f"❌ 预测失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    print("🚀 开始价格连续性修复验证...")
    
    # 测试精确模式
    test_precise_mode_continuity()
    
    # 测试不同采样次数
    test_different_sample_counts()
    
    # 测试校准机制
    test_calibration_effectiveness()
    
    print("\n✅ 价格连续性修复验证完成！")
    print("\n💡 修复说明:")
    print("• 使用中位数聚合替代均值聚合，更抗异常值")
    print("• 添加价格连续性校准，自动修正大跳空")
    print("• 跳空超过±3%时自动校准到±2%以内")
    print("• 保持整个预测序列的价格关系合理性")
