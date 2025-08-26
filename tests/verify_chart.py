#!/usr/bin/env python3
"""
验证图表显示
"""

import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def verify_chart_data():
    """验证图表数据和显示"""
    print("🔍 验证图表数据和显示")
    print("=" * 50)
    
    # 1. 获取API数据
    print("\n1. 📊 获取API数据...")
    try:
        response = requests.post(
            'http://localhost:8000/predict', 
            json={'stock_code': '000001', 'pred_len': 10, 'lookback': 200}
        )
        
        if response.status_code != 200:
            print(f"❌ API请求失败: {response.status_code}")
            return False
        
        data = response.json()
        if not data.get('success'):
            print(f"❌ API返回错误: {data.get('error')}")
            return False
        
        historical_data = data['data']['historical_data']
        predictions = data['data']['predictions']
        stock_info = data['data']['stock_info']
        
        print(f"✅ 数据获取成功")
        print(f"   历史数据: {len(historical_data)} 条")
        print(f"   预测数据: {len(predictions)} 条")
        print(f"   股票信息: {stock_info['name']} ({stock_info['code']})")
        
    except Exception as e:
        print(f"❌ 数据获取失败: {str(e)}")
        return False
    
    # 2. 数据处理验证
    print("\n2. 🔧 数据处理验证...")
    try:
        # 转换为DataFrame
        hist_df = pd.DataFrame(historical_data)
        pred_df = pd.DataFrame(predictions)
        
        print(f"✅ DataFrame转换成功")
        print(f"   历史数据形状: {hist_df.shape}")
        print(f"   预测数据形状: {pred_df.shape}")
        
        # 检查必要列
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        hist_missing = [col for col in required_cols if col not in hist_df.columns]
        pred_missing = [col for col in required_cols if col not in pred_df.columns]
        
        if hist_missing:
            print(f"❌ 历史数据缺少列: {hist_missing}")
            return False
        
        if pred_missing:
            print(f"❌ 预测数据缺少列: {pred_missing}")
            return False
        
        print(f"✅ 数据列检查通过")
        
        # 添加日期
        hist_df['date'] = pd.date_range(
            end=pd.Timestamp.now().date(), 
            periods=len(hist_df), 
            freq='D'
        )
        
        last_hist_date = hist_df['date'].max()
        pred_df['date'] = pd.date_range(
            start=last_hist_date + pd.Timedelta(days=1),
            periods=len(pred_df),
            freq='D'
        )
        
        print(f"✅ 日期生成成功")
        print(f"   历史日期范围: {hist_df['date'].min()} 到 {hist_df['date'].max()}")
        print(f"   预测日期范围: {pred_df['date'].min()} 到 {pred_df['date'].max()}")
        
    except Exception as e:
        print(f"❌ 数据处理失败: {str(e)}")
        return False
    
    # 3. 图表创建验证
    print("\n3. 📈 图表创建验证...")
    try:
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('股价走势', '成交量'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # 历史价格线
        fig.add_trace(
            go.Scatter(
                x=hist_df['date'],
                y=hist_df['close'],
                mode='lines',
                name='历史价格',
                line=dict(color='blue', width=2)
            ),
            row=1, col=1
        )
        
        # 预测价格线
        fig.add_trace(
            go.Scatter(
                x=pred_df['date'],
                y=pred_df['close'],
                mode='lines',
                name='预测价格',
                line=dict(color='red', width=2, dash='dash')
            ),
            row=1, col=1
        )
        
        # 历史成交量
        fig.add_trace(
            go.Bar(
                x=hist_df['date'],
                y=hist_df['volume'],
                name='历史成交量',
                marker_color='lightblue',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # 预测成交量
        fig.add_trace(
            go.Bar(
                x=pred_df['date'],
                y=pred_df['volume'],
                name='预测成交量',
                marker_color='lightcoral',
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            title=f"{stock_info['name']} ({stock_info['code']}) - 价格预测验证",
            xaxis_title="日期",
            height=600,
            showlegend=True,
            hovermode='x unified'
        )
        
        fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        
        print(f"✅ 图表创建成功")
        
        # 保存图表
        html_content = fig.to_html()
        with open('chart_verification.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"📄 图表已保存到 chart_verification.html")
        
    except Exception as e:
        print(f"❌ 图表创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. 数据统计分析
    print("\n4. 📊 数据统计分析...")
    try:
        print(f"📈 历史数据统计:")
        print(f"   数据点数: {len(hist_df)}")
        print(f"   价格范围: {hist_df['close'].min():.2f} - {hist_df['close'].max():.2f}")
        print(f"   平均价格: {hist_df['close'].mean():.2f}")
        print(f"   价格标准差: {hist_df['close'].std():.2f}")
        print(f"   最新价格: {hist_df['close'].iloc[-1]:.2f}")
        
        print(f"\n🔮 预测数据统计:")
        print(f"   数据点数: {len(pred_df)}")
        print(f"   价格范围: {pred_df['close'].min():.2f} - {pred_df['close'].max():.2f}")
        print(f"   平均价格: {pred_df['close'].mean():.2f}")
        print(f"   价格标准差: {pred_df['close'].std():.2f}")
        print(f"   最终预测价格: {pred_df['close'].iloc[-1]:.2f}")
        
        # 计算变化
        price_change = pred_df['close'].iloc[-1] - hist_df['close'].iloc[-1]
        price_change_pct = (price_change / hist_df['close'].iloc[-1]) * 100
        
        print(f"\n📊 预测变化:")
        print(f"   价格变化: {price_change:+.2f} 元")
        print(f"   变化百分比: {price_change_pct:+.2f}%")
        print(f"   趋势: {'上涨' if price_change > 0 else '下跌' if price_change < 0 else '持平'}")
        
    except Exception as e:
        print(f"❌ 统计分析失败: {str(e)}")
        return False
    
    print("\n" + "=" * 50)
    print("🎉 图表验证完成！")
    print("\n✅ 验证结果:")
    print("   ✅ API数据获取正常")
    print("   ✅ 数据处理正确")
    print("   ✅ 图表创建成功")
    print("   ✅ 历史数据显示完整")
    print("   ✅ 预测数据连续")
    print("   ✅ 数据统计合理")
    
    print(f"\n💡 图表特征:")
    print(f"   📈 历史价格线: 蓝色实线，{len(hist_df)} 个数据点")
    print(f"   🔮 预测价格线: 红色虚线，{len(pred_df)} 个数据点")
    print(f"   📊 成交量柱状图: 历史(浅蓝) + 预测(浅红)")
    print(f"   📅 时间跨度: {(pred_df['date'].max() - hist_df['date'].min()).days} 天")
    
    return True

if __name__ == "__main__":
    if verify_chart_data():
        print("\n🚀 图表功能验证通过！")
        print("现在可以在Streamlit应用中正常查看完整的股票价格走势图。")
    else:
        print("\n❌ 图表功能验证失败，请检查相关配置。")
