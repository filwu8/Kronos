#!/usr/bin/env python3
import requests
import json

print('🧪 测试日期修复')
print('=' * 30)

try:
    response = requests.post('http://localhost:8000/predict', 
                           json={'stock_code': '000001', 'pred_len': 5}, 
                           timeout=15)
    
    if response.status_code == 200:
        data = response.json()
        if data.get('success'):
            predictions = data['data']['predictions']
            print(f'✅ 预测成功，获得 {len(predictions)} 条预测数据')
            print('📅 预测日期:')
            for i, pred in enumerate(predictions):
                print(f'   {i+1}. {pred["date"]} - 收盘价: ¥{pred["close"]:.2f}')
        else:
            print(f'❌ 预测失败: {data.get("error")}')
    else:
        print(f'❌ HTTP错误: {response.status_code}')
        
except Exception as e:
    print(f'❌ 请求异常: {str(e)}')
