#!/usr/bin/env python3
"""
测试400错误修复
"""

import requests
import time

def test_available_stocks():
    """测试获取可用股票列表"""
    print("📋 获取可用股票列表...")
    
    try:
        from app.akshare_adapter import AkshareDataAdapter
        adapter = AkshareDataAdapter()
        stocks = adapter.list_available_stocks()
        
        print(f"   ✅ 找到 {len(stocks)} 只股票")
        print(f"   📊 前10只: {', '.join(stocks[:10])}")
        
        return stocks
    except Exception as e:
        print(f"   ❌ 获取失败: {str(e)}")
        return []

def test_valid_stock():
    """测试有效股票代码"""
    print("\n✅ 测试有效股票 (000001):")
    
    try:
        start_time = time.time()
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000001', 'pred_len': 5},
            timeout=20
        )
        end_time = time.time()
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data['data']['summary']
                print(f"   ✅ 预测成功 ({end_time - start_time:.2f}s)")
                print(f"   📊 {data['data']['stock_info']['name']}")
                print(f"   💰 ¥{summary['current_price']:.2f} → ¥{summary['predicted_price']:.2f}")
                return True
            else:
                print(f"   ❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"   ❌ HTTP错误: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
        return False

def test_invalid_stock():
    """测试无效股票代码"""
    print("\n❌ 测试无效股票 (000968):")
    
    try:
        response = requests.post(
            'http://localhost:8000/predict',
            json={'stock_code': '000968', 'pred_len': 5},
            timeout=10
        )
        
        if response.status_code == 400:
            data = response.json()
            print(f"   ✅ 正确返回400错误")
            print(f"   📝 错误信息: {data.get('detail', '未知错误')}")
            
            # 检查是否包含可用股票建议
            if 'available_stocks' in data or '可用股票' in str(data):
                print(f"   ✅ 包含可用股票建议")
            else:
                print(f"   ⚠️ 未包含可用股票建议")
            
            return True
        else:
            print(f"   ❌ 应该返回400，实际返回: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
    except Exception as e:
        print(f"   ❌ 请求异常: {str(e)}")
        return False

def test_multiple_valid_stocks():
    """测试多个有效股票"""
    print("\n🔄 测试多个有效股票:")
    
    test_stocks = ['000001', '000002', '000004']
    success_count = 0
    
    for stock_code in test_stocks:
        try:
            response = requests.post(
                'http://localhost:8000/predict',
                json={'stock_code': stock_code, 'pred_len': 3},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    stock_name = data['data']['stock_info']['name']
                    current_price = data['data']['summary']['current_price']
                    print(f"   ✅ {stock_code} ({stock_name}): ¥{current_price:.2f}")
                    success_count += 1
                else:
                    print(f"   ❌ {stock_code}: {data.get('error')}")
            else:
                print(f"   ❌ {stock_code}: HTTP {response.status_code}")
        except Exception as e:
            print(f"   ❌ {stock_code}: {str(e)}")
    
    print(f"   📊 成功率: {success_count}/{len(test_stocks)}")
    return success_count == len(test_stocks)

def main():
    """主测试函数"""
    print("🔧 测试400错误修复")
    print("=" * 50)
    
    # 1. 获取可用股票
    available_stocks = test_available_stocks()
    
    # 2. 测试有效股票
    valid_test = test_valid_stock()
    
    # 3. 测试无效股票
    invalid_test = test_invalid_stock()
    
    # 4. 测试多个股票
    multiple_test = test_multiple_valid_stocks()
    
    # 总结
    print("\n" + "=" * 50)
    print("📊 修复验证结果:")
    
    if len(available_stocks) > 0:
        print(f"✅ 可用股票: {len(available_stocks)} 只")
    else:
        print("❌ 无法获取可用股票列表")
    
    if valid_test:
        print("✅ 有效股票预测: 正常")
    else:
        print("❌ 有效股票预测: 失败")
    
    if invalid_test:
        print("✅ 无效股票处理: 正确返回400错误")
    else:
        print("❌ 无效股票处理: 错误处理有问题")
    
    if multiple_test:
        print("✅ 批量预测: 正常")
    else:
        print("❌ 批量预测: 部分失败")
    
    # 使用建议
    if len(available_stocks) > 0:
        print(f"\n💡 使用建议:")
        print(f"   请使用以下有效股票代码进行测试:")
        print(f"   推荐股票: {', '.join(available_stocks[:10])}")
        print(f"   总共可用: {len(available_stocks)} 只股票")
        
        print(f"\n🌐 前端测试:")
        print(f"   1. 访问: http://localhost:8501")
        print(f"   2. 输入有效代码: 000001, 000002, 000004")
        print(f"   3. 避免使用: 000968 等无效代码")

if __name__ == "__main__":
    main()
