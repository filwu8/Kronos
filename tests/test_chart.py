#!/usr/bin/env python3
"""
测试图表创建
"""

import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def test_chart_creation():
    """测试图表创建过程"""
    print("🎨 测试图表创建过程")
    
    # 获取真实数据
    response = requests.post(
        'http://localhost:8000/predict', 
        json={'stock_code': '000001', 'pred_len': 5, 'lookback': 100}
    )
    
    if response.status_code != 200:
        print("❌ 无法获取数据")
        return
    
    data = response.json()
    if not data.get('success'):
        print("❌ API返回错误")
        return
    
    historical_data = data['data']['historical_data']
    predictions = data['data']['predictions']
    stock_info = data['data']['stock_info']
    
    print(f"📊 原始数据:")
    print(f"  历史数据: {len(historical_data)} 条")
    print(f"  预测数据: {len(predictions)} 条")
    
    # 模拟图表创建过程
    try:
        # 准备历史数据
        hist_df = pd.DataFrame(historical_data)
        print(f"\n📈 历史数据DataFrame:")
        print(f"  形状: {hist_df.shape}")
        print(f"  列: {list(hist_df.columns)}")
        print(f"  索引: {hist_df.index}")
        
        # 生成日期序列
        hist_df['date'] = pd.date_range(
            end=pd.Timestamp.now().date(), 
            periods=len(hist_df), 
            freq='D'
        )
        print(f"  日期范围: {hist_df['date'].min()} 到 {hist_df['date'].max()}")
        print(f"  价格范围: {hist_df['close'].min():.2f} 到 {hist_df['close'].max():.2f}")
        
        # 准备预测数据
        pred_df = pd.DataFrame(predictions)
        print(f"\n🔮 预测数据DataFrame:")
        print(f"  形状: {pred_df.shape}")
        print(f"  列: {list(pred_df.columns)}")
        
        # 生成预测日期序列
        last_hist_date = hist_df['date'].max()
        pred_df['date'] = pd.date_range(
            start=last_hist_date + pd.Timedelta(days=1),
            periods=len(pred_df),
            freq='D'
        )
        print(f"  日期范围: {pred_df['date'].min()} 到 {pred_df['date'].max()}")
        print(f"  价格范围: {pred_df['close'].min():.2f} 到 {pred_df['close'].max():.2f}")
        
        # 检查数据连续性
        print(f"\n🔗 数据连续性检查:")
        print(f"  历史数据最后日期: {hist_df['date'].iloc[-1]}")
        print(f"  预测数据第一日期: {pred_df['date'].iloc[0]}")
        print(f"  历史数据最后价格: {hist_df['close'].iloc[-1]:.2f}")
        print(f"  预测数据第一价格: {pred_df['close'].iloc[0]:.2f}")
        
        # 创建简单图表测试
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=('股价走势', '成交量'),
            vertical_spacing=0.1,
            row_heights=[0.7, 0.3]
        )
        
        # 添加历史价格线
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
        
        # 添加预测价格线
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
        
        print(f"\n✅ 图表创建成功")
        print(f"  历史价格线: {len(hist_df)} 个数据点")
        print(f"  预测价格线: {len(pred_df)} 个数据点")
        
        # 检查数据点是否为空
        if len(hist_df) == 0:
            print("⚠️ 警告: 历史数据为空")
        if len(pred_df) == 0:
            print("⚠️ 警告: 预测数据为空")
        
        # 检查价格数据是否有效
        if hist_df['close'].isna().any():
            print("⚠️ 警告: 历史价格包含NaN值")
        if pred_df['close'].isna().any():
            print("⚠️ 警告: 预测价格包含NaN值")
        
        # 保存图表用于调试
        fig.update_layout(
            title=f"{stock_info['name']} ({stock_info['code']}) - 价格预测",
            xaxis_title="日期",
            height=600,
            showlegend=True,
            hovermode='x unified'
        )
        
        fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
        fig.update_yaxes(title_text="成交量", row=2, col=1)
        
        # 输出图表HTML用于调试
        html_content = fig.to_html()
        with open('debug_chart.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"📄 图表已保存到 debug_chart.html")
        
        return True
        
    except Exception as e:
        print(f"❌ 图表创建失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_chart_creation()
