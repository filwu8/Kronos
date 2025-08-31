import requests, sys, json

API='http://localhost:8000/predict'

req={
  'stock_code':'000001',
  'period':'6mo',
  'pred_len':10,
  'lookback':200,
  'sample_count':1,
  'debug': False
}

r=requests.post(API, json=req, timeout=120)
print('status', r.status_code)
if r.status_code!=200:
    print(r.text)
    sys.exit(1)

data=r.json()
assert data.get('success'), data
pred=data['data']['predictions']

def is_num(x):
    try:
        float(x); return True
    except: return False

# Basic OHLC and uncertainty checks
for i,row in enumerate(pred):
    # required
    for k in ['open','high','low','close']:
        assert k in row and is_num(row[k]), f'missing {k} at {i}'
    o=float(row['open']); h=float(row['high']); l=float(row['low']); c=float(row['close'])
    assert h>=max(o,c)-1e-9, f'h<{max(o,c)} at {i}'
    assert l<=min(o,c)+1e-9, f'l>{min(o,c)} at {i}'

    # uncertainty if present
    if all(k in row for k in ['close_upper','close_lower']):
        up=float(row['close_upper']); lo=float(row['close_lower'])
        assert lo<=c<=up, f'close not within bounds at {i}: {lo} {c} {up}'
        if 'close_max' in row: assert float(row['close_max'])>=up-1e-9
        if 'close_min' in row: assert float(row['close_min'])<=lo+1e-9

print('sanity ok, n=', len(pred))

