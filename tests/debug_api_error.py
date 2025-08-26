#!/usr/bin/env python3
"""
调试API错误
"""

import requests
import json

def debug_api_configuration():
    """调试API配置"""
    print("🔍 调试API配置和错误")
    print("=" * 50)
    
    # 1. 检查API配置
    print("\n1. 📋 API配置信息:")
    import os
    api_url = os.getenv('API_BASE_URL', 'http://localhost:8000')
    print(f"   配置的API地址: {api_url}")
    
    # 2. 检查API健康状态
    print("\n2. 🏥 API健康检查:")
    try:
        response = requests.get(f'{api_url}/health', timeout=5)
        print(f"   状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"   API状态: {data['status']}")
            print(f"   模型加载: {data['model_status']['model_loaded']}")
            print(f"   使用模拟: {data['model_status']['use_mock']}")
            print(f"   设备: {data['model_status']['device']}")
        else:
            print(f"   错误响应: {response.text}")
    except Exception as e:
        print(f"   连接失败: {str(e)}")
        return False
    
    # 3. 测试预测API
    print("\n3. 🔮 测试预测API:")
    try:
        # 测试最简单的请求
        response = requests.post(
            f'{api_url}/predict',
            json={'stock_code': '000001'},
            timeout=30
        )
        
        print(f"   状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   预测成功: {data.get('success')}")
            if data.get('success'):
                stock_info = data['data']['stock_info']
                summary = data['data']['summary']
                print(f"   股票: {stock_info['name']} ({stock_info['code']})")
                print(f"   当前价格: ¥{summary['current_price']:.2f}")
                print(f"   预测价格: ¥{summary['predicted_price']:.2f}")
            else:
                print(f"   预测错误: {data.get('error')}")
        elif response.status_code == 400:
            print(f"   400错误 - 请求参数问题:")
            try:
                error_data = response.json()
                print(f"   错误详情: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   错误文本: {response.text}")
        elif response.status_code == 422:
            print(f"   422错误 - 参数验证失败:")
            try:
                error_data = response.json()
                print(f"   验证错误: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"   错误文本: {response.text}")
        else:
            print(f"   其他HTTP错误: {response.status_code}")
            print(f"   错误内容: {response.text}")
            
    except Exception as e:
        print(f"   请求异常: {str(e)}")
        return False
    
    # 4. 检查API文档
    print("\n4. 📚 API文档检查:")
    try:
        response = requests.get(f'{api_url}/docs', timeout=5)
        print(f"   文档访问: {response.status_code}")
        if response.status_code == 200:
            print(f"   API文档可访问: {api_url}/docs")
        else:
            print(f"   文档访问失败: {response.text}")
    except Exception as e:
        print(f"   文档访问异常: {str(e)}")
    
    # 5. 检查API端点
    print("\n5. 🛣️ API端点检查:")
    endpoints = [
        ('/health', 'GET'),
        ('/predict', 'POST'),
        ('/stocks/000001/info', 'GET'),
        ('/model/status', 'GET')
    ]
    
    for endpoint, method in endpoints:
        try:
            if method == 'GET':
                response = requests.get(f'{api_url}{endpoint}', timeout=5)
            else:
                response = requests.post(f'{api_url}{endpoint}', 
                                       json={'stock_code': '000001'}, timeout=5)
            
            print(f"   {method} {endpoint}: {response.status_code}")
            
        except Exception as e:
            print(f"   {method} {endpoint}: 异常 - {str(e)}")
    
    return True

def test_streamlit_api_call():
    """测试Streamlit中的API调用"""
    print("\n6. 🖥️ 测试Streamlit API调用:")
    
    # 模拟Streamlit中的API调用
    try:
        import os
        API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:8000")
        
        payload = {
            'stock_code': '000001',
            'pred_len': 10,
            'lookback': 100,
            'temperature': 1.0,
            'top_p': 0.9,
            'sample_count': 1
        }
        
        print(f"   API地址: {API_BASE_URL}")
        print(f"   请求参数: {json.dumps(payload, indent=2, ensure_ascii=False)}")
        
        response = requests.post(
            f"{API_BASE_URL}/predict",
            json=payload,
            timeout=60
        )
        
        print(f"   响应状态: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✅ Streamlit API调用成功")
                return True
            else:
                print(f"   ❌ API返回错误: {data.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            print(f"   错误内容: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ 调用异常: {str(e)}")
        return False

def main():
    """主函数"""
    success = debug_api_configuration()
    
    if success:
        streamlit_success = test_streamlit_api_call()
        
        print("\n" + "=" * 50)
        print("📊 调试结果总结:")
        
        if streamlit_success:
            print("✅ API配置和调用都正常")
            print("\n🔧 如果Streamlit中仍有400错误，可能原因:")
            print("   1. 前端参数验证问题")
            print("   2. 网络连接问题")
            print("   3. 服务重启后状态不同步")
            
            print("\n💡 解决建议:")
            print("   1. 重启Streamlit服务")
            print("   2. 检查浏览器控制台错误")
            print("   3. 清除浏览器缓存")
            
        else:
            print("❌ API调用存在问题")
            print("\n🔧 需要检查:")
            print("   1. API服务状态")
            print("   2. 请求参数格式")
            print("   3. 网络连接")
    else:
        print("\n❌ API基础配置有问题")
        print("请检查API服务是否正常运行")

if __name__ == "__main__":
    main()
