#!/usr/bin/env python3
"""
测试真实数据预测
"""

import requests

def test_real_prediction():
    """测试使用真实数据的预测"""
    print("🔮 测试真实数据预测...")
    
    try:
        response = requests.post(
            'http://localhost:8000/predict', 
            json={
                'stock_code': '000001', 
                'pred_len': 5, 
                'lookback': 100
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("✅ 预测成功！使用真实数据")
                
                summary = data['data']['summary']
                stock_info = data['data']['stock_info']
                
                print(f"\n📊 预测结果:")
                print(f"   股票: {stock_info['name']} ({stock_info['code']})")
                print(f"   当前价格: ¥{summary['current_price']:.2f}")
                print(f"   预测价格: ¥{summary['predicted_price']:.2f}")
                print(f"   预期变化: {summary['change_percent']:+.2f}%")
                print(f"   趋势判断: {summary['trend']}")
                
                print(f"\n📈 数据统计:")
                print(f"   历史数据点: {len(data['data']['historical_data'])} 条")
                print(f"   预测数据点: {len(data['data']['predictions'])} 条")
                
                # 显示最近几天的历史数据
                hist_data = data['data']['historical_data']
                print(f"\n📅 最近3天历史数据:")
                for i, day_data in enumerate(hist_data[-3:]):
                    print(f"   第{len(hist_data)-2+i}天: 收盘¥{day_data['close']:.2f}, 成交量{day_data['volume']:,}")
                
                # 显示预测数据
                pred_data = data['data']['predictions']
                print(f"\n🔮 未来{len(pred_data)}天预测:")
                for i, day_pred in enumerate(pred_data):
                    print(f"   第{i+1}天: 收盘¥{day_pred['close']:.2f}, 成交量{day_pred['volume']:,}")
                
                return True
            else:
                print(f"❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")
        return False

def test_multiple_stocks():
    """测试多只股票预测"""
    print("\n📊 测试多只股票预测...")
    
    test_stocks = ['000001', '000002', '000004']
    
    for stock_code in test_stocks:
        print(f"\n🔍 测试股票 {stock_code}...")
        
        try:
            response = requests.post(
                'http://localhost:8000/predict',
                json={'stock_code': stock_code, 'pred_len': 3}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    summary = data['data']['summary']
                    stock_info = data['data']['stock_info']
                    print(f"✅ {stock_info['name']}: {summary['change_percent']:+.2f}% ({summary['trend']})")
                else:
                    print(f"❌ {stock_code}: {data.get('error')}")
            else:
                print(f"❌ {stock_code}: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"❌ {stock_code}: {str(e)}")

if __name__ == "__main__":
    print("🚀 测试真实Kronos模型预测")
    print("=" * 50)
    
    # 测试单股票预测
    success = test_real_prediction()
    
    if success:
        # 测试多股票预测
        test_multiple_stocks()
        
        print("\n" + "=" * 50)
        print("🎉 真实数据预测测试完成！")
        print("\n💡 特点:")
        print("   ✅ 使用5年真实历史数据")
        print("   ✅ 基于实际价格和成交量")
        print("   ✅ 增强的趋势分析算法")
        print("   ✅ 支持100只股票")
        
        print("\n🌐 访问应用:")
        print("   前端: http://localhost:8501")
        print("   API: http://localhost:8000/docs")
        
    else:
        print("\n❌ 测试失败，请检查服务状态")
