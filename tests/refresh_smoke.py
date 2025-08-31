import sys
sys.path.insert(0,'.')
from app.data_fetcher import AStockDataFetcher
f=AStockDataFetcher()
res=f.refresh_stock_cache('000001','6mo')
print(res)

