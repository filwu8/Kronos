#!/usr/bin/env python3
"""
检查Kronos数据需求和当前状态
"""

import os
import sys
from pathlib import Path
import subprocess

def check_qlib_installation():
    """检查Qlib安装状态"""
    print("📦 检查Qlib安装状态...")
    
    try:
        import qlib
        print(f"✅ Qlib已安装，版本: {qlib.__version__}")
        return True
    except ImportError:
        print("❌ Qlib未安装")
        return False

def check_qlib_data():
    """检查Qlib数据"""
    print("\n📊 检查Qlib数据...")
    
    data_path = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    
    if not data_path.exists():
        print(f"❌ Qlib数据目录不存在: {data_path}")
        return False
    
    print(f"✅ Qlib数据目录存在: {data_path}")
    
    # 检查数据文件
    essential_dirs = ['calendars', 'instruments', 'features']
    missing_dirs = []
    
    for dir_name in essential_dirs:
        dir_path = data_path / dir_name
        if dir_path.exists():
            print(f"✅ {dir_name} 目录存在")
        else:
            print(f"❌ {dir_name} 目录缺失")
            missing_dirs.append(dir_name)
    
    if missing_dirs:
        print(f"❌ 缺少关键目录: {missing_dirs}")
        return False
    
    # 检查股票数据文件数量
    features_dir = data_path / "features"
    if features_dir.exists():
        stock_dirs = [d for d in features_dir.iterdir() if d.is_dir()]
        print(f"✅ 股票数据文件数量: {len(stock_dirs)}")
        
        if len(stock_dirs) > 0:
            print(f"样本股票: {[d.name for d in stock_dirs[:5]]}")
            return True
        else:
            print("❌ 没有找到股票数据文件")
            return False
    
    return False

def check_kronos_models():
    """检查Kronos模型文件"""
    print("\n🤖 检查Kronos模型文件...")
    
    model_paths = [
        "./models/Kronos-Tokenizer-base",
        "./models/Kronos-small",
        "finetune/outputs/models"
    ]
    
    found_models = []
    
    for model_path in model_paths:
        path = Path(model_path)
        if path.exists():
            print(f"✅ 模型目录存在: {model_path}")
            found_models.append(model_path)
        else:
            print(f"❌ 模型目录不存在: {model_path}")
    
    if not found_models:
        print("❌ 没有找到任何Kronos模型文件")
        return False
    
    return True

def check_current_data_source():
    """检查当前数据源"""
    print("\n📈 检查当前数据源...")
    
    # 检查data_fetcher.py
    data_fetcher_path = Path("app/data_fetcher.py")
    if data_fetcher_path.exists():
        with open(data_fetcher_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'akshare' in content:
            print("📊 当前使用akshare数据源")
        if 'yfinance' in content:
            print("📊 当前使用yfinance数据源")
        if 'qlib' in content.lower():
            print("📊 当前使用Qlib数据源")
        else:
            print("⚠️ 当前未使用Qlib数据源")
    
    # 检查prediction_service.py
    pred_service_path = Path("app/prediction_service.py")
    if pred_service_path.exists():
        with open(pred_service_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if 'use_mock = True' in content:
            print("⚠️ 当前使用模拟预测模式")
        if 'Kronos' in content and 'mock' not in content.lower():
            print("✅ 当前使用真实Kronos模型")

def analyze_data_requirements():
    """分析数据需求"""
    print("\n📋 分析Kronos数据需求...")
    
    print("🎯 Kronos模型数据需求:")
    print("  - 数据源: Qlib格式的中国A股数据")
    print("  - 数据字段: open, high, low, close, volume, vwap")
    print("  - 最小历史长度: lookback_window + predict_window + 1")
    print("  - 默认配置: 90 + 10 + 1 = 101天")
    print("  - 推荐历史长度: 2-3年以上")
    print("  - 数据质量: 无缺失值，经过复权处理")
    
    print("\n📊 当前应用数据状态:")
    print("  - 数据源: akshare + yfinance (实时获取)")
    print("  - 历史长度: 100天")
    print("  - 预测模式: 模拟模式")
    print("  - 数据格式: 非Qlib格式")

def provide_recommendations():
    """提供建议"""
    print("\n💡 改进建议:")
    
    print("\n🔧 立即可做的改进:")
    print("1. 安装Qlib: pip install pyqlib")
    print("2. 下载A股数据: python setup_qlib_data.py")
    print("3. 验证数据: python test_qlib_data.py")
    
    print("\n🚀 进阶改进:")
    print("1. 下载Kronos预训练模型")
    print("2. 创建Qlib数据适配器")
    print("3. 更新预测服务使用真实模型")
    print("4. 集成到Web应用")
    
    print("\n📚 参考资源:")
    print("- 详细指南: QLIB_DATA_SETUP.md")
    print("- 自动化脚本: setup_qlib_data.py")
    print("- Qlib官方文档: https://github.com/microsoft/qlib")
    print("- Kronos模型: https://huggingface.co/Kronos")

def estimate_resources():
    """估算资源需求"""
    print("\n💾 资源需求估算:")
    
    print("📁 存储空间:")
    print("  - Qlib A股数据: ~2-5GB")
    print("  - Kronos模型文件: ~1-2GB")
    print("  - 总计: ~3-7GB")
    
    print("⏱️ 时间需求:")
    print("  - Qlib安装: 5-10分钟")
    print("  - 数据下载: 30分钟-2小时")
    print("  - 模型下载: 10-30分钟")
    print("  - 代码集成: 2-4小时")
    
    print("🖥️ 计算资源:")
    print("  - 内存: 建议8GB以上")
    print("  - CPU: 多核处理器")
    print("  - GPU: 可选，但会显著提升预测速度")

def main():
    """主函数"""
    print("🔍 Kronos数据需求检查报告")
    print("=" * 60)
    
    # 检查各项状态
    qlib_installed = check_qlib_installation()
    qlib_data_ready = check_qlib_data() if qlib_installed else False
    models_ready = check_kronos_models()
    
    check_current_data_source()
    analyze_data_requirements()
    
    print("\n" + "=" * 60)
    print("📊 检查结果总结:")
    
    status_items = [
        ("Qlib安装", qlib_installed),
        ("Qlib数据", qlib_data_ready),
        ("Kronos模型", models_ready)
    ]
    
    all_ready = True
    for item, status in status_items:
        icon = "✅" if status else "❌"
        print(f"  {icon} {item}: {'就绪' if status else '未就绪'}")
        if not status:
            all_ready = False
    
    if all_ready:
        print("\n🎉 所有组件都已就绪！可以使用真实的Kronos模型进行预测。")
    else:
        print("\n⚠️ 部分组件未就绪，当前使用模拟模式。")
        provide_recommendations()
    
    estimate_resources()
    
    print("\n🔗 下一步:")
    if not qlib_installed:
        print("1. 运行: python setup_qlib_data.py")
    elif not qlib_data_ready:
        print("1. 完成Qlib数据下载")
    elif not models_ready:
        print("1. 下载Kronos预训练模型")
    else:
        print("1. 集成真实模型到应用")
    
    print("2. 参考: QLIB_DATA_SETUP.md")

if __name__ == "__main__":
    main()
