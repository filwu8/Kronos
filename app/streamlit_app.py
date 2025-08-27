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
    from chinese_menu import ChineseMenu, render_chinese_header, render_chinese_footer, create_chinese_sidebar, create_sidebar_status_section
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
/* FORCE REMOVE TOP SPACING - High specificity selectors */
.stApp, [data-testid="stAppViewContainer"], .main, .main > div,
.block-container, .main .block-container, [data-testid="block-container"] {
    margin-top: 0 !important;
    padding-top: 0 !important;
}

[data-testid="stHeader"], .stApp > header, header[data-testid="stHeader"] {
    display: none !important;
    height: 0 !important;
    margin: 0 !important;
    padding: 0 !important;
}

/* Sidebar button consistency */
.css-1d391kg .stButton > button, [data-testid="stSidebar"] .stButton > button {
    min-width: 200px !important;
    width: 100% !important;
    height: 45px !important;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    font-size: 14px !important;
    padding: 8px 12px !important;
    box-sizing: border-box !important;
}
"""

    bundle_html = f"<style>{aggressive_css}{''.join(css_bundle)}</style>\n<script>{''.join(js_bundle)}</script>"
    st.markdown(bundle_html, unsafe_allow_html=True)

# 加载本地资源
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
            timeout=60
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

        # 处理历史数据的日期字段
        if 'date' in hist_df.columns:
            # 确保日期格式正确
            hist_df['date'] = pd.to_datetime(hist_df['date'], errors='coerce')
            # 移除无效日期
            hist_df = hist_df.dropna(subset=['date'])
        else:
            # 如果没有日期字段，生成工作日日期序列
            hist_df['date'] = pd.date_range(
                end=pd.Timestamp.now().date(),
                periods=len(hist_df),
                freq='B'  # 工作日频率
            )

        # 准备预测数据
        pred_df = pd.DataFrame(predictions)

        # 处理预测数据的日期字段
        if 'date' in pred_df.columns:
            pred_df['date'] = pd.to_datetime(pred_df['date'], errors='coerce')
        else:
            # 生成预测日期序列，基于历史数据的最后日期
            if len(hist_df) > 0 and 'date' in hist_df.columns:
                last_hist_date = hist_df['date'].max()
                # 生成下一个工作日开始的预测日期
                pred_df['date'] = pd.date_range(
                    start=last_hist_date + pd.Timedelta(days=1),
                    periods=len(pred_df),
                    freq='B'  # 工作日频率
                )
            else:
                # 如果没有历史日期，从今天开始
                pred_df['date'] = pd.date_range(
                    start=pd.Timestamp.now().date() + pd.Timedelta(days=1),
                    periods=len(pred_df),
                    freq='B'
                )

        # 验证数据完整性
        required_cols = ['open', 'high', 'low', 'close', 'volume']

        # 检查历史数据
        for col in required_cols:
            if col not in hist_df.columns:
                print(f"历史数据缺少列: {col}")
                return None

        # 检查预测数据
        for col in required_cols:
            if col not in pred_df.columns:
                print(f"预测数据缺少列: {col}")
                return None

        # 确保数据类型正确
        for col in required_cols:
            hist_df[col] = pd.to_numeric(hist_df[col], errors='coerce')
            pred_df[col] = pd.to_numeric(pred_df[col], errors='coerce')

        # 移除空值
        hist_df = hist_df.dropna(subset=required_cols)
        pred_df = pred_df.dropna(subset=required_cols)

        if len(hist_df) == 0:
            print("历史数据为空")
            return None

        if len(pred_df) == 0:
            print("预测数据为空")
            return None

        # 创建子图
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
                line=dict(color='blue', width=2),
                hovertemplate='<b>历史价格</b><br>' +
                             '日期: %{x|%Y-%m-%d}<br>' +
                             '收盘价: ¥%{y:.2f}<extra></extra>'
            ),
            row=1, col=1
        )

        # 获取真实的蒙特卡洛不确定性区间
        if 'close_upper' in pred_df.columns and 'close_lower' in pred_df.columns:
            # 使用真实的蒙特卡洛预测区间
            pred_upper = pred_df['close_upper']
            pred_lower = pred_df['close_lower']
        else:
            # 回退到模拟区间
            pred_mean = pred_df['close']
            pred_volatility = pred_mean * 0.15
            pred_upper = pred_mean + pred_volatility
            pred_lower = pred_mean - pred_volatility

        # 预测不确定性区间 (阴影区域)
        fig.add_trace(
            go.Scatter(
                x=pred_df['date'].tolist() + pred_df['date'].tolist()[::-1],
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

        # 预测价格线 (均值)
        fig.add_trace(
            go.Scatter(
                x=pred_df['date'],
                y=pred_df['close'],
                mode='lines',
                name='预测均值',
                line=dict(color='red', width=3),
                hovertemplate='<b>预测价格</b><br>' +
                             '日期: %{x|%Y-%m-%d}<br>' +
                             '预测价: ¥%{y:.2f}<br>' +
                             '区间: ¥%{customdata[0]:.2f} - ¥%{customdata[1]:.2f}<extra></extra>',
                customdata=list(zip(pred_lower, pred_upper))
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
                opacity=0.7,
                hovertemplate='<b>历史成交量</b><br>' +
                             '日期: %{x|%Y-%m-%d}<br>' +
                             '成交量: %{customdata}<extra></extra>',
                customdata=[format_volume(v) for v in hist_df['volume']]
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
                opacity=0.7,
                hovertemplate='<b>预测成交量</b><br>' +
                             '日期: %{x|%Y-%m-%d}<br>' +
                             '成交量: %{customdata}<extra></extra>',
                customdata=[format_volume(v) for v in pred_df['volume']]
            ),
            row=2, col=1
        )

        # 更新布局
        fig.update_layout(
            title=f"{stock_info['name']} ({stock_info['code']}) - 价格预测",
            xaxis_title="日期",
            height=600,
            showlegend=True,
            hovermode='x unified',
            # 中文化配置
            font=dict(family="Arial, sans-serif", size=12),
            # 工具栏中文化
            modebar=dict(
                bgcolor='rgba(255,255,255,0.8)',
                color='rgba(0,0,0,0.8)',
                activecolor='rgba(0,0,0,1)',
                # 自定义工具栏按钮
                remove=['lasso2d', 'select2d']
            )
        )

        fig.update_yaxes(title_text="价格 (元)", row=1, col=1)
        fig.update_yaxes(title_text="成交量 (手)", row=2, col=1)

        # 更新X轴格式
        fig.update_xaxes(
            tickformat='%Y-%m-%d',
            tickangle=45,
            row=1, col=1
        )
        fig.update_xaxes(
            tickformat='%Y-%m-%d',
            tickangle=45,
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
    if logo_uri:
        title_html = (
            '<div class="title-banner">'
            '<h1 class="main-header gradient-title glow">'
            f'<img class="title-logo" src="{logo_uri}" alt="Logo">'
            'Gordon Wang 的股票预测系统'
            '</h1>'
            '<p class="main-subtitle">基于RTX 5090 GPU加速的智能股票预测平台</p>'
            '</div>'
        )
    else:
        title_html = (
            '<div class="title-banner">'
            '<h1 class="main-header gradient-title glow">Gordon Wang 的股票预测系统</h1>'
            '<p class="main-subtitle">基于RTX 5090 GPU加速的智能股票预测平台</p>'
            '</div>'
        )
    st.markdown(title_html, unsafe_allow_html=True)

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

    # 预测按钮（统一侧边栏按钮宽度）
    if st.sidebar.button("🚀 开始预测", type="primary", use_container_width=True):
        if not stock_code:
            st.error("请输入股票代码")
            return

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
                            'filename': f'{data["stock_info"]["name"]}_股价预测_{datetime.now().strftime("%Y%m%d")}',
                            'height': 800,
                            'width': 1200,
                            'scale': 2  # 高清图片
                        }
                    }
                    st.plotly_chart(fig, use_container_width=True, config=config)

                    # 使用HTML组件强制执行JavaScript
                    import streamlit.components.v1 as components
                    components.html("""
                    <script>
                    // 等待页面完全加载
                    setTimeout(function() {
                        const tooltipMap = {
                            'Pan': '平移 - 拖拽移动图表',
                            'Box Zoom': '框选缩放 - 选择区域放大',
                            'Zoom in': '放大 - 点击放大图表',
                            'Zoom out': '缩小 - 点击缩小图表',
                            'Autoscale': '自适应 - 自动最佳视角',
                            'Reset axes': '重置 - 回到原始视图',
                            'Download plot as a png': '保存 - 下载高清图片'
                        };

                        function translateToolbar() {
                            let translated = 0;
                            const buttons = parent.document.querySelectorAll('.modebar-btn');

                            buttons.forEach(btn => {
                                const title = btn.getAttribute('title');
                                if (title && tooltipMap[title]) {
                                    btn.setAttribute('title', tooltipMap[title]);
                                    translated++;
                                }
                            });

                            console.log('🔧 工具栏中文化: 翻译了 ' + translated + ' 个按钮');
                            return translated;
                        }

                        // 多次尝试翻译
                        translateToolbar();
                        setTimeout(translateToolbar, 500);
                        setTimeout(translateToolbar, 1000);
                        setTimeout(translateToolbar, 2000);

                        // 监听父页面的变化
                        const observer = new MutationObserver(function() {
                            setTimeout(translateToolbar, 100);
                        });

                        if (parent.document.body) {
                            observer.observe(parent.document.body, {
                                childList: true,
                                subtree: true
                            });
                        }
                    }, 1000);
                    </script>
                    """, height=0)

                    # 使用更强的方法中文化工具栏
                    st.markdown("""
                    <style>
                    /* 隐藏英文提示，用CSS伪元素显示中文 */
                    .modebar-btn[data-title="Pan"]:hover::after {
                        content: "平移 - 拖拽移动图表";
                        position: absolute;
                        background: rgba(0,0,0,0.8);
                        color: white;
                        padding: 4px 8px;
                        border-radius: 4px;
                        font-size: 12px;
                        white-space: nowrap;
                        z-index: 1000;
                        bottom: -30px;
                        left: 50%;
                        transform: translateX(-50%);
                    }
                    </style>

                    <script>
                    // 强化的工具栏中文化
                    function forceTranslateToolbar() {
                        const tooltipMap = {
                            'Pan': '平移 - 拖拽移动图表',
                            'Box Zoom': '框选缩放 - 选择区域放大',
                            'Zoom in': '放大 - 点击放大图表',
                            'Zoom out': '缩小 - 点击缩小图表',
                            'Autoscale': '自适应 - 自动最佳视角',
                            'Reset axes': '重置 - 回到原始视图',
                            'Download plot as a png': '保存 - 下载高清图片'
                        };

                        let translated = 0;

                        // 方法1: 直接修改title属性
                        document.querySelectorAll('.modebar-btn').forEach(btn => {
                            const title = btn.getAttribute('title');
                            if (title && tooltipMap[title]) {
                                btn.setAttribute('title', tooltipMap[title]);
                                btn.setAttribute('data-title', title); // 保存原始title
                                translated++;
                            }
                        });

                        // 方法2: 修改data-title属性（Plotly有时使用这个）
                        document.querySelectorAll('[data-title]').forEach(btn => {
                            const title = btn.getAttribute('data-title');
                            if (title && tooltipMap[title]) {
                                btn.setAttribute('data-title', tooltipMap[title]);
                                btn.setAttribute('title', tooltipMap[title]);
                                translated++;
                            }
                        });

                        // 方法3: 查找特定的工具栏按钮类
                        const buttonSelectors = [
                            '[data-title="Pan"]',
                            '[data-title="Box Zoom"]',
                            '[data-title="Zoom in"]',
                            '[data-title="Zoom out"]',
                            '[data-title="Autoscale"]',
                            '[data-title="Reset axes"]',
                            '[data-title="Download plot as a png"]'
                        ];

                        buttonSelectors.forEach(selector => {
                            const btn = document.querySelector(selector);
                            if (btn) {
                                const originalTitle = btn.getAttribute('data-title');
                                if (tooltipMap[originalTitle]) {
                                    btn.setAttribute('title', tooltipMap[originalTitle]);
                                    translated++;
                                }
                            }
                        });

                        console.log('🔧 工具栏中文化: 翻译了 ' + translated + ' 个按钮');

                        // 强制刷新工具栏
                        const modebar = document.querySelector('.modebar');
                        if (modebar) {
                            modebar.style.display = 'none';
                            setTimeout(() => {
                                modebar.style.display = 'block';
                            }, 10);
                        }

                        return translated;
                    }

                    // 页面加载后立即执行
                    if (document.readyState === 'loading') {
                        document.addEventListener('DOMContentLoaded', forceTranslateToolbar);
                    } else {
                        forceTranslateToolbar();
                    }

                    // 多次尝试，确保成功
                    setTimeout(forceTranslateToolbar, 100);
                    setTimeout(forceTranslateToolbar, 500);
                    setTimeout(forceTranslateToolbar, 1000);
                    setTimeout(forceTranslateToolbar, 2000);
                    setTimeout(forceTranslateToolbar, 5000);

                    // 监听Plotly图表事件
                    window.addEventListener('plotly_afterplot', function() {
                        setTimeout(forceTranslateToolbar, 100);
                    });

                    // 监听DOM变化
                    const observer = new MutationObserver(function(mutations) {
                        let shouldTranslate = false;
                        mutations.forEach(function(mutation) {
                            if (mutation.addedNodes.length > 0) {
                                mutation.addedNodes.forEach(function(node) {
                                    if (node.nodeType === 1 && (
                                        node.classList.contains('modebar') ||
                                        node.querySelector('.modebar') ||
                                        node.classList.contains('modebar-btn')
                                    )) {
                                        shouldTranslate = true;
                                    }
                                });
                            }
                        });

                        if (shouldTranslate) {
                            setTimeout(forceTranslateToolbar, 50);
                        }
                    });

                    observer.observe(document.body, {
                        childList: true,
                        subtree: true
                    });
                    </script>
                    """, unsafe_allow_html=True)

                    # 添加醒目的工具栏说明
                    st.info("💡 **图表工具栏中英文对照** (右上角白色工具条)")

                    # 创建工具栏对照表
                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.markdown("""
                        **🛠️ 基础操作**
                        - 🖱️ **Pan** = 平移
                        - 🔍 **Box Zoom** = 框选缩放
                        - ➕ **Zoom in** = 放大
                        """)

                    with col2:
                        st.markdown("""
                        **🔧 视图控制**
                        - ➖ **Zoom out** = 缩小
                        - 🔄 **Autoscale** = 自适应
                        - 🏠 **Reset axes** = 重置
                        """)

                    with col3:
                        st.markdown("""
                        **💾 导出功能**
                        - 📷 **Download plot as a png** = 保存图片
                        """)

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
                        st.markdown("""
                        **🛠️ 工具栏使用说明**

                        图表右上角工具栏从左到右依次为：

                        1. **🖱️ 平移 (Pan)**: 拖拽图表移动视角
                        2. **🔍 框选缩放 (Box Zoom)**: 拖拽选择区域放大
                        3. **➕ 放大 (Zoom in)**: 点击放大图表
                        4. **➖ 缩小 (Zoom out)**: 点击缩小图表
                        5. **🔄 自适应 (Autoscale)**: 自动调整到最佳视角
                        6. **🏠 重置 (Reset axes)**: 恢复到原始视角
                        7. **📷 保存 (Download)**: 下载高清PNG图片

                        💡 **提示**: 如果工具栏显示英文，请参考上述对照表
                        """)
                else:
                    st.error("图表创建返回空值，请检查数据格式")
                    # 显示调试信息
                    st.write("调试信息:")
                    st.write(f"历史数据条数: {len(data['historical_data'])}")
                    st.write(f"预测数据条数: {len(data['predictions'])}")
                    if len(data['historical_data']) > 0:
                        st.write(f"历史数据样本: {data['historical_data'][0]}")
                    if len(data['predictions']) > 0:
                        st.write(f"预测数据样本: {data['predictions'][0]}")
            except Exception as e:
                st.error(f"图表生成失败: {str(e)}")
                import traceback
                st.code(traceback.format_exc())

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
                st.subheader("ℹ️ 模型信息")
                metadata = data['metadata']
                st.write(f"**模型版本**: {metadata['model_version']}")
                st.write(f"**数据源**: {metadata['data_source']}")
                st.write(f"**预测时间**: {metadata['prediction_time'][:19]}")
                st.write(f"**模拟模式**: {'是' if metadata['use_mock'] else '否'}")

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

        else:
            st.error(f"❌ 预测失败: {result['error']}")

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
