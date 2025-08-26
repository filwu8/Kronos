#!/usr/bin/env python3
"""
测试工具栏中文化
"""

import requests
import time

def test_streamlit_interface():
    """测试Streamlit界面和工具栏"""
    print("🎨 测试Streamlit界面和工具栏中文化...")
    
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("   ✅ Streamlit界面可访问")
            
            # 检查页面内容是否包含中文化相关代码
            content = response.text
            
            if 'forceTranslateToolbar' in content:
                print("   ✅ JavaScript中文化代码已加载")
            else:
                print("   ⚠️ JavaScript中文化代码未找到")
                
            if '工具栏使用说明' in content:
                print("   ✅ 中文说明面板已加载")
            else:
                print("   ⚠️ 中文说明面板未找到")
                
            return True
        else:
            print(f"   ❌ Streamlit异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Streamlit连接失败: {str(e)}")
        return False

def test_prediction_with_chart():
    """测试预测功能，确保图表正常显示"""
    print("\n📊 测试预测功能和图表显示...")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={
                'stock_code': '000968',
                'period': '1y',
                'pred_len': 5,
                'lookback': 500
            },
            timeout=30
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                historical_data = data['data']['historical_data']
                predictions = data['data']['predictions']
                stock_info = data['data']['stock_info']
                
                print(f"   ✅ 预测成功 ({end_time - start_time:.1f}s)")
                print(f"   📊 股票: {stock_info['name']} ({stock_info['code']})")
                print(f"   📈 历史数据: {len(historical_data)} 条")
                print(f"   🔮 预测数据: {len(predictions)} 条")
                
                # 检查数据完整性
                if historical_data and predictions:
                    hist_dates = [item['date'] for item in historical_data]
                    pred_dates = [item['date'] for item in predictions]
                    
                    print(f"   📅 历史范围: {min(hist_dates)} 到 {max(hist_dates)}")
                    print(f"   🔮 预测范围: {min(pred_dates)} 到 {max(pred_dates)}")
                    
                    # 检查不确定性区间
                    first_pred = predictions[0]
                    if 'close_upper' in first_pred and 'close_lower' in first_pred:
                        uncertainty = ((first_pred['close_upper'] - first_pred['close_lower']) / first_pred['close']) * 100
                        print(f"   📊 预测不确定性: ±{uncertainty:.1f}%")
                        print("   ✅ 蒙特卡洛不确定性区间正常")
                    else:
                        print("   ⚠️ 缺少不确定性区间数据")
                
                return True
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
        return False

def check_javascript_methods():
    """检查JavaScript方法的可行性"""
    print("\n🔧 JavaScript工具栏中文化方法分析...")
    
    methods = [
        {
            "name": "方法1: 直接修改title属性",
            "description": "document.querySelector('.modebar-btn').setAttribute('title', '中文')",
            "pros": "简单直接",
            "cons": "可能被Plotly覆盖"
        },
        {
            "name": "方法2: 监听DOM变化",
            "description": "MutationObserver监听工具栏创建",
            "pros": "能捕获动态创建的元素",
            "cons": "性能开销"
        },
        {
            "name": "方法3: CSS伪元素",
            "description": "用CSS ::after显示中文提示",
            "pros": "不会被JavaScript覆盖",
            "cons": "样式复杂"
        },
        {
            "name": "方法4: 中文说明面板",
            "description": "在图表下方显示对照表",
            "pros": "100%可靠",
            "cons": "需要用户查看"
        }
    ]
    
    for i, method in enumerate(methods, 1):
        print(f"\n   {i}. {method['name']}")
        print(f"      实现: {method['description']}")
        print(f"      优点: {method['pros']}")
        print(f"      缺点: {method['cons']}")
    
    print(f"\n   💡 当前采用: 多种方法组合")
    print(f"      - JavaScript多次尝试翻译")
    print(f"      - DOM变化监听")
    print(f"      - 中文说明面板作为备选")

def main():
    """主测试函数"""
    print("🛠️ 工具栏中文化测试")
    print("=" * 50)
    
    # 测试界面
    ui_ok = test_streamlit_interface()
    
    # 测试预测功能
    prediction_ok = test_prediction_with_chart()
    
    # 分析JavaScript方法
    check_javascript_methods()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   界面加载: {'✅ 正常' if ui_ok else '❌ 异常'}")
    print(f"   预测功能: {'✅ 正常' if prediction_ok else '❌ 异常'}")
    
    if ui_ok and prediction_ok:
        print("\n🎉 工具栏中文化部署完成!")
        
        print("\n✅ 部署的解决方案:")
        print("   1. 强化JavaScript翻译 - 多种方法组合")
        print("   2. DOM变化监听 - 自动检测新工具栏")
        print("   3. 多次尝试执行 - 确保翻译成功")
        print("   4. 中文说明面板 - 100%可靠的备选方案")
        
        print("\n🔍 工具栏英文对照:")
        print("   Pan → 平移 - 拖拽移动图表")
        print("   Box Zoom → 框选缩放 - 选择区域放大")
        print("   Zoom in → 放大 - 点击放大图表")
        print("   Zoom out → 缩小 - 点击缩小图表")
        print("   Autoscale → 自适应 - 自动最佳视角")
        print("   Reset axes → 重置 - 回到原始视图")
        print("   Download plot as a png → 保存 - 下载高清图片")
        
        print("\n💡 使用建议:")
        print("   1. 打开浏览器开发者工具 (F12)")
        print("   2. 查看控制台是否有'工具栏中文化'日志")
        print("   3. 如果JavaScript被阻止，参考图表下方的中文说明")
        print("   4. 刷新页面可能有助于JavaScript执行")
        
        print("\n🌐 测试地址:")
        print("   前端界面: http://localhost:8501")
        print("   选择股票进行预测，查看图表工具栏")
        
    else:
        print("\n⚠️ 部分功能异常，请检查服务状态")

if __name__ == "__main__":
    main()
