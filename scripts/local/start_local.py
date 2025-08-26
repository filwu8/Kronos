#!/usr/bin/env python3
"""
RTX 5090 GPU加速股票预测系统 - 本地启动脚本
"""

import os
import sys
import time
import subprocess
import multiprocessing
from pathlib import Path

def check_environment():
    """检查运行环境"""
    print("🔍 检查运行环境...")
    
    # 检查Python版本
    python_version = sys.version_info
    if python_version.major < 3 or python_version.minor < 8:
        print(f"❌ Python版本过低: {python_version.major}.{python_version.minor}")
        print("   需要Python 3.8+")
        return False
    
    print(f"✅ Python版本: {python_version.major}.{python_version.minor}.{python_version.micro}")
    
    # 检查必要的包
    required_packages = [
        'torch', 'fastapi', 'streamlit', 'pandas', 'numpy', 'plotly'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}: 已安装")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package}: 未安装")
    
    if missing_packages:
        print(f"\n📦 安装缺失的包:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    return True

def check_gpu():
    """检查GPU状态"""
    print("\n🚀 检查GPU状态...")
    
    try:
        import torch
        print(f"PyTorch版本: {torch.__version__}")
        
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1024**3
            print(f"✅ GPU: {gpu_name}")
            print(f"✅ 显存: {gpu_memory:.1f} GB")
            
            # 测试GPU计算
            try:
                x = torch.randn(100, 100, device='cuda')
                y = torch.mm(x, x)
                print("✅ GPU计算测试通过")
                return True
            except Exception as e:
                print(f"❌ GPU计算测试失败: {str(e)}")
                return False
        else:
            print("⚠️ CUDA不可用，将使用CPU模式")
            return False
    except ImportError:
        print("❌ PyTorch未安装")
        return False

def setup_environment():
    """设置环境变量"""
    print("\n⚙️ 设置环境变量...")
    
    # 基础路径
    base_dir = Path(__file__).parent.parent.parent
    volumes_dir = base_dir / "volumes"
    
    # 设置环境变量
    env_vars = {
        "PYTHONPATH": f"{base_dir};{volumes_dir}",
        "DEPLOYMENT_MODE": "local",
        "API_HOST": "0.0.0.0",
        "API_PORT": "8000",
        "STREAMLIT_HOST": "0.0.0.0", 
        "STREAMLIT_PORT": "8501",
        "USE_MOCK": "false",
        "AUTO_DOWNLOAD_DATA": "true"
    }
    
    for key, value in env_vars.items():
        os.environ[key] = value
        print(f"   {key}={value}")

def start_api_service():
    """启动API服务"""
    print("🔌 启动API服务...")
    
    try:
        # 切换到项目根目录
        base_dir = Path(__file__).parent.parent.parent
        os.chdir(base_dir)
        
        # 启动uvicorn
        subprocess.run([
            sys.executable, "-m", "uvicorn",
            "app.api:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ])
    except KeyboardInterrupt:
        print("API服务已停止")
    except Exception as e:
        print(f"❌ API服务启动失败: {str(e)}")

def start_streamlit_service():
    """启动Streamlit服务"""
    print("🎨 启动Streamlit服务...")
    
    try:
        # 切换到项目根目录
        base_dir = Path(__file__).parent.parent.parent
        os.chdir(base_dir)
        
        # 启动streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "app/streamlit_app.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501"
        ])
    except KeyboardInterrupt:
        print("Streamlit服务已停止")
    except Exception as e:
        print(f"❌ Streamlit服务启动失败: {str(e)}")

def wait_for_services():
    """等待服务启动"""
    print("⏳ 等待服务启动...")
    
    import requests
    
    # 等待API服务
    for i in range(30):
        try:
            response = requests.get("http://localhost:8000/health", timeout=1)
            if response.status_code == 200:
                print("✅ API服务已启动")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("⚠️ API服务启动超时")
    
    # 等待Streamlit服务
    for i in range(30):
        try:
            response = requests.get("http://localhost:8501", timeout=1)
            if response.status_code == 200:
                print("✅ Streamlit服务已启动")
                break
        except:
            pass
        time.sleep(1)
    else:
        print("⚠️ Streamlit服务启动超时")

def main():
    """主函数"""
    print("🚀 RTX 5090 GPU加速股票预测系统 - 本地版本")
    print("=" * 60)
    
    # 1. 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请解决上述问题后重试")
        return
    
    # 2. 检查GPU
    gpu_available = check_gpu()
    if gpu_available:
        os.environ["DEVICE"] = "cuda"
    else:
        os.environ["DEVICE"] = "cpu"
    
    # 3. 设置环境
    setup_environment()
    
    print("\n🌐 服务地址:")
    print("   前端界面: http://localhost:8501")
    print("   API文档: http://localhost:8000/docs")
    print("   健康检查: http://localhost:8000/health")
    print("\n按 Ctrl+C 停止所有服务")
    
    try:
        # 4. 启动服务
        api_process = multiprocessing.Process(target=start_api_service)
        streamlit_process = multiprocessing.Process(target=start_streamlit_service)
        
        api_process.start()
        time.sleep(3)  # 等待API服务启动
        streamlit_process.start()
        
        # 5. 等待服务就绪
        wait_for_services()
        
        print("\n✅ 所有服务已启动!")
        print("🎉 系统已就绪，可以开始使用")
        
        # 6. 等待进程结束
        api_process.join()
        streamlit_process.join()
        
    except KeyboardInterrupt:
        print("\n🛑 正在停止服务...")
        if 'api_process' in locals() and api_process.is_alive():
            api_process.terminate()
            api_process.join()
        if 'streamlit_process' in locals() and streamlit_process.is_alive():
            streamlit_process.terminate()
            streamlit_process.join()
        print("✅ 所有服务已停止")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
