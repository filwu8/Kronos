#!/usr/bin/env python3
"""
简化启动脚本
用于本地开发和测试
"""

import subprocess
import sys
import time
import os
import signal
import threading
from pathlib import Path

def run_command(cmd, name, log_file=None):
    """运行命令"""
    print(f"🚀 启动 {name}...")
    
    if log_file:
        with open(log_file, 'w') as f:
            process = subprocess.Popen(
                cmd, 
                shell=True, 
                stdout=f, 
                stderr=subprocess.STDOUT,
                preexec_fn=os.setsid if os.name != 'nt' else None
            )
    else:
        process = subprocess.Popen(
            cmd, 
            shell=True,
            preexec_fn=os.setsid if os.name != 'nt' else None
        )
    
    return process

def check_service(url, name, timeout=30):
    """检查服务是否启动"""
    import requests
    
    print(f"⏳ 等待 {name} 启动...")
    
    for i in range(timeout):
        try:
            response = requests.get(url, timeout=2)
            if response.status_code == 200:
                print(f"✅ {name} 启动成功")
                return True
        except:
            pass
        time.sleep(1)
    
    print(f"❌ {name} 启动超时")
    return False

def main():
    """主函数"""
    print("🚀 Kronos股票预测应用启动器")
    print("=" * 40)
    
    # 检查Python环境
    if sys.version_info < (3, 8):
        print("❌ 需要Python 3.8或更高版本")
        return 1
    
    # 检查依赖
    try:
        import streamlit
        import fastapi
        import uvicorn
        print("✅ 依赖检查通过")
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行: pip install -r app/requirements.txt")
        return 1
    
    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    # 设置环境变量
    os.environ['PYTHONPATH'] = str(Path.cwd())
    os.environ['USE_MOCK_MODEL'] = 'true'
    os.environ['DEVICE'] = 'cpu'
    
    processes = []
    
    try:
        # 启动API服务
        api_cmd = "python -m uvicorn app.api:app --host 0.0.0.0 --port 8000 --reload"
        api_process = run_command(api_cmd, "API服务", "logs/api.log")
        processes.append(("API", api_process))
        
        # 等待API启动
        if not check_service("http://localhost:8000/health", "API服务"):
            print("❌ API服务启动失败")
            return 1
        
        # 启动前端服务
        frontend_cmd = "python -m streamlit run app/streamlit_app.py --server.address 0.0.0.0 --server.port 8501"
        frontend_process = run_command(frontend_cmd, "前端服务", "logs/frontend.log")
        processes.append(("前端", frontend_process))
        
        # 等待前端启动
        if not check_service("http://localhost:8501", "前端服务"):
            print("❌ 前端服务启动失败")
            return 1
        
        print("\n🎉 应用启动成功!")
        print("📊 访问地址:")
        print("   前端界面: http://localhost:8501")
        print("   API文档: http://localhost:8000/docs")
        print("   健康检查: http://localhost:8000/health")
        print("\n按 Ctrl+C 停止服务")
        
        # 运行测试
        print("\n🔍 运行基础测试...")
        test_cmd = "python test_app.py"
        test_process = subprocess.run(test_cmd, shell=True, capture_output=True, text=True)
        
        if test_process.returncode == 0:
            print("✅ 基础测试通过")
        else:
            print("⚠️ 部分测试失败，但服务仍在运行")
        
        # 保持运行
        while True:
            time.sleep(1)
            
            # 检查进程状态
            for name, process in processes:
                if process.poll() is not None:
                    print(f"❌ {name} 进程意外退出")
                    return 1
    
    except KeyboardInterrupt:
        print("\n🛑 收到停止信号...")
    
    except Exception as e:
        print(f"❌ 启动失败: {str(e)}")
        return 1
    
    finally:
        # 清理进程
        print("🧹 清理进程...")
        for name, process in processes:
            try:
                if os.name != 'nt':
                    os.killpg(os.getpgid(process.pid), signal.SIGTERM)
                else:
                    process.terminate()
                print(f"✅ {name} 已停止")
            except:
                pass
    
    print("👋 应用已停止")
    return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
