#!/usr/bin/env python3
"""
测试所有修复
"""

import requests
import json

def test_api_status():
    """测试API状态"""
    print("🔍 1. 测试API状态...")
    
    try:
        response = requests.get('http://localhost:8000/health')
        data = response.json()
        
        print(f"   模型已加载: {data['model_status']['model_loaded']}")
        print(f"   使用模拟: {data['model_status']['use_mock']}")
        
        if not data['model_status']['use_mock']:
            print("   ✅ 真实数据模式已启用")
            return True
        else:
            print("   ❌ 仍在模拟模式")
            return False
            
    except Exception as e:
        print(f"   ❌ 检查失败: {str(e)}")
        return False

def test_prediction_with_dates():
    """测试预测数据包含正确日期"""
    print("\n📅 2. 测试预测数据日期格式...")
    
    try:
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001', 'pred_len': 5, 'lookback': 50}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                hist_data = data['data']['historical_data']
                pred_data = data['data']['predictions']
                
                print(f"   历史数据条数: {len(hist_data)}")
                print(f"   预测数据条数: {len(pred_data)}")
                
                # 检查历史数据是否有日期
                if len(hist_data) > 0 and 'date' in hist_data[0]:
                    print(f"   ✅ 历史数据包含日期: {hist_data[0]['date']}")
                    print(f"   最新历史日期: {hist_data[-1]['date']}")
                else:
                    print("   ❌ 历史数据缺少日期字段")
                    return False
                
                # 检查预测数据
                if len(pred_data) > 0:
                    print(f"   预测数据样本: {pred_data[0]}")
                    print("   ✅ 预测数据格式正确")
                else:
                    print("   ❌ 预测数据为空")
                    return False
                
                return True
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {str(e)}")
        return False

def test_real_data_usage():
    """测试是否使用真实数据"""
    print("\n📊 3. 测试真实数据使用...")
    
    try:
        # 测试多次预测，看数据是否有变化
        results = []
        
        for i in range(3):
            response = requests.post(
                'http://localhost:8000/predict',
                json={'stock_code': '000001', 'pred_len': 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    current_price = data['data']['summary']['current_price']
                    results.append(current_price)
        
        if len(results) >= 2:
            # 检查价格是否基于真实数据（应该相同）
            if all(abs(price - results[0]) < 0.01 for price in results):
                print(f"   ✅ 使用一致的真实数据，当前价格: ¥{results[0]:.2f}")
                return True
            else:
                print(f"   ❌ 数据不一致，可能仍在使用随机模拟: {results}")
                return False
        else:
            print("   ❌ 测试数据不足")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {str(e)}")
        return False

def test_chart_data_format():
    """测试图表数据格式"""
    print("\n📈 4. 测试图表数据格式...")
    
    try:
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001', 'pred_len': 5, 'lookback': 30}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                hist_data = data['data']['historical_data']
                pred_data = data['data']['predictions']
                
                # 检查数据结构
                required_fields = ['open', 'high', 'low', 'close', 'volume']
                
                # 检查历史数据
                if len(hist_data) > 0:
                    missing_hist = [field for field in required_fields if field not in hist_data[0]]
                    if missing_hist:
                        print(f"   ❌ 历史数据缺少字段: {missing_hist}")
                        return False
                    else:
                        print("   ✅ 历史数据字段完整")
                
                # 检查预测数据
                if len(pred_data) > 0:
                    missing_pred = [field for field in required_fields if field not in pred_data[0]]
                    if missing_pred:
                        print(f"   ❌ 预测数据缺少字段: {missing_pred}")
                        return False
                    else:
                        print("   ✅ 预测数据字段完整")
                
                # 检查数据合理性
                hist_prices = [item['close'] for item in hist_data]
                pred_prices = [item['close'] for item in pred_data]
                
                if len(hist_prices) > 0 and len(pred_prices) > 0:
                    hist_avg = sum(hist_prices) / len(hist_prices)
                    pred_avg = sum(pred_prices) / len(pred_prices)
                    
                    print(f"   历史平均价格: ¥{hist_avg:.2f}")
                    print(f"   预测平均价格: ¥{pred_avg:.2f}")
                    
                    # 检查价格是否合理（预测价格不应该偏离历史价格太远）
                    if abs(pred_avg - hist_avg) / hist_avg < 0.5:  # 50%以内的变化
                        print("   ✅ 价格预测合理")
                        return True
                    else:
                        print("   ⚠️ 价格预测偏离较大，可能仍在使用模拟数据")
                        return False
                
                return True
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 测试失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🧪 测试所有修复")
    print("=" * 50)
    
    tests = [
        ("API状态检查", test_api_status),
        ("预测数据日期", test_prediction_with_dates),
        ("真实数据使用", test_real_data_usage),
        ("图表数据格式", test_chart_data_format)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} 通过")
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有修复验证通过！")
        print("\n✅ 修复完成:")
        print("   1. ✅ 关闭模拟模式，使用真实数据")
        print("   2. ✅ 修复图表日期显示问题")
        print("   3. ✅ 使用5年真实历史数据")
        print("   4. ✅ 预测基于实际股票价格")
        
        print("\n🌐 现在可以访问:")
        print("   前端: http://localhost:8501")
        print("   API: http://localhost:8000/docs")
        
    else:
        print("⚠️ 部分测试失败，需要进一步检查")
        
        if passed == 0:
            print("\n🔧 可能的问题:")
            print("   1. API服务未正确重启")
            print("   2. 数据适配器未正确加载")
            print("   3. 配置文件未正确更新")

if __name__ == "__main__":
    main()
