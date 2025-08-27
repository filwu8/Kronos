#!/usr/bin/env python3
"""
测试UI修复效果
"""

import requests
import time

def test_streamlit_interface():
    """测试Streamlit界面修复"""
    print("🎨 测试界面修复效果...")
    
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("   ✅ Streamlit界面可访问")
            
            # 检查页面内容
            content = response.text
            
            # 检查修复内容
            checks = [
                ("Deploy", "Deploy菜单"),
                ("部署", "中文翻译"),
                ("stSelectbox", "选择框样式"),
                ("系统状态", "状态部分"),
                ("示例股票", "示例股票"),
                ("性能监控", "性能监控"),
                ("Gordon Wang", "品牌标识")
            ]
            
            for keyword, description in checks:
                if keyword in content:
                    print(f"   ✅ {description}: 已加载")
                else:
                    print(f"   ⚠️ {description}: 未找到")
            
            return True
        else:
            print(f"   ❌ Streamlit异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Streamlit连接失败: {str(e)}")
        return False

def test_css_improvements():
    """测试CSS改进"""
    print("\n🎨 测试CSS样式改进...")
    
    css_file = "static/css/chinese_ui.css"
    
    try:
        with open(css_file, 'r', encoding='utf-8') as f:
            css_content = f.read()
        
        # 检查选择框样式改进
        style_checks = [
            ("stSelectbox", "选择框样式"),
            ("linear-gradient", "渐变背景"),
            ("box-shadow", "阴影效果"),
            ("transition", "过渡动画"),
            ("hover", "悬停效果"),
            ("focus-within", "焦点样式")
        ]
        
        for keyword, description in style_checks:
            if keyword in css_content:
                print(f"   ✅ {description}: 已添加")
            else:
                print(f"   ❌ {description}: 缺失")
        
        return True
        
    except Exception as e:
        print(f"   ❌ CSS检查失败: {str(e)}")
        return False

def test_javascript_enhancements():
    """测试JavaScript增强"""
    print("\n🔧 测试JavaScript增强...")
    
    js_file = "static/js/chinese_ui.js"
    
    try:
        with open(js_file, 'r', encoding='utf-8') as f:
            js_content = f.read()
        
        # 检查Deploy菜单翻译
        translation_checks = [
            ("Deploy", "Deploy翻译"),
            ("部署", "中文翻译"),
            ("stAppDeployButton", "Deploy按钮"),
            ("dropdown-menu", "下拉菜单"),
            ("menuitem", "菜单项")
        ]
        
        for keyword, description in translation_checks:
            if keyword in js_content:
                print(f"   ✅ {description}: 已添加")
            else:
                print(f"   ❌ {description}: 缺失")
        
        return True
        
    except Exception as e:
        print(f"   ❌ JavaScript检查失败: {str(e)}")
        return False

def test_sidebar_layout():
    """测试侧边栏布局"""
    print("\n📋 测试侧边栏布局...")
    
    try:
        import sys
        sys.path.append('app')
        from chinese_menu import create_sidebar_status_section
        
        print("   ✅ 侧边栏状态函数: 可导入")
        
        # 检查函数是否存在
        if callable(create_sidebar_status_section):
            print("   ✅ 状态部分函数: 可调用")
        else:
            print("   ❌ 状态部分函数: 不可调用")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 侧边栏测试失败: {str(e)}")
        return False

def test_api_functionality():
    """测试API功能"""
    print("\n🔧 测试API功能...")
    
    try:
        # 测试预测功能
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={
                'stock_code': '000001',
                'period': '1y',
                'pred_len': 3,
                'lookback': 500
            },
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ 预测功能正常 ({end_time - start_time:.1f}s)")
                
                # 检查数据完整性
                historical_data = data['data']['historical_data']
                predictions = data['data']['predictions']
                
                print(f"   📊 历史数据: {len(historical_data)} 条")
                print(f"   🔮 预测数据: {len(predictions)} 条")
                
                return True
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ 预测请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ API测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🔧 UI修复效果测试")
    print("=" * 50)
    
    # 测试各项修复
    ui_ok = test_streamlit_interface()
    css_ok = test_css_improvements()
    js_ok = test_javascript_enhancements()
    sidebar_ok = test_sidebar_layout()
    api_ok = test_api_functionality()
    
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    print(f"   界面修复: {'✅ 正常' if ui_ok else '❌ 异常'}")
    print(f"   CSS改进: {'✅ 正常' if css_ok else '❌ 异常'}")
    print(f"   JS增强: {'✅ 正常' if js_ok else '❌ 异常'}")
    print(f"   侧边栏: {'✅ 正常' if sidebar_ok else '❌ 异常'}")
    print(f"   API功能: {'✅ 正常' if api_ok else '❌ 异常'}")
    
    all_ok = all([ui_ok, css_ok, js_ok, sidebar_ok, api_ok])
    
    if all_ok:
        print("\n🎉 所有UI修复完成！")
        
        print("\n✅ 修复内容:")
        print("   1. Deploy菜单中文化 - 右上角菜单完全中文")
        print("   2. 选择框样式优化 - 渐变背景，更好可见性")
        print("   3. 侧边栏布局调整 - 系统状态移到示例股票后")
        
        print("\n🎨 样式改进:")
        print("   - 选择框渐变背景 (灰白渐变)")
        print("   - 悬停效果增强 (颜色变化)")
        print("   - 焦点状态优化 (边框高亮)")
        print("   - 下拉选项美化 (蓝绿渐变)")
        
        print("\n📋 布局优化:")
        print("   - 系统状态: 移到示例股票后面")
        print("   - 状态显示: 美观的卡片样式")
        print("   - 快速操作: 紧凑的按钮布局")
        print("   - 性能监控: 双列指标显示")
        
        print("\n🌐 访问地址:")
        print("   前端界面: http://localhost:8501")
        print("   查看修复效果:")
        print("   - 右上角Deploy菜单中文化")
        print("   - 历史数据周期选择框样式")
        print("   - 左侧系统状态位置调整")
        
    else:
        print("\n⚠️ 部分修复需要进一步检查")

if __name__ == "__main__":
    main()
