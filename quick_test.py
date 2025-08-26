#!/usr/bin/env python3
import requests
import time

print('🧪 快速系统验证')
print('=' * 40)

# 1. API健康检查
try:
    r = requests.get('http://localhost:8000/health', timeout=5)
    if r.status_code == 200:
        data = r.json()
        print(f'✅ API服务: 正常')
        print(f'   设备: {data["model_status"]["device"]}')
        print(f'   GPU: {data["model_status"]["cuda_available"]}')
    else:
        print(f'❌ API服务: 异常 ({r.status_code})')
except Exception as e:
    print(f'❌ API服务: 连接失败')

# 2. 预测功能测试
try:
    start = time.time()
    r = requests.post('http://localhost:8000/predict', 
                     json={'stock_code': '000001', 'pred_len': 3}, 
                     timeout=15)
    end = time.time()
    
    if r.status_code == 200:
        data = r.json()
        if data.get('success'):
            summary = data['data']['summary']
            print(f'✅ 预测功能: 正常 ({end-start:.1f}s)')
            print(f'   股票: {data["data"]["stock_info"]["name"]}')
            print(f'   价格: ¥{summary["current_price"]:.2f}')
            print(f'   趋势: {summary["trend"]}')
        else:
            print(f'❌ 预测功能: 失败 - {data.get("error")}')
    else:
        print(f'❌ 预测功能: HTTP {r.status_code}')
except Exception as e:
    print(f'❌ 预测功能: 异常 - {str(e)}')

# 3. Streamlit检查
try:
    r = requests.get('http://localhost:8501', timeout=5)
    if r.status_code == 200:
        print(f'✅ Streamlit: 正常')
    else:
        print(f'❌ Streamlit: 异常 ({r.status_code})')
except Exception as e:
    print(f'❌ Streamlit: 连接失败')

print('')
print('🎯 系统状态: 就绪')
print('🌐 前端地址: http://localhost:8501')
print('📚 API文档: http://localhost:8000/docs')
