#!/usr/bin/env python3
"""
检查API返回的数据结构
"""

import requests
import json

def check_api_data():
    """检查API返回的数据"""
    print("🔍 检查API返回的数据结构")
    
    try:
        response = requests.post(
            'http://localhost:8000/predict', 
            json={'stock_code': '000001', 'pred_len': 5, 'lookback': 100}
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                hist_data = data['data']['historical_data']
                pred_data = data['data']['predictions']
                
                print(f"✅ API调用成功")
                print(f"📊 历史数据数量: {len(hist_data)}")
                print(f"🔮 预测数据数量: {len(pred_data)}")
                
                if len(hist_data) > 0:
                    print(f"\n📈 历史数据样本:")
                    print(f"第一条: {hist_data[0]}")
                    print(f"最后一条: {hist_data[-1]}")
                    
                    # 检查价格范围
                    prices = [item['close'] for item in hist_data]
                    print(f"价格范围: {min(prices):.2f} - {max(prices):.2f}")
                
                if len(pred_data) > 0:
                    print(f"\n🔮 预测数据样本:")
                    print(f"第一条: {pred_data[0]}")
                    print(f"最后一条: {pred_data[-1]}")
                    
                    # 检查预测价格范围
                    pred_prices = [item['close'] for item in pred_data]
                    print(f"预测价格范围: {min(pred_prices):.2f} - {max(pred_prices):.2f}")
                
                # 检查数据连续性
                if len(hist_data) > 1:
                    last_hist_price = hist_data[-1]['close']
                    first_pred_price = pred_data[0]['close'] if len(pred_data) > 0 else 0
                    print(f"\n🔗 数据连续性:")
                    print(f"最后历史价格: {last_hist_price:.2f}")
                    print(f"第一个预测价格: {first_pred_price:.2f}")
                    print(f"价格跳跃: {abs(first_pred_price - last_hist_price):.2f}")
                
            else:
                print(f"❌ API返回错误: {data.get('error')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求异常: {str(e)}")

if __name__ == "__main__":
    check_api_data()
