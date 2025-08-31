#!/usr/bin/env python3
import requests

print('🧪 快速刷新验证')
print('=' * 40)

try:
    r = requests.post('http://localhost:8000/refresh/000001', params={'period':'6mo'}, timeout=60)
    if r.status_code == 200:
        data = r.json()
        if data.get('success'):
            info = data.get('data', {})
            print(f"✅ 刷新成功: 来源={info.get('source')} 最后日期={info.get('last_date')} 行数={info.get('rows')}")
        else:
            print(f"❌ 刷新失败: {data.get('error')}")
    else:
        print(f"❌ 刷新请求失败: HTTP {r.status_code}")
except Exception as e:
    print(f"❌ 刷新异常: {str(e)}")

