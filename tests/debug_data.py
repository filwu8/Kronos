#!/usr/bin/env python3
"""
调试数据结构脚本
"""

import requests
import json
import pandas as pd

def debug_api_data():
    """调试API返回的数据结构"""
    print("🔍 调试API数据结构")
    print("=" * 40)
    
    try:
        # 测试预测API
        response = requests.post(
            "http://localhost:8000/predict",
            json={
                "stock_code": "000001",
                "pred_len": 5,
                "lookback": 50
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("✅ API调用成功")
                
                # 检查数据结构
                result_data = data['data']
                
                print("\n📊 数据结构分析:")
                print(f"- stock_info: {type(result_data.get('stock_info'))}")
                print(f"- historical_data: {type(result_data.get('historical_data'))}")
                print(f"- predictions: {type(result_data.get('predictions'))}")
                print(f"- summary: {type(result_data.get('summary'))}")
                
                # 检查历史数据
                hist_data = result_data.get('historical_data', [])
                print(f"\n📈 历史数据:")
                print(f"- 数量: {len(hist_data)}")
                if len(hist_data) > 0:
                    print(f"- 第一条: {hist_data[0]}")
                    print(f"- 字段: {list(hist_data[0].keys())}")
                
                # 检查预测数据
                pred_data = result_data.get('predictions', [])
                print(f"\n🔮 预测数据:")
                print(f"- 数量: {len(pred_data)}")
                if len(pred_data) > 0:
                    print(f"- 第一条: {pred_data[0]}")
                    print(f"- 字段: {list(pred_data[0].keys())}")
                
                # 转换为DataFrame测试
                print(f"\n🧪 DataFrame转换测试:")
                try:
                    hist_df = pd.DataFrame(hist_data)
                    print(f"- 历史数据DataFrame形状: {hist_df.shape}")
                    print(f"- 历史数据列: {list(hist_df.columns)}")
                    print(f"- 历史数据索引: {hist_df.index}")
                    
                    pred_df = pd.DataFrame(pred_data)
                    print(f"- 预测数据DataFrame形状: {pred_df.shape}")
                    print(f"- 预测数据列: {list(pred_df.columns)}")
                    print(f"- 预测数据索引: {pred_df.index}")
                    
                    # 检查是否有日期相关字段
                    print(f"\n📅 日期字段检查:")
                    for col in hist_df.columns:
                        if 'date' in col.lower() or 'time' in col.lower():
                            print(f"- 历史数据日期字段: {col}")
                    
                    for col in pred_df.columns:
                        if 'date' in col.lower() or 'time' in col.lower():
                            print(f"- 预测数据日期字段: {col}")
                    
                    # 检查索引是否是日期
                    print(f"- 历史数据索引类型: {type(hist_df.index)}")
                    print(f"- 预测数据索引类型: {type(pred_df.index)}")
                    
                except Exception as e:
                    print(f"❌ DataFrame转换失败: {str(e)}")
                
            else:
                print(f"❌ API返回错误: {data.get('error')}")
        else:
            print(f"❌ HTTP错误: {response.status_code}")
            print(f"响应: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")

def test_chart_creation():
    """测试图表创建"""
    print("\n🎨 测试图表创建")
    print("=" * 40)
    
    # 模拟数据
    historical_data = [
        {"open": 10.0, "high": 10.5, "low": 9.8, "close": 10.2, "volume": 1000000, "amount": 10200000},
        {"open": 10.2, "high": 10.8, "low": 10.0, "close": 10.5, "volume": 1200000, "amount": 12600000},
        {"open": 10.5, "high": 11.0, "low": 10.3, "close": 10.8, "volume": 1100000, "amount": 11880000},
    ]
    
    predictions = [
        {"open": 10.8, "high": 11.2, "low": 10.6, "close": 11.0, "volume": 1050000, "amount": 11550000},
        {"open": 11.0, "high": 11.5, "low": 10.9, "close": 11.3, "volume": 1150000, "amount": 12995000},
    ]
    
    stock_info = {"name": "测试股票", "code": "000001"}
    
    try:
        # 导入必要的库
        import sys
        sys.path.append('.')
        from app.streamlit_app import create_price_chart
        
        # 创建图表
        fig = create_price_chart(historical_data, predictions, stock_info)
        
        if fig is not None:
            print("✅ 图表创建成功")
        else:
            print("❌ 图表创建失败")
            
    except Exception as e:
        print(f"❌ 图表创建异常: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_api_data()
    test_chart_creation()
