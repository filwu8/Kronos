#!/usr/bin/env python3
"""
Qlib数据自动化准备脚本
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import requests
import zipfile
import tempfile

def run_command(cmd, description=""):
    """运行命令并处理错误"""
    print(f"🔄 {description}")
    print(f"执行命令: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=3600)
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(f"输出: {result.stdout}")
            return True
        else:
            print(f"❌ {description} 失败")
            print(f"错误: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} 超时")
        return False
    except Exception as e:
        print(f"❌ {description} 异常: {str(e)}")
        return False

def check_python_packages():
    """检查Python包依赖"""
    print("\n📦 检查Python包依赖...")
    
    required_packages = [
        'numpy', 'pandas', 'torch', 'requests'
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} 已安装")
        except ImportError:
            print(f"❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"⚠️ 缺少包: {missing_packages}")
        return False
    
    return True

def install_qlib():
    """安装Qlib"""
    print("\n📥 安装Qlib...")
    
    # 检查是否已安装
    try:
        import qlib
        print("✅ Qlib已安装")
        return True
    except ImportError:
        pass
    
    # 安装Qlib
    success = run_command("pip install pyqlib", "安装pyqlib")
    
    if success:
        try:
            import qlib
            print("✅ Qlib安装验证成功")
            return True
        except ImportError:
            print("❌ Qlib安装验证失败")
            return False
    
    return False

def setup_qlib_data_directory():
    """设置Qlib数据目录"""
    print("\n📁 设置Qlib数据目录...")
    
    # 创建数据目录
    data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"✅ 数据目录创建: {data_dir}")
    return str(data_dir)

def download_qlib_data_official():
    """使用官方方法下载Qlib数据"""
    print("\n⬇️ 使用官方方法下载Qlib数据...")
    
    cmd = "python -m qlib.run.get_data qlib_data --target_dir ~/.qlib/qlib_data/cn_data --region cn"
    success = run_command(cmd, "下载官方Qlib数据")
    
    return success

def download_qlib_data_alternative():
    """备用方法下载Qlib数据"""
    print("\n⬇️ 使用备用方法下载Qlib数据...")
    
    # 这里可以添加其他数据源的下载逻辑
    # 例如从其他镜像站点下载
    
    print("⚠️ 备用下载方法需要手动实现")
    print("请参考以下链接手动下载数据:")
    print("- https://github.com/microsoft/qlib/blob/main/scripts/data_collector/yahoo/README.md")
    print("- https://qlib.readthedocs.io/en/latest/component/data.html")
    
    return False

def verify_qlib_data():
    """验证Qlib数据"""
    print("\n🔍 验证Qlib数据...")
    
    try:
        import qlib
        from qlib.config import REG_CN
        from qlib.data import D
        
        # 初始化Qlib
        data_path = str(Path.home() / ".qlib" / "qlib_data" / "cn_data")
        qlib.init(provider_uri=data_path, region=REG_CN)
        
        # 测试数据访问
        instruments = D.instruments('csi300')
        print(f"✅ CSI300成分股数量: {len(instruments)}")
        
        if len(instruments) > 0:
            # 测试获取单只股票数据
            sample_stock = instruments[0]
            data = D.features([sample_stock], ['$close', '$volume'], 
                            start_time='2023-01-01', end_time='2023-12-31')
            print(f"✅ 样本股票 {sample_stock} 数据形状: {data.shape}")
            
            if len(data) > 0:
                print("✅ Qlib数据验证成功")
                return True
        
        print("❌ Qlib数据验证失败：数据为空")
        return False
        
    except Exception as e:
        print(f"❌ Qlib数据验证失败: {str(e)}")
        return False

def update_requirements():
    """更新requirements.txt添加Qlib"""
    print("\n📝 更新requirements.txt...")
    
    req_file = Path("app/requirements.txt")
    if not req_file.exists():
        print("❌ requirements.txt文件不存在")
        return False
    
    # 读取现有内容
    with open(req_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否已包含qlib
    if 'qlib' in content.lower():
        print("✅ requirements.txt已包含qlib")
        return True
    
    # 添加qlib
    with open(req_file, 'a', encoding='utf-8') as f:
        f.write("\n# Qlib数据处理\n")
        f.write("pyqlib>=0.9.0\n")
    
    print("✅ 已添加pyqlib到requirements.txt")
    return True

def create_qlib_test_script():
    """创建Qlib测试脚本"""
    print("\n📄 创建Qlib测试脚本...")
    
    test_script = """#!/usr/bin/env python3
\"\"\"
Qlib数据测试脚本
\"\"\"

import qlib
from qlib.config import REG_CN
from qlib.data import D
from pathlib import Path

def test_qlib_data():
    \"\"\"测试Qlib数据\"\"\"
    print("🔍 测试Qlib数据访问...")
    
    try:
        # 初始化Qlib
        data_path = str(Path.home() / ".qlib" / "qlib_data" / "cn_data")
        qlib.init(provider_uri=data_path, region=REG_CN)
        print(f"✅ Qlib初始化成功: {data_path}")
        
        # 获取股票列表
        instruments = D.instruments('csi300')
        print(f"✅ CSI300成分股数量: {len(instruments)}")
        
        if len(instruments) > 0:
            # 显示前10只股票
            print(f"前10只股票: {instruments[:10]}")
            
            # 测试数据获取
            sample_stocks = instruments[:3]
            fields = ['$open', '$high', '$low', '$close', '$volume']
            
            data = D.features(sample_stocks, fields, 
                            start_time='2023-01-01', end_time='2023-12-31')
            
            print(f"✅ 数据获取成功")
            print(f"数据形状: {data.shape}")
            print(f"数据列: {data.columns.tolist()}")
            print(f"数据时间范围: {data.index.min()} 到 {data.index.max()}")
            
            # 显示样本数据
            print("\\n📊 样本数据:")
            print(data.head())
            
            return True
        else:
            print("❌ 没有找到股票数据")
            return False
            
    except Exception as e:
        print(f"❌ Qlib测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_qlib_data()
"""
    
    with open("test_qlib_data.py", 'w', encoding='utf-8') as f:
        f.write(test_script)
    
    print("✅ 已创建test_qlib_data.py")
    return True

def main():
    """主函数"""
    print("🚀 Qlib数据自动化准备开始")
    print("=" * 50)
    
    # 步骤1：检查Python环境
    if not check_python_packages():
        print("❌ Python环境检查失败，请先安装必要的包")
        return 1
    
    # 步骤2：安装Qlib
    if not install_qlib():
        print("❌ Qlib安装失败")
        return 1
    
    # 步骤3：设置数据目录
    data_dir = setup_qlib_data_directory()
    
    # 步骤4：下载数据
    print("\n⬇️ 开始下载Qlib数据...")
    print("⚠️ 注意：数据下载可能需要较长时间（30分钟到几小时）")
    
    # 尝试官方方法
    if download_qlib_data_official():
        print("✅ 官方方法下载成功")
    else:
        print("❌ 官方方法下载失败，尝试备用方法...")
        if not download_qlib_data_alternative():
            print("❌ 所有下载方法都失败")
            print("请手动下载数据，参考QLIB_DATA_SETUP.md")
            return 1
    
    # 步骤5：验证数据
    if not verify_qlib_data():
        print("❌ 数据验证失败")
        return 1
    
    # 步骤6：更新配置
    update_requirements()
    create_qlib_test_script()
    
    print("\n" + "=" * 50)
    print("🎉 Qlib数据准备完成！")
    print("\n📋 后续步骤:")
    print("1. 运行 python test_qlib_data.py 验证数据")
    print("2. 下载Kronos预训练模型")
    print("3. 更新应用配置以使用真实模型")
    print("4. 参考 QLIB_DATA_SETUP.md 进行完整集成")
    
    print(f"\n📁 数据位置: {data_dir}")
    print("📄 测试脚本: test_qlib_data.py")
    print("📖 详细指南: QLIB_DATA_SETUP.md")
    
    return 0

if __name__ == "__main__":
    exit(main())
"""
