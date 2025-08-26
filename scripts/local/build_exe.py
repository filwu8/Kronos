#!/usr/bin/env python3
"""
本地exe构建脚本
支持RTX 5090 GPU加速的股票预测系统
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def install_build_dependencies():
    """安装构建依赖"""
    print("📦 安装构建依赖...")
    
    dependencies = [
        "pyinstaller",
        "auto-py-to-exe",
        "cx_Freeze"
    ]
    
    for dep in dependencies:
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", dep], check=True)
            print(f"   ✅ {dep} 安装成功")
        except subprocess.CalledProcessError:
            print(f"   ❌ {dep} 安装失败")

def prepare_build_environment():
    """准备构建环境"""
    print("🔧 准备构建环境...")
    
    # 创建构建目录
    build_dir = Path("build")
    dist_dir = Path("dist")
    
    if build_dir.exists():
        shutil.rmtree(build_dir)
    if dist_dir.exists():
        shutil.rmtree(dist_dir)
    
    build_dir.mkdir(exist_ok=True)
    dist_dir.mkdir(exist_ok=True)
    
    print("   ✅ 构建目录已准备")

def create_main_entry():
    """创建主入口文件"""
    print("📝 创建主入口文件...")
    
    main_content = '''#!/usr/bin/env python3
"""
RTX 5090 GPU加速股票预测系统 - 本地exe版本
主入口文件
"""

import sys
import os
import multiprocessing
import subprocess
import time
from pathlib import Path

# 添加应用路径
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))
sys.path.insert(0, str(app_dir / "volumes"))

def check_gpu_support():
    """检查GPU支持"""
    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            print(f"✅ 检测到GPU: {gpu_name}")
            return True
        else:
            print("⚠️ 未检测到GPU，使用CPU模式")
            return False
    except ImportError:
        print("❌ PyTorch未安装")
        return False

def start_api_service():
    """启动API服务"""
    print("🚀 启动API服务...")
    try:
        import uvicorn
        from app.api import app
        
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            log_level="info"
        )
    except Exception as e:
        print(f"❌ API服务启动失败: {str(e)}")

def start_streamlit_service():
    """启动Streamlit服务"""
    print("🎨 启动Streamlit服务...")
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run",
            "app/streamlit_app.py",
            "--server.address", "0.0.0.0",
            "--server.port", "8501"
        ])
    except Exception as e:
        print(f"❌ Streamlit服务启动失败: {str(e)}")

def main():
    """主函数"""
    print("🚀 RTX 5090 GPU加速股票预测系统")
    print("=" * 50)
    
    # 检查GPU支持
    gpu_available = check_gpu_support()
    
    # 设置环境变量
    os.environ["DEPLOYMENT_MODE"] = "exe"
    if gpu_available:
        os.environ["DEVICE"] = "cuda"
    else:
        os.environ["DEVICE"] = "cpu"
    
    print("\\n🌐 服务地址:")
    print("   前端界面: http://localhost:8501")
    print("   API文档: http://localhost:8000/docs")
    print("\\n按 Ctrl+C 停止服务")
    
    try:
        # 使用多进程启动服务
        api_process = multiprocessing.Process(target=start_api_service)
        streamlit_process = multiprocessing.Process(target=start_streamlit_service)
        
        api_process.start()
        time.sleep(3)  # 等待API服务启动
        streamlit_process.start()
        
        # 等待进程结束
        api_process.join()
        streamlit_process.join()
        
    except KeyboardInterrupt:
        print("\\n🛑 正在停止服务...")
        if 'api_process' in locals():
            api_process.terminate()
        if 'streamlit_process' in locals():
            streamlit_process.terminate()
        print("✅ 服务已停止")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
'''
    
    with open("main.py", "w", encoding="utf-8") as f:
        f.write(main_content)
    
    print("   ✅ 主入口文件已创建")

def create_pyinstaller_spec():
    """创建PyInstaller配置文件"""
    print("⚙️ 创建PyInstaller配置...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app', 'app'),
        ('volumes/config', 'volumes/config'),
        ('volumes/data', 'volumes/data'),
    ],
    hiddenimports=[
        'uvicorn',
        'fastapi',
        'streamlit',
        'torch',
        'pandas',
        'numpy',
        'plotly',
        'akshare',
        'requests',
        'pydantic',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='KronosGPU',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico' if os.path.exists('assets/icon.ico') else None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='KronosGPU',
)
'''
    
    with open("kronos.spec", "w", encoding="utf-8") as f:
        f.write(spec_content)
    
    print("   ✅ PyInstaller配置已创建")

def build_executable():
    """构建可执行文件"""
    print("🔨 开始构建可执行文件...")
    
    try:
        # 使用PyInstaller构建
        subprocess.run([
            "pyinstaller",
            "--clean",
            "--noconfirm",
            "kronos.spec"
        ], check=True)
        
        print("   ✅ 可执行文件构建成功")
        print(f"   📁 输出目录: {Path('dist/KronosGPU').absolute()}")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ 构建失败: {str(e)}")
        return False

def create_installer():
    """创建安装程序"""
    print("📦 创建安装程序...")
    
    # 这里可以添加NSIS或其他安装程序创建逻辑
    print("   💡 可以使用NSIS创建Windows安装程序")
    print("   💡 可以使用Inno Setup创建安装向导")

def main():
    """主构建流程"""
    print("🏗️ RTX 5090 GPU股票预测系统 - exe构建工具")
    print("=" * 60)
    
    # 1. 安装依赖
    install_build_dependencies()
    
    # 2. 准备环境
    prepare_build_environment()
    
    # 3. 创建入口文件
    create_main_entry()
    
    # 4. 创建配置文件
    create_pyinstaller_spec()
    
    # 5. 构建可执行文件
    success = build_executable()
    
    if success:
        # 6. 创建安装程序
        create_installer()
        
        print("\\n🎉 构建完成!")
        print("📁 可执行文件位置: dist/KronosGPU/")
        print("🚀 运行: dist/KronosGPU/KronosGPU.exe")
    else:
        print("\\n❌ 构建失败")

if __name__ == "__main__":
    main()
'''
