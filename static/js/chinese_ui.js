// Gordon Wang 股票预测系统 - 中文化脚本

// 中文化映射表
const chineseTranslations = {
    // Streamlit 默认文本
    'Settings': '设置',
    'Print': '打印',
    'Record a screencast': '录制屏幕',
    'Report a bug': '报告错误',
    'Get help': '获取帮助',
    'About': '关于',
    'Deploy this app': '部署应用',
    'Rerun': '重新运行',
    'Clear cache': '清除缓存',
    'Developer options': '开发者选项',
    'Wide mode': '宽屏模式',
    'Run on save': '保存时运行',
    'Light theme': '浅色主题',
    'Dark theme': '深色主题',
    'Auto theme': '自动主题',

    // Deploy菜单相关
    'Deploy': '部署',
    'Streamlit Community Cloud': 'Streamlit 社区云',
    'Other platforms': '其他平台',
    'Learn more': '了解更多',
    'Documentation': '文档',
    'Community': '社区',
    'GitHub': 'GitHub',
    'Twitter': 'Twitter',

    // 工具栏文本
    'Pan': '平移',
    'Box Zoom': '框选缩放',
    'Zoom in': '放大',
    'Zoom out': '缩小',
    'Autoscale': '自适应',
    'Reset axes': '重置',
    'Download plot as a png': '保存图片',

    // 常用界面文本
    'Loading...': '加载中...',
    'Error': '错误',
    'Success': '成功',
    'Warning': '警告',
    'Info': '信息',
    'Please wait': '请稍候',
    'Processing': '处理中',
    'Complete': '完成',
    'Failed': '失败',

    // 表单文本
    'Submit': '提交',
    'Reset': '重置',
    'Cancel': '取消',
    'Confirm': '确认',
    'Save': '保存',
    'Load': '加载',
    'Export': '导出',
    'Import': '导入',
    'Search': '搜索',
    'Filter': '筛选',
    'Sort': '排序',

    // 数据相关
    'No data available': '暂无数据',
    'Data loaded successfully': '数据加载成功',
    'Data loading failed': '数据加载失败',
    'Invalid input': '输入无效',
    'Required field': '必填字段',

    // 时间相关
    'Today': '今天',
    'Yesterday': '昨天',
    'Last week': '上周',
    'Last month': '上月',
    'Last year': '去年',
    'Custom range': '自定义范围'
};

// 工具栏中文化函数
function translateToolbar() {
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

    // 翻译工具栏按钮（同时处理 data-title / title / aria-label）
    document.querySelectorAll('.modebar-btn').forEach(btn => {
        const key = btn.getAttribute('data-title') || btn.getAttribute('title') || btn.getAttribute('aria-label');
        if (key && tooltipMap[key]) {
            const zh = tooltipMap[key];
            btn.setAttribute('data-title', zh);
            btn.setAttribute('title', zh);
            btn.setAttribute('aria-label', zh);
            translated++;
        }
    });

    console.log(`🔧 工具栏中文化: 翻译了 ${translated} 个按钮`);
    return translated;
}

// 通用文本翻译函数
function translateText(element) {
    if (!element) return;

    const text = element.textContent.trim();
    if (chineseTranslations[text]) {
        element.textContent = chineseTranslations[text];
        return true;
    }
    return false;
}

// 翻译页面中的所有文本
function translatePage() {
    let translated = 0;

    // 翻译按钮文本
    document.querySelectorAll('button').forEach(btn => {
        if (translateText(btn)) translated++;
    });

    // 翻译链接文本
    document.querySelectorAll('a').forEach(link => {
        if (translateText(link)) translated++;
    });

    // 翻译标签文本
    document.querySelectorAll('label').forEach(label => {
        if (translateText(label)) translated++;
    });

    // 翻译菜单项
    document.querySelectorAll('[role="menuitem"]').forEach(item => {
        if (translateText(item)) translated++;
    });

    // 特别处理Deploy菜单
    document.querySelectorAll('[data-testid="stAppDeployButton"]').forEach(btn => {
        if (translateText(btn)) translated++;
    });

    // 翻译下拉菜单内容
    document.querySelectorAll('.dropdown-menu li').forEach(item => {
        if (translateText(item)) translated++;
    });

    // 翻译弹出菜单
    document.querySelectorAll('[role="menu"] [role="menuitem"]').forEach(item => {
        if (translateText(item)) translated++;
    });

    // 翻译工具提示
    document.querySelectorAll('[title]').forEach(element => {
        const title = element.getAttribute('title');
        if (chineseTranslations[title]) {
            element.setAttribute('title', chineseTranslations[title]);
            translated++;
        }
    });

    console.log(`🌐 页面中文化: 翻译了 ${translated} 个文本元素`);
    return translated;
}

// 完全移除Streamlit广告元素
function hideStreamlitElements() {
    // 隐藏Deploy按钮
    const deployButtons = document.querySelectorAll('[data-testid="stAppDeployButton"]');
    deployButtons.forEach(btn => {
        btn.style.display = 'none';
        btn.remove();
    });

    // 隐藏右上角菜单
    const topMenus = document.querySelectorAll('.css-1rs6os, .css-17eq0hr, .css-1kyxreq, .css-1v0mbdj');
    topMenus.forEach(menu => {
        menu.style.display = 'none';
        menu.remove();
    });

    // 隐藏"Made with Streamlit"
    const streamlitLinks = document.querySelectorAll('a[href*="streamlit.io"]');
    streamlitLinks.forEach(link => {
        link.style.display = 'none';
        link.remove();
    });

    // 隐藏主菜单
    const mainMenu = document.querySelector('#MainMenu');
    if (mainMenu) {
        mainMenu.style.display = 'none';
        mainMenu.remove();
    }

    // 隐藏页脚
    const footers = document.querySelectorAll('footer');
    footers.forEach(footer => {
        footer.style.display = 'none';
        footer.remove();
    });

    // 隐藏顶部工具栏
    const toolbars = document.querySelectorAll('.css-18e3th9');
    toolbars.forEach(toolbar => {
        toolbar.style.display = 'none';
    });

    // 强制隐藏系统 Header 占位
    const headerEl = document.querySelector('[data-testid="stHeader"]');
    if (headerEl) {
        headerEl.style.setProperty('display', 'none', 'important');
        headerEl.style.minHeight = '0px';
        headerEl.style.height = '0px';
        headerEl.style.padding = '0px';
        headerEl.style.margin = '0px';
        headerEl.style.overflow = 'hidden';
    }

    // 移除所有Streamlit品牌元素
    const brandElements = document.querySelectorAll('.css-1dp5vir, .css-hi6a2p');
    brandElements.forEach(element => {
        element.style.display = 'none';
        element.remove();
    });

    // console.log('🚫 已移除Streamlit广告元素');
}

// 添加自定义导航栏
function addCustomNavbar() {
    if (document.getElementById('custom-navbar')) return; // 防重复插入
    const navbar = document.createElement('div');
    navbar.id = 'custom-navbar';
    navbar.className = 'custom-navbar';
    navbar.innerHTML = `
        <h1>🚀 Gordon Wang 的股票预测系统</h1>
        <p style="margin: 5px 0 0 0; text-align: center; font-size: 14px; opacity: 0.9;">
            基于RTX 5090 GPU加速的智能股票预测平台
        </p>
    `;

    // 插入到页面顶部
    const mainContainer = document.querySelector('.main');
    if (mainContainer) {
        mainContainer.insertBefore(navbar, mainContainer.firstChild);
    }
}

// 添加加载动画
function showLoading(message = '加载中...') {
    const loadingDiv = document.createElement('div');
    loadingDiv.id = 'custom-loading';
    loadingDiv.innerHTML = `
        <div style="text-align: center; padding: 20px;">
            <div class="loading-spinner"></div>
            <p>${message}</p>
        </div>
    `;
    document.body.appendChild(loadingDiv);
}

function hideLoading() {
    const loadingDiv = document.getElementById('custom-loading');
    if (loadingDiv) {
        loadingDiv.remove();
    }
}

// 添加成功/错误消息
function showMessage(message, type = 'info') {
    const messageDiv = document.createElement('div');
    messageDiv.className = `${type}-message`;
    messageDiv.textContent = message;
    messageDiv.style.position = 'fixed';
    messageDiv.style.top = '20px';
    messageDiv.style.right = '20px';
    messageDiv.style.zIndex = '9999';
    messageDiv.style.minWidth = '300px';

    document.body.appendChild(messageDiv);

    // 3秒后自动消失
    setTimeout(() => {
        messageDiv.remove();
    }, 3000);
}

// 主初始化函数
function tightenTopWhitespace() {
    // 仅收敛主区第一个 stVerticalBlock 内部：在“标题容器”之前隐藏所有容器
    const root = document.querySelector('[data-testid="stAppViewContainer"]') || document.body;
    const firstBlock = [...root.querySelectorAll('[data-testid="stVerticalBlock"]')]
        .find(el => !el.closest('[data-testid="stSidebar"]') && !el.closest('[data-testid="stSidebarUserContent"]'));
    if (!firstBlock) return;
    const containers = [...firstBlock.querySelectorAll('[data-testid="stElementContainer"]')];

    // 用更稳健的方式定位标题容器：优先查找 .main-header，其次匹配中文/英文标题文本
    const isTitleContainer = (ec) => {
        if (ec.querySelector('.main-header')) return true;
        const t = (ec.innerText || '').trim();
        return /🚀\s*Gordon\s+Wang|股票预测系统|RTX\s*5090/.test(t);

    };




    const titleIdx = containers.findIndex(isTitleContainer);
    if (titleIdx > 0) {
        for (let i = 0; i < titleIdx; i++) {
            const ec = containers[i];
            ec.style.display = 'none';
            ec.setAttribute('data-collapsed', 'true');
        }
    }
}


function pinTitleBanner() {
    // AGGRESSIVE TOP SPACING REMOVAL
    function removeTopSpacing() {
        // Remove all headers
        const headers = document.querySelectorAll('[data-testid="stHeader"], .stApp > header, header');
        headers.forEach(header => {
            header.style.setProperty('display', 'none', 'important');
            header.style.setProperty('height', '0', 'important');
            header.style.setProperty('margin', '0', 'important');
            header.style.setProperty('padding', '0', 'important');
        });

        // Remove top spacing from all main containers
        const containers = document.querySelectorAll('.stApp, [data-testid="stAppViewContainer"], .main, .main > div, .block-container, .main .block-container, [data-testid="block-container"]');
        containers.forEach(container => {
            container.style.setProperty('margin-top', '0', 'important');
            container.style.setProperty('padding-top', '0', 'important');
        });

        // Force body and html to have no top spacing
        document.body.style.setProperty('margin-top', '0', 'important');
        document.body.style.setProperty('padding-top', '0', 'important');
        document.documentElement.style.setProperty('margin-top', '0', 'important');
        document.documentElement.style.setProperty('padding-top', '0', 'important');
    }

    function ensurePortal() {
        let portal = document.getElementById('title-banner-portal');
        if (!portal) {
            portal = document.createElement('div');
            portal.id = 'title-banner-portal';
            Object.assign(portal.style, {
                position: 'fixed', top: '0px', left: '0', right: '0', zIndex: '1100'
            });
            document.body.appendChild(portal);
        }
        return portal;
    }

    function apply() {
        // Always remove top spacing first
        removeTopSpacing();

        const banner = document.querySelector('.title-banner');
        // 标题可能尚未渲染，等待后续MutationObserver回调
        if (!banner) return;

        // 将横幅挂到 body 顶层门户，避免父级 transform 影响
        const portal = ensurePortal();
        if (banner.parentNode !== portal) {
            portal.appendChild(banner);
            banner.style.position = 'relative';
            banner.style.top = '0px';
            banner.style.left = '0';
            banner.style.right = '0';
            banner.style.margin = '0';
        }

        // 记录横幅高度，供主容器预留占位
        const h = Math.ceil(banner.getBoundingClientRect().height);
        document.documentElement.style.setProperty('--title-banner-offset', '0px');
        document.documentElement.style.setProperty('--title-banner-h', h + 'px');

        // 将根滚动容器的 padding-top 设为横幅高度，避免横幅覆盖内容
        const mainContainer = document.querySelector('.main .block-container');
        if (mainContainer) {
            mainContainer.style.paddingTop = `0px`; // Force zero padding
        }
    }

    // 初次与后续响应
    removeTopSpacing(); // Call immediately
    apply();
    window.addEventListener('resize', () => requestAnimationFrame(apply));
    const obs = new MutationObserver(() => requestAnimationFrame(apply));
    obs.observe(document.body, { childList: true, subtree: true, attributes: true });
}

function fixSidebarButtons() {
    const sidebarButtons = document.querySelectorAll('.css-1d391kg .stButton > button, [data-testid="stSidebar"] .stButton > button');
    sidebarButtons.forEach(button => {
        // 更温和：只处理不换行和溢出
        button.style.setProperty('white-space', 'nowrap', 'important');
        button.style.setProperty('overflow', 'hidden', 'important');
        button.style.setProperty('text-overflow', 'ellipsis', 'important');
        button.style.setProperty('box-sizing', 'border-box', 'important');
        button.style.removeProperty('height');
        button.style.removeProperty('min-height');
        button.style.removeProperty('display');
        button.style.removeProperty('align-items');
        button.style.removeProperty('justify-content');
        button.style.removeProperty('font-size');
        button.style.removeProperty('line-height');
        button.style.removeProperty('padding');
    });
}

function initializeChineseUI() {
    console.log('🚀 初始化Gordon Wang股票预测系统中文界面...');

    // 隐藏Streamlit默认元素
    hideStreamlitElements();

    // 压缩顶部多余空白
    tightenTopWhitespace();

    // 保留/恢复自定义导航栏（如有）
    // addCustomNavbar(); // 暂停插入自定义导航栏，避免与标题横幅叠加造成顶部间距

    // 固定标题横幅
    pinTitleBanner();

    // Fix sidebar buttons
    fixSidebarButtons();

    // 翻译页面文本
    translatePage();

    // 翻译工具栏
    translateToolbar();

    console.log('✅ 中文界面初始化完成');
}

// DOM加载完成后执行
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChineseUI);
} else {
    initializeChineseUI();
}

// 定期检查并翻译新元素，同时修复按钮样式
setInterval(() => {
    translatePage();
    translateToolbar();
    fixSidebarButtons(); // Continuously fix sidebar buttons
}, 2000);

// 监听DOM变化，自动翻译新元素
const observer = new MutationObserver(function(mutations) {
    let shouldTranslate = false;

    mutations.forEach(function(mutation) {
        if (mutation.addedNodes.length > 0) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1) { // 元素节点
                    shouldTranslate = true;
                }
            });
        }
    });

    if (shouldTranslate) {
        setTimeout(() => {
            translatePage();
            translateToolbar();
        }, 100);
    }
});

observer.observe(document.body, {
    childList: true,
    subtree: true
});

// 导出函数供外部使用
window.ChineseUI = {
    translate: translatePage,
    translateToolbar: translateToolbar,
    showLoading: showLoading,
    hideLoading: hideLoading,
    showMessage: showMessage
};
