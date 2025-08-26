#!/usr/bin/env python3
"""
API测试脚本
"""

import requests
import json
import time

API_BASE_URL = "http://localhost:8000"

def test_api():
    print("🔍 测试Kronos股票预测API")
    print("=" * 40)
    
    # 1. 健康检查
    print("\n1. 健康检查...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API服务正常")
            print(f"   模型状态: {data['model_status']['model_loaded']}")
            print(f"   使用模拟: {data['model_status']['use_mock']}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API连接失败: {str(e)}")
        return False
    
    # 2. 股票信息测试
    print("\n2. 股票信息测试...")
    test_codes = ["000001", "600000"]
    
    for code in test_codes:
        try:
            response = requests.get(f"{API_BASE_URL}/stocks/{code}/info", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    info = data['data']
                    print(f"✅ {code}: {info['name']} ({info['market']})")
                else:
                    print(f"❌ {code}: 获取信息失败")
            else:
                print(f"❌ {code}: HTTP {response.status_code}")
        except Exception as e:
            print(f"❌ {code}: {str(e)}")
    
    # 3. 股票预测测试
    print("\n3. 股票预测测试...")
    
    test_request = {
        "stock_code": "000001",
        "period": "6mo",
        "pred_len": 10,
        "lookback": 100,
        "temperature": 1.0,
        "top_p": 0.9,
        "sample_count": 1
    }
    
    try:
        print(f"   请求参数: {test_request}")
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=test_request,
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data['data']['summary']
                print("✅ 预测成功")
                print(f"   股票: {data['data']['stock_info']['name']}")
                print(f"   当前价格: ¥{summary['current_price']:.2f}")
                print(f"   预测价格: ¥{summary['predicted_price']:.2f}")
                print(f"   预期变化: {summary['change_percent']:.2f}%")
                print(f"   趋势: {summary['trend']}")
                print(f"   预测天数: {summary['prediction_days']}")
                return True
            else:
                print(f"❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 预测请求失败: HTTP {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 预测请求异常: {str(e)}")
        return False

def test_batch_prediction():
    """测试批量预测"""
    print("\n4. 批量预测测试...")
    
    batch_request = {
        "stock_codes": ["000001", "600000"],
        "period": "6mo",
        "pred_len": 5
    }
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/predict/batch",
            json=batch_request,
            timeout=120
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                results = data['data']
                print(f"✅ 批量预测成功，处理了 {len(results)} 只股票")
                for code, result in results.items():
                    if result.get('success'):
                        summary = result['data']['summary']
                        print(f"   {code}: {summary['change_percent']:.2f}% ({summary['trend']})")
                    else:
                        print(f"   {code}: 失败 - {result.get('error')}")
                return True
            else:
                print(f"❌ 批量预测失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 批量预测请求失败: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 批量预测异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始API测试")
    
    # 基础测试
    if not test_api():
        print("\n❌ 基础测试失败")
        return 1
    
    # 批量预测测试
    if not test_batch_prediction():
        print("\n⚠️ 批量预测测试失败")
    
    print("\n" + "=" * 40)
    print("🎉 API测试完成！")
    print("\n📋 访问信息:")
    print(f"   API文档: {API_BASE_URL}/docs")
    print(f"   健康检查: {API_BASE_URL}/health")
    print(f"   模型状态: {API_BASE_URL}/model/status")
    
    return 0

if __name__ == "__main__":
    exit(main())
