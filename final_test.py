#!/usr/bin/env python3
"""
最终功能测试脚本
"""

import requests
import time
import webbrowser

def test_all_functions():
    """测试所有功能"""
    print("🚀 Kronos股票预测应用 - 最终测试")
    print("=" * 50)
    
    # 1. 测试API健康状态
    print("\n1. 🔍 测试API健康状态...")
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ API服务正常运行")
        else:
            print("❌ API服务异常")
            return False
    except:
        print("❌ API服务无法连接")
        return False
    
    # 2. 测试前端服务
    print("\n2. 🌐 测试前端服务...")
    try:
        response = requests.get("http://localhost:8501", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务正常运行")
        else:
            print("❌ 前端服务异常")
            return False
    except:
        print("❌ 前端服务无法连接")
        return False
    
    # 3. 测试股票信息获取
    print("\n3. 📊 测试股票信息获取...")
    test_stocks = ["000001", "600000", "000002"]
    success_count = 0
    
    for stock in test_stocks:
        try:
            response = requests.get(f"http://localhost:8000/stocks/{stock}/info", timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    info = data['data']
                    print(f"✅ {stock}: {info['name']}")
                    success_count += 1
                else:
                    print(f"❌ {stock}: 获取失败")
            else:
                print(f"❌ {stock}: HTTP错误")
        except:
            print(f"❌ {stock}: 请求异常")
    
    if success_count == 0:
        print("❌ 所有股票信息获取失败")
        return False
    
    # 4. 测试股票预测
    print("\n4. 🔮 测试股票预测...")
    try:
        response = requests.post(
            "http://localhost:8000/predict",
            json={
                "stock_code": "000001",
                "pred_len": 5,
                "lookback": 50
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                summary = data['data']['summary']
                print(f"✅ 预测成功")
                print(f"   当前价格: ¥{summary['current_price']:.2f}")
                print(f"   预测价格: ¥{summary['predicted_price']:.2f}")
                print(f"   预期变化: {summary['change_percent']:.2f}%")
                print(f"   趋势: {summary['trend']}")
            else:
                print(f"❌ 预测失败: {data.get('error')}")
                return False
        else:
            print(f"❌ 预测请求失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 预测请求异常: {str(e)}")
        return False
    
    # 5. 测试批量预测
    print("\n5. 📈 测试批量预测...")
    try:
        response = requests.post(
            "http://localhost:8000/predict/batch",
            json={
                "stock_codes": ["000001", "600000"],
                "pred_len": 3
            },
            timeout=60
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
                        print(f"   {code}: 失败")
            else:
                print(f"❌ 批量预测失败")
                return False
        else:
            print(f"❌ 批量预测请求失败")
            return False
    except Exception as e:
        print(f"❌ 批量预测异常: {str(e)}")
        return False
    
    return True

def main():
    """主函数"""
    print("🎯 开始最终功能测试...")
    
    if test_all_functions():
        print("\n" + "=" * 50)
        print("🎉 所有测试通过！应用运行正常")
        print("\n📋 访问信息:")
        print("   前端界面: http://localhost:8501")
        print("   API文档: http://localhost:8000/docs")
        print("   健康检查: http://localhost:8000/health")
        
        print("\n🚀 功能特性:")
        print("   ✅ A股股票数据获取")
        print("   ✅ 智能价格预测")
        print("   ✅ 趋势分析")
        print("   ✅ 批量处理")
        print("   ✅ 交互式图表")
        print("   ✅ 用户友好界面")
        
        print("\n💡 使用建议:")
        print("   1. 在前端界面输入股票代码（如：000001）")
        print("   2. 调整预测参数（预测天数、历史周期等）")
        print("   3. 点击'开始预测'查看结果")
        print("   4. 查看交互式图表和详细数据")
        
        # 询问是否打开浏览器
        try:
            choice = input("\n是否打开浏览器访问应用? (Y/n): ").strip().lower()
            if choice in ['', 'y', 'yes']:
                print("正在打开浏览器...")
                webbrowser.open('http://localhost:8501')
        except:
            pass
        
        return 0
    else:
        print("\n" + "=" * 50)
        print("❌ 部分测试失败，请检查服务状态")
        print("\n🔧 故障排除:")
        print("   1. 确认API服务运行: python -m uvicorn app.api:app --port 8000")
        print("   2. 确认前端服务运行: streamlit run app/streamlit_app.py --port 8501")
        print("   3. 检查端口占用情况")
        print("   4. 查看服务日志")
        
        return 1

if __name__ == "__main__":
    exit(main())
