#!/usr/bin/env python3
"""
测试A股涨跌幅限制修复效果
"""

import requests
import json

def test_daily_limit_fix():
    """测试涨跌幅限制修复"""
    print("🔍 测试A股涨跌幅限制修复效果...")
    
    # 测试000968（您遇到23%涨幅问题的股票）
    response = requests.post(
        'http://localhost:8000/predict',
        json={
            'stock_code': '000968',
            'pred_len': 30,
            'sample_count': 3,  # 平衡模式
            'lookback': 400
        },
        timeout=60
    )
    
    if response.status_code == 200:
        result = response.json()
        if result.get('success'):
            historical = result['data']['historical_data']
            predictions = result['data']['predictions']
            
            print(f"✅ 预测成功，返回{len(predictions)}天数据")
            print(f"📊 历史最后收盘价: {historical[-1]['close']:.2f}")
            
            # 检查每日涨跌幅
            print(f"\n📈 涨跌幅检查 (前10天):")
            print(f"{'日期':<6} {'开盘':<8} {'最高':<8} {'最低':<8} {'收盘':<8} {'涨跌幅':<8} {'状态'}")
            print("-" * 60)
            
            prev_close = historical[-1]['close']
            max_violation = 0
            violation_days = 0
            
            for i, pred in enumerate(predictions[:10]):
                day = i + 1
                o, h, l, c = pred['open'], pred['high'], pred['low'], pred['close']
                
                # 计算涨跌幅
                change_pct = (c - prev_close) / prev_close * 100
                
                # 检查是否超出10%限制
                if abs(change_pct) > 10.0:
                    status = f"❌ 超限{abs(change_pct):.1f}%"
                    violation_days += 1
                    max_violation = max(max_violation, abs(change_pct))
                elif abs(change_pct) > 8.0:
                    status = f"⚠️ 接近限制"
                else:
                    status = "✅ 正常"
                
                print(f"第{day:<4}天 {o:<8.2f} {h:<8.2f} {l:<8.2f} {c:<8.2f} {change_pct:<8.2f}% {status}")
                
                prev_close = c
            
            # 总结
            print(f"\n📋 涨跌幅限制检查结果:")
            print(f"违规天数: {violation_days}/10")
            print(f"最大违规幅度: {max_violation:.2f}%")
            
            if violation_days == 0:
                print("🎉 完美！所有预测都符合A股涨跌幅限制")
            elif violation_days <= 2:
                print("✅ 良好，仅有少量违规")
            else:
                print("❌ 需要进一步修复，违规较多")
                
            # 检查日内价格关系
            print(f"\n🔍 OHLC关系检查:")
            ohlc_errors = 0
            for i, pred in enumerate(predictions[:5]):
                o, h, l, c = pred['open'], pred['high'], pred['low'], pred['close']
                min_oc = min(o, c)
                max_oc = max(o, c)
                
                if l <= min_oc <= max_oc <= h:
                    status = "✅"
                else:
                    status = "❌"
                    ohlc_errors += 1
                
                print(f"第{i+1}天 {status}: L={l:.2f} ≤ min(O,C)={min_oc:.2f} ≤ max(O,C)={max_oc:.2f} ≤ H={h:.2f}")
            
            if ohlc_errors == 0:
                print("✅ OHLC关系全部正确")
            else:
                print(f"❌ {ohlc_errors}天OHLC关系异常")
                
        else:
            print(f"❌ 预测失败: {result.get('error', '未知错误')}")
    else:
        print(f"❌ API请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")

def test_multiple_stocks():
    """测试多个股票的涨跌幅限制"""
    print("\n🔄 测试多个股票的涨跌幅限制...")
    
    stocks = ['000968', '000001', '000002', '600000']
    
    for stock_code in stocks:
        print(f"\n📊 测试股票: {stock_code}")
        
        try:
            response = requests.post(
                'http://localhost:8000/predict',
                json={
                    'stock_code': stock_code,
                    'pred_len': 5,
                    'sample_count': 1
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    historical = result['data']['historical_data']
                    predictions = result['data']['predictions']
                    
                    prev_close = historical[-1]['close']
                    violations = 0
                    
                    for i, pred in enumerate(predictions):
                        change_pct = (pred['close'] - prev_close) / prev_close * 100
                        if abs(change_pct) > 10.0:
                            violations += 1
                        prev_close = pred['close']
                    
                    if violations == 0:
                        print(f"  ✅ 无违规")
                    else:
                        print(f"  ❌ {violations}天违规")
                else:
                    print(f"  ❌ 预测失败")
            else:
                print(f"  ❌ API错误")
                
        except Exception as e:
            print(f"  ❌ 异常: {str(e)}")

if __name__ == "__main__":
    test_daily_limit_fix()
    test_multiple_stocks()
    
    print("\n💡 A股涨跌幅限制说明:")
    print("• 主板股票(000xxx, 600xxx): ±10%")
    print("• 科创板股票(688xxx): ±20%")
    print("• 创业板股票(300xxx): ±20%")
    print("• ST股票: ±5%")
    print("• 新股上市前5日: 无涨跌幅限制")
