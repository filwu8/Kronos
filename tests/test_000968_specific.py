#!/usr/bin/env python3
"""
专门测试000968股票30天平衡模式的涨跌幅问题
"""

import requests
import json

def test_000968_30days():
    """测试000968股票30天平衡模式"""
    print("🔍 测试000968股票30天平衡模式涨跌幅限制...")
    
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
            
            # 详细检查每日涨跌幅
            print(f"\n📈 详细涨跌幅检查 (30天):")
            print(f"{'日期':<6} {'开盘':<8} {'最高':<8} {'最低':<8} {'收盘':<8} {'涨跌幅':<8} {'状态'}")
            print("-" * 65)
            
            prev_close = historical[-1]['close']
            violations = []
            max_violation = 0
            
            for i, pred in enumerate(predictions):
                day = i + 1
                o, h, l, c = pred['open'], pred['high'], pred['low'], pred['close']
                
                # 计算涨跌幅
                change_pct = (c - prev_close) / prev_close * 100
                
                # 检查是否超出10%限制
                if abs(change_pct) > 10.0:
                    status = f"❌ 超限{abs(change_pct):.1f}%"
                    violations.append((day, change_pct))
                    max_violation = max(max_violation, abs(change_pct))
                elif abs(change_pct) > 8.0:
                    status = f"⚠️ 接近限制"
                else:
                    status = "✅ 正常"
                
                # 特别标记23%这样的异常涨幅
                if abs(change_pct) > 20.0:
                    status = f"🚨 严重超限{abs(change_pct):.1f}%"
                
                print(f"第{day:<4}天 {o:<8.2f} {h:<8.2f} {l:<8.2f} {c:<8.2f} {change_pct:<8.2f}% {status}")
                
                prev_close = c
            
            # 总结
            print(f"\n📋 涨跌幅限制检查结果:")
            print(f"违规天数: {len(violations)}/30")
            print(f"最大违规幅度: {max_violation:.2f}%")
            
            if len(violations) == 0:
                print("🎉 完美！所有预测都符合A股10%涨跌幅限制")
            elif max_violation > 20.0:
                print("🚨 发现严重违规！存在超过20%的异常涨跌幅")
                print("违规详情:")
                for day, change in violations:
                    print(f"  第{day}天: {change:.2f}%")
            elif len(violations) <= 3:
                print("✅ 基本符合，仅有少量轻微违规")
            else:
                print("❌ 需要进一步修复，违规较多")
                
        else:
            print(f"❌ 预测失败: {result.get('error', '未知错误')}")
    else:
        print(f"❌ API请求失败: {response.status_code}")
        print(f"错误信息: {response.text}")

def test_multiple_runs():
    """多次运行测试，检查一致性"""
    print("\n🔄 多次运行测试，检查涨跌幅限制的一致性...")
    
    for run in range(3):
        print(f"\n第{run+1}次运行:")
        
        try:
            response = requests.post(
                'http://localhost:8000/predict',
                json={
                    'stock_code': '000968',
                    'pred_len': 10,
                    'sample_count': 3
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
                    max_change = 0
                    
                    for pred in predictions:
                        change_pct = abs((pred['close'] - prev_close) / prev_close * 100)
                        if change_pct > 10.0:
                            violations += 1
                        max_change = max(max_change, change_pct)
                        prev_close = pred['close']
                    
                    print(f"  违规天数: {violations}/10, 最大涨跌幅: {max_change:.2f}%")
                else:
                    print(f"  预测失败: {result.get('error', '未知')}")
            else:
                print(f"  API错误: {response.status_code}")
                
        except Exception as e:
            print(f"  异常: {str(e)}")

if __name__ == "__main__":
    test_000968_30days()
    test_multiple_runs()
    
    print("\n💡 如果仍然发现23%这样的异常涨幅:")
    print("1. 检查日志中的涨跌幅限制执行情况")
    print("2. 确认修复代码是否正确执行")
    print("3. 可能需要在更早的阶段进行限制")
    print("4. 考虑在模型预测阶段就加入约束")
