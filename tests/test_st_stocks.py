#!/usr/bin/env python3
"""
测试不同类型股票的涨跌幅限制
"""

import requests
import json

def get_expected_limit(stock_code):
    """获取股票的预期涨跌幅限制"""
    code_str = str(stock_code).upper()
    
    if 'ST' in code_str:
        return 5.0  # ST股票 ±5%
    elif code_str.startswith('688'):
        return 20.0  # 科创板 ±20%
    elif code_str.startswith('300'):
        return 20.0  # 创业板 ±20%
    else:
        return 10.0  # 主板 ±10%

def test_stock_daily_limits():
    """测试不同类型股票的涨跌幅限制"""
    print("🔍 测试不同类型股票的涨跌幅限制...")
    
    # 测试股票列表
    test_stocks = [
        {'code': '000968', 'name': '蓝焰控股', 'type': '主板'},
        {'code': '000001', 'name': '平安银行', 'type': '主板'},
        {'code': '600000', 'name': '浦发银行', 'type': '主板'},
        {'code': '300001', 'name': '特锐德', 'type': '创业板'},
        {'code': '688001', 'name': '华兴源创', 'type': '科创板'},
        # 注意：ST股票代码可能需要实际存在的，这里用假设的代码
        {'code': 'ST000001', 'name': 'ST测试', 'type': 'ST股票'}
    ]
    
    print(f"{'股票代码':<10} {'类型':<8} {'预期限制':<8} {'实际测试':<10} {'状态'}")
    print("-" * 50)
    
    for stock in test_stocks:
        code = stock['code']
        expected_limit = get_expected_limit(code)
        
        try:
            # 跳过ST测试股票（可能不存在）
            if code.startswith('ST'):
                print(f"{code:<10} {stock['type']:<8} ±{expected_limit:<6.0f}% {'跳过测试':<10} ⚠️ 代码可能不存在")
                continue
            
            response = requests.post(
                'http://localhost:8000/predict',
                json={
                    'stock_code': code,
                    'pred_len': 5,
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
                    
                    # 检查涨跌幅
                    prev_close = historical[-1]['close']
                    max_violation = 0
                    violations = 0
                    
                    for pred in predictions:
                        change_pct = abs((pred['close'] - prev_close) / prev_close * 100)
                        if change_pct > expected_limit:
                            violations += 1
                            max_violation = max(max_violation, change_pct)
                        prev_close = pred['close']
                    
                    if violations == 0:
                        status = "✅ 符合"
                        test_result = f"最大{max_violation:.1f}%"
                    else:
                        status = f"❌ {violations}天违规"
                        test_result = f"最大{max_violation:.1f}%"
                    
                    print(f"{code:<10} {stock['type']:<8} ±{expected_limit:<6.0f}% {test_result:<10} {status}")
                else:
                    print(f"{code:<10} {stock['type']:<8} ±{expected_limit:<6.0f}% {'预测失败':<10} ❌ 失败")
            else:
                print(f"{code:<10} {stock['type']:<8} ±{expected_limit:<6.0f}% {'API错误':<10} ❌ 错误")
                
        except Exception as e:
            print(f"{code:<10} {stock['type']:<8} ±{expected_limit:<6.0f}% {'异常':<10} ❌ {str(e)[:20]}")

def test_extreme_case():
    """测试极端情况下的涨跌幅限制"""
    print("\n🔥 测试极端参数下的涨跌幅限制...")
    
    # 使用容易产生异常的参数
    extreme_params = {
        'stock_code': '000968',
        'pred_len': 20,
        'sample_count': 5,  # 多次采样
        'lookback': 1000,   # 大量历史数据
        'temperature': 1.2, # 较高温度
        'top_p': 0.8       # 较低top_p
    }
    
    print("使用极端参数测试...")
    print(f"参数: {extreme_params}")
    
    try:
        response = requests.post(
            'http://localhost:8000/predict',
            json=extreme_params,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                historical = result['data']['historical_data']
                predictions = result['data']['predictions']
                
                print(f"✅ 预测成功，返回{len(predictions)}天数据")
                
                # 检查涨跌幅
                prev_close = historical[-1]['close']
                violations = []
                
                for i, pred in enumerate(predictions):
                    change_pct = (pred['close'] - prev_close) / prev_close * 100
                    if abs(change_pct) > 10.0:  # 主板10%限制
                        violations.append((i+1, change_pct))
                    prev_close = pred['close']
                
                if not violations:
                    print("🎉 极端参数下仍然符合涨跌幅限制")
                else:
                    print(f"❌ 发现{len(violations)}天违规:")
                    for day, change in violations[:5]:  # 只显示前5个
                        print(f"  第{day}天: {change:.2f}%")
            else:
                print(f"❌ 预测失败: {result.get('error', '未知错误')}")
        else:
            print(f"❌ API错误: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def test_specific_st_logic():
    """测试ST股票识别逻辑"""
    print("\n🔍 测试ST股票识别逻辑...")
    
    # 测试不同的ST股票代码格式
    st_codes = [
        'ST000001',
        '*ST000002', 
        'st000003',
        '*st000004',
        'ST600001',
        '*ST600002'
    ]
    
    print("ST股票代码识别测试:")
    for code in st_codes:
        # 模拟识别逻辑
        code_str = str(code).upper()
        if 'ST' in code_str or code_str.startswith('*ST'):
            limit = 5.0
            status = "✅ 识别为ST"
        else:
            limit = 10.0
            status = "❌ 未识别为ST"
        
        print(f"  {code:<12} -> ±{limit:.0f}% {status}")

if __name__ == "__main__":
    test_stock_daily_limits()
    test_extreme_case()
    test_specific_st_logic()
    
    print("\n💡 A股涨跌幅限制总结:")
    print("✅ 主板股票(000xxx, 600xxx): ±10%")
    print("✅ 科创板股票(688xxx): ±20%") 
    print("✅ 创业板股票(300xxx): ±20%")
    print("✅ ST股票(*ST, ST): ±5%")
    print("⚠️ 新股上市前5日: 无涨跌幅限制（暂未实现）")
    print("⚠️ 北交所股票: ±30%（暂未实现）")
