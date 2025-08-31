import requests, sys, json
req={'stock_code':'000001','period':'6mo','pred_len':3,'lookback':100,'sample_count':1}
r=requests.post('http://localhost:8000/predict', json=req, timeout=60)
print('status', r.status_code)
try:
    j=r.json()
    print('success', j.get('success'))
    d=j.get('data')
    print('data is None?', d is None)
    if isinstance(d, dict):
        s=d.get('summary')
        print('summary is None?', s is None)
        if isinstance(s, dict):
            print('summary keys', sorted(list(s.keys())))
except Exception as e:
    print('json parse err', e)
    print('text', r.text[:400])
    sys.exit(1)

