#!/bin/bash
# Kronos模型下载脚本

set -e

echo "🤖 开始下载Kronos预训练模型"
echo "============================="

# 检查git和git-lfs
if ! command -v git &> /dev/null; then
    echo "❌ Git未安装，请先安装Git"
    exit 1
fi

# 检查git-lfs
if ! git lfs version &> /dev/null; then
    echo "📦 安装Git LFS..."
    
    # 根据操作系统安装git-lfs
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        if command -v apt-get &> /dev/null; then
            sudo apt-get update && sudo apt-get install -y git-lfs
        elif command -v yum &> /dev/null; then
            sudo yum install -y git-lfs
        else
            echo "❌ 无法自动安装git-lfs，请手动安装"
            exit 1
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew install git-lfs
        else
            echo "❌ 请先安装Homebrew或手动安装git-lfs"
            exit 1
        fi
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "win32" ]]; then
        # Windows
        echo "❌ 请手动安装Git LFS: https://git-lfs.github.io/"
        exit 1
    fi
    
    # 初始化git-lfs
    git lfs install
    echo "✅ Git LFS安装完成"
fi

# 创建模型目录
echo "📁 创建模型目录..."
mkdir -p volumes/models
cd volumes/models

# 下载Kronos-Tokenizer-base
echo ""
echo "⬇️ 下载Kronos-Tokenizer-base..."
if [ ! -d "Kronos-Tokenizer-base" ]; then
    echo "正在克隆Kronos-Tokenizer-base仓库..."
    git clone https://huggingface.co/Kronos/Kronos-Tokenizer-base
    
    if [ $? -eq 0 ]; then
        echo "✅ Kronos-Tokenizer-base下载成功"
    else
        echo "❌ Kronos-Tokenizer-base下载失败"
        
        # 尝试备用方法
        echo "🔄 尝试备用下载方法..."
        rm -rf Kronos-Tokenizer-base
        
        # 使用wget下载（如果可用）
        if command -v wget &> /dev/null; then
            echo "使用wget下载..."
            mkdir -p Kronos-Tokenizer-base
            cd Kronos-Tokenizer-base
            
            # 下载主要文件
            wget -c https://huggingface.co/Kronos/Kronos-Tokenizer-base/resolve/main/config.json
            wget -c https://huggingface.co/Kronos/Kronos-Tokenizer-base/resolve/main/pytorch_model.bin
            wget -c https://huggingface.co/Kronos/Kronos-Tokenizer-base/resolve/main/tokenizer.json
            wget -c https://huggingface.co/Kronos/Kronos-Tokenizer-base/resolve/main/tokenizer_config.json
            
            cd ..
            echo "✅ Kronos-Tokenizer-base备用下载完成"
        else
            echo "❌ 备用下载也失败，请手动下载"
        fi
    fi
else
    echo "✅ Kronos-Tokenizer-base已存在"
fi

# 下载Kronos-small
echo ""
echo "⬇️ 下载Kronos-small..."
if [ ! -d "Kronos-small" ]; then
    echo "正在克隆Kronos-small仓库..."
    git clone https://huggingface.co/Kronos/Kronos-small
    
    if [ $? -eq 0 ]; then
        echo "✅ Kronos-small下载成功"
    else
        echo "❌ Kronos-small下载失败"
        
        # 尝试备用方法
        echo "🔄 尝试备用下载方法..."
        rm -rf Kronos-small
        
        if command -v wget &> /dev/null; then
            echo "使用wget下载..."
            mkdir -p Kronos-small
            cd Kronos-small
            
            # 下载主要文件
            wget -c https://huggingface.co/Kronos/Kronos-small/resolve/main/config.json
            wget -c https://huggingface.co/Kronos/Kronos-small/resolve/main/pytorch_model.bin
            wget -c https://huggingface.co/Kronos/Kronos-small/resolve/main/generation_config.json
            
            cd ..
            echo "✅ Kronos-small备用下载完成"
        else
            echo "❌ 备用下载也失败，请手动下载"
        fi
    fi
else
    echo "✅ Kronos-small已存在"
fi

# 返回根目录
cd ../..

# 验证下载的模型
echo ""
echo "🔍 验证下载的模型..."

check_model() {
    local model_dir=$1
    local model_name=$2
    
    if [ -d "volumes/models/$model_dir" ]; then
        echo "✅ $model_name 目录存在"
        
        # 检查关键文件
        local files=("config.json" "pytorch_model.bin")
        local missing_files=()
        
        for file in "${files[@]}"; do
            if [ -f "volumes/models/$model_dir/$file" ]; then
                echo "  ✅ $file 存在"
            else
                echo "  ❌ $file 缺失"
                missing_files+=("$file")
            fi
        done
        
        if [ ${#missing_files[@]} -eq 0 ]; then
            echo "  🎉 $model_name 完整"
            return 0
        else
            echo "  ⚠️ $model_name 不完整，缺少: ${missing_files[*]}"
            return 1
        fi
    else
        echo "❌ $model_name 目录不存在"
        return 1
    fi
}

tokenizer_ok=false
predictor_ok=false

if check_model "Kronos-Tokenizer-base" "Kronos-Tokenizer-base"; then
    tokenizer_ok=true
fi

if check_model "Kronos-small" "Kronos-small"; then
    predictor_ok=true
fi

# 更新配置文件
echo ""
echo "📝 更新配置文件..."

# 更新finetune/config.py
if [ -f "finetune/config.py" ]; then
    echo "更新 finetune/config.py..."
    
    # 备份原文件
    cp finetune/config.py finetune/config.py.backup
    
    # 更新模型路径
    sed -i.tmp 's|self.pretrained_tokenizer_path = ".*"|self.pretrained_tokenizer_path = "./volumes/models/Kronos-Tokenizer-base"|g' finetune/config.py
    sed -i.tmp 's|self.pretrained_predictor_path = ".*"|self.pretrained_predictor_path = "./volumes/models/Kronos-small"|g' finetune/config.py
    
    # 清理临时文件
    rm -f finetune/config.py.tmp
    
    echo "✅ finetune/config.py 更新完成"
else
    echo "⚠️ finetune/config.py 不存在，跳过更新"
fi

# 创建模型测试脚本
cat > test_models.py << 'EOF'
#!/usr/bin/env python3
"""测试Kronos模型加载"""

import os
import sys
from pathlib import Path

def test_model_loading():
    """测试模型加载"""
    print("🤖 测试Kronos模型加载")
    print("=" * 40)
    
    model_dir = Path("volumes/models")
    
    # 检查模型目录
    tokenizer_dir = model_dir / "Kronos-Tokenizer-base"
    predictor_dir = model_dir / "Kronos-small"
    
    print(f"📁 模型目录: {model_dir}")
    print(f"🔤 Tokenizer: {tokenizer_dir}")
    print(f"🧠 Predictor: {predictor_dir}")
    
    # 检查文件
    models_info = [
        (tokenizer_dir, "Kronos-Tokenizer-base"),
        (predictor_dir, "Kronos-small")
    ]
    
    all_ok = True
    
    for model_path, model_name in models_info:
        print(f"\n🔍 检查 {model_name}...")
        
        if not model_path.exists():
            print(f"❌ 目录不存在: {model_path}")
            all_ok = False
            continue
        
        # 检查关键文件
        required_files = ["config.json", "pytorch_model.bin"]
        missing_files = []
        
        for file_name in required_files:
            file_path = model_path / file_name
            if file_path.exists():
                file_size = file_path.stat().st_size
                print(f"  ✅ {file_name}: {file_size:,} bytes")
            else:
                print(f"  ❌ {file_name}: 缺失")
                missing_files.append(file_name)
        
        if missing_files:
            print(f"  ⚠️ 缺少文件: {missing_files}")
            all_ok = False
        else:
            print(f"  🎉 {model_name} 完整")
    
    print("\n" + "=" * 40)
    if all_ok:
        print("🎉 所有模型文件完整！")
        print("\n📋 后续步骤:")
        print("1. 更新应用配置使用真实模型")
        print("2. 重启应用: docker-compose restart")
        print("3. 测试预测功能")
    else:
        print("❌ 部分模型文件缺失")
        print("\n🔧 解决方案:")
        print("1. 重新运行: ./download_models.sh")
        print("2. 检查网络连接")
        print("3. 手动下载模型文件")
    
    return all_ok

if __name__ == "__main__":
    test_model_loading()
EOF

echo "📄 已创建模型测试脚本: test_models.py"

# 运行测试
echo ""
echo "🔍 运行模型验证..."
if command -v python3 &> /dev/null; then
    python3 test_models.py
else
    echo "⚠️ Python3不可用，请手动验证模型"
fi

# 计算总大小
echo ""
echo "📊 计算模型大小..."
if [ -d "volumes/models" ]; then
    total_size=$(du -sh volumes/models 2>/dev/null | cut -f1 || echo "未知")
    echo "📦 模型总大小: $total_size"
fi

echo ""
echo "============================="
echo "🎉 模型下载流程完成！"
echo ""
echo "📋 下载结果:"
echo "- Tokenizer: volumes/models/Kronos-Tokenizer-base/"
echo "- Predictor: volumes/models/Kronos-small/"
echo ""
echo "🔧 后续步骤:"
echo "1. 运行 python3 test_models.py 验证模型"
echo "2. 更新应用配置使用真实模型"
echo "3. 重启应用: docker-compose restart"
echo ""
echo "📖 详细文档: QLIB_DATA_SETUP.md"

# 提供手动下载链接
echo ""
echo "🔗 手动下载链接（如果自动下载失败）:"
echo "- Kronos-Tokenizer-base: https://huggingface.co/Kronos/Kronos-Tokenizer-base"
echo "- Kronos-small: https://huggingface.co/Kronos/Kronos-small"
