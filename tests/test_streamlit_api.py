#!/usr/bin/env python3
"""
测试Streamlit API调用
"""

import requests
import os

def test_streamlit_api_call():
    """测试Streamlit中的API调用逻辑"""
    print("🧪 测试Streamlit API调用逻辑")
    print("=" * 50)
    
    # 使用与Streamlit相同的配置
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    print(f"API地址: {API_BASE_URL}")
    
    # 模拟Streamlit中的get_stock_prediction函数
    def get_stock_prediction(stock_code, **params):
        """获取股票预测"""
        try:
            payload = {
                "stock_code": stock_code,
                **params
            }
            
            print(f"请求参数: {payload}")
            
            response = requests.post(
                f"{API_BASE_URL}/predict",
                json=payload,
                timeout=60
            )
            
            print(f"响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"错误响应: {response.text}")
                return {
                    "success": False,
                    "error": f"API请求失败: {response.status_code}"
                }
        except Exception as e:
            print(f"请求异常: {str(e)}")
            return {
                "success": False,
                "error": f"请求异常: {str(e)}"
            }
    
    # 测试1: 最简单的调用
    print("\n1. 📊 测试最简单的调用:")
    result1 = get_stock_prediction("000001")
    print(f"结果: {result1.get('success')}")
    if not result1.get('success'):
        print(f"错误: {result1.get('error')}")
    
    # 测试2: 带参数的调用
    print("\n2. 📊 测试带参数的调用:")
    result2 = get_stock_prediction(
        "000001",
        pred_len=10,
        lookback=100,
        temperature=1.0
    )
    print(f"结果: {result2.get('success')}")
    if not result2.get('success'):
        print(f"错误: {result2.get('error')}")
    
    # 测试3: 模拟Streamlit界面的调用
    print("\n3. 📊 模拟Streamlit界面调用:")
    
    # 这些是Streamlit界面可能传递的参数
    streamlit_params = {
        'pred_len': 10,
        'lookback': 100,
        'temperature': 1.0,
        'top_p': 0.9,
        'sample_count': 1
    }
    
    result3 = get_stock_prediction("000001", **streamlit_params)
    print(f"结果: {result3.get('success')}")
    if result3.get('success'):
        data = result3['data']
        print(f"股票: {data['stock_info']['name']}")
        print(f"历史数据: {len(data['historical_data'])} 条")
        print(f"预测数据: {len(data['predictions'])} 条")
    else:
        print(f"错误: {result3.get('error')}")
    
    # 测试4: 检查API健康状态
    print("\n4. 🏥 检查API健康状态:")
    def check_api_health():
        """检查API服务状态"""
        try:
            response = requests.get(f"{API_BASE_URL}/health", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    health = check_api_health()
    print(f"API健康状态: {health}")
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 测试结果总结:")
    
    results = [result1, result2, result3]
    success_count = sum(1 for r in results if r.get('success'))
    
    print(f"成功率: {success_count}/{len(results)}")
    
    if success_count == len(results):
        print("✅ 所有API调用都成功")
        print("\n💡 如果Streamlit中仍有400错误:")
        print("   1. 清除浏览器缓存")
        print("   2. 重新加载页面")
        print("   3. 检查浏览器控制台错误")
        print("   4. 尝试不同的股票代码")
    else:
        print("❌ 部分API调用失败")
        print("\n🔧 需要检查:")
        print("   1. API服务状态")
        print("   2. 请求参数格式")
        print("   3. 网络连接")
    
    return success_count == len(results)

def test_direct_browser_access():
    """测试直接浏览器访问"""
    print("\n🌐 浏览器访问测试:")
    
    API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    urls_to_test = [
        f"{API_BASE_URL}/health",
        f"{API_BASE_URL}/docs",
        f"{API_BASE_URL}/stocks/000001/info"
    ]
    
    for url in urls_to_test:
        try:
            response = requests.get(url, timeout=5)
            print(f"   {url}: {response.status_code}")
        except Exception as e:
            print(f"   {url}: 异常 - {str(e)}")

if __name__ == "__main__":
    success = test_streamlit_api_call()
    test_direct_browser_access()
    
    if success:
        print(f"\n🎉 API调用测试全部通过！")
        print(f"现在可以访问 http://localhost:8501 测试前端")
    else:
        print(f"\n⚠️ API调用存在问题，需要进一步调试")
