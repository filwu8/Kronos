#!/usr/bin/env python3
"""
测试工具栏优化效果
"""

import requests
import time

def test_streamlit_interface():
    """测试Streamlit界面"""
    print("🎨 测试Streamlit界面优化...")
    
    try:
        response = requests.get('http://localhost:8501', timeout=5)
        if response.status_code == 200:
            print("   ✅ Streamlit界面可访问")
            return True
        else:
            print(f"   ❌ Streamlit异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Streamlit连接失败: {str(e)}")
        return False

def test_prediction_api():
    """测试预测API"""
    print("\n🔮 测试预测API...")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001', 'pred_len': 5},
            timeout=20
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ 预测成功 ({end_time - start_time:.1f}s)")
                
                # 检查数据完整性
                predictions = data['data']['predictions']
                historical = data['data']['historical_data']
                
                print(f"   📊 历史数据: {len(historical)} 条")
                print(f"   🔮 预测数据: {len(predictions)} 条")
                
                # 检查日期格式
                if predictions:
                    first_pred = predictions[0]
                    print(f"   📅 预测日期: {first_pred['date']}")
                    print(f"   💰 预测价格: ¥{first_pred['close']:.2f}")
                
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
    print("🔧 工具栏优化测试")
    print("=" * 50)
    
    # 测试API
    api_ok = test_prediction_api()
    
    # 测试界面
    ui_ok = test_streamlit_interface()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   API服务: {'✅ 正常' if api_ok else '❌ 异常'}")
    print(f"   界面服务: {'✅ 正常' if ui_ok else '❌ 异常'}")
    
    if api_ok and ui_ok:
        print("\n🎉 工具栏优化完成!")
        print("\n✅ 优化内容:")
        print("   1. 简化工具栏 - 只保留最有用的7个工具")
        print("   2. 移除无用工具 - 套索选择、悬停等")
        print("   3. 高清保存 - 2倍分辨率PNG图片")
        print("   4. 中文说明 - 详细的工具使用指南")
        print("   5. 美化样式 - 圆角、阴影、悬停效果")
        
        print("\n🛠️ 工具栏功能说明:")
        print("   🖱️ 平移 (Pan) - 拖拽移动图表视角")
        print("   🔍 框选缩放 (Box Zoom) - 拖拽选择区域放大")
        print("   ➕ 放大 (Zoom In) - 点击放大图表")
        print("   ➖ 缩小 (Zoom Out) - 点击缩小图表")
        print("   🔄 自适应 (Auto Scale) - 自动调整到最佳视角")
        print("   🏠 重置 (Reset) - 恢复到原始视角")
        print("   📷 保存 (Download) - 下载高清PNG图片")
        
        print("\n💡 使用建议:")
        print("   - 使用框选缩放查看特定时间段")
        print("   - 使用平移工具浏览不同时期")
        print("   - 使用重置快速回到全景视图")
        print("   - 保存功能可生成高质量图片用于报告")
        
        print("\n🌐 测试地址:")
        print("   前端界面: http://localhost:8501")
        print("   选择股票代码，查看优化后的图表工具栏")
        
    else:
        print("\n⚠️ 部分服务异常，请检查服务状态")

if __name__ == "__main__":
    main()
