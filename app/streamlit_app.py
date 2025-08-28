"""
Streamlit前端应用
股票预测Web界面
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import requests
import os
from pathlib import Path

# 导入静态资源管理器和中文菜单
try:
    from static_manager import StaticResourceManager
    from chinese_menu import ChineseMenu, create_chinese_sidebar, create_sidebar_status_section
except ImportError:
    StaticResourceManager = None
    ChineseMenu = None
    create_sidebar_status_section = None
import json
from datetime import datetime, timedelta
import time
import base64

# 页面配置
st.set_page_config(
    page_title="Gordon Wang 的股票预测系统",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_local_resources():
    """加载本地静态资源"""
    # 检查静态资源目录
    static_dir = Path("static")
    if not static_dir.exists():
        st.warning("⚠️ 静态资源目录不存在，正在创建...")
        static_dir.mkdir(exist_ok=True)
        (static_dir / "css").mkdir(exist_ok=True)
        (static_dir / "js").mkdir(exist_ok=True)

    # 合并注入：将多个CSS与JS一次性注入，减少顶部容器占位
    css_bundle = []
    for css_path in ["static/css/chinese_ui.css", "static/css/local.css"]:
        p = Path(css_path)
        if p.exists():
            css_bundle.append(p.read_text(encoding='utf-8'))

    js_bundle = []
    for js_path in ["static/js/chinese_ui.js"]:
        p = Path(js_path)
        if p.exists():
            js_bundle.append(p.read_text(encoding='utf-8'))

    # 使用一次 st.markdown 注入，避免 iframe 产生额外占位
    # Add aggressive top spacing removal CSS
    aggressive_css = """
/* Keep header hidden only, avoid over-aggressive global resets */
[data-testid="stHeader"] { display: none !important; }
"""

    # 限制标题跑马灯位移范围，避免溢出
    css_bundle.append("""
    .title-banner { overflow: hidden; }
    .main-header.moving { animation: rainbow-move 8s linear infinite; }
    @keyframes rainbow-move {
      0% { transform: translateX(0); }
      85% { transform: translateX(0); }
      100% { transform: translateX(0); }
    }
    """)

    bundle_html = f"<style>{aggressive_css}{''.join(css_bundle)}</style>\n<script>{''.join(js_bundle)}</script>"
    st.markdown(bundle_html, unsafe_allow_html=True)

# 加载本地资源（注入 CSS/JS bundle）
load_local_resources()



# 读取根目录 logo.png 并返回 data URI，避免静态路径加载失败
def get_logo_data_uri() -> str:
    try:
        p = Path("logo.png")
        if p.exists():
            b64 = base64.b64encode(p.read_bytes()).decode('utf-8')
            return f"data:image/png;base64,{b64}"
    except Exception:
        pass
    return ""

# API配置 - 支持容器内部通信
import os
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")

# 自定义CSS合并：移入静态文件或bundle中，避免重复注入容器
# 注：如需新增样式，建议追加到 static/css/chinese_ui.css 或 static/css/local.css 中


def check_api_health():
    """检查API服务状态"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def get_stock_prediction(stock_code, **params):
    """获取股票预测"""
    try:
        payload = {
            "stock_code": stock_code,
            **params
        }

        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=payload,
            timeout=120  # 压缩超时：避免前端长期挂起，后端内部有CPU回退与缓存
        )

        if response.status_code == 200:
            return response.json()
        else:
            return {
                "success": False,
                "error": f"API请求失败: {response.status_code}"
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"请求异常: {str(e)}"
        }


def get_stock_info(stock_code):
    """获取股票信息"""
    try:
        response = requests.get(f"{API_BASE_URL}/stocks/{stock_code}/info", timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None


def format_volume(volume):
    """格式化成交量显示"""
    if volume >= 100000000:  # 1亿以上
        return f"{volume/100000000:.1f}亿手"
    elif volume >= 10000:  # 1万以上
        return f"{volume/10000:.1f}万手"
    else:
        return f"{volume:.0f}手"

def format_amount(amount):
    """格式化成交额显示"""
    if amount >= 100000000:  # 1亿以上
        return f"{amount/100000000:.1f}亿元"
    elif amount >= 10000:  # 1万以上
        return f"{amount/10000:.1f}万元"
    else:
        return f"{amount:.0f}元"

def create_price_chart(historical_data, predictions, stock_info):
    """创建价格预测图表"""
    try:
        # 准备历史数据
        hist_df = pd.DataFrame(historical_data)

        # 处理历史数据的日期字段（优先使用字符串，避免浏览器/时区偏移）
        if 'date' in hist_df.columns:
            hist_df['date_str'] = hist_df['date'].astype(str)
        else:
            # 如果没有日期字段，生成工作日日期字符串序列
            tmp_dates = pd.bdate_range(end=pd.Timestamp.today().normalize(), periods=len(hist_df))
            hist_df['date_str'] = pd.Series(tmp_dates).dt.strftime('%Y-%m-%d')


        # 统一历史数据X轴（无论是否存在 date 列，都提供字符串X轴）
        hist_x = (
            hist_df['date_str'] if 'date_str' in hist_df.columns else (
                hist_df['date'].astype(str) if 'date' in hist_df.columns else pd.Series(range(len(hist_df))).astype(str)
            )
        )

        # 为悬浮提示准备日期标签（YY-MM-DD）
        if 'date_str' in hist_df.columns:
            _hist_dt = pd.to_datetime(hist_df['date_str'], errors='coerce')
            hist_df['date_label'] = _hist_dt.dt.strftime('%Y-%m-%d')
        elif 'date' in hist_df.columns:
            _hist_dt = pd.to_datetime(hist_df['date'], errors='coerce')
            hist_df['date_label'] = _hist_dt.dt.strftime('%Y-%m-%d')
        else:
            # 无日期信息，使用X轴字符串兜底
            _tmp = pd.to_datetime(hist_x, errors='coerce')
            hist_df['date_label'] = _tmp.dt.strftime('%Y-%m-%d').fillna(hist_x)


        # 准备预测数据
        pred_df = pd.DataFrame(predictions)

        # 处理预测数据的日期字段（统一字符串，避免浏览器解析偏移）
        if 'date' in pred_df.columns:
            pred_df['date'] = pred_df['date'].astype(str)
        else:
            if len(pred_df) > 0:
                # 生成预测日期序列（字符串）
                if len(hist_df) > 0 and 'date' in hist_df.columns:
                    hist_df = hist_df.sort_values('date')
                    last_hist_str = str(hist_df['date'].iloc[-1])
                    last_dt = pd.to_datetime(last_hist_str, errors='coerce')
                    pred_dates = pd.bdate_range(start=last_dt + pd.Timedelta(days=1), periods=len(pred_df))
                else:
                    pred_dates = pd.bdate_range(start=pd.Timestamp.now().normalize() + pd.Timedelta(days=1), periods=len(pred_df))
                pred_df['date'] = pd.Series(pred_dates).dt.strftime('%Y-%m-%d')

        # 额外保障：去掉与历史重叠的预测日期（字符串比较）
        if len(hist_df) > 0 and 'date' in hist_df.columns and len(pred_df) > 0 and 'date' in pred_df.columns:
            hist_df = hist_df.sort_values('date')
            last_hist_str = str(hist_df['date'].iloc[-1])
            pred_df = pred_df[pred_df['date'] > last_hist_str]

        # 历史数据完整性（仅要求历史K线必要列）
        hist_required = ['open', 'high', 'low', 'close', 'volume']
        for col in hist_required:
            if col not in hist_df.columns:
                print(f"历史数据缺少列: {col}")
                return None
        for col in hist_required:
            hist_df[col] = pd.to_numeric(hist_df[col], errors='coerce')
        hist_df = hist_df.dropna(subset=hist_required)
        if len(hist_df) == 0:
            print("历史数据为空")
            return None

        # 预测数据为可选：仅对存在的列做转换
        if len(pred_df) > 0:
            for c in ['open','high','low','close','volume']:
                if c in pred_df.columns:
                    pred_df[c] = pd.to_numeric(pred_df[c], errors='coerce')
            # 按可用列过滤空值（至少需要 close 才绘制预测均值）
            if 'close' in pred_df.columns:
                pred_df = pred_df.dropna(subset=['close'])

        # 创建两行子图（上：K线；下：成交量），共享X轴，避免遮挡
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=False,
            vertical_spacing=0.03,
            row_heights=[0.70, 0.30]
        )

        # 成交量单位自适应（仅两档）：手 / 万手（预测成交量可选）
        # 成交量转为数值，避免字符串/缺失导致柱子等高
        hist_df['_volume_num'] = pd.to_numeric(hist_df['volume'], errors='coerce') if 'volume' in hist_df.columns else pd.Series([0]*len(hist_df))
        vol_max_hist = float(hist_df['_volume_num'].fillna(0).max()) if len(hist_df) > 0 else 0.0
        vol_max_pred = float(pd.to_numeric(pred_df['volume'], errors='coerce').fillna(0).max()) if (len(pred_df) > 0 and ('volume' in pred_df.columns)) else 0.0
        vol_max = max(vol_max_hist, vol_max_pred)
        if vol_max < 1e4:
            vol_unit = '手'; vol_factor = 1.0; vol_decimals = 0
        else:
            vol_unit = '万手'; vol_factor = 1e4; vol_decimals = 2

        hist_vol_plot = hist_df['_volume_num'].fillna(0) / vol_factor
        pred_vol_plot = (pd.to_numeric(pred_df['volume'], errors='coerce').fillna(0) / vol_factor) if ('volume' in pred_df.columns and len(pred_df) > 0) else None
        # 按中文规则构建成交量标签与K线悬浮文本
        vol_label = hist_vol_plot.map(lambda v: f"{v:.2f} 万手" if vol_unit == '万手' else f"{v:.0f} 手")


        # 计算涨跌额/涨跌幅并构建K线悬浮文本
        hist_df['prev_close'] = pd.to_numeric(hist_df['close'], errors='coerce').shift(1)
        hist_df['chg'] = pd.to_numeric(hist_df['close'], errors='coerce') - hist_df['prev_close']
        hist_df['chg_pct'] = (hist_df['chg'] / hist_df['prev_close']) * 100
        hist_df['chg_disp'] = hist_df['chg'].map(lambda x: '-' if pd.isna(x) else f"{x:+.2f}")
        hist_df['chg_pct_disp'] = hist_df['chg_pct'].map(lambda x: '-' if (pd.isna(x) or np.isinf(x)) else f"{x:+.2f}%")

        hist_hover_text = [
            f"<b>历史K线</b><br>"
            f"日期: {d}<br>"
            f"开盘: ¥{o:.2f}<br>"
            f"最高: ¥{h:.2f}<br>"
            f"最低: ¥{l:.2f}<br>"
            f"收盘: ¥{c:.2f}<br>"
            f"涨跌额: {da}<br>"
            f"涨跌幅: {dp}<br>"
            f"成交量: {vl}"
            for d,o,h,l,c,da,dp,vl in zip(
                hist_df['date_label'], hist_df['open'], hist_df['high'], hist_df['low'], hist_df['close'], hist_df['chg_disp'], hist_df['chg_pct_disp'], vol_label
            )
        ]

        # 构建成交量悬浮文本（历史/预测）
        hist_bar_text = [f"日期: {d}<br>成交量: {vl}" for d, vl in zip(hist_df['date_label'], vol_label)]


        # 历史价格蜡烛图（上图）
        fig.add_trace(
            go.Candlestick(
                x=hist_x,
                open=hist_df['open'],
                high=hist_df['high'],
                low=hist_df['low'],
                close=hist_df['close'],
                name='历史K线',
                increasing_line_color='red',
                decreasing_line_color='green',
                text=hist_hover_text,
                hoverinfo='text',
                showlegend=True
            ),
            row=1, col=1
        )

        # 预测区间与均值（若有预测数据再绘制）
        has_pred = (pred_df is not None) and (len(pred_df) > 0) and ('close' in pred_df.columns)
        if has_pred:
            # 获取真实的蒙特卡洛不确定性区间
            if 'close_upper' in pred_df.columns and 'close_lower' in pred_df.columns:
                pred_upper = pred_df['close_upper']

                # 为成交量悬浮准备标签（手/万手，中文格式）
                vol_label = hist_vol_plot.map(lambda v: f"{v:.2f} {vol_unit}" if vol_unit == '万手' else f"{v:.0f} {vol_unit}")

                pred_lower = pred_df['close_lower']
            else:
                pred_mean = pred_df['close']
                pred_volatility = pred_mean * 0.15
                pred_upper = pred_mean + pred_volatility
                pred_lower = pred_mean - pred_volatility

            # 预测不确定性区间 (阴影区域)
            fig.add_trace(
                go.Scatter(
                    x=pred_df['date'].astype(str).tolist() + pred_df['date'].astype(str).tolist()[::-1],
                    y=pred_upper.tolist() + pred_lower.tolist()[::-1],
                    fill='toself',
                    fillcolor='rgba(255, 0, 0, 0.2)',
                    line=dict(color='rgba(255,255,255,0)'),
                    name='预测区间',
                    hoverinfo='skip',
                    showlegend=True
                ),
                row=1, col=1
            )


            # 计算预测相对历史最后收盘的涨跌额/涨跌幅（中文格式）
            try:
                last_close_val = float(hist_df['close'].iloc[-1]) if len(hist_df) > 0 else None
            except Exception:
                last_close_val = None
            if last_close_val is not None and len(pred_df) > 0:
                pred_df['_chg'] = pd.to_numeric(pred_df['close'], errors='coerce') - last_close_val
                pred_df['_chg_pct'] = (pred_df['_chg'] / last_close_val) * 100
                chg_disp = pred_df['_chg'].map(lambda x: '-' if pd.isna(x) else f"{x:+.2f}")
                chg_pct_disp = pred_df['_chg_pct'].map(lambda x: '-' if (pd.isna(x) or np.isinf(x)) else f"{x:+.2f}%")
            else:
                chg_disp = ['-'] * len(pred_df)
                chg_pct_disp = ['-'] * len(pred_df)

            # 预测价格线 (均值)
            # 构造更全面的预测悬浮信息（中文）：开/高/低/预测价、涨跌额/幅、区间、成交量
            try:
                pred_df['_open'] = pd.to_numeric(pred_df.get('open'), errors='coerce')
                pred_df['_high'] = pd.to_numeric(pred_df.get('high'), errors='coerce')
                pred_df['_low']  = pd.to_numeric(pred_df.get('low'), errors='coerce')
            except Exception:
                pred_df['_open'] = np.nan; pred_df['_high'] = np.nan; pred_df['_low'] = np.nan
            open_disp = pred_df['_open'].map(lambda x: '-' if pd.isna(x) else f"¥{x:.2f}")
            high_disp = pred_df['_high'].map(lambda x: '-' if pd.isna(x) else f"¥{x:.2f}")
            low_disp  = pred_df['_low'].map(lambda x: '-' if pd.isna(x) else f"¥{x:.2f}")
            if ('volume' in pred_df.columns and len(pred_df) > 0):
                _pred_vol = pd.to_numeric(pred_df['volume'], errors='coerce').fillna(0) / vol_factor
                pred_vol_label = _pred_vol.map(lambda v: f"{v:.2f} 万手" if vol_unit=='万手' else f"{v:.0f} 手")
            else:
                pred_vol_label = pd.Series(['-']*len(pred_df))

            fig.add_trace(
                go.Scatter(
                    x=pred_df['date'].astype(str),
                    y=pred_df['close'],
                    mode='lines',
                    name='预测均值',
                    line=dict(color='red', width=3),
                    hovertemplate='<b>预测价格</b><br>' +
                                  '预测价: ¥%{y:.2f}<br>' +
                                  '开盘: %{customdata[4]}<br>' +
                                  '最高: %{customdata[5]}<br>' +
                                  '最低: %{customdata[6]}<br>' +
                                  '涨跌额: %{customdata[2]}<br>' +
                                  '涨跌幅: %{customdata[3]}<br>' +
                                  '区间: ¥%{customdata[0]:.2f} - ¥%{customdata[1]:.2f}<br>' +
                                  '成交量: %{customdata[7]}<extra></extra>',
                    customdata=np.stack([
                        np.asarray(pred_lower),
                        np.asarray(pred_upper),
                        np.asarray(chg_disp),
                        np.asarray(chg_pct_disp),
                        np.asarray(open_disp),
                        np.asarray(high_disp),
                        np.asarray(low_disp),
                        np.asarray(pred_vol_label)
                    ], axis=-1)
                ),
                row=1, col=1
            )

        # 历史成交量（下图）
        fig.add_trace(
            go.Bar(
                x=hist_x,
                y=hist_vol_plot,
                name='历史成交量',
                marker_color='lightblue',
                opacity=0.6,
                customdata=np.stack([hist_df['date_label'].values, hist_vol_plot.values], axis=-1),
                hovertemplate='<b>历史成交量</b><br>' +
                              '日期: %{customdata[0]}<br>' +
                              '成交量: %{customdata[1]:.2f} ' + ('万手' if vol_unit=='万手' else '手') + '<extra></extra>'
            ),
            row=2, col=1
        )

        # 预测成交量（下图，若有）
        if has_pred and ('volume' in pred_df.columns):
            fig.add_trace(
                go.Bar(
                    x=pred_df['date'].astype(str),
                    y=pred_vol_plot,
                    name='预测成交量',
                    marker_color='lightcoral',
                    opacity=0.6,
                    customdata=np.stack([pred_df['date'].astype(str).values, pred_vol_plot.values], axis=-1),
                    hovertemplate='<b>预测成交量</b><br>' +
                                  '日期: %{customdata[0]}<br>' +
                                  '成交量: %{customdata[1]:.2f} ' + ('万手' if vol_unit=='万手' else '手') + '<extra></extra>'
                ),
                row=2, col=1
            )

        # 安全生成标题，避免 stock_info 为空导致下标错误
        _si = stock_info or {}
        _name = _si.get('name') or '股票'
        _code = _si.get('code') or ''
        _title_text = f"{_name} ({_code}) - 价格预测" if _code else f"{_name} - 价格预测"

        # 布局（上下子图、共享X轴）
        fig.update_layout(
            title=_title_text,
            height=680,
            margin=dict(t=80, l=60, r=20, b=20),
            showlegend=True,
            hovermode='x unified',
            font=dict(family="Arial, sans-serif", size=12),
            modebar=dict(
                bgcolor='rgba(255,255,255,0.8)',
                color='rgba(0,0,0,0.8)',
                activecolor='rgba(0,0,0,1)',
                remove=['lasso2d', 'select2d']
            )
        )
        # 统一头部日期，中文格式（跨版本更稳定）
        fig.update_xaxes(hoverformat='%Y-%m-%d', row=1, col=1)
        fig.update_xaxes(hoverformat='%Y-%m-%d', row=2, col=1)


        # 轴标题与样式
        fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
        fig.update_yaxes(title_text=f"成交量 ({vol_unit})", row=2, col=1, showgrid=True)

        # X 轴（统一在底部）
        fig.update_xaxes(
            tickformat='%Y-%m-%d',
            tickangle=0,
            showgrid=True,
            ticks="outside",
            row=2, col=1
        )

        return fig

    except Exception as e:
        print(f"图表创建失败: {str(e)}")
        return None


def create_metrics_display(summary):
    """创建指标展示"""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="当前价格",
            value=f"¥{summary['current_price']:.2f}"
        )

    with col2:
        st.metric(
            label="预测价格",
            value=f"¥{summary['predicted_price']:.2f}",
            delta=f"{summary['change_percent']:.2f}%"
        )

    with col3:
        st.metric(
            label="预期变化",
            value=f"¥{summary['change_amount']:.2f}"
        )

    with col4:
        trend_color = "🔴" if summary['trend'] == "下跌" else "🟢" if summary['trend'] == "上涨" else "🟡"
        st.metric(
            label="趋势预测",
            value=f"{trend_color} {summary['trend']}"
        )


def main():
    """主应用"""
    # 渲染中文化界面
    if ChineseMenu:
        # 创建中文化侧边栏
        create_chinese_sidebar()

        # 创建菜单管理器
        menu = ChineseMenu()

        # 检查当前页面
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'stock_prediction'

        # 根据选择的页面渲染不同内容
        if st.session_state.current_page == 'stock_prediction':
            render_stock_prediction_content()
        else:
            # 其他页面暂时显示开发中
            st.info(f"📝 {menu.get_page_title(st.session_state.current_page)} 功能开发中...")
            render_stock_prediction_content()  # 临时显示预测页面
    else:
        # 备选方案：原始界面
        render_stock_prediction_content()

def render_stock_prediction_content():
    """渲染股票预测内容"""
    # 标题（主副标题作为一个视觉整体且统一居中）
    logo_uri = get_logo_data_uri()
    SUBTITLE_TEXT = "基于RTX 5090 GPU加速的智能股票预测平台"
    def build_title_html(animation_state: str, logo_data_uri: str | None) -> str:
        logo_html = f'<img class="title-logo" src="{logo_data_uri}" alt="Logo">' if logo_data_uri else ''
        return (
            '<div class="title-banner">'
            f'<h1 id="main-title" class="main-header gradient-title glow {animation_state}" data-state="{animation_state}">'
            f'{logo_html}'
            'Gordon Wang 的股票预测系统'
            '</h1>'
            f'<p class="main-subtitle">{SUBTITLE_TEXT}</p>'
            '</div>'
        )

    animation_state = st.session_state.get('title_animation_state', 'idle')
    title_html = build_title_html(animation_state, logo_uri)
    title_slot = st.empty()
    # 健康指示器占位
    status_slot = st.empty()



    title_slot.markdown(title_html, unsafe_allow_html=True)

    # 本次运行是否已渲染预测结果（用于避免重复渲染）
    rendered_result = False




    # 检查API状态
    if not check_api_health():
        st.error("⚠️ API服务不可用，请检查后端服务是否启动")
        st.info("请确保运行: `python app/api.py` 或 `uvicorn app.api:app --host 0.0.0.0 --port 8000`")
        return

    # 侧边栏配置
    st.sidebar.header("📊 预测配置")

    # 股票代码输入
    stock_code = st.sidebar.text_input(
        "股票代码",
        value="000001",
        help="输入6位股票代码，如：000001、600000"
    ).strip()

    # 预测参数
    pred_len = st.sidebar.slider("预测天数", 1, 60, 30)
    # 历史数据周期选项（中文显示，英文值）
    period_options = {
        "6个月": "6mo",
        "1年": "1y",
        "2年": "2y",
        "5年": "5y"
    }
    period_display = st.sidebar.selectbox("历史数据周期", list(period_options.keys()), index=1)
    period = period_options[period_display]

    # 高级参数
    with st.sidebar.expander("🔧 高级参数"):
        # 性能模式选择
        performance_mode = st.selectbox(
            "性能模式",
            ["标准模式", "高性能模式 (RTX 5090)"],
            index=1,
            help="RTX 5090用户推荐高性能模式"
        )

        # 根据性能模式调整默认值
        if performance_mode == "高性能模式 (RTX 5090)":
            max_lookback = 5000
            default_lookback = 2000
            help_text = "RTX 5090性能强劲，支持超大数据量处理"
        else:
            max_lookback = 1000
            default_lookback = 400
            help_text = "标准模式，适合一般硬件配置"

        lookback = st.slider("历史数据长度", 50, max_lookback, default_lookback, help=help_text)
        temperature = st.slider("采样温度", 0.1, 2.0, 1.0, 0.1)
        top_p = st.slider("核采样概率", 0.1, 1.0, 0.9, 0.05)
        sample_count = st.slider("采样次数", 1, 3, 1)

    # 若未点击“开始预测”，但 session_state 有历史结果，直接回显（不触发侧边栏按钮）
    last = st.session_state.get('last_prediction')
    if last and last.get('success') and not rendered_result:
        data = last['data']
        summary = data['summary']
        st.subheader("📊 预测摘要")
        create_metrics_display(summary)
        st.subheader("📈 价格走势图")
        try:
            fig = create_price_chart(
                data['historical_data'],
                data['predictions'],
                data['stock_info']
            )
            if fig is not None:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error("无法生成价格走势图（历史数据缺失或格式不符）")
            rendered_result = True
        except Exception as e:
            st.error(f"价格走势图渲染失败: {e}")

    # 侧边栏紧凑与徽章定位已在 create_chinese_sidebar() 统一处理，避免重复脚本

    # 刷新该股票数据（刷新成功后自动触发预测）
    if st.sidebar.button("🔄 刷新该股票数据", type="secondary", use_container_width=True):
        try:
            import requests, os
            api_base = os.getenv("API_BASE_URL", "http://localhost:8000")
            r = requests.post(f"{api_base}/refresh/{stock_code}", timeout=30)
            if r.status_code == 200 and r.json().get('success'):
                info = r.json()['data']
                st.sidebar.success(f"已更新: {info['last_date']} 来源: {info['source']}")
                # 自动触发一次预测
                st.session_state['auto_trigger_predict'] = True
                st.experimental_rerun()
            else:
                try:
                    detail = r.json().get('detail')
                except Exception:
                    detail = r.text[:200]
                st.sidebar.error(f"刷新失败: {detail}")
        except Exception as e:
            st.sidebar.error(f"刷新失败: {e}")

    # 刷新成功后的自动预测（兜底）
    if st.session_state.get('auto_trigger_predict'):
        st.session_state['auto_trigger_predict'] = False
        st.experimental_rerun()

    # 预测按钮（统一侧边栏按钮宽度）
    if st.sidebar.button("🚀 开始预测", type="primary", use_container_width=True):
        if not stock_code:
            st.error("请输入股票代码")
            return

        # 启动动画并即时重渲染标题
        st.session_state['title_animation_state'] = 'moving'
        # 立即重绘标题占位，确保动画启动
        animation_state = st.session_state.get('title_animation_state', 'idle')
        _logo_uri = get_logo_data_uri()
        live_title_html = build_title_html(animation_state, _logo_uri)
        # 先绘制标题，再用脚本强制重启动画，确保元素已存在
        title_slot.markdown(live_title_html, unsafe_allow_html=True)
        try:
            import streamlit.components.v1 as components
            components.html("""
            <script>
            (function(){
              try {
                setTimeout(function(){
                  var el = parent && parent.document ? parent.document.getElementById('main-title') : document.getElementById('main-title');
                  if(!el) return;
                  el.classList.remove('static');
                  el.classList.remove('idle');
                  // 通过移除/添加 moving 触发重排，确保动画启动
                  el.classList.remove('moving');
                  void el.offsetWidth;
                  el.classList.add('moving');
                }, 80);
              } catch(e) { /* noop */ }
            })();
            </script>
            """, height=0)
        except Exception:
            pass

        # 显示加载状态
        with st.spinner(f"正在预测 {stock_code}..."):

            # 获取股票信息
            stock_info_response = get_stock_info(stock_code)

            if stock_info_response and stock_info_response.get('success'):
                stock_info = stock_info_response['data']
                st.success(f"✅ 找到股票: {stock_info['name']} ({stock_info['code']})")
            else:
                st.warning("⚠️ 无法获取股票信息，继续预测...")
                stock_info = {'name': 'Unknown', 'code': stock_code}

            # 执行预测
            result = get_stock_prediction(
                stock_code=stock_code,
                period=period,
                pred_len=pred_len,
                lookback=lookback,
                temperature=temperature,
                top_p=top_p,
                sample_count=sample_count
            )


        # 显示结果
        if result['success']:
            data = result['data']
            summary = data['summary']

            # 显示指标
            st.subheader("📊 预测摘要")
            create_metrics_display(summary)

            # 显示图表
            st.subheader("📈 价格走势图")
            try:
                fig = create_price_chart(
                    data['historical_data'],
                    data['predictions'],
                    data['stock_info']
                )
                if fig is not None:
                    # 生成导出图片的安全文件名，避免 stock_info 为空报错
                    _si = data.get('stock_info') or {}
                    _stock_name = _si.get('name') or _si.get('code') or '股票'
                    _img_filename = f"{_stock_name}_股价预测_{datetime.now().strftime('%Y%m%d')}"

                    # 配置简化的中文工具栏
                    config = {
                        'displayModeBar': True,
                        'displaylogo': False,
                        'locale': 'zh-CN',
                        # 只保留最有用的工具
                        'modeBarButtons': [
                            ['pan2d', 'zoom2d'],           # 平移、框选缩放
                            ['zoomIn2d', 'zoomOut2d'],     # 放大、缩小
                            ['autoScale2d', 'resetScale2d'], # 自适应、重置
                            ['toImage']                     # 保存图片
                        ],
                        # 移除不常用的工具
                        'modeBarButtonsToRemove': [
                            'lasso2d', 'select2d', 'hoverClosestCartesian',
                            'hoverCompareCartesian', 'toggleSpikelines'
                        ],
                        # 中文工具提示
                        'modeBarButtonsToAdd': [
                            {
                                'name': '平移',
                                'icon': 'pan2d',
                                'title': '拖拽移动图表视角'
                            }
                        ],
                        'toImageButtonOptions': {
                            'format': 'png',
                            'filename': _img_filename,
                            'height': 800,
                            'width': 1200,
                            'scale': 2  # 高清图片
                        }
                    }
                    st.plotly_chart(fig, use_container_width=True, config=config)

                    # 为图表添加“左键锁定 + 键盘左右移动”功能（不绘制新虚线，驱动 Plotly 原生 hover）
                    import streamlit.components.v1 as components
                    components.html("""
                    <script>
                    (function(){
                      function setup(){
                        const plots = parent.document.querySelectorAll('.js-plotly-plot');
                        const plt = plots[plots.length-1];
                        if(!plt || !parent.Plotly) return;
                        const P = parent.Plotly;

                        // 以第一条曲线的 x 作为参考（x unified 模式会对齐所有 trace）
                        let xvals = [];
                        try { xvals = (plt.data && plt.data[0] && plt.data[0].x) ? plt.data[0].x.slice() : []; } catch(e) {}
                        if(!xvals || xvals.length === 0) return;

                        let idx = xvals.length - 1;  // 当前索引
                        let locked = false;           // 是否锁定（左键切换）

                        function clamp(i){ return Math.max(0, Math.min(i, xvals.length-1)); }
                        function draw(){
                          const x = xvals[clamp(idx)];
                          try { P.Fx.hover(plt, [{xval: x}], ['x']); } catch(e) {}
                        }

                        // hover 跟随：未锁定时更新 idx；锁定时强制回到锁定位置
                        function onHover(ev){
                          if (locked) { draw(); return; }
                          if (ev && ev.points && ev.points[0]) {
                            const p = ev.points[0];
                            if (typeof p.pointNumber === 'number') idx = p.pointNumber;
                            else {
                              const i = xvals.indexOf(p.x);
                              if (i >= 0) idx = i;
                            }
                          }
                        }

                        function onKey(e){
                          if(!locked) return;
                          if(e.key === 'ArrowLeft') { idx = clamp(idx-1); draw(); e.preventDefault(); }
                          else if(e.key === 'ArrowRight') { idx = clamp(idx+1); draw(); e.preventDefault(); }
                        }

                        function toggleLock(){
                          locked = !locked;
                          if (locked) {
                            draw();
                            parent.window.addEventListener('keydown', onKey);
                          } else {
                            parent.window.removeEventListener('keydown', onKey);
                          }
                        }

                        // 事件绑定
                        if (plt.on) {
                          plt.on('plotly_hover', onHover);
                          plt.on('plotly_unhover', function(){ if(locked) draw(); });
                        }
                        // 左键点击切换锁定
                        plt.addEventListener('click', function(e){ if(e.button===0){ toggleLock(); e.preventDefault(); }});
                        // 悬停控制键盘监听
                        plt.addEventListener('mouseenter', function(){ if(locked) parent.window.addEventListener('keydown', onKey); });
                        plt.addEventListener('mouseleave', function(){ if(!locked) parent.window.removeEventListener('keydown', onKey); });

                        // 初始定位
                        draw();
                      }
                      setTimeout(setup, 500);
                      setTimeout(setup, 1200);
                    })();
                    </script>
                    """, height=0)




                    # 简化：移除冗余的工具栏中文化（保留静态资源版本）
                    st.markdown("")



                    # 图表说明
                    st.markdown("---")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.markdown("""
                        **📊 蒙特卡洛预测说明**
                        - **红色实线**: 30次蒙特卡洗模拟的平均预测价格
                        - **红色阴影区域**: 25%-75%分位数区间（50%概率范围）
                        - **蓝色实线**: 历史真实价格数据
                        - **预测方法**: Kronos-small模型 + 30条独立预测路径
                        - **不确定性**: 阴影区域越宽表示预测分歧越大
                        """)

                    with col2:
                        pass




            except Exception as e:
                st.error(f"图表生成失败: {str(e)}")

            # 详细信息
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📋 预测详情")
                st.write(f"**波动率**: {summary['volatility']:.2f}%")
                st.write(f"**置信度**: {summary['confidence']}")
                st.write(f"**预测天数**: {summary['prediction_days']} 天")

                # 风险提示
                if abs(summary['change_percent']) > 10:
                    st.warning("⚠️ 预测变化幅度较大，请注意风险")
                elif summary['volatility'] > 30:
                    st.warning("⚠️ 股票波动率较高，请谨慎投资")

            with col2:
                st.subheader("ℹ️ 模型与数据来源")
                metadata = data['metadata']
                st.write(f"**模型版本**: {metadata.get('model_version','-')}")
                # 历史数据（核对用）
                with st.expander("📜 历史数据（核对）"):
                    try:
                        hist_df = pd.DataFrame(data['historical_data'])
                        # 按日期升序
                        hist_df['date'] = pd.to_datetime(hist_df['date'])
                        hist_df = hist_df.sort_values('date')
                        # 成交量单位：手/万手（万手保留2位）
                        if 'volume' in hist_df.columns:
                            vmax = float(hist_df['volume'].max()) if len(hist_df) else 0.0
                            if vmax >= 1e4:
                                hist_df['成交量 (万手)'] = (hist_df['volume'] / 1e4).round(2)
                            else:
                                hist_df['成交量 (手)'] = hist_df['volume'].round(0).astype('Int64')

                        # 选择展示列
                        cols = ['date', 'open', 'high', 'low', 'close']
                        if '成交量 (万手)' in hist_df.columns:
                            cols.append('成交量 (万手)')
                        elif '成交量 (手)' in hist_df.columns:
                            cols.append('成交量 (手)')
                        show_df = hist_df[cols].rename(columns={
                            'date': '日期', 'open': '开盘价 (元)', 'high': '最高价 (元)', 'low': '最低价 (元)', 'close': '收盘价 (元)'
                        })
                        st.dataframe(show_df.tail(200), use_container_width=True)
                    except Exception as _:
                        st.info("历史数据暂不可用")

                ds = metadata.get('data_source','unknown')
                cs = metadata.get('cache_status','unknown')
                cw = '已写入' if metadata.get('cache_written', False) else '未写入'
                st.write(f"**数据源**: {ds}（缓存: {cs}/{cw}）")
                st.write(f"**预测时间**: {metadata.get('prediction_time','')[:19]}")
                st.write(f"**模拟模式**: {'是' if metadata.get('use_mock') else '否'}")

            # 数据表格
            with st.expander("📊 查看预测数据"):
                pred_df = pd.DataFrame(data['predictions'])

                # 重命名列为中文
                column_names = {
                    'date': '日期',
                    'open': '开盘价 (元)',
                    'high': '最高价 (元)',
                    'low': '最低价 (元)',
                    'close': '收盘价 (元)',
                    'volume': '成交量 (手)',
                    'amount': '成交额 (万元)'
                }

                # 重命名列
                pred_df = pred_df.rename(columns=column_names)

                # 成交量单位自适应（两档）：手 / 万手（万手保留2位小数）
                if '成交量 (手)' in pred_df.columns:
                    vol_max = float(pred_df['成交量 (手)'].max()) if len(pred_df) else 0.0
                    if vol_max >= 1e4:
                        pred_df['成交量 (万手)'] = (pred_df['成交量 (手)'] / 1e4).round(2)
                        pred_df.drop(columns=['成交量 (手)'], inplace=True)
                    else:
                        # 保留整数手
                        pred_df['成交量 (手)'] = pred_df['成交量 (手)'].round(0).astype('Int64')

                # 格式化数值
                for col in ['开盘价 (元)', '最高价 (元)', '最低价 (元)', '收盘价 (元)']:
                    if col in pred_df.columns:
                        pred_df[col] = pred_df[col].round(2)

                if '成交额 (万元)' in pred_df.columns:
                    pred_df['成交额 (万元)'] = (pred_df['成交额 (万元)'] / 10000).round(2)

                st.dataframe(pred_df, use_container_width=True)

            # 免责声明
            st.markdown("---")
            st.markdown("""
            **⚠️ 免责声明**

            本预测结果仅供参考，不构成投资建议。股票投资存在风险，请根据自身情况谨慎决策。
            预测模型基于历史数据，无法保证未来表现。
            """)
            # 停止彩虹动画，固定在标题后方，并即时重绘标题
            st.session_state['title_animation_state'] = 'static'
            final_state2 = st.session_state.get('title_animation_state', 'static')
            _logo_uri = get_logo_data_uri()
            final_title_html2 = build_title_html(final_state2, _logo_uri)
            title_slot.markdown(final_title_html2, unsafe_allow_html=True)

        else:
            st.error(f"❌ 预测失败: {result['error']}")
            # 失败时也停止动画，避免一直运动
            st.session_state['title_animation_state'] = 'static'

    # 示例股票
    st.sidebar.markdown("---")
    st.sidebar.subheader("💡 示例股票")
    example_stocks = {
        "平安银行": "000001",
        "浦发银行": "600000",
        "万科A": "000002",
        "招商银行": "600036"
    }

    for name, code in example_stocks.items():
        if st.sidebar.button(f"{name} ({code})", key=f"example_{code}", use_container_width=True):
            st.experimental_set_query_params(stock_code=code)
            st.experimental_rerun()

    # 添加系统状态部分
    if create_sidebar_status_section:
        create_sidebar_status_section()

    # 底部信息
    st.sidebar.markdown("---")
    st.sidebar.markdown("""
    **🤖 Powered by Gordon**

    基于深度学习的金融时序预测模型
    """)


if __name__ == "__main__":
    main()
