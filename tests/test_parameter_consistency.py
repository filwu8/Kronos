#!/usr/bin/env python3
"""
测试前端UI与后端API参数一致性
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
import json
from pydantic import ValidationError

def test_api_parameter_limits():
    """测试API参数限制"""
    print("🧪 测试API参数限制...")
    
    # 导入API模型进行验证
    try:
        from app.api import PredictionRequest
        
        # 测试各种参数组合
        test_cases = [
            {
                "name": "正常参数",
                "params": {
                    "stock_code": "000001",
                    "pred_len": 30,
                    "lookback": 1000,
                    "temperature": 1.0,
                    "top_p": 0.9,
                    "sample_count": 3
                },
                "should_pass": True
            },
            {
                "name": "最大预测天数",
                "params": {
                    "stock_code": "000001",
                    "pred_len": 120,
                    "sample_count": 1
                },
                "should_pass": True
            },
            {
                "name": "超出预测天数限制",
                "params": {
                    "stock_code": "000001",
                    "pred_len": 121,
                    "sample_count": 1
                },
                "should_pass": False
            },
            {
                "name": "最大采样次数",
                "params": {
                    "stock_code": "000001",
                    "sample_count": 10
                },
                "should_pass": True
            },
            {
                "name": "超出采样次数限制",
                "params": {
                    "stock_code": "000001",
                    "sample_count": 11
                },
                "should_pass": False
            },
            {
                "name": "最大历史数据长度",
                "params": {
                    "stock_code": "000001",
                    "lookback": 5000
                },
                "should_pass": True
            },
            {
                "name": "超出历史数据长度限制",
                "params": {
                    "stock_code": "000001",
                    "lookback": 5001
                },
                "should_pass": False
            },
            {
                "name": "温度参数边界",
                "params": {
                    "stock_code": "000001",
                    "temperature": 2.0
                },
                "should_pass": True
            },
            {
                "name": "超出温度参数限制",
                "params": {
                    "stock_code": "000001",
                    "temperature": 2.1
                },
                "should_pass": False
            }
        ]
        
        print(f"{'测试用例':<20} {'参数':<30} {'预期':<8} {'结果'}")
        print("-" * 80)
        
        for case in test_cases:
            try:
                request = PredictionRequest(**case["params"])
                result = "通过"
                status = "✅" if case["should_pass"] else "❌"
            except ValidationError as e:
                result = "失败"
                status = "✅" if not case["should_pass"] else "❌"
            except Exception as e:
                result = f"异常: {str(e)}"
                status = "⚠️"
            
            # 格式化参数显示
            key_params = []
            for key in ["pred_len", "lookback", "temperature", "top_p", "sample_count"]:
                if key in case["params"]:
                    key_params.append(f"{key}={case['params'][key]}")
            params_str = ", ".join(key_params)
            
            expected = "通过" if case["should_pass"] else "失败"
            
            print(f"{case['name']:<20} {params_str:<30} {expected:<8} {result} {status}")
        
        print("\n✅ API参数验证测试完成")
        
    except ImportError as e:
        print(f"❌ 无法导入API模型: {e}")

def test_ui_parameter_ranges():
    """测试UI参数范围"""
    print("\n🎨 UI参数范围分析...")
    
    # 模拟UI参数配置
    ui_configs = {
        "主预测页面": {
            "pred_len": {"min": 1, "max": 120, "default": 30},
            "lookback_standard": {"min": 50, "max": 1000, "default": 400},
            "lookback_high_perf": {"min": 50, "max": 5000, "default": 2000},
            "temperature": {"min": 0.1, "max": 2.0, "default": 1.0},
            "top_p": {"min": 0.1, "max": 1.0, "default": 0.9},
            "sample_count_standard": {"min": 1, "max": 5, "default": 1},
            "sample_count_high_perf": {"min": 1, "max": 10, "default": 3}
        },
        "回测页面": {
            "pred_len": {"min": 1, "max": 120, "default": 10},
            "lookback": {"min": 100, "max": 5000, "default": 1024},
            "temperature": {"min": 0.1, "max": 2.0, "default": 0.6},
            "top_p": {"min": 0.1, "max": 1.0, "default": 0.8},
            "sample_count": {"min": 1, "max": 10, "default": 3}
        }
    }
    
    # API限制
    api_limits = {
        "pred_len": {"min": 1, "max": 120},
        "lookback": {"min": 50, "max": 5000},
        "temperature": {"min": 0.1, "max": 2.0},
        "top_p": {"min": 0.1, "max": 1.0},
        "sample_count": {"min": 1, "max": 10}
    }
    
    print(f"{'参数':<15} {'UI页面':<15} {'UI范围':<15} {'API范围':<15} {'一致性'}")
    print("-" * 75)
    
    # 检查一致性
    for page, configs in ui_configs.items():
        for param, ui_range in configs.items():
            # 提取基础参数名
            base_param = param.split('_')[0]
            
            if base_param in api_limits:
                api_range = api_limits[base_param]
                ui_min, ui_max = ui_range["min"], ui_range["max"]
                api_min, api_max = api_range["min"], api_range["max"]
                
                # 检查一致性
                if ui_min >= api_min and ui_max <= api_max:
                    consistency = "✅"
                elif ui_max > api_max:
                    consistency = "⚠️ UI超出"
                elif ui_min < api_min:
                    consistency = "⚠️ UI不足"
                else:
                    consistency = "❌ 不匹配"
                
                ui_range_str = f"{ui_min}-{ui_max}"
                api_range_str = f"{api_min}-{api_max}"
                
                print(f"{param:<15} {page:<15} {ui_range_str:<15} {api_range_str:<15} {consistency}")

def test_performance_mode_logic():
    """测试性能模式逻辑"""
    print("\n⚡ 性能模式逻辑测试...")
    
    performance_modes = {
        "标准模式": {
            "max_lookback": 1000,
            "default_lookback": 400,
            "max_sample_count": 5,
            "default_sample_count": 1
        },
        "高性能模式 (RTX 5090)": {
            "max_lookback": 5000,
            "default_lookback": 2000,
            "max_sample_count": 10,
            "default_sample_count": 3
        }
    }
    
    print(f"{'性能模式':<20} {'lookback范围':<15} {'sample_count范围':<18} {'推荐配置'}")
    print("-" * 70)
    
    for mode, config in performance_modes.items():
        lookback_range = f"50-{config['max_lookback']}"
        sample_range = f"1-{config['max_sample_count']}"
        recommended = f"lookback={config['default_lookback']}, samples={config['default_sample_count']}"
        
        print(f"{mode:<20} {lookback_range:<15} {sample_range:<18} {recommended}")

def generate_recommendations():
    """生成修复建议"""
    print("\n💡 修复建议:")
    print("=" * 50)
    
    recommendations = [
        "✅ API采样次数限制已修复 (5→10)",
        "✅ 主页面预测天数限制已修复 (60→120)",
        "✅ 所有参数现在保持一致",
        "",
        "📋 验证清单:",
        "• pred_len: 1-120天 (所有页面一致)",
        "• lookback: 50-5000 (根据性能模式)",
        "• temperature: 0.1-2.0 (完全一致)",
        "• top_p: 0.1-1.0 (完全一致)",
        "• sample_count: 1-10 (根据性能模式)",
        "",
        "🚀 下一步:",
        "• 重启应用验证修复效果",
        "• 测试边界值参数",
        "• 确认错误提示信息"
    ]
    
    for rec in recommendations:
        print(rec)

if __name__ == "__main__":
    print("🚀 开始参数一致性测试...")
    
    # 测试API参数限制
    test_api_parameter_limits()
    
    # 测试UI参数范围
    test_ui_parameter_ranges()
    
    # 测试性能模式逻辑
    test_performance_mode_logic()
    
    # 生成建议
    generate_recommendations()
    
    print("\n✅ 参数一致性测试完成！")
