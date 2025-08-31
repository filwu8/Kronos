#!/usr/bin/env python3
import requests

try:
    response = requests.post(
        'http://localhost:8000/predict', 
        json={
            'stock_code': '000968', 
            'pred_len': 5, 
            'sample_count': 1
        }, 
        timeout=30
    )
    
    print(f'状态码: {response.status_code}')
    
    if response.status_code == 200:
        result = response.json()
        print(f'成功: {result.get("success")}')
        if result.get("success"):
            predictions = result["data"]["predictions"]
            print(f'预测天数: {len(predictions)}')
            
            # 检查第一天的OHLC关系
            first_day = predictions[0]
            o, h, l, c = first_day['open'], first_day['high'], first_day['low'], first_day['close']
            print(f'第一天: O={o:.2f}, H={h:.2f}, L={l:.2f}, C={c:.2f}')
            
            # 验证OHLC关系
            min_oc = min(o, c)
            max_oc = max(o, c)
            if l <= min_oc <= max_oc <= h:
                print('✅ OHLC关系正确')
            else:
                print('❌ OHLC关系异常')
        else:
            print(f'预测失败: {result.get("error")}')
    else:
        print(f'API错误: {response.text}')
        
except Exception as e:
    print(f'测试失败: {e}')
