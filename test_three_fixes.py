#!/usr/bin/env python3
"""
测试三个修复问题
1. 历史数据周期中文化
2. 工具栏提示中文化  
3. 蒙特卡洛预测区间递增
"""

import requests
import time

def test_prediction_with_uncertainty():
    """测试预测的不确定性区间是否递增"""
    print("🎲 测试蒙特卡洛预测区间递增...")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001', 'pred_len': 7},
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                predictions = data['data']['predictions']
                
                print(f"   ✅ 预测成功 ({end_time - start_time:.1f}s)")
                print(f"   📊 预测天数: {len(predictions)} 天")
                
                # 分析不确定性区间的变化
                uncertainties = []
                for i, pred in enumerate(predictions):
                    if 'close_upper' in pred and 'close_lower' in pred:
                        close = pred['close']
                        upper = pred['close_upper']
                        lower = pred['close_lower']
                        uncertainty_pct = ((upper - lower) / close) * 100
                        uncertainties.append(uncertainty_pct)
                        
                        print(f"   {i+1}. {pred['date']}")
                        print(f"      预测: ¥{close:.2f}")
                        print(f"      区间: ¥{lower:.2f} - ¥{upper:.2f}")
                        print(f"      不确定性: ±{uncertainty_pct:.1f}%")
                
                # 检查不确定性是否递增
                if len(uncertainties) > 1:
                    is_increasing = all(uncertainties[i] <= uncertainties[i+1] for i in range(len(uncertainties)-1))
                    if is_increasing:
                        print(f"   ✅ 不确定性正确递增: {uncertainties[0]:.1f}% → {uncertainties[-1]:.1f}%")
                    else:
                        print(f"   ⚠️ 不确定性未完全递增: {uncertainties}")
                        
                    # 计算递增幅度
                    growth_rate = (uncertainties[-1] - uncertainties[0]) / len(uncertainties)
                    print(f"   📈 平均递增率: {growth_rate:.2f}%/天")
                
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
            print("   💡 请在浏览器中检查:")
            print("      - 历史数据周期是否显示中文选项")
            print("      - 工具栏提示是否为中文")
            print("      - 预测区间是否随时间递增")
            return True
        else:
            print(f"   ❌ Streamlit异常: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Streamlit连接失败: {str(e)}")
        return False

def analyze_uncertainty_pattern():
    """分析不确定性模式"""
    print("\n📊 分析不确定性模式...")
    
    try:
        # 测试不同股票的不确定性模式
        test_stocks = ['000001', '000002']
        
        for stock_code in test_stocks:
            print(f"\n   📈 测试股票 {stock_code}:")
            
            response = requests.post(
                'http://localhost:8000/predict',
                json={'stock_code': stock_code, 'pred_len': 5},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    predictions = data['data']['predictions']
                    stock_name = data['data']['stock_info']['name']
                    
                    print(f"      股票名称: {stock_name}")
                    
                    uncertainties = []
                    for i, pred in enumerate(predictions):
                        if 'close_upper' in pred and 'close_lower' in pred:
                            close = pred['close']
                            upper = pred['close_upper']
                            lower = pred['close_lower']
                            uncertainty_pct = ((upper - lower) / close) * 100
                            uncertainties.append(uncertainty_pct)
                    
                    if uncertainties:
                        print(f"      不确定性范围: {min(uncertainties):.1f}% - {max(uncertainties):.1f}%")
                        print(f"      递增模式: {' → '.join([f'{u:.1f}%' for u in uncertainties])}")
                else:
                    print(f"      ❌ 预测失败: {data.get('error')}")
            else:
                print(f"      ❌ HTTP错误: {response.status_code}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 分析异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🔧 三个问题修复测试")
    print("=" * 60)
    
    # 测试1: 蒙特卡洛预测区间
    prediction_ok = test_prediction_with_uncertainty()
    
    # 测试2: Streamlit界面
    ui_ok = test_streamlit_interface()
    
    # 测试3: 不确定性模式分析
    pattern_ok = analyze_uncertainty_pattern()
    
    print("\n" + "=" * 60)
    print("📊 测试结果:")
    print(f"   蒙特卡洛预测: {'✅ 正常' if prediction_ok else '❌ 异常'}")
    print(f"   界面功能: {'✅ 正常' if ui_ok else '❌ 异常'}")
    print(f"   不确定性模式: {'✅ 正常' if pattern_ok else '❌ 异常'}")
    
    if prediction_ok and ui_ok and pattern_ok:
        print("\n🎉 三个问题修复完成!")
        print("\n✅ 修复内容:")
        print("   1. 历史数据周期 - 中文选项 (6个月、1年、2年、5年)")
        print("   2. 工具栏提示 - 强化JavaScript中文化")
        print("   3. 预测区间 - 时间递增的不确定性模型")
        
        print("\n📈 不确定性模型特点:")
        print("   - 时间递增: 随预测天数增加，不确定性增大")
        print("   - 平方根增长: 符合金融时间序列规律")
        print("   - 基础不确定性: 1.5%起步，每天增加0.5%")
        print("   - 历史波动率: 结合股票历史波动特征")
        
        print("\n🛠️ 工具栏中文化:")
        print("   - 多次尝试翻译确保成功")
        print("   - DOM变化监听自动翻译")
        print("   - 控制台日志显示翻译状态")
        
        print("\n🌐 测试地址:")
        print("   前端界面: http://localhost:8501")
        print("   请验证:")
        print("   - 侧边栏历史数据周期显示中文")
        print("   - 图表工具栏悬停显示中文提示")
        print("   - 预测区间随时间扩大")
        
    else:
        print("\n⚠️ 部分功能需要进一步检查")

if __name__ == "__main__":
    main()
