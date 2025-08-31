import sys
sys.path.insert(0,'.')
from app.data_fetcher import AStockDataFetcher

f = AStockDataFetcher()
old = f._load_from_cache('000001')
print('old tz:', None if old is None else getattr(old.index, 'tz', None))
res = f.refresh_stock_cache('000001','6mo')
print('refresh result:', res)

