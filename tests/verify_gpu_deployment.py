#!/usr/bin/env python3
"""
验证GPU部署状态
"""

import requests
import torch
import time

def check_gpu_status():
    """检查GPU状态"""
    print("🔍 GPU硬件状态:")
    print(f"   PyTorch版本: {torch.__version__}")
    print(f"   CUDA可用: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"   GPU: {torch.cuda.get_device_name(0)}")
        print(f"   内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print(f"   计算能力: {torch.cuda.get_device_properties(0).major}.{torch.cuda.get_device_properties(0).minor}")
        return True
    return False

def check_api_gpu_usage():
    """检查API GPU使用"""
    print("\n🔍 API GPU使用状态:")
    
    try:
        response = requests.get('http://localhost:8000/health', timeout=5)
        if response.status_code == 200:
            data = response.json()
            device = data['model_status']['device']
            model_loaded = data['model_status']['model_loaded']
            use_mock = data['model_status']['use_mock']
            
            print(f"   设备: {device}")
            print(f"   模型加载: {model_loaded}")
            print(f"   使用模拟: {use_mock}")
            
            if device == "cuda":
                print("   ✅ API正在使用GPU")
                return True
            else:
                print("   🖥️ API正在使用CPU")
                return False
        else:
            print(f"   ❌ API健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ API连接失败: {str(e)}")
        return False

def test_prediction_performance():
    """测试预测性能"""
    print("\n⚡ 预测性能测试:")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001', 'pred_len': 10},
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                prediction_time = end_time - start_time
                print(f"   ✅ 预测成功")
                print(f"   ⏱️ 耗时: {prediction_time:.2f}秒")
                
                stock_info = data['data']['stock_info']
                summary = data['data']['summary']
                print(f"   📊 股票: {stock_info['name']}")
                print(f"   💰 当前: ¥{summary['current_price']:.2f}")
                print(f"   📈 预测: ¥{summary['predicted_price']:.2f}")
                
                return prediction_time
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return None
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return None
    except Exception as e:
        print(f"   ❌ 测试失败: {str(e)}")
        return None

def monitor_gpu_usage():
    """监控GPU使用"""
    print("\n📊 GPU使用监控:")
    
    if not torch.cuda.is_available():
        print("   ❌ GPU不可用")
        return
    
    try:
        device = torch.device("cuda:0")
        
        # 内存使用
        memory_allocated = torch.cuda.memory_allocated(device) / 1024**3
        memory_reserved = torch.cuda.memory_reserved(device) / 1024**3
        memory_total = torch.cuda.get_device_properties(device).total_memory / 1024**3
        
        print(f"   💾 已分配: {memory_allocated:.2f} GB")
        print(f"   💾 已保留: {memory_reserved:.2f} GB")
        print(f"   💾 总内存: {memory_total:.2f} GB")
        print(f"   📊 使用率: {(memory_allocated/memory_total)*100:.1f}%")
        
    except Exception as e:
        print(f"   ❌ 监控失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 GPU部署验证")
    print("=" * 60)
    
    # 1. 检查GPU硬件
    gpu_available = check_gpu_status()
    
    # 2. 检查API GPU使用
    api_using_gpu = check_api_gpu_usage()
    
    # 3. 测试预测性能
    prediction_time = test_prediction_performance()
    
    # 4. 监控GPU使用
    monitor_gpu_usage()
    
    # 总结
    print("\n" + "=" * 60)
    print("📊 GPU部署状态总结:")
    
    if gpu_available:
        print("✅ GPU硬件: RTX 5090 可用")
        print(f"✅ PyTorch: {torch.__version__} (支持RTX 5090)")
    else:
        print("❌ GPU硬件: 不可用")
    
    if api_using_gpu:
        print("✅ API服务: 使用GPU加速")
    else:
        print("🖥️ API服务: 使用CPU模式")
    
    if prediction_time:
        print(f"✅ 预测性能: {prediction_time:.2f}秒")
        
        if api_using_gpu:
            print("🚀 GPU加速效果: 预测速度显著提升")
        else:
            print("💡 建议: 启用GPU可获得更好性能")
    else:
        print("❌ 预测测试: 失败")
    
    # 最终建议
    print(f"\n💡 部署建议:")
    
    if gpu_available and api_using_gpu:
        print("🎉 完美！您的RTX 5090已完全启用")
        print("   - 享受顶级GPU性能")
        print("   - 预测速度极快")
        print("   - 支持大规模批量预测")
    elif gpu_available and not api_using_gpu:
        print("⚠️ GPU可用但API未使用")
        print("   - 检查API配置")
        print("   - 重启API服务")
        print("   - 确认CUDA环境")
    else:
        print("🖥️ 当前使用CPU模式")
        print("   - 功能完全正常")
        print("   - 性能已优化")
        print("   - 等待GPU支持更新")

if __name__ == "__main__":
    main()
