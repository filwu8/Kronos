#!/bin/bash
# 5年历史数据下载脚本

set -e

echo "🚀 开始下载5年以上A股历史数据"
echo "=================================="

# 检查Docker是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker未运行，请先启动Docker"
    exit 1
fi

# 创建必要的目录
echo "📁 创建数据存储目录..."
mkdir -p volumes/qlib_data
mkdir -p volumes/data
mkdir -p volumes/models
mkdir -p volumes/logs

# 设置目录权限
chmod 755 volumes/qlib_data
chmod 755 volumes/data
chmod 755 volumes/models

echo "✅ 目录创建完成"

# 方法1：在容器中下载数据
echo ""
echo "🎯 方法1：使用Docker容器下载数据"
echo "这将在隔离的容器环境中下载数据..."

# 构建镜像（如果需要）
echo "🔨 构建Docker镜像..."
docker-compose build

# 运行数据下载服务
echo "⬇️ 开始下载数据（这可能需要30分钟到2小时）..."
docker-compose --profile data-download up data-downloader

# 检查下载结果
echo ""
echo "🔍 检查下载结果..."

if [ -d "volumes/qlib_data/cn_data" ]; then
    echo "✅ Qlib数据下载成功"
    echo "📊 数据位置: volumes/qlib_data/cn_data"
    
    # 统计数据文件数量
    if [ -d "volumes/qlib_data/cn_data/features" ]; then
        stock_count=$(find volumes/qlib_data/cn_data/features -maxdepth 1 -type d | wc -l)
        echo "📈 股票数据文件数量: $((stock_count - 1))"
    fi
else
    echo "⚠️ Qlib数据下载可能失败，尝试备用方法..."
fi

if [ -d "volumes/data/akshare_data" ]; then
    csv_count=$(find volumes/data/akshare_data -name "*.csv" | wc -l)
    echo "✅ akshare数据下载成功，文件数量: $csv_count"
fi

if [ -d "volumes/data/tushare_data" ]; then
    csv_count=$(find volumes/data/tushare_data -name "*.csv" | wc -l)
    echo "✅ tushare数据下载成功，文件数量: $csv_count"
fi

# 方法2：本地下载（备用）
echo ""
echo "🎯 方法2：本地环境下载（备用方案）"
echo "如果容器下载失败，可以在本地环境运行..."

# 检查Python环境
if command -v python3 &> /dev/null; then
    echo "✅ Python3 可用"
    
    # 询问是否在本地运行
    read -p "是否在本地环境下载数据? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "📦 安装依赖..."
        pip3 install pyqlib akshare yfinance tushare pandas
        
        echo "⬇️ 开始本地下载..."
        python3 download_5year_data.py
        
        # 复制到volumes目录
        if [ -d "$HOME/.qlib/qlib_data" ]; then
            echo "📋 复制数据到volumes目录..."
            cp -r "$HOME/.qlib/qlib_data"/* volumes/qlib_data/
            echo "✅ 数据复制完成"
        fi
    fi
else
    echo "❌ Python3 不可用，跳过本地下载"
fi

# 验证最终结果
echo ""
echo "🔍 最终验证..."

total_size=0
if [ -d "volumes/qlib_data" ]; then
    qlib_size=$(du -sh volumes/qlib_data 2>/dev/null | cut -f1 || echo "0")
    echo "📊 Qlib数据大小: $qlib_size"
fi

if [ -d "volumes/data" ]; then
    data_size=$(du -sh volumes/data 2>/dev/null | cut -f1 || echo "0")
    echo "📊 其他数据大小: $data_size"
fi

# 创建数据验证脚本
cat > verify_data.py << 'EOF'
#!/usr/bin/env python3
"""验证下载的数据"""

import os
from pathlib import Path
import pandas as pd

def verify_qlib_data():
    """验证Qlib数据"""
    qlib_dir = Path("volumes/qlib_data/cn_data")
    
    if not qlib_dir.exists():
        print("❌ Qlib数据目录不存在")
        return False
    
    print(f"✅ Qlib数据目录: {qlib_dir}")
    
    # 检查关键目录
    essential_dirs = ['calendars', 'instruments', 'features']
    for dir_name in essential_dirs:
        dir_path = qlib_dir / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name} 目录存在")
        else:
            print(f"❌ {dir_name} 目录缺失")
            return False
    
    # 统计股票数量
    features_dir = qlib_dir / "features"
    if features_dir.exists():
        stock_dirs = [d for d in features_dir.iterdir() if d.is_dir()]
        print(f"📈 股票数据数量: {len(stock_dirs)}")
        
        if len(stock_dirs) > 0:
            print(f"样本股票: {[d.name for d in stock_dirs[:5]]}")
            return True
    
    return False

def verify_csv_data():
    """验证CSV数据"""
    data_dirs = [
        Path("volumes/data/akshare_data"),
        Path("volumes/data/tushare_data")
    ]
    
    total_files = 0
    for data_dir in data_dirs:
        if data_dir.exists():
            csv_files = list(data_dir.glob("*.csv"))
            print(f"✅ {data_dir.name}: {len(csv_files)} 个CSV文件")
            total_files += len(csv_files)
            
            # 检查第一个文件
            if csv_files:
                sample_file = csv_files[0]
                try:
                    df = pd.read_csv(sample_file)
                    print(f"   样本文件 {sample_file.name}: {len(df)} 条记录")
                except Exception as e:
                    print(f"   ❌ 读取 {sample_file.name} 失败: {e}")
    
    return total_files > 0

def main():
    print("🔍 验证下载的数据")
    print("=" * 40)
    
    qlib_ok = verify_qlib_data()
    csv_ok = verify_csv_data()
    
    print("\n📊 验证结果:")
    print(f"Qlib数据: {'✅ 可用' if qlib_ok else '❌ 不可用'}")
    print(f"CSV数据: {'✅ 可用' if csv_ok else '❌ 不可用'}")
    
    if qlib_ok or csv_ok:
        print("\n🎉 数据下载成功！")
        print("📋 后续步骤:")
        print("1. 下载Kronos预训练模型")
        print("2. 更新应用配置")
        print("3. 重启应用使用真实数据")
    else:
        print("\n❌ 数据下载失败")
        print("请检查网络连接或手动下载数据")

if __name__ == "__main__":
    main()
EOF

echo "📄 已创建数据验证脚本: verify_data.py"

# 运行验证
echo ""
echo "🔍 运行数据验证..."
if command -v python3 &> /dev/null; then
    python3 verify_data.py
else
    echo "⚠️ Python3不可用，请手动验证数据"
fi

echo ""
echo "=================================="
echo "🎉 数据下载流程完成！"
echo ""
echo "📋 下载结果:"
echo "- Qlib数据: volumes/qlib_data/"
echo "- CSV数据: volumes/data/"
echo "- 日志文件: volumes/logs/"
echo ""
echo "🔧 后续步骤:"
echo "1. 运行 python3 verify_data.py 验证数据"
echo "2. 下载Kronos模型: ./download_models.sh"
echo "3. 重启应用: docker-compose up -d"
echo ""
echo "📖 详细文档: QLIB_DATA_SETUP.md"
