#!/usr/bin/env python3
"""
验证下载的Kronos模型
"""

import os
import json
from pathlib import Path

def check_model_files(model_dir, model_name):
    """检查模型文件完整性"""
    print(f"\n🔍 检查 {model_name}")
    print("-" * 40)
    
    if not model_dir.exists():
        print(f"❌ 模型目录不存在: {model_dir}")
        return False
    
    print(f"✅ 模型目录存在: {model_dir}")
    
    # 检查必需文件
    required_files = {
        "config.json": "配置文件",
        "model.safetensors": "模型权重文件",
        "README.md": "说明文档"
    }
    
    missing_files = []
    file_info = {}
    
    for file_name, description in required_files.items():
        file_path = model_dir / file_name
        if file_path.exists():
            file_size = file_path.stat().st_size
            file_info[file_name] = file_size
            print(f"✅ {description}: {file_name} ({file_size:,} bytes)")
        else:
            print(f"❌ {description}: {file_name} (缺失)")
            missing_files.append(file_name)
    
    # 读取配置文件
    config_path = model_dir / "config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            print(f"\n📋 模型配置:")
            for key, value in config.items():
                print(f"   {key}: {value}")
                
        except Exception as e:
            print(f"❌ 配置文件读取失败: {str(e)}")
    
    # 检查README
    readme_path = model_dir / "README.md"
    if readme_path.exists():
        try:
            with open(readme_path, 'r', encoding='utf-8') as f:
                readme_content = f.read()
            
            print(f"\n📖 README信息:")
            # 显示前几行
            lines = readme_content.split('\n')[:10]
            for line in lines:
                if line.strip():
                    print(f"   {line}")
                    
        except Exception as e:
            print(f"❌ README读取失败: {str(e)}")
    
    if missing_files:
        print(f"\n⚠️ 缺少文件: {missing_files}")
        return False
    else:
        print(f"\n🎉 {model_name} 文件完整")
        return True

def analyze_model_sizes():
    """分析模型大小"""
    print(f"\n📊 模型大小分析")
    print("=" * 40)
    
    models_dir = Path('volumes/models')
    total_size = 0
    
    for model_subdir in models_dir.iterdir():
        if model_subdir.is_dir():
            model_size = sum(f.stat().st_size for f in model_subdir.rglob('*') if f.is_file())
            total_size += model_size
            
            print(f"📦 {model_subdir.name}: {model_size:,} bytes ({model_size/1024/1024:.1f} MB)")
    
    print(f"\n📦 总大小: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
    
    return total_size

def check_model_compatibility():
    """检查模型兼容性"""
    print(f"\n🔧 模型兼容性检查")
    print("=" * 40)
    
    # 检查Tokenizer配置
    tokenizer_config_path = Path("models/Kronos-Tokenizer-base/config.json")
    predictor_config_path = Path("models/Kronos-small/config.json")
    
    compatibility_issues = []
    
    if tokenizer_config_path.exists() and predictor_config_path.exists():
        try:
            with open(tokenizer_config_path, 'r') as f:
                tokenizer_config = json.load(f)
            
            with open(predictor_config_path, 'r') as f:
                predictor_config = json.load(f)
            
            # 检查关键参数匹配
            print("🔍 检查关键参数匹配:")
            
            # 检查bits参数
            if 's1_bits' in tokenizer_config and 's1_bits' in predictor_config:
                if tokenizer_config['s1_bits'] == predictor_config['s1_bits']:
                    print(f"✅ s1_bits 匹配: {tokenizer_config['s1_bits']}")
                else:
                    issue = f"s1_bits 不匹配: Tokenizer={tokenizer_config['s1_bits']}, Predictor={predictor_config['s1_bits']}"
                    print(f"❌ {issue}")
                    compatibility_issues.append(issue)
            
            if 's2_bits' in tokenizer_config and 's2_bits' in predictor_config:
                if tokenizer_config['s2_bits'] == predictor_config['s2_bits']:
                    print(f"✅ s2_bits 匹配: {tokenizer_config['s2_bits']}")
                else:
                    issue = f"s2_bits 不匹配: Tokenizer={tokenizer_config['s2_bits']}, Predictor={predictor_config['s2_bits']}"
                    print(f"❌ {issue}")
                    compatibility_issues.append(issue)
            
            # 检查输入维度
            if 'd_in' in tokenizer_config:
                d_in = tokenizer_config['d_in']
                print(f"✅ 输入维度: {d_in} (应该匹配数据特征数)")
                
                # 检查是否与我们的数据兼容
                expected_features = 6  # open, high, low, close, volume, amount
                if d_in == expected_features:
                    print(f"✅ 输入维度与数据特征匹配: {d_in}")
                else:
                    issue = f"输入维度不匹配: 模型期望{d_in}, 数据有{expected_features}个特征"
                    print(f"⚠️ {issue}")
                    compatibility_issues.append(issue)
            
        except Exception as e:
            print(f"❌ 配置文件解析失败: {str(e)}")
            compatibility_issues.append(f"配置文件解析失败: {str(e)}")
    
    if compatibility_issues:
        print(f"\n⚠️ 发现兼容性问题:")
        for issue in compatibility_issues:
            print(f"   - {issue}")
        return False
    else:
        print(f"\n✅ 模型兼容性检查通过")
        return True

def update_config_files():
    """更新配置文件中的模型路径"""
    print(f"\n📝 更新配置文件")
    print("=" * 40)
    
    # 更新finetune/config.py
    config_file = Path("finetune/config.py")
    
    if config_file.exists():
        try:
            # 读取原文件
            with open(config_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 备份原文件
            backup_file = config_file.with_suffix('.py.backup')
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # 更新模型路径
            updated_content = content.replace(
                'self.pretrained_tokenizer_path = "path/to/your/Kronos-Tokenizer-base"',
                'self.pretrained_tokenizer_path = "./models/Kronos-Tokenizer-base"'
            ).replace(
                'self.pretrained_predictor_path = "path/to/your/Kronos-small"',
                'self.pretrained_predictor_path = "./models/Kronos-small"'
            )
            
            # 写入更新后的内容
            with open(config_file, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ 已更新 {config_file}")
            print(f"✅ 原文件备份到 {backup_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 更新配置文件失败: {str(e)}")
            return False
    else:
        print(f"⚠️ 配置文件不存在: {config_file}")
        return False

def main():
    """主函数"""
    print("🤖 验证Kronos模型下载结果")
    print("=" * 60)
    
    models_dir = Path('volumes/models')
    
    if not models_dir.exists():
        print("❌ models目录不存在")
        return 1
    
    # 检查各个模型
    tokenizer_ok = check_model_files(
        models_dir / "Kronos-Tokenizer-base", 
        "Kronos-Tokenizer-base"
    )
    
    predictor_ok = check_model_files(
        models_dir / "Kronos-small", 
        "Kronos-small"
    )
    
    # 分析模型大小
    total_size = analyze_model_sizes()
    
    # 检查兼容性
    compatibility_ok = check_model_compatibility()
    
    # 更新配置文件
    config_updated = update_config_files()
    
    print("\n" + "=" * 60)
    print("📊 验证结果总结")
    
    results = [
        ("Kronos-Tokenizer-base", tokenizer_ok),
        ("Kronos-small", predictor_ok),
        ("模型兼容性", compatibility_ok),
        ("配置文件更新", config_updated)
    ]
    
    all_ok = True
    for item, status in results:
        icon = "✅" if status else "❌"
        print(f"   {icon} {item}: {'就绪' if status else '有问题'}")
        if not status:
            all_ok = False
    
    if all_ok:
        print(f"\n🎉 所有模型验证通过！")
        print(f"\n📋 模型信息:")
        print(f"   📦 总大小: {total_size/1024/1024:.1f} MB")
        print(f"   🔤 Tokenizer: models/Kronos-Tokenizer-base/")
        print(f"   🧠 Predictor: models/Kronos-small/")
        
        print(f"\n🔧 后续步骤:")
        print(f"   1. 创建数据适配器连接akshare数据")
        print(f"   2. 更新预测服务使用真实模型")
        print(f"   3. 测试端到端预测流程")
        print(f"   4. 重启应用验证效果")
        
    else:
        print(f"\n⚠️ 部分验证失败，请检查相关问题")
        print(f"\n🔧 故障排除:")
        print(f"   1. 重新下载缺失的模型文件")
        print(f"   2. 检查网络连接")
        print(f"   3. 验证Git LFS是否正常工作")
    
    return 0 if all_ok else 1

if __name__ == "__main__":
    exit(main())
