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

// 工具栏中文化函数（支持 iframe 及父文档中的 Plotly 图表）
function translateToolbar() {
    const tooltipMap = {
        // 常见按钮
        'Pan': '平移',
        'Box Zoom': '框选缩放',
        'Zoom': '缩放',
        'Zoom in': '放大',
        'Zoom out': '缩小',
        'Zoom 2D': '缩放',
        'Lasso Select': '套索选择',
        'Autoscale': '自适应',
        'Reset axes': '重置',
        'Download plot as a png': '保存图片',
        'Download plot as png': '保存图片'
    };

    function applyInDocument(doc) {
        let translated = 0;
        if (!doc) return translated;
        const nodes = doc.querySelectorAll('.modebar-btn, [data-title], [title], [aria-label]');
        nodes.forEach(btn => {
            const key = btn.getAttribute('data-title') || btn.getAttribute('title') || btn.getAttribute('aria-label');
            if (key && tooltipMap[key]) {
                const zh = tooltipMap[key];
                btn.setAttribute('data-title', zh);
                btn.setAttribute('title', zh);
                btn.setAttribute('aria-label', zh);
                translated++;
            }
        });
        return translated;
    }

    let total = 0;

    // 当前文档与父文档（组件运行在 iframe 时可作用到父文档）
    const docs = [document];
    try { if (parent && parent.document) docs.push(parent.document); } catch (e) {}

    docs.forEach(doc => {
        total += applyInDocument(doc);
        // 同时尝试作用到该文档内的所有 iframe
        const iframes = Array.from(doc.querySelectorAll('iframe'));
        iframes.forEach(iframe => {
            try {
                const idoc = iframe.contentDocument || (iframe.contentWindow && iframe.contentWindow.document);
                if (idoc) {
                    total += applyInDocument(idoc);
                    const observer = new MutationObserver(() => setTimeout(() => applyInDocument(idoc), 50));
                    observer.observe(idoc.body || idoc, { childList: true, subtree: true });
                }
            } catch (e) {
                // 跨域或沙箱限制的 iframe 可能无法访问，忽略
            }
        });
    });

    console.log(`🔧 工具栏中文化: 总计翻译 ${total} 个按钮`);
    return total;
}
// 每隔 1 秒尝试翻译一次，确保动态渲染后仍为中文
setInterval(translateToolbar, 1000);


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
    const docs = [document];
    try { if (parent && parent.document) docs.push(parent.document); } catch(e) {}

    // 隐藏Deploy按钮 / 右上角菜单 / 主菜单 / 品牌链接
    docs.forEach(doc => {
        doc.querySelectorAll('[data-testid="stAppDeployButton"]').forEach(btn => { btn.style.display='none'; try{btn.remove();}catch(_){} });
        doc.querySelectorAll('.css-1rs6os, .css-17eq0hr, .css-1kyxreq, .css-1v0mbdj').forEach(menu => { menu.style.display='none'; try{menu.remove();}catch(_){} });
        doc.querySelectorAll('a[href*="streamlit.io"]').forEach(link => { link.style.display='none'; try{link.remove();}catch(_){} });
        const mainMenu = doc.querySelector('#MainMenu'); if (mainMenu) { mainMenu.style.display='none'; try{mainMenu.remove();}catch(_){} }
    });

    // 隐藏页脚
    docs.forEach(doc => {
        doc.querySelectorAll('footer').forEach(footer => { footer.style.display='none'; try{footer.remove();}catch(_){} });
    });

    // 隐藏顶部工具栏
    docs.forEach(doc => {
        doc.querySelectorAll('.css-18e3th9').forEach(toolbar => { toolbar.style.display='none'; });
    });

    // 强制隐藏系统 Header 占位
    docs.forEach(doc => {
        const headerEl = doc.querySelector('[data-testid="stHeader"]');
        if (headerEl) {
            headerEl.style.setProperty('display', 'none', 'important');
            headerEl.style.minHeight = '0px';
            headerEl.style.height = '0px';
            headerEl.style.padding = '0px';
            headerEl.style.margin = '0px';
            headerEl.style.overflow = 'hidden';
        }
    });
}

// 自定义导航栏功能已停用，移除冗余代码

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
    const docs = [document];
    try { if (parent && parent.document) docs.push(parent.document); } catch(e) {}

    docs.forEach(doc => {
        const main = doc.querySelector('.main .block-container');
        if (!main) return;
        const containers = Array.from(main.querySelectorAll('.element-container'));
        if (!containers.length) return;

        let hitTitle = false;
        for (const ec of containers) {
            if (hitTitle) break;
            const hasTitle = ec.querySelector('.title-banner') || ec.querySelector('.main-header') || /Gordon\s+Wang|股票预测系统|RTX\s*5090/.test((ec.innerText || '').trim());
            if (hasTitle) { hitTitle = true; continue; }

            const fc = ec.firstElementChild;
            const tag = fc ? fc.tagName.toLowerCase() : '';
            const cls = fc ? (fc.className || '') : '';
            const html = (ec.innerHTML || '').trim();
            const htmlWithoutStyleScript = html.replace(/<\/(?:style|script)>[\s\S]*?<(?=style|script)|<(?:style|script)[\s\S]*?<\/(?:style|script)>/gi, '').trim();
            const isStyleOnly = tag === 'div' && cls.includes('stMarkdown') && htmlWithoutStyleScript === '';
            const isIframe = tag === 'iframe';
            if (isStyleOnly || isIframe) {
                ec.style.display = 'none';
                ec.setAttribute('data-collapsed', 'true');
            }
        }
    });
}


function pinTitleBanner() {
    // 移除Streamlit默认头部和过大的顶部留白
    function removeTopSpacing() {
        // Remove all headers
        const headers = document.querySelectorAll('[data-testid="stHeader"], .stApp > header, header');
        headers.forEach(header => {
            header.style.setProperty('display', 'none', 'important');
            header.style.setProperty('height', '0', 'important');
            header.style.setProperty('margin', '0', 'important');
            header.style.setProperty('padding', '0', 'important');
        });

        // 清除根容器的 margin-top，并让 CSS 控制统一的 0.25rem 顶部留白
        const containers = document.querySelectorAll('.stApp, [data-testid="stAppViewContainer"], .main, .main > div, .block-container, .main .block-container, [data-testid="block-container"]');
        containers.forEach(container => {
            container.style.setProperty('margin-top', '0', 'important');
            container.style.removeProperty('padding-top');
        });

        // Force body and html to have no top spacing
        document.body.style.setProperty('margin-top', '0', 'important');
        document.body.style.setProperty('padding-top', '0', 'important');
        document.documentElement.style.setProperty('margin-top', '0', 'important');
        document.documentElement.style.setProperty('padding-top', '0', 'important');
    }

    function apply() {
        // Always remove top spacing first
        removeTopSpacing();
        // Also tighten containers before the title if present
        try { tightenTopWhitespace(); } catch(e) {}

        const banner = document.querySelector('.title-banner');
        // 标题可能尚未渲染，等待后续MutationObserver回调
        if (!banner) return;

        // 确保横幅保持在文档正常流中（使用CSS的sticky），并清理之前的内联定位
        ['position','top','left','right','margin'].forEach(p => banner.style.removeProperty(p));

        // 清理旧版变量，避免产生额外占位
        document.documentElement.style.setProperty('--title-banner-offset', '0px');
        document.documentElement.style.setProperty('--title-banner-h', '0px');
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
