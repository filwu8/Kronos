#!/usr/bin/env python3
"""
中文化菜单组件
"""

import streamlit as st
from typing import Dict, List, Optional

class ChineseMenu:
    """中文化菜单管理器"""

    def __init__(self):
        self.pages = {
            "stock_prediction": {
                "title": "📈 股票预测",
                "icon": "📈",
                "description": "智能股票价格预测分析"
            },
            "data_analysis": {
                "title": "📊 数据分析",
                "icon": "📊",
                "description": "历史数据深度分析"
            },
            "portfolio_management": {
                "title": "💼 投资组合",
                "icon": "💼",
                "description": "投资组合管理工具"
            },
            "risk_assessment": {
                "title": "⚠️ 风险评估",
                "icon": "⚠️",
                "description": "投资风险量化分析"
            },
            "market_overview": {
                "title": "🌍 市场概览",
                "icon": "🌍",
                "description": "全市场实时监控"
            },
            "settings": {
                "title": "⚙️ 系统设置",
                "icon": "⚙️",
                "description": "个性化配置选项"
            },
            "help": {
                "title": "❓ 帮助中心",
                "icon": "❓",
                "description": "使用指南和常见问题"
            },
            "about": {
                "title": "ℹ️ 关于系统",
                "icon": "ℹ️",
                "description": "系统信息和版本说明"
            }
        }

        # 菜单分组
        self.menu_groups = {
            "核心功能": ["stock_prediction", "data_analysis"],
            "投资工具": ["portfolio_management", "risk_assessment"],
            "市场信息": ["market_overview"],
            "系统管理": ["settings", "help", "about"]
        }

    def render_sidebar_menu(self) -> str:
        """渲染侧边栏菜单"""
        st.sidebar.markdown("## 🚀 Gordon Wang 股票预测系统")
        st.sidebar.markdown("---")

        # 当前页面状态
        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'stock_prediction'

        selected_page = st.session_state.current_page

        # 渲染分组菜单
        for group_name, page_ids in self.menu_groups.items():
            st.sidebar.markdown(f"### {group_name}")

            for page_id in page_ids:
                page_info = self.pages[page_id]

                # 创建按钮
                if st.sidebar.button(
                    f"{page_info['icon']} {page_info['title']}",
                    key=f"menu_{page_id}",
                    help=page_info['description'],
                    use_container_width=True
                ):
                    st.session_state.current_page = page_id
                    st.rerun()

            st.sidebar.markdown("---")

        return st.session_state.current_page

    def render_top_navigation(self) -> str:
        """渲染顶部导航栏"""
        # 创建导航栏
        nav_cols = st.columns(len(self.pages))

        if 'current_page' not in st.session_state:
            st.session_state.current_page = 'stock_prediction'

        for i, (page_id, page_info) in enumerate(self.pages.items()):
            with nav_cols[i]:
                if st.button(
                    f"{page_info['icon']} {page_info['title']}",
                    key=f"nav_{page_id}",
                    help=page_info['description']
                ):
                    st.session_state.current_page = page_id
                    st.rerun()

        return st.session_state.current_page

    def render_breadcrumb(self, current_page: str) -> None:
        """渲染面包屑导航"""
        if current_page in self.pages:
            page_info = self.pages[current_page]

            # 找到当前页面所属的分组
            current_group = None
            for group_name, page_ids in self.menu_groups.items():
                if current_page in page_ids:
                    current_group = group_name
                    break

            # 显示面包屑
            breadcrumb = f"🏠 首页 > {current_group} > {page_info['title']}"
            st.markdown(f"**导航路径**: {breadcrumb}")

    def get_page_title(self, page_id: str) -> str:
        """获取页面标题"""
        if page_id in self.pages:
            return self.pages[page_id]['title']
        return "未知页面"

    def get_page_description(self, page_id: str) -> str:
        """获取页面描述"""
        if page_id in self.pages:
            return self.pages[page_id]['description']
        return ""

# 旧的头部渲染已由 streamlit_app 的 title-banner 替代

def render_chinese_footer():
    """渲染中文化页面底部"""
    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("""
        **🔧 技术栈**
        - Python + Streamlit
        - Plotly 图表
        - RTX 5090 GPU加速
        - Kronos-small 模型
        """)

    with col2:
        st.markdown("""
        **📊 功能特色**
        - 蒙特卡洛预测
        - 不确定性量化
        - 实时数据分析
        - 高性能计算
        """)

    with col3:
        st.markdown("""
        **📞 联系信息**
        - 开发者: Gordon Wang
        - 版本: v1.0.0
        - 更新: 2025-08-26
        """)

    st.markdown("""
    <div style="text-align: center; padding: 20px; color: #666;">
        <p>© 2025 Gordon Wang 股票预测系统. 保留所有权利.</p>
        <p>本系统仅供学习和研究使用，投资有风险，决策需谨慎。</p>
    </div>
    """, unsafe_allow_html=True)

def create_chinese_sidebar():
    """创建完全中文化的侧边栏（紧凑样式 + 徽章定位 + 清理冗余）"""
    # 样式：压缩侧边栏间距、统一按钮尺寸、紧凑分隔线
    st.sidebar.markdown(
        """
    <style>
      /* 顶部覆盖层：将“系统菜单”与X平行并保持中线居中 */
      [data-testid="stSidebar"] { position: relative; }
      #sys-menu-overlay {
        position: absolute; top: 0; left: 0; width: 100%; height: 28px;
        display: flex; align-items: center; justify-content: center;
        pointer-events: none; z-index: 10;
      }

      /* 顶部“系统菜单”样式：与X平行左侧、但标题整体居中（使用绝对定位覆盖） */
      /* 系统菜单标题基础样式（尺寸更大，行内紧凑） */
      .sys-menu-badge {
        display: inline-flex; align-items: center; justify-content: center;
        margin: 0; padding: 0;
        background: transparent !important; border-radius: 0;
        color: inherit; font-size: 32px; font-weight: 800; letter-spacing: 0.2px; line-height: 1.2;
      }

      /* 侧边栏整体更紧凑 */
      [data-testid="stSidebar"] * { box-sizing: border-box; }
      [data-testid="stSidebar"] hr { margin: 6px 0; opacity: .6; }
      [data-testid="stSidebar"] h1,
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3 { margin: 6px 0 4px; line-height: 1.2; }
      /* 统一二级标题字号：略小于“系统菜单”，又比正文略大 */
      [data-testid="stSidebar"] h2,
      [data-testid="stSidebar"] h3 { font-size: 15px; font-weight: 700; }
      [data-testid="stSidebar"] p { margin: 2px 0 6px; }
      [data-testid="stSidebar"] [data-testid="column"] { padding: 0 4px; }

      /* 压缩侧栏顶部头部按钮区域，避免徽章上方出现大空白 */
      [data-testid="stSidebar"] [data-testid="baseButton-header"] {
        padding: 0 4px !important; margin: 0 !important;
        min-height: 24px !important; height: 24px !important;
      }
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] { padding-top: 0 !important; margin-top: 0 !important; }
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] > div:first-child { margin-top: 0 !important; padding-top: 0 !important; }
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] h1:first-of-type,
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] h2:first-of-type,
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] h3:first-of-type { margin-top: 0 !important; }

      /* 将头部下方紧贴到 X 下一行：收紧第一个分隔符/容器的上边距 */
      [data-testid="stSidebar"] [data-testid="stSidebarContent"] > :is(div, section, hr):first-child { margin-top: 0 !important; }

      /* 关闭按钮尺寸更小，减少头部占位 */
      [data-testid="stSidebar"] button[kind="headerClose"]{
        width: 22px; height: 22px; min-height: 22px;
        padding: 0 !important; margin: 0 !important;
      }

      /* 按钮更紧凑（主/次） */
      [data-testid="stSidebar"] div[data-testid="baseButton-secondary"] button,
      [data-testid="stSidebar"] div[data-testid="baseButton-primary"] button {
        padding: 6px 8px !important; min-height: 28px !important;
        font-size: 13px !important; line-height: 1.1 !important;
      }
      [data-testid="stSidebar"] div[data-testid^="baseButton-"] { margin-bottom: 6px; }

      /* 指标块更紧凑 */
      [data-testid="stSidebar"] [data-testid="stMetricValue"] { font-size: 14px; }
      [data-testid="stSidebar"] [data-testid="stMetricDelta"] { font-size: 11px; }
      [data-testid="stSidebar"] [data-testid="stMetricLabel"] { font-size: 11px; margin-bottom: 0; }
    </style>
    <div id="sys-menu-overlay"><div id="system-menu-banner" class="sys-menu-badge" title="系统菜单">🚀 系统菜单</div></div>
    """,
        unsafe_allow_html=True,
    )

    # 脚本：将徽章靠近侧边栏关闭按钮，并清理空白按钮容器（集中于此，移除页面内重复脚本）
    try:
        import streamlit.components.v1 as components
        with st.sidebar:
            components.html(
                """
                <script>
                (function(){
                  let tries = 0;
                  function tick(){
                    try{
                      const doc = parent.document;
                      const sidebar = doc.querySelector('[data-testid="stSidebar"]');
                      const overlay = doc.querySelector('#sys-menu-overlay');
                      const badge = doc.querySelector('#system-menu-banner');
                      if(sidebar && overlay && badge){
                        if (badge.parentElement !== overlay){ overlay.appendChild(badge); }
                        // 调整蓝色主体距顶部的间距：仅保留约1个字高
                        try{
                          const content = sidebar.querySelector('[data-testid="stSidebarContent"]');
                          const headerBtn = sidebar.querySelector('[data-testid="baseButton-header"]');
                          const headerBottom = headerBtn ? headerBtn.getBoundingClientRect().bottom : sidebar.getBoundingClientRect().top;
                          const firstBlock = content && content.firstElementChild;
                          if(firstBlock){
                            const fs = parseFloat(getComputedStyle(firstBlock).fontSize) || 16; // 1em
                            const desired = fs; // 视觉上一行字高
                            const firstTop = firstBlock.getBoundingClientRect().top;
                            const gap = firstTop - headerBottom;
                            const diff = gap - desired;
                            if (diff > 1) {
                              firstBlock.style.marginTop = (-diff) + 'px';
                            }
                          }
                        }catch(e){}
                        return;
                      }
                    }catch(e){}
                    if(++tries < 20) setTimeout(tick, 200);
                  }
                  tick();
                })();
                </script>
                """,
                height=0,
            )
    except Exception:
        pass

def create_sidebar_status_section():
    """创建侧边栏状态部分（在示例股票后面显示）"""
    st.sidebar.markdown("---")

    # 系统状态
    st.sidebar.markdown("### 📊 系统状态")

    # 动态状态容器（由前端脚本自动刷新，不触发rerun）
    st.sidebar.markdown('<div id="sidebar-status-live"></div>', unsafe_allow_html=True)
    try:
        import streamlit.components.v1 as components
        components.html("""
        <script>
        (function(){
          const base = (window.API_BASE_URL || 'http://localhost:8000');
          async function tick(){
            try{
              const r1 = await fetch(base + '/health', {cache:'no-store'});
              const h = await r1.json();
              const r2 = await fetch(base + '/model/status', {cache:'no-store'});
              const ms = await r2.json();
              const el = parent.document.querySelector('#sidebar-status-live');
              if(!el) return;
              const device = (ms.device || 'cpu');
              const cls = (device === 'cuda') ? 'gpu' : 'cpu';
              const label = (device === 'cuda') ? 'GPU 加速' : 'CPU 兼容模式';
              const data_source = (ms.data_source || 'unknown');
              const cache_status = (ms.cache_status || 'unknown');
              const cache_written = !!ms.cache_written;
              const api_ok = (h.status === 'healthy');
              const ds_map = {cache:'缓存', akshare:'akshare', yfinance:'yfinance', unknown:'未知'};
              const cs_map = {hit:'命中', miss:'未命中', stale:'过期', unknown:'未知'};
              const ds_label = ds_map[data_source] || data_source;
              const cs_label = cs_map[cache_status] || cache_status;
              const write_label = cache_written ? '已写入' : '未写入';
              el.innerHTML = `
                <div class="system-status inline ${cls}">
                  <span class="icon"></span>
                  <span class="label">${label}</span>
                </div>
                <div style="margin-top:8px;font-size:13px;opacity:0.9;">${api_ok ? '🟢 API服务: 正常运行' : '🔴 API服务: 异常'}</div>
                <div style="margin-top:4px;font-size:13px;opacity:0.9;">📦 数据源: ${ds_label}（缓存: ${cs_label}/${write_label}）</div>
                <div style=\"margin-top:4px;font-size:13px;opacity:0.9;\">🧠 模型: ${(ms.model_loaded ? '已加载' : '未加载')}</div>
              `;
            }catch(e){}
          }
          tick(); setInterval(tick, 2000);
        })();
        </script>
        """, height=0)
    except Exception:
        st.sidebar.info("系统状态信息暂不可用")

    st.sidebar.markdown("---")

    # 快速操作
    st.sidebar.markdown("### ⚡ 快速操作")

    col1, col2 = st.sidebar.columns(2)

    with col1:
        if st.button("🔄 刷新", use_container_width=True, key="refresh_data"):
            st.rerun()

    with col2:
        if st.button("🧹 清缓存", use_container_width=True, key="clear_cache"):
            st.cache_data.clear()
            st.sidebar.success("缓存已清除!")

    if st.sidebar.button("📥 导出报告", use_container_width=True, key="export_report"):
        st.sidebar.info("📝 报告导出功能开发中...")

    st.sidebar.markdown("---")

    # 性能监控
    st.sidebar.markdown("### 🚀 性能监控")

    # 使用更紧凑的指标显示
    col1, col2 = st.sidebar.columns(2)

    import os, requests
    api_base = os.getenv("API_BASE_URL", "http://localhost:8000")

    usage = None
    try:
        r = requests.get(f"{api_base}/metrics/usage", timeout=2)
        if r.status_code == 200 and r.json().get('success'):
            usage = r.json()['data']
    except Exception:
        usage = None

    with col1:
        if usage and usage.get('device') == 'cuda' and usage.get('gpu'):
            gpu = usage['gpu']
            util = (str(gpu.get('util_percent')) + '%') if gpu.get('util_percent') is not None else (str(gpu.get('mem_percent')) + '%')
            st.metric("GPU利用率", util)
            st.metric("显存使用", f"{gpu.get('mem_allocated_gb', 0)} / {gpu.get('mem_total_gb', 0)} GB")
        else:
            cpu = (usage or {}).get('cpu', {})
            st.metric("CPU利用率", f"{cpu.get('percent','-')}%")
            st.metric("内存使用", f"{cpu.get('mem_used_gb','-')} / {cpu.get('mem_total_gb','-')} GB")

    with col2:
        # 速度与响应时间可后续接入真实统计；先显示占位或最近一次耗时
        st.metric("预测速度", "- /s")
        st.metric("响应时间", "- s")

if __name__ == "__main__":
    # 测试中文菜单
    menu = ChineseMenu()
    # 头部由主应用渲染的 title-banner 负责

    current_page = menu.render_sidebar_menu()
    menu.render_breadcrumb(current_page)

    st.write(f"当前页面: {menu.get_page_title(current_page)}")
    st.write(f"页面描述: {menu.get_page_description(current_page)}")

    render_chinese_footer()

    # 新增：蒙特卡洛预测说明（放在“🚀 性能监控”后面，左侧同级菜单块）
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 蒙特卡洛预测说明")
    st.sidebar.markdown(
        """
        - 红色实线: 30次蒙特卡洛模拟的平均预测价格
        - 红色阴影区域: 25%-75%分位数区间（50%概率范围）
        - 蓝色实线: 历史真实价格数据
        - 预测方法: Kronos-small模型 + 30条独立预测路径
        - 不确定性: 阴影区域越宽表示预测分歧越大
        """
    )

