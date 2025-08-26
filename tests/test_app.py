#!/usr/bin/env python3
"""
应用测试脚本
测试API和前端功能
"""

import requests
import json
import time
import sys
from datetime import datetime

# 配置
API_BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8501"

def test_api_health():
    """测试API健康状态"""
    print("🔍 测试API健康状态...")
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)
        if response.status_code == 200:
            data = response.json()
            print("✅ API服务正常")
            print(f"   模型状态: {data.get('model_status', {})}")
            return True
        else:
            print(f"❌ API健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API连接失败: {str(e)}")
        return False

def test_stock_info():
    """测试股票信息获取"""
    print("\n🔍 测试股票信息获取...")
    test_codes = ["000001", "600000", "000002"]
    
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

def test_stock_prediction():
    """测试股票预测"""
    print("\n🔍 测试股票预测...")
    
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
                print(f"   当前价格: ¥{summary['current_price']:.2f}")
                print(f"   预测价格: ¥{summary['predicted_price']:.2f}")
                print(f"   预期变化: {summary['change_percent']:.2f}%")
                print(f"   趋势: {summary['trend']}")
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
    print("\n🔍 测试批量预测...")
    
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

def test_frontend_access():
    """测试前端访问"""
    print("\n🔍 测试前端访问...")
    try:
        response = requests.get(FRONTEND_URL, timeout=10)
        if response.status_code == 200:
            print("✅ 前端服务可访问")
            print(f"   URL: {FRONTEND_URL}")
            return True
        else:
            print(f"❌ 前端访问失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 前端连接失败: {str(e)}")
        return False

def test_api_docs():
    """测试API文档"""
    print("\n🔍 测试API文档...")
    try:
        response = requests.get(f"{API_BASE_URL}/docs", timeout=10)
        if response.status_code == 200:
            print("✅ API文档可访问")
            print(f"   URL: {API_BASE_URL}/docs")
            return True
        else:
            print(f"❌ API文档访问失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API文档连接失败: {str(e)}")
        return False

def run_performance_test():
    """运行性能测试"""
    print("\n🔍 运行性能测试...")
    
    # 测试多个并发请求
    import threading
    import time
    
    results = []
    
    def make_request():
        start_time = time.time()
        try:
            response = requests.get(f"{API_BASE_URL}/stocks/000001/info", timeout=10)
            end_time = time.time()
            results.append({
                'success': response.status_code == 200,
                'duration': end_time - start_time
            })
        except:
            results.append({
                'success': False,
                'duration': 0
            })
    
    # 创建5个并发请求
    threads = []
    for i in range(5):
        thread = threading.Thread(target=make_request)
        threads.append(thread)
        thread.start()
    
    # 等待所有请求完成
    for thread in threads:
        thread.join()
    
    # 分析结果
    success_count = sum(1 for r in results if r['success'])
    avg_duration = sum(r['duration'] for r in results) / len(results)
    
    print(f"   并发请求: 5个")
    print(f"   成功率: {success_count}/5 ({success_count/5*100:.1f}%)")
    print(f"   平均响应时间: {avg_duration:.2f}秒")
    
    return success_count >= 4  # 至少80%成功率

def main():
    """主测试函数"""
    print("🚀 开始测试Kronos股票预测应用")
    print(f"⏰ 测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)
    
    # 等待服务启动
    print("⏳ 等待服务启动...")
    time.sleep(5)
    
    # 运行测试
    tests = [
        ("API健康检查", test_api_health),
        ("股票信息获取", test_stock_info),
        ("股票预测", test_stock_prediction),
        ("批量预测", test_batch_prediction),
        ("前端访问", test_frontend_access),
        ("API文档", test_api_docs),
        ("性能测试", run_performance_test),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            print(f"❌ {test_name} 测试异常: {str(e)}")
            results[test_name] = False
    
    # 输出测试总结
    print("\n" + "=" * 50)
    print("📊 测试总结")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总体结果: {passed}/{total} 测试通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 所有测试通过！应用运行正常。")
        print("\n📋 访问信息:")
        print(f"   前端界面: {FRONTEND_URL}")
        print(f"   API文档: {API_BASE_URL}/docs")
        print(f"   健康检查: {API_BASE_URL}/health")
        return 0
    else:
        print("⚠️ 部分测试失败，请检查应用状态。")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
