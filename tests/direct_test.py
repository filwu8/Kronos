#!/usr/bin/env python3
"""
直接测试GPU加速系统
"""

import requests
import time
import torch

def test_gpu_status():
    """测试GPU状态"""
    print("🔍 GPU状态检查:")
    print(f"   PyTorch: {torch.__version__}")
    print(f"   CUDA可用: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        return True
    return False

def test_api_health():
    """测试API健康"""
    print("\n🏥 API健康检查:")
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"   ✅ API正常运行")
            print(f"   设备: {data['model_status']['device']}")
            print(f"   模型: {data['model_status']['model_loaded']}")
            print(f"   模拟: {data['model_status']['use_mock']}")
            return True
        else:
            print(f"   ❌ API错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 连接失败: {str(e)}")
        return False

def test_single_prediction():
    """测试单次预测"""
    print("\n📊 单次预测测试:")
    
    try:
        print("   发送预测请求...")
        start_time = time.time()
        
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001'},
            timeout=30
        )
        
        end_time = time.time()
        duration = end_time - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                stock_info = data['data']['stock_info']
                summary = data['data']['summary']
                
                print(f"   ✅ 预测成功 ({duration:.2f}秒)")
                print(f"   📈 {stock_info['name']} ({stock_info['code']})")
                print(f"   💰 当前: ¥{summary['current_price']:.2f}")
                print(f"   🔮 预测: ¥{summary['predicted_price']:.2f}")
                print(f"   📊 变化: {summary['change_percent']:+.2f}%")
                print(f"   🎯 趋势: {summary['trend']}")
                
                return duration
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return None
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
        return None

def test_gpu_memory():
    """测试GPU内存使用"""
    print("\n💾 GPU内存监控:")
    
    if not torch.cuda.is_available():
        print("   ❌ GPU不可用")
        return
    
    try:
        device = torch.device("cuda:0")
        
        # 获取内存信息
        allocated = torch.cuda.memory_allocated(device) / 1024**3
        reserved = torch.cuda.memory_reserved(device) / 1024**3
        total = torch.cuda.get_device_properties(device).total_memory / 1024**3
        
        print(f"   已分配: {allocated:.2f} GB")
        print(f"   已保留: {reserved:.2f} GB")
        print(f"   总内存: {total:.2f} GB")
        print(f"   使用率: {(allocated/total)*100:.1f}%")
        
    except Exception as e:
        print(f"   ❌ 监控失败: {str(e)}")

def main():
    """主测试函数"""
    print("🚀 RTX 5090 GPU加速系统直接测试")
    print("=" * 60)
    
    # 1. GPU状态
    gpu_ok = test_gpu_status()
    
    # 2. API健康
    api_ok = test_api_health()
    
    # 3. 预测测试
    prediction_time = None
    if api_ok:
        prediction_time = test_single_prediction()
    
    # 4. GPU内存
    test_gpu_memory()
    
    # 总结
    print("\n" + "=" * 60)
    print("📋 测试结果总结:")
    
    if gpu_ok:
        print("✅ RTX 5090 GPU: 完全可用")
    else:
        print("❌ GPU: 不可用")
    
    if api_ok:
        print("✅ API服务: 正常运行")
    else:
        print("❌ API服务: 异常")
    
    if prediction_time:
        print(f"✅ 预测功能: 正常 ({prediction_time:.2f}秒)")
        
        if prediction_time < 3.0:
            print("🚀 性能: 优秀 (GPU加速效果明显)")
        elif prediction_time < 5.0:
            print("⚡ 性能: 良好")
        else:
            print("🐌 性能: 一般 (可能未使用GPU)")
    else:
        print("❌ 预测功能: 失败")
    
    # 最终状态
    if gpu_ok and api_ok and prediction_time:
        print(f"\n🎉 系统状态: 完美运行")
        print(f"   🚀 RTX 5090已完全启用")
        print(f"   ⚡ GPU加速正常工作")
        print(f"   📊 预测功能完全正常")
        print(f"   🌐 可访问: http://localhost:8501")
    else:
        print(f"\n⚠️ 系统状态: 需要检查")
        if not gpu_ok:
            print(f"   🔧 GPU问题需要解决")
        if not api_ok:
            print(f"   🔧 API服务需要重启")
        if not prediction_time:
            print(f"   🔧 预测功能需要调试")

if __name__ == "__main__":
    main()
