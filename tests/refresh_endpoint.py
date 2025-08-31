import requests
import sys

url = 'http://localhost:8000/refresh/000001'
try:
    r = requests.post(url, params={'period':'6mo'}, timeout=120)
    print('status', r.status_code)
    if r.headers.get('content-type','').startswith('application/json'):
        print(r.json())
    else:
        print(r.text[:400])
except Exception as e:
    print('request failed:', e)
    sys.exit(1)

