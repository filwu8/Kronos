#!/usr/bin/env python3
"""
GPU性能测试
"""

import torch
import time
import numpy as np
import requests
from datetime import datetime

def test_gpu_availability():
    """测试GPU可用性"""
    print("🔍 GPU可用性检测")
    print("=" * 50)
    
    print(f"PyTorch版本: {torch.__version__}")
    print(f"CUDA可用: {torch.cuda.is_available()}")
    
    if torch.cuda.is_available():
        print(f"CUDA版本: {torch.version.cuda}")
        print(f"GPU数量: {torch.cuda.device_count()}")
        
        for i in range(torch.cuda.device_count()):
            props = torch.cuda.get_device_properties(i)
            print(f"GPU {i}: {props.name}")
            print(f"  内存: {props.total_memory / 1024**3:.1f} GB")
            print(f"  计算能力: {props.major}.{props.minor}")
            print(f"  多处理器: {props.multi_processor_count}")
        
        # 测试GPU内存
        try:
            device = torch.device("cuda:0")
            x = torch.randn(1000, 1000, device=device)
            y = torch.randn(1000, 1000, device=device)
            z = torch.mm(x, y)
            print(f"✅ GPU计算测试通过")
            
            # 清理内存
            del x, y, z
            torch.cuda.empty_cache()
            
        except Exception as e:
            print(f"❌ GPU计算测试失败: {str(e)}")
            return False
        
        return True
    else:
        print("❌ CUDA不可用")
        return False

def benchmark_cpu_vs_gpu():
    """CPU vs GPU性能对比"""
    print("\n⚡ CPU vs GPU性能对比")
    print("=" * 50)
    
    if not torch.cuda.is_available():
        print("❌ GPU不可用，跳过性能对比")
        return
    
    # 测试矩阵运算性能
    size = 2000
    iterations = 10
    
    print(f"测试: {size}x{size} 矩阵乘法，{iterations} 次迭代")
    
    # CPU测试
    print("\n🖥️ CPU性能测试...")
    cpu_times = []
    
    for i in range(iterations):
        start_time = time.time()
        
        x_cpu = torch.randn(size, size)
        y_cpu = torch.randn(size, size)
        z_cpu = torch.mm(x_cpu, y_cpu)
        
        end_time = time.time()
        cpu_times.append(end_time - start_time)
        
        if i == 0:
            print(f"  第1次: {cpu_times[0]:.3f}s")
    
    cpu_avg = np.mean(cpu_times)
    print(f"  平均时间: {cpu_avg:.3f}s")
    
    # GPU测试
    print("\n🚀 GPU性能测试...")
    gpu_times = []
    device = torch.device("cuda:0")
    
    # 预热GPU
    x_gpu = torch.randn(size, size, device=device)
    y_gpu = torch.randn(size, size, device=device)
    torch.mm(x_gpu, y_gpu)
    torch.cuda.synchronize()
    
    for i in range(iterations):
        torch.cuda.synchronize()
        start_time = time.time()
        
        x_gpu = torch.randn(size, size, device=device)
        y_gpu = torch.randn(size, size, device=device)
        z_gpu = torch.mm(x_gpu, y_gpu)
        
        torch.cuda.synchronize()
        end_time = time.time()
        gpu_times.append(end_time - start_time)
        
        if i == 0:
            print(f"  第1次: {gpu_times[0]:.3f}s")
    
    gpu_avg = np.mean(gpu_times)
    print(f"  平均时间: {gpu_avg:.3f}s")
    
    # 性能对比
    speedup = cpu_avg / gpu_avg
    print(f"\n📊 性能对比:")
    print(f"  CPU平均: {cpu_avg:.3f}s")
    print(f"  GPU平均: {gpu_avg:.3f}s")
    print(f"  加速比: {speedup:.1f}x")
    
    if speedup > 1:
        print(f"  🚀 GPU比CPU快 {speedup:.1f} 倍")
    else:
        print(f"  ⚠️ GPU性能未达预期")
    
    # 清理GPU内存
    torch.cuda.empty_cache()

def test_api_with_gpu():
    """测试API使用GPU"""
    print("\n🔌 测试API GPU使用")
    print("=" * 50)
    
    # 重启API服务以使用GPU配置
    print("请重启API服务以应用GPU配置...")
    print("命令: python -m uvicorn app.api:app --host 0.0.0.0 --port 8000")
    
    # 等待用户重启服务
    input("按回车键继续测试API...")
    
    try:
        # 测试健康检查
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            device = data['model_status']['device']
            print(f"✅ API服务运行正常")
            print(f"📱 使用设备: {device}")
            
            if device == "cuda":
                print(f"🚀 API正在使用GPU")
            else:
                print(f"🖥️ API正在使用CPU")
        else:
            print(f"❌ API健康检查失败: {response.status_code}")
            return False
        
        # 测试预测性能
        print(f"\n⏱️ 测试预测性能...")
        
        start_time = time.time()
        response = requests.post(
            "http://localhost:8000/predict",
            json={"stock_code": "000001", "pred_len": 10},
            timeout=60
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                prediction_time = end_time - start_time
                print(f"✅ 预测成功")
                print(f"⏱️ 预测耗时: {prediction_time:.2f}s")
                
                stock_info = data['data']['stock_info']
                summary = data['data']['summary']
                print(f"📊 股票: {stock_info['name']}")
                print(f"💰 当前价格: ¥{summary['current_price']:.2f}")
                print(f"📈 预测价格: ¥{summary['predicted_price']:.2f}")
                
                return True
            else:
                print(f"❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 预测请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ API测试失败: {str(e)}")
        return False

def monitor_gpu_usage():
    """监控GPU使用情况"""
    print("\n📊 GPU使用监控")
    print("=" * 50)
    
    if not torch.cuda.is_available():
        print("❌ GPU不可用")
        return
    
    try:
        # 获取GPU信息
        device = torch.device("cuda:0")
        
        # 内存使用情况
        memory_allocated = torch.cuda.memory_allocated(device) / 1024**3
        memory_reserved = torch.cuda.memory_reserved(device) / 1024**3
        memory_total = torch.cuda.get_device_properties(device).total_memory / 1024**3
        
        print(f"📱 GPU设备: {torch.cuda.get_device_name(device)}")
        print(f"💾 已分配内存: {memory_allocated:.2f} GB")
        print(f"💾 已保留内存: {memory_reserved:.2f} GB")
        print(f"💾 总内存: {memory_total:.2f} GB")
        print(f"📊 内存使用率: {(memory_allocated/memory_total)*100:.1f}%")
        
        # GPU利用率（需要nvidia-ml-py库）
        try:
            import pynvml
            pynvml.nvmlInit()
            handle = pynvml.nvmlDeviceGetHandleByIndex(0)
            utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
            temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
            
            print(f"🔥 GPU利用率: {utilization.gpu}%")
            print(f"🌡️ GPU温度: {temperature}°C")
            
        except ImportError:
            print("💡 安装 nvidia-ml-py 可获取更详细的GPU信息")
            print("   命令: pip install nvidia-ml-py")
        
    except Exception as e:
        print(f"❌ GPU监控失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 GPU性能测试和配置")
    print("=" * 60)
    
    # 1. 检测GPU
    gpu_available = test_gpu_availability()
    
    if gpu_available:
        # 2. 性能对比
        benchmark_cpu_vs_gpu()
        
        # 3. GPU监控
        monitor_gpu_usage()
        
        # 4. API测试
        test_api_with_gpu()
        
        print("\n" + "=" * 60)
        print("🎉 GPU配置完成！")
        
        print(f"\n✅ GPU配置总结:")
        print(f"   🚀 GPU型号: {torch.cuda.get_device_name(0)}")
        print(f"   💾 GPU内存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
        print(f"   ⚡ CUDA版本: {torch.version.cuda}")
        print(f"   📦 PyTorch版本: {torch.__version__}")
        
        print(f"\n🔧 使用GPU的好处:")
        print(f"   ⚡ 预测速度显著提升")
        print(f"   🧠 支持更大的模型")
        print(f"   📊 并行处理能力强")
        print(f"   🚀 适合批量预测")
        
        print(f"\n💡 下一步:")
        print(f"   1. 重启API服务应用GPU配置")
        print(f"   2. 测试预测性能提升")
        print(f"   3. 监控GPU使用情况")
        
    else:
        print("\n❌ GPU配置失败")
        print("请检查CUDA安装和PyTorch版本")

if __name__ == "__main__":
    main()
