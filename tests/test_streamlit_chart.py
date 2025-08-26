#!/usr/bin/env python3
"""
测试Streamlit图表显示
"""

import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta

def test_chart_in_streamlit():
    """在Streamlit中测试图表"""
    st.title("🔍 图表显示测试")
    
    if st.button("测试图表创建"):
        with st.spinner("获取数据中..."):
            # 获取数据
            try:
                response = requests.post(
                    'http://localhost:8000/predict', 
                    json={'stock_code': '000001', 'pred_len': 5, 'lookback': 50}
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get('success'):
                        st.success("✅ 数据获取成功")
                        
                        historical_data = data['data']['historical_data']
                        predictions = data['data']['predictions']
                        stock_info = data['data']['stock_info']
                        
                        st.write(f"📊 历史数据: {len(historical_data)} 条")
                        st.write(f"🔮 预测数据: {len(predictions)} 条")
                        
                        # 显示原始数据样本
                        with st.expander("查看原始数据"):
                            st.write("历史数据样本:")
                            st.json(historical_data[:2])
                            st.write("预测数据样本:")
                            st.json(predictions[:2])
                        
                        # 创建图表
                        st.subheader("📈 图表测试")
                        
                        try:
                            # 准备数据
                            hist_df = pd.DataFrame(historical_data)
                            pred_df = pd.DataFrame(predictions)
                            
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
                            
                            st.write("📅 数据处理完成:")
                            st.write(f"历史数据日期范围: {hist_df['date'].min()} 到 {hist_df['date'].max()}")
                            st.write(f"预测数据日期范围: {pred_df['date'].min()} 到 {pred_df['date'].max()}")
                            
                            # 创建图表
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
                                title=f"{stock_info['name']} ({stock_info['code']}) - 价格预测测试",
                                xaxis_title="日期",
                                height=600,
                                showlegend=True,
                                hovermode='x unified'
                            )
                            
                            fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
                            fig.update_yaxes(title_text="成交量", row=2, col=1)
                            
                            st.success("✅ 图表创建成功")
                            st.plotly_chart(fig, use_container_width=True)
                            
                            # 显示数据统计
                            st.subheader("📊 数据统计")
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.write("**历史数据统计:**")
                                st.write(f"数据点数: {len(hist_df)}")
                                st.write(f"价格范围: {hist_df['close'].min():.2f} - {hist_df['close'].max():.2f}")
                                st.write(f"最新价格: {hist_df['close'].iloc[-1]:.2f}")
                            
                            with col2:
                                st.write("**预测数据统计:**")
                                st.write(f"数据点数: {len(pred_df)}")
                                st.write(f"价格范围: {pred_df['close'].min():.2f} - {pred_df['close'].max():.2f}")
                                st.write(f"最终预测价格: {pred_df['close'].iloc[-1]:.2f}")
                            
                        except Exception as e:
                            st.error(f"❌ 图表创建失败: {str(e)}")
                            st.code(str(e))
                            import traceback
                            st.code(traceback.format_exc())
                    else:
                        st.error(f"❌ API返回错误: {data.get('error')}")
                else:
                    st.error(f"❌ HTTP错误: {response.status_code}")
            except Exception as e:
                st.error(f"❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    test_chart_in_streamlit()
