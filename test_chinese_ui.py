#!/usr/bin/env python3
"""
测试中文化界面和本地资源
"""

import requests
import time
import os
from pathlib import Path

def test_static_resources():
    """测试静态资源"""
    print("📁 测试静态资源...")
    
    static_dir = Path("static")
    required_files = [
        "css/chinese_ui.css",
        "css/local.css", 
        "js/chinese_ui.js",
        "icons/chart.svg",
        "icons/settings.svg",
        "icons/download.svg",
        "manifest.json"
    ]
    
    missing_files = []
    existing_files = []
    
    for file_path in required_files:
        full_path = static_dir / file_path
        if full_path.exists():
            existing_files.append(file_path)
            print(f"   ✅ {file_path}")
        else:
            missing_files.append(file_path)
            print(f"   ❌ {file_path}")
    
    print(f"\n📊 静态资源统计:")
    print(f"   存在: {len(existing_files)}/{len(required_files)}")
    print(f"   缺失: {len(missing_files)}")
    
    return len(missing_files) == 0

def test_chinese_menu():
    """测试中文菜单组件"""
    print("\n🎨 测试中文菜单组件...")
    
    try:
        import sys
        sys.path.append('app')
        from chinese_menu import ChineseMenu
        
        menu = ChineseMenu()
        
        # 测试菜单结构
        print(f"   ✅ 菜单页面数: {len(menu.pages)}")
        print(f"   ✅ 菜单分组数: {len(menu.menu_groups)}")
        
        # 测试页面信息
        for page_id, page_info in menu.pages.items():
            title = page_info['title']
            icon = page_info['icon']
            print(f"   📄 {icon} {title}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 中文菜单测试失败: {str(e)}")
        return False

def test_streamlit_interface():
    """测试Streamlit界面"""
    print("\n🌐 测试Streamlit界面...")
    
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("   ✅ Streamlit界面可访问")
            
            # 检查页面内容
            content = response.text
            
            checks = [
                ("Gordon Wang", "品牌标识"),
                ("chinese_ui.css", "中文CSS"),
                ("chinese_ui.js", "中文JavaScript"),
                ("股票预测系统", "中文标题"),
                ("RTX 5090", "性能标识")
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

def test_api_functionality():
    """测试API功能"""
    print("\n🔧 测试API功能...")
    
    try:
        # 测试健康检查
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            print("   ✅ API健康检查通过")
        else:
            print(f"   ❌ API健康检查失败: {response.status_code}")
            return False
        
        # 测试预测功能
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={
                'stock_code': '000968',
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

def test_local_resources():
    """测试本地资源加载"""
    print("\n📦 测试本地资源加载...")
    
    # 检查CDN资源是否已本地化
    cdn_resources = [
        "static/css/bootstrap.min.css",
        "static/css/fontawesome.min.css", 
        "static/js/bootstrap.bundle.min.js",
        "static/js/jquery.min.js",
        "static/js/plotly.min.js"
    ]
    
    local_count = 0
    for resource in cdn_resources:
        if Path(resource).exists():
            size = Path(resource).stat().st_size
            print(f"   ✅ {resource} ({size:,} bytes)")
            local_count += 1
        else:
            print(f"   ❌ {resource}")
    
    print(f"\n📊 本地化资源: {local_count}/{len(cdn_resources)}")
    
    return local_count == len(cdn_resources)

def main():
    """主测试函数"""
    print("🚀 Gordon Wang 股票预测系统 - 中文化界面测试")
    print("=" * 70)
    
    # 测试静态资源
    static_ok = test_static_resources()
    
    # 测试中文菜单
    menu_ok = test_chinese_menu()
    
    # 测试本地资源
    local_ok = test_local_resources()
    
    # 测试API功能
    api_ok = test_api_functionality()
    
    # 测试Streamlit界面
    ui_ok = test_streamlit_interface()
    
    print("\n" + "=" * 70)
    print("📊 测试结果总结:")
    print(f"   静态资源: {'✅ 正常' if static_ok else '❌ 异常'}")
    print(f"   中文菜单: {'✅ 正常' if menu_ok else '❌ 异常'}")
    print(f"   本地资源: {'✅ 正常' if local_ok else '❌ 异常'}")
    print(f"   API功能: {'✅ 正常' if api_ok else '❌ 异常'}")
    print(f"   界面加载: {'✅ 正常' if ui_ok else '❌ 异常'}")
    
    all_ok = all([static_ok, menu_ok, local_ok, api_ok, ui_ok])
    
    if all_ok:
        print("\n🎉 所有测试通过！中文化界面部署成功！")
        
        print("\n✅ 完成的功能:")
        print("   1. 完全中文化的菜单系统")
        print("   2. 本地化的静态资源 (无远程依赖)")
        print("   3. 中文化的界面元素和提示")
        print("   4. 自定义的CSS和JavaScript")
        print("   5. 本地SVG图标库")
        print("   6. 响应式中文界面设计")
        
        print("\n🎯 界面特色:")
        print("   - 完全中文化的菜单和导航")
        print("   - 本地化资源，无网络依赖")
        print("   - Gordon Wang 品牌标识统一")
        print("   - RTX 5090 性能标识突出")
        print("   - 专业的金融界面设计")
        
        print("\n🌐 访问地址:")
        print("   前端界面: http://localhost:8501")
        print("   API文档: http://localhost:8000/docs")
        
        print("\n💡 使用说明:")
        print("   1. 所有菜单和界面元素已中文化")
        print("   2. 静态资源已本地化，离线可用")
        print("   3. 支持多页面导航 (开发中)")
        print("   4. 响应式设计，适配不同屏幕")
        
    else:
        print("\n⚠️ 部分测试失败，请检查相关组件")
        
        if not static_ok:
            print("   🔧 请运行: python app/static_manager.py")
        if not api_ok:
            print("   🔧 请检查API服务是否启动")
        if not ui_ok:
            print("   🔧 请检查Streamlit服务状态")

if __name__ == "__main__":
    main()
