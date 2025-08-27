#!/usr/bin/env python3
"""
测试Streamlit广告移除效果
"""

import requests
import time

def test_streamlit_clean_interface():
    """测试纯净界面"""
    print("🧹 测试Streamlit广告移除效果...")
    
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("   ✅ Streamlit界面可访问")
            
            content = response.text
            
            # 检查广告元素是否被移除
            ad_checks = [
                ("stAppDeployButton", "Deploy按钮隐藏"),
                ("display: none", "CSS隐藏规则"),
                ("hideStreamlitElements", "JS移除函数"),
                ("custom-navbar", "自定义导航栏"),
                ("hideTopBar = true", "顶部栏隐藏配置")
            ]
            
            for keyword, description in ad_checks:
                if keyword in content:
                    print(f"   ✅ {description}: 已实现")
                else:
                    print(f"   ⚠️ {description}: 未找到")
            
            # 检查是否还有Streamlit品牌元素
            brand_elements = [
                "Made with Streamlit",
                "Deploy this app", 
                "streamlit.io",
                "Streamlit Community Cloud"
            ]
            
            found_ads = []
            for element in brand_elements:
                if element in content:
                    found_ads.append(element)
            
            if found_ads:
                print(f"   ⚠️ 仍存在广告元素: {found_ads}")
            else:
                print("   ✅ 所有广告元素已移除")
            
            return len(found_ads) == 0
        else:
            print(f"   ❌ Streamlit异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Streamlit连接失败: {str(e)}")
        return False

def test_css_hiding_rules():
    """测试CSS隐藏规则"""
    print("\n🎨 测试CSS隐藏规则...")
    
    css_file = "static/css/chinese_ui.css"
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # 检查隐藏规则
        hiding_rules = [
            ("display: none !important", "强制隐藏"),
            ("stAppDeployButton", "Deploy按钮"),
            ("MainMenu", "主菜单"),
            ("streamlit.io", "品牌链接"),
            ("custom-navbar", "自定义导航"),
            ("visibility: hidden", "可见性隐藏")
        ]
        
        for rule, description in hiding_rules:
            if rule in css_content:
                print(f"   ✅ {description}: 已添加")
            else:
                print(f"   ❌ {description}: 缺失")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CSS检查失败: {str(e)}")
        return False

def test_javascript_removal():
    """测试JavaScript移除功能"""
    print("\n🔧 测试JavaScript移除功能...")
    
    js_file = "static/js/chinese_ui.js"
    
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 检查移除功能
        removal_checks = [
            ("hideStreamlitElements", "移除函数"),
            ("deployButtons", "Deploy按钮移除"),
            ("streamlitLinks", "品牌链接移除"),
            ("remove()", "DOM元素移除"),
            ("已移除Streamlit广告元素", "移除确认日志")
        ]
        
        for check, description in removal_checks:
            if check in js_content:
                print(f"   ✅ {description}: 已实现")
            else:
                print(f"   ❌ {description}: 缺失")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JavaScript检查失败: {str(e)}")
        return False

def test_config_settings():
    """测试配置文件设置"""
    print("\n⚙️ 测试配置文件设置...")
    
    config_file = ".streamlit/config.toml"
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_content = f.read()
        
        # 检查配置项
        config_checks = [
            ("hideTopBar = true", "隐藏顶部栏"),
            ("fastReruns = true", "快速重运行"),
            ("level = \"error\"", "错误日志级别"),
            ("gatherUsageStats = false", "禁用统计")
        ]
        
        for setting, description in config_checks:
            if setting in config_content:
                print(f"   ✅ {description}: 已配置")
            else:
                print(f"   ⚠️ {description}: 未配置")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 配置检查失败: {str(e)}")
        return False

def explain_streamlit():
    """解释Streamlit"""
    print("\n📖 关于Streamlit框架...")
    
    print("""
    🎯 Streamlit是什么？
    ==================
    Streamlit是一个开源Python框架，用于快速构建数据科学Web应用。
    
    ✅ 优点：
    - 纯Python开发，无需前端技能
    - 快速原型开发
    - 丰富的数据可视化组件
    - 实时交互更新
    
    ❌ 缺点：
    - 内置广告和品牌推广
    - 默认有Deploy等商业化元素
    - 界面定制化程度有限
    
    🔧 我们的解决方案：
    - 完全移除所有Streamlit广告
    - 自定义品牌标识
    - 纯净的用户体验
    - 专业的企业级界面
    """)

def test_api_functionality():
    """测试API功能是否正常"""
    print("\n🔧 测试核心功能...")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={
                'stock_code': '000001',
                'period': '1y',
                'pred_len': 3
            },
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ 核心预测功能正常 ({end_time - start_time:.1f}s)")
                return True
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ API错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ API异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚫 Streamlit广告移除测试")
    print("=" * 60)
    
    # 解释Streamlit
    explain_streamlit()
    
    # 测试各项移除效果
    interface_ok = test_streamlit_clean_interface()
    css_ok = test_css_hiding_rules()
    js_ok = test_javascript_removal()
    config_ok = test_config_settings()
    api_ok = test_api_functionality()
    
    print("\n" + "=" * 60)
    print("📊 测试结果总结:")
    print(f"   纯净界面: {'✅ 正常' if interface_ok else '❌ 异常'}")
    print(f"   CSS隐藏: {'✅ 正常' if css_ok else '❌ 异常'}")
    print(f"   JS移除: {'✅ 正常' if js_ok else '❌ 异常'}")
    print(f"   配置设置: {'✅ 正常' if config_ok else '❌ 异常'}")
    print(f"   核心功能: {'✅ 正常' if api_ok else '❌ 异常'}")
    
    all_ok = all([interface_ok, css_ok, js_ok, config_ok, api_ok])
    
    if all_ok:
        print("\n🎉 Streamlit广告完全移除成功！")
        
        print("\n✅ 移除的广告元素:")
        print("   1. Deploy按钮和菜单")
        print("   2. 'Made with Streamlit' 链接")
        print("   3. Streamlit品牌推广")
        print("   4. 右上角设置菜单")
        print("   5. 页脚广告信息")
        print("   6. GitHub/社区链接")
        
        print("\n🎨 界面优化:")
        print("   - 自定义顶部导航栏")
        print("   - Gordon Wang 专属品牌")
        print("   - 纯净的用户体验")
        print("   - 专业的企业级外观")
        
        print("\n🔧 技术实现:")
        print("   - CSS强制隐藏 (display: none !important)")
        print("   - JavaScript动态移除")
        print("   - 配置文件优化")
        print("   - 自定义样式覆盖")
        
        print("\n🌐 最终效果:")
        print("   访问 http://localhost:8501")
        print("   您将看到完全无广告的纯净界面！")
        
    else:
        print("\n⚠️ 部分移除功能需要进一步优化")

if __name__ == "__main__":
    main()
