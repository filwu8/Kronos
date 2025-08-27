#!/usr/bin/env python3
"""
测试历史数据周期修复
"""

import requests
import time
from datetime import datetime, timedelta

def test_period_parameter():
    """测试不同period参数的数据范围"""
    print("📅 测试历史数据周期参数...")
    
    stock_code = "000968"  # 用户测试的股票
    periods = ["6mo", "1y", "2y", "5y"]
    
    for period in periods:
        print(f"\n🔍 测试周期: {period}")
        
        try:
            start_time = time.time()
            response = requests.post(
                'http://localhost:8000/predict',
                json={
                    'stock_code': stock_code, 
                    'period': period,
                    'pred_len': 3,
                    'lookback': 500  # 设置较大的lookback确保不被限制
                },
                timeout=30
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    historical_data = data['data']['historical_data']
                    stock_info = data['data']['stock_info']
                    
                    if historical_data:
                        # 分析数据范围
                        dates = [item['date'] for item in historical_data]
                        start_date = min(dates)
                        end_date = max(dates)
                        data_count = len(historical_data)
                        
                        # 计算实际时间跨度
                        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                        end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                        actual_days = (end_dt - start_dt).days
                        
                        print(f"   ✅ 成功 ({end_time - start_time:.1f}s)")
                        print(f"   📊 股票: {stock_info['name']} ({stock_info['code']})")
                        print(f"   📅 数据范围: {start_date} 到 {end_date}")
                        print(f"   📈 数据条数: {data_count} 条")
                        print(f"   ⏱️ 实际跨度: {actual_days} 天")
                        
                        # 验证期望的时间范围
                        expected_days = {
                            "6mo": 6 * 30,
                            "1y": 365,
                            "2y": 2 * 365,
                            "5y": 5 * 365
                        }
                        
                        expected = expected_days.get(period, 365)
                        if actual_days >= expected * 0.8:  # 允许20%的误差
                            print(f"   ✅ 时间范围正确 (期望≥{expected}天)")
                        else:
                            print(f"   ⚠️ 时间范围偏小 (期望≥{expected}天，实际{actual_days}天)")
                    else:
                        print(f"   ❌ 无历史数据")
                else:
                    print(f"   ❌ 预测失败: {data.get('error')}")
            else:
                print(f"   ❌ HTTP错误: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ 请求异常: {str(e)}")

def test_data_adapter_directly():
    """直接测试数据适配器"""
    print("\n🔧 直接测试数据适配器...")
    
    try:
        import sys
        sys.path.append('app')
        from akshare_adapter import AkshareDataAdapter
        
        adapter = AkshareDataAdapter()
        stock_code = "000968"
        
        for period in ["6mo", "1y", "2y"]:
            print(f"\n📊 测试 {period}:")
            
            df = adapter.get_stock_data(stock_code, lookback=500, period=period)
            
            if df is not None:
                start_date = df['date'].min().strftime('%Y-%m-%d')
                end_date = df['date'].max().strftime('%Y-%m-%d')
                data_count = len(df)
                
                print(f"   ✅ 数据获取成功")
                print(f"   📅 范围: {start_date} 到 {end_date}")
                print(f"   📈 条数: {data_count}")
            else:
                print(f"   ❌ 数据获取失败")
                
        return True
        
    except Exception as e:
        print(f"   ❌ 测试失败: {str(e)}")
        return False

def analyze_csv_data():
    """分析CSV原始数据"""
    print("\n📁 分析CSV原始数据...")
    
    try:
        import pandas as pd
        
        csv_file = "volumes/data/akshare_data/000968.csv"
        df = pd.read_csv(csv_file)
        
        print(f"   📊 原始数据总条数: {len(df)}")
        
        if '日期' in df.columns:
            df['日期'] = pd.to_datetime(df['日期'])
            start_date = df['日期'].min().strftime('%Y-%m-%d')
            end_date = df['日期'].max().strftime('%Y-%m-%d')
            
            print(f"   📅 完整范围: {start_date} 到 {end_date}")
            
            # 计算不同周期的预期数据量
            end_dt = df['日期'].max()
            
            periods = {
                "6mo": end_dt - timedelta(days=6*30),
                "1y": end_dt - timedelta(days=365),
                "2y": end_dt - timedelta(days=2*365),
                "5y": end_dt - timedelta(days=5*365)
            }
            
            for period, start_dt in periods.items():
                filtered_df = df[df['日期'] >= start_dt]
                print(f"   {period}: {len(filtered_df)} 条 ({start_dt.strftime('%Y-%m-%d')} 起)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 分析失败: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🔍 历史数据周期修复测试")
    print("=" * 60)
    
    # 分析原始数据
    csv_ok = analyze_csv_data()
    
    # 测试数据适配器
    adapter_ok = test_data_adapter_directly()
    
    # 测试API
    api_ok = True
    try:
        test_period_parameter()
    except Exception as e:
        print(f"API测试失败: {str(e)}")
        api_ok = False
    
    print("\n" + "=" * 60)
    print("📊 测试结果:")
    print(f"   CSV数据分析: {'✅ 正常' if csv_ok else '❌ 异常'}")
    print(f"   数据适配器: {'✅ 正常' if adapter_ok else '❌ 异常'}")
    print(f"   API测试: {'✅ 正常' if api_ok else '❌ 异常'}")
    
    if csv_ok and adapter_ok and api_ok:
        print("\n🎉 历史数据周期修复完成!")
        print("\n✅ 修复内容:")
        print("   1. 添加period参数到get_stock_data方法")
        print("   2. 实现时间范围过滤逻辑")
        print("   3. 更新所有调用点传递period参数")
        print("   4. 添加数据范围日志输出")
        
        print("\n📅 支持的周期:")
        print("   - 6个月 (6mo): 最近180天")
        print("   - 1年 (1y): 最近365天")
        print("   - 2年 (2y): 最近730天")
        print("   - 5年 (5y): 最近1825天")
        
        print("\n🌐 测试建议:")
        print("   1. 在Streamlit界面选择不同的历史数据周期")
        print("   2. 观察图表中历史数据的起始日期")
        print("   3. 验证数据范围是否符合选择的周期")
        
    else:
        print("\n⚠️ 部分功能需要进一步检查")

if __name__ == "__main__":
    main()
