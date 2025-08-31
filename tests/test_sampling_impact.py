#!/usr/bin/env python3
"""
测试不同采样次数对预测准确度的影响
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
import time
from app.prediction_service import get_prediction_service

def test_sampling_impact():
    """测试不同采样次数的影响"""
    print("🧪 测试采样次数对预测准确度的影响...")
    
    service = get_prediction_service(use_mock=True)
    stock_code = '000001'
    
    # 测试不同的采样次数
    sample_counts = [1, 3, 5, 10]
    results = {}
    
    for sample_count in sample_counts:
        print(f"\n📊 测试采样次数: {sample_count}")
        
        # 记录多次运行的结果
        predictions = []
        times = []
        
        for run in range(5):  # 每个采样次数运行5次
            start_time = time.time()
            
            try:
                result = service.predict_stock(
                    stock_code, 
                    lookback=30, 
                    pred_len=5,
                    sample_count=sample_count
                )
                
                if result['success']:
                    historical_data = result['data']['historical_data']
                    pred_data = result['data']['predictions']
                    
                    last_close = historical_data[-1]['close']
                    first_pred_open = pred_data[0]['open']
                    gap_percent = (first_pred_open - last_close) / last_close * 100
                    
                    predictions.append({
                        'gap_percent': gap_percent,
                        'first_open': first_pred_open,
                        'last_close': last_close,
                        'pred_close': pred_data[-1]['close']
                    })
                    
                    elapsed = time.time() - start_time
                    times.append(elapsed)
                    
                    print(f"  运行{run+1}: 跳空{gap_percent:.2f}%, 用时{elapsed:.2f}s")
                else:
                    print(f"  运行{run+1}: 失败 - {result.get('error', '未知错误')}")
                    
            except Exception as e:
                print(f"  运行{run+1}: 异常 - {str(e)}")
        
        if predictions:
            # 计算统计指标
            gaps = [p['gap_percent'] for p in predictions]
            gap_mean = np.mean(gaps)
            gap_std = np.std(gaps)
            gap_range = np.max(gaps) - np.min(gaps)
            avg_time = np.mean(times)
            
            results[sample_count] = {
                'gap_mean': gap_mean,
                'gap_std': gap_std,
                'gap_range': gap_range,
                'avg_time': avg_time,
                'predictions': predictions
            }
            
            print(f"  📈 统计结果:")
            print(f"    平均跳空: {gap_mean:.2f}%")
            print(f"    跳空标准差: {gap_std:.2f}%")
            print(f"    跳空范围: {gap_range:.2f}%")
            print(f"    平均用时: {avg_time:.2f}s")
    
    return results

def analyze_results(results):
    """分析结果"""
    print("\n📊 采样次数影响分析:")
    print("=" * 60)
    print(f"{'采样次数':<8} {'平均跳空':<10} {'标准差':<8} {'范围':<8} {'用时':<8} {'稳定性'}")
    print("-" * 60)
    
    for sample_count, data in results.items():
        stability = "优秀" if data['gap_std'] < 0.5 else "良好" if data['gap_std'] < 1.0 else "一般" if data['gap_std'] < 2.0 else "较差"
        
        print(f"{sample_count:<8} {data['gap_mean']:<10.2f} {data['gap_std']:<8.2f} {data['gap_range']:<8.2f} {data['avg_time']:<8.2f} {stability}")
    
    # 分析趋势
    print("\n🔍 趋势分析:")
    
    sample_counts = sorted(results.keys())
    stds = [results[sc]['gap_std'] for sc in sample_counts]
    times = [results[sc]['avg_time'] for sc in sample_counts]
    
    # 稳定性改善
    print("  稳定性改善:")
    for i in range(1, len(sample_counts)):
        prev_std = stds[i-1]
        curr_std = stds[i]
        improvement = (prev_std - curr_std) / prev_std * 100
        print(f"    {sample_counts[i-1]}→{sample_counts[i]}次: {improvement:+.1f}%")
    
    # 时间成本
    print("  时间成本:")
    base_time = times[0]
    for i, sc in enumerate(sample_counts):
        time_ratio = times[i] / base_time
        print(f"    {sc}次采样: {time_ratio:.1f}x 基准时间")
    
    # 效率分析
    print("  效率分析 (稳定性提升/时间成本):")
    for i in range(1, len(sample_counts)):
        stability_gain = (stds[0] - stds[i]) / stds[0]
        time_cost = times[i] / times[0] - 1
        efficiency = stability_gain / (time_cost + 0.01)  # 避免除零
        print(f"    {sample_counts[i]}次采样: 效率指数 {efficiency:.2f}")

def test_convergence():
    """测试采样收敛性"""
    print("\n🔄 测试采样收敛性...")
    
    service = get_prediction_service(use_mock=True)
    stock_code = '000001'
    
    # 逐步增加采样次数，观察收敛
    max_samples = 15
    convergence_data = []
    
    for n in range(1, max_samples + 1):
        try:
            result = service.predict_stock(
                stock_code, 
                lookback=30, 
                pred_len=3,
                sample_count=n
            )
            
            if result['success']:
                historical_data = result['data']['historical_data']
                pred_data = result['data']['predictions']
                
                last_close = historical_data[-1]['close']
                first_pred_open = pred_data[0]['open']
                gap_percent = (first_pred_open - last_close) / last_close * 100
                
                convergence_data.append({
                    'sample_count': n,
                    'gap_percent': gap_percent
                })
                
                print(f"  {n}次采样: 跳空{gap_percent:.2f}%")
        
        except Exception as e:
            print(f"  {n}次采样: 失败 - {str(e)}")
    
    # 分析收敛性
    if len(convergence_data) >= 5:
        print("\n📈 收敛性分析:")
        
        gaps = [d['gap_percent'] for d in convergence_data]
        
        # 计算滑动标准差
        window_size = 3
        moving_stds = []
        for i in range(window_size, len(gaps)):
            window_std = np.std(gaps[i-window_size:i])
            moving_stds.append(window_std)
        
        # 找到收敛点（标准差稳定）
        convergence_threshold = 0.1
        convergence_point = None
        
        for i in range(1, len(moving_stds)):
            if abs(moving_stds[i] - moving_stds[i-1]) < convergence_threshold:
                convergence_point = i + window_size
                break
        
        if convergence_point:
            print(f"  🎯 预测在{convergence_point}次采样后趋于收敛")
        else:
            print(f"  ⚠️ 在{max_samples}次采样内未观察到明显收敛")
        
        # 显示最后几次的稳定性
        if len(gaps) >= 5:
            last_5_std = np.std(gaps[-5:])
            print(f"  📊 最后5次采样标准差: {last_5_std:.3f}%")

def recommend_sampling():
    """给出采样建议"""
    print("\n💡 采样次数建议:")
    print("=" * 50)
    
    recommendations = [
        ("实时交易", "1次", "优先响应速度，可接受一定波动"),
        ("日常预测", "3次", "平衡准确度和效率的最佳选择"),
        ("重要决策", "5次", "提供更高的预测稳定性"),
        ("研究分析", "10次", "追求最高准确度，不考虑时间成本"),
        ("回测验证", "3-5次", "确保结果可靠性和可重复性")
    ]
    
    for scenario, count, reason in recommendations:
        print(f"  {scenario:<8}: {count:<6} - {reason}")

if __name__ == "__main__":
    print("🚀 开始采样次数影响测试...")
    
    # 主要测试
    results = test_sampling_impact()
    
    if results:
        # 分析结果
        analyze_results(results)
        
        # 收敛性测试
        test_convergence()
        
        # 给出建议
        recommend_sampling()
    
    print("\n✅ 测试完成！")
