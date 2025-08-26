#!/usr/bin/env python3
"""
测试RTX 5090 GPU支持
"""

import torch
import time

def test_rtx5090():
    """测试RTX 5090支持"""
    print("🚀 测试RTX 5090 GPU支持")
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
        
        # 测试GPU计算
        print("\n🧪 GPU计算测试:")
        try:
            device = torch.device("cuda:0")
            
            # 简单测试
            print("  测试1: 基础矩阵运算...")
            x = torch.randn(100, 100, device=device)
            y = torch.randn(100, 100, device=device)
            z = torch.mm(x, y)
            print("  ✅ 基础运算成功")
            
            # 性能测试
            print("  测试2: 性能测试...")
            size = 2000
            start_time = time.time()
            
            x = torch.randn(size, size, device=device)
            y = torch.randn(size, size, device=device)
            z = torch.mm(x, y)
            torch.cuda.synchronize()
            
            end_time = time.time()
            gpu_time = end_time - start_time
            
            print(f"  ✅ {size}x{size} 矩阵乘法: {gpu_time:.3f}s")
            
            # 内存测试
            print("  测试3: 内存使用...")
            memory_allocated = torch.cuda.memory_allocated(device) / 1024**3
            memory_reserved = torch.cuda.memory_reserved(device) / 1024**3
            memory_total = torch.cuda.get_device_properties(device).total_memory / 1024**3
            
            print(f"  已分配: {memory_allocated:.2f} GB")
            print(f"  已保留: {memory_reserved:.2f} GB")
            print(f"  总内存: {memory_total:.2f} GB")
            print(f"  使用率: {(memory_allocated/memory_total)*100:.1f}%")
            
            # 清理
            del x, y, z
            torch.cuda.empty_cache()
            
            print("\n🎉 RTX 5090 GPU测试全部通过！")
            return True
            
        except Exception as e:
            print(f"  ❌ GPU测试失败: {str(e)}")
            return False
    else:
        print("❌ CUDA不可用")
        return False

if __name__ == "__main__":
    success = test_rtx5090()
    
    if success:
        print("\n✅ RTX 5090已就绪！")
        print("现在可以重启API服务使用GPU加速")
    else:
        print("\n❌ GPU测试失败")
        print("将继续使用CPU模式")
