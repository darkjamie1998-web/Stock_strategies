import tushare as ts
import pandas as pd
import time
from datetime import datetime, timedelta


class TushareClient:
    _instance = None

    def __init__(self, token: str):
        self.token = token
        ts.set_token(token)
        self.pro = ts.pro_api()
        self._last_call = 0
        self._min_interval = 0.3

    def _rate_limit(self):
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

    def call(self, func_name: str, **kwargs):
        self._rate_limit()
        func = getattr(self.pro, func_name, None)
        if func is None:
            raise ValueError(f"Unknown tushare API: {func_name}")
        try:
            result = func(**kwargs)
            if result is None or result.empty:
                return pd.DataFrame()
            return result
        except Exception as e:
            raise RuntimeError(f"Tushare {func_name} error: {e}")

    def get_sw_index_list(self):
        return self.call('index_basic', market='SW')

    def get_sw_daily(self, ts_code: str, start_date: str = None, end_date: str = None):
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        return self.call('sw_daily', ts_code=ts_code, start_date=start_date, end_date=end_date)

    def get_ths_index_list(self):
        return self.call('ths_index', exchange='A', type='N')

    def get_ths_daily(self, ts_code: str, start_date: str = None, end_date: str = None):
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        return self.call('ths_daily', ts_code=ts_code, start_date=start_date, end_date=end_date)

    def get_fund_basic(self):
        return self.call('fund_basic', market='E')

    def get_fund_daily(self, ts_code: str, start_date: str = None, end_date: str = None):
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=90)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        return self.call('fund_daily', ts_code=ts_code, start_date=start_date, end_date=end_date)

    def get_daily_basic(self, ts_code: str, start_date: str = None, end_date: str = None):
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=30)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        return self.call('daily_basic', ts_code=ts_code, start_date=start_date, end_date=end_date)

    def get_index_weekly(self, ts_code: str, start_date: str = None, end_date: str = None):
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        return self.call('index_weekly', ts_code=ts_code, start_date=start_date, end_date=end_date)
