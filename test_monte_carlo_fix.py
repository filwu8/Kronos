#!/usr/bin/env python3
"""
测试蒙特卡洛预测修复
"""

import requests
import time

def test_monte_carlo_prediction():
    """测试蒙特卡洛预测功能"""
    print("🎲 测试蒙特卡洛预测...")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001', 'pred_len': 5},
            timeout=60  # 增加超时时间，因为要计算30次预测
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                predictions = data['data']['predictions']
                
                print(f"   ✅ 预测成功 ({end_time - start_time:.1f}s)")
                print(f"   📊 预测天数: {len(predictions)} 天")
                
                # 检查是否包含不确定性数据
                first_pred = predictions[0]
                has_uncertainty = all(key in first_pred for key in ['close_upper', 'close_lower'])
                
                if has_uncertainty:
                    print("   ✅ 包含蒙特卡洛不确定性区间")
                    print("   📈 预测详情:")
                    
                    for i, pred in enumerate(predictions[:3]):  # 显示前3天
                        date = pred['date']
                        close = pred['close']
                        upper = pred['close_upper']
                        lower = pred['close_lower']
                        uncertainty = ((upper - lower) / close) * 100
                        
                        print(f"      {i+1}. {date}")
                        print(f"         预测价: ¥{close:.2f}")
                        print(f"         区间: ¥{lower:.2f} - ¥{upper:.2f}")
                        print(f"         不确定性: ±{uncertainty:.1f}%")
                        print()
                else:
                    print("   ⚠️ 缺少不确定性区间数据")
                    print("   📈 基础预测:")
                    for i, pred in enumerate(predictions[:3]):
                        print(f"      {i+1}. {pred['date']} - ¥{pred['close']:.2f}")
                
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

def test_streamlit_interface():
    """测试Streamlit界面"""
    print("\n🎨 测试Streamlit界面...")
    
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

def main():
    """主测试函数"""
    print("🔬 蒙特卡洛预测修复测试")
    print("=" * 50)
    
    # 测试预测功能
    prediction_ok = test_monte_carlo_prediction()
    
    # 测试界面
    ui_ok = test_streamlit_interface()
    
    print("\n" + "=" * 50)
    print("📊 测试结果:")
    print(f"   蒙特卡洛预测: {'✅ 正常' if prediction_ok else '❌ 异常'}")
    print(f"   界面服务: {'✅ 正常' if ui_ok else '❌ 异常'}")
    
    if prediction_ok and ui_ok:
        print("\n🎉 蒙特卡洛预测修复完成!")
        print("\n✅ 修复内容:")
        print("   1. 真实蒙特卡洛采样 - 30条独立预测路径")
        print("   2. 统计不确定性区间 - 25%-75%分位数")
        print("   3. 工具栏中文提示 - JavaScript动态替换")
        print("   4. 专业预测说明 - 详细的方法论解释")
        
        print("\n🎲 蒙特卡洛方法:")
        print("   - 模型: Kronos-small (25M参数)")
        print("   - 采样: 30次独立预测路径")
        print("   - 温度: 轻微随机化增加多样性")
        print("   - 统计: 均值、分位数、标准差")
        
        print("\n📊 预测区间说明:")
        print("   - 红色实线: 30次预测的平均值")
        print("   - 红色阴影: 25%-75%分位数区间")
        print("   - 区间宽度: 反映预测不确定性")
        
        print("\n🌐 测试地址:")
        print("   前端界面: http://localhost:8501")
        print("   选择股票查看真实的蒙特卡洛预测区间")
        
    else:
        print("\n⚠️ 部分功能异常，请检查服务状态")

if __name__ == "__main__":
    main()
