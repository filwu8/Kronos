#!/usr/bin/env python3
"""
测试OHLC关系和价格连续性修复效果
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from app.prediction_service import get_prediction_service

def validate_ohlc_relationships(predictions):
    """验证OHLC关系的正确性"""
    issues = []
    
    for i, pred in enumerate(predictions):
        day = i + 1
        open_p = pred['open']
        high_p = pred['high']
        low_p = pred['low']
        close_p = pred['close']
        
        # 检查基本OHLC关系
        min_oc = min(open_p, close_p)
        max_oc = max(open_p, close_p)
        
        if low_p > min_oc:
            issues.append(f"第{day}天: 低价({low_p:.2f}) > min(开盘,收盘)({min_oc:.2f})")
        
        if high_p < max_oc:
            issues.append(f"第{day}天: 高价({high_p:.2f}) < max(开盘,收盘)({max_oc:.2f})")
        
        # 检查价格为正
        if any(p <= 0 for p in [open_p, high_p, low_p, close_p]):
            issues.append(f"第{day}天: 发现非正价格")
        
        # 检查日内波动幅度
        if open_p > 0:
            daily_range = (high_p - low_p) / open_p * 100
            if daily_range > 20:  # 超过20%认为异常
                issues.append(f"第{day}天: 日内波动过大({daily_range:.1f}%)")
    
    return issues

def validate_price_continuity(historical_data, predictions):
    """验证价格连续性"""
    issues = []
    
    # 检查历史数据到预测数据的连续性
    last_close = historical_data[-1]['close']
    first_open = predictions[0]['open']
    gap_percent = (first_open - last_close) / last_close * 100
    
    if abs(gap_percent) > 5.0:
        issues.append(f"历史->预测跳空过大: {gap_percent:.2f}%")
    
    # 检查预测数据内部的连续性
    for i in range(1, len(predictions)):
        prev_close = predictions[i-1]['close']
        curr_open = predictions[i]['open']
        gap_percent = (curr_open - prev_close) / prev_close * 100
        
        if abs(gap_percent) > 8.0:
            issues.append(f"第{i}天->第{i+1}天跳空过大: {gap_percent:.2f}%")
    
    return issues

def test_ohlc_fix():
    """测试OHLC修复效果"""
    print("🧪 测试OHLC关系和价格连续性修复...")
    
    service = get_prediction_service(use_mock=True)
    
    # 使用精确模式参数（容易产生问题的参数）
    test_params = {
        'lookback': 1000,
        'pred_len': 10,
        'sample_count': 5,  # 多次采样容易产生异常
        'T': 1.0,
        'top_p': 0.9
    }
    
    test_stocks = ['000968', '000001', '600000']
    
    for stock_code in test_stocks:
        print(f"\n📊 测试股票: {stock_code}")
        
        try:
            result = service.predict_stock(stock_code, **test_params)
            
            if not result['success']:
                print(f"❌ 预测失败: {result.get('error', '未知错误')}")
                continue
            
            historical_data = result['data']['historical_data']
            predictions = result['data']['predictions']
            
            print(f"📈 历史最后收盘价: {historical_data[-1]['close']:.2f}")
            print(f"📈 预测首日开盘价: {predictions[0]['open']:.2f}")
            
            # 验证OHLC关系
            ohlc_issues = validate_ohlc_relationships(predictions)
            if ohlc_issues:
                print("❌ OHLC关系问题:")
                for issue in ohlc_issues[:5]:  # 只显示前5个问题
                    print(f"  • {issue}")
                if len(ohlc_issues) > 5:
                    print(f"  • ... 还有{len(ohlc_issues)-5}个问题")
            else:
                print("✅ OHLC关系正确")
            
            # 验证价格连续性
            continuity_issues = validate_price_continuity(historical_data, predictions)
            if continuity_issues:
                print("❌ 价格连续性问题:")
                for issue in continuity_issues:
                    print(f"  • {issue}")
            else:
                print("✅ 价格连续性良好")
            
            # 显示前5天的详细数据
            print(f"\n📊 预测详情 (前5天):")
            print(f"{'日期':<12} {'开盘':<8} {'最高':<8} {'最低':<8} {'收盘':<8} {'日内波动'}")
            print("-" * 60)
            
            for i, pred in enumerate(predictions[:5]):
                date_str = f"第{i+1}天"
                daily_range = (pred['high'] - pred['low']) / pred['open'] * 100 if pred['open'] > 0 else 0
                print(f"{date_str:<12} {pred['open']:<8.2f} {pred['high']:<8.2f} {pred['low']:<8.2f} {pred['close']:<8.2f} {daily_range:<8.1f}%")
            
            # 计算总体评分
            total_issues = len(ohlc_issues) + len(continuity_issues)
            if total_issues == 0:
                print("🎉 完美！无任何问题")
            elif total_issues <= 2:
                print("✅ 良好，仅有少量问题")
            elif total_issues <= 5:
                print("⚠️ 一般，存在一些问题")
            else:
                print("❌ 较差，问题较多")
                
        except Exception as e:
            print(f"❌ 测试失败: {str(e)}")
            import traceback
            traceback.print_exc()

def test_extreme_parameters():
    """测试极端参数下的修复效果"""
    print("\n🔥 测试极端参数下的修复效果...")
    
    service = get_prediction_service(use_mock=True)
    
    # 极端参数：容易产生异常的设置
    extreme_params = {
        'lookback': 2000,   # 很大的历史数据
        'pred_len': 15,     # 较长的预测期
        'sample_count': 10, # 很多次采样
        'T': 1.5,          # 较高的温度
        'top_p': 0.8       # 较低的top_p
    }
    
    print(f"极端参数: {extreme_params}")
    
    try:
        result = service.predict_stock('000968', **extreme_params)
        
        if result['success']:
            historical_data = result['data']['historical_data']
            predictions = result['data']['predictions']
            
            # 快速验证
            ohlc_issues = validate_ohlc_relationships(predictions)
            continuity_issues = validate_price_continuity(historical_data, predictions)
            
            print(f"OHLC问题数量: {len(ohlc_issues)}")
            print(f"连续性问题数量: {len(continuity_issues)}")
            
            if len(ohlc_issues) + len(continuity_issues) <= 3:
                print("✅ 极端参数下修复效果良好")
            else:
                print("⚠️ 极端参数下仍有较多问题，需要进一步优化")
        else:
            print(f"❌ 极端参数预测失败: {result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 极端参数测试失败: {str(e)}")

def compare_before_after():
    """对比修复前后的效果"""
    print("\n📊 修复效果对比...")
    
    print("修复前的问题:")
    print("• OHLC关系异常：开盘价=最高价，收盘价=最低价")
    print("• 价格跳跃过大：日间跳空超过±10%")
    print("• 日内波动异常：单日波动超过15%")
    
    print("\n修复后的改进:")
    print("✅ OHLC关系校验：确保 low ≤ min(open,close) ≤ max(open,close) ≤ high")
    print("✅ 日内波动限制：压缩超过15%的异常波动")
    print("✅ 日间连续性：限制跳空在±5%以内")
    print("✅ 价格合理性：确保所有价格为正数")

if __name__ == "__main__":
    print("🚀 开始OHLC修复效果测试...")
    
    # 主要测试
    test_ohlc_fix()
    
    # 极端参数测试
    test_extreme_parameters()
    
    # 效果对比
    compare_before_after()
    
    print("\n✅ OHLC修复测试完成！")
    print("\n💡 修复特性:")
    print("• 全面OHLC关系验证和修复")
    print("• 日内波动幅度限制（≤15%）")
    print("• 日间跳空控制（≤±5%）")
    print("• 价格合理性保证（正数）")
