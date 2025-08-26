#!/usr/bin/env python3
"""
最终日期修复验证
确认所有日期显示都正常
"""

import requests
import json
from datetime import datetime, timedelta

def test_api_prediction():
    """测试API预测的日期格式"""
    print("🔌 测试API预测日期格式...")
    
    try:
        response = requests.post('http://localhost:8000/predict', 
                               json={'stock_code': '000001', 'pred_len': 7}, 
                               timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                predictions = data['data']['predictions']
                historical = data['data']['historical_data']
                
                print(f"   ✅ 获得 {len(predictions)} 条预测数据")
                print(f"   ✅ 获得 {len(historical)} 条历史数据")
                
                # 检查历史数据日期
                print("\n   📊 历史数据日期样本:")
                for i in range(min(3, len(historical))):
                    hist = historical[-(i+1)]  # 最近的几条
                    print(f"      {hist['date']} - 收盘: ¥{hist['close']:.2f}")
                
                # 检查预测数据日期
                print("\n   🔮 预测数据日期:")
                for i, pred in enumerate(predictions):
                    print(f"      {i+1}. {pred['date']} - 收盘: ¥{pred['close']:.2f}")
                
                # 验证日期连续性
                last_hist_date = datetime.strptime(historical[-1]['date'], '%Y-%m-%d')
                first_pred_date = datetime.strptime(predictions[0]['date'], '%Y-%m-%d')
                
                date_gap = (first_pred_date - last_hist_date).days
                print(f"\n   📅 日期连续性: 历史数据最后日期到预测第一天间隔 {date_gap} 天")
                
                if date_gap <= 3:  # 考虑周末
                    print("   ✅ 日期连续性正常")
                else:
                    print("   ⚠️ 日期连续性可能有问题")
                
                return True
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
        return False

def test_different_stocks():
    """测试不同股票的日期格式"""
    print("\n📈 测试不同股票日期格式...")
    
    test_stocks = ['000001', '000002', '000004']
    
    for stock_code in test_stocks:
        try:
            response = requests.post('http://localhost:8000/predict', 
                                   json={'stock_code': stock_code, 'pred_len': 3}, 
                                   timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    predictions = data['data']['predictions']
                    stock_name = data['data']['stock_info']['name']
                    
                    print(f"   ✅ {stock_code} ({stock_name}):")
                    for pred in predictions:
                        print(f"      {pred['date']} - ¥{pred['close']:.2f}")
                else:
                    print(f"   ❌ {stock_code}: {data.get('error')}")
            else:
                print(f"   ❌ {stock_code}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {stock_code}: {str(e)}")

def test_date_range_validity():
    """测试日期范围的有效性"""
    print("\n📅 测试日期范围有效性...")
    
    try:
        response = requests.post('http://localhost:8000/predict', 
                               json={'stock_code': '000001', 'pred_len': 10}, 
                               timeout=20)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                predictions = data['data']['predictions']
                
                # 检查所有日期都是未来日期
                today = datetime.now().date()
                future_dates = []
                invalid_dates = []
                
                for pred in predictions:
                    pred_date = datetime.strptime(pred['date'], '%Y-%m-%d').date()
                    if pred_date > today:
                        future_dates.append(pred_date)
                    else:
                        invalid_dates.append(pred_date)
                
                print(f"   ✅ 未来日期: {len(future_dates)} 个")
                print(f"   ❌ 无效日期: {len(invalid_dates)} 个")
                
                if len(invalid_dates) == 0:
                    print("   ✅ 所有预测日期都是有效的未来日期")
                    
                    # 检查日期是否连续
                    sorted_dates = sorted(future_dates)
                    consecutive = True
                    for i in range(1, len(sorted_dates)):
                        gap = (sorted_dates[i] - sorted_dates[i-1]).days
                        if gap > 3:  # 允许周末间隔
                            consecutive = False
                            break
                    
                    if consecutive:
                        print("   ✅ 预测日期连续性正常")
                    else:
                        print("   ⚠️ 预测日期可能不连续")
                        
                    return True
                else:
                    print("   ❌ 存在无效的预测日期")
                    return False
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 异常: {str(e)}")
        return False

def test_streamlit_compatibility():
    """测试Streamlit兼容性"""
    print("\n🎨 测试Streamlit服务...")
    
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("   ✅ Streamlit服务正常运行")
            print("   💡 请在浏览器中测试图表显示是否正常")
            return True
        else:
            print(f"   ❌ Streamlit服务异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Streamlit连接失败: {str(e)}")
        return False

def main():
    """主验证函数"""
    print("🔬 RTX 5090 GPU股票预测系统 - 日期修复最终验证")
    print("=" * 70)
    
    tests = [
        ("API预测日期", test_api_prediction),
        ("多股票日期", test_different_stocks),
        ("日期有效性", test_date_range_validity),
        ("Streamlit兼容", test_streamlit_compatibility)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name}: 通过")
            else:
                print(f"❌ {test_name}: 失败")
        except Exception as e:
            print(f"❌ {test_name}: 异常 - {str(e)}")
    
    print("\n" + "=" * 70)
    print(f"📊 验证结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 日期修复完全成功!")
        print("\n✅ 修复内容:")
        print("   1. ✅ 预测数据日期格式正确")
        print("   2. ✅ 历史数据日期显示正常") 
        print("   3. ✅ 日期连续性验证通过")
        print("   4. ✅ 未来日期有效性确认")
        print("   5. ✅ 多股票日期一致性")
        
        print("\n🌐 测试地址:")
        print("   前端界面: http://localhost:8501")
        print("   API文档: http://localhost:8000/docs")
        
        print("\n💡 使用建议:")
        print("   - 在Streamlit界面中选择股票代码")
        print("   - 查看预测图表中的日期轴")
        print("   - 确认日期显示为正确的未来日期")
        
    else:
        print("⚠️ 部分测试未通过，请检查相关功能")

if __name__ == "__main__":
    main()
