"""
股票数据模型
"""
from dataclasses import dataclass
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np


@dataclass
class StockInfo:
    """股票基本信息"""
    code: str
    name: str
    exchange: Optional[str] = None
    industry: Optional[str] = None
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return f"{self.code} {self.name}" if self.name else self.code
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'code': self.code,
            'name': self.name,
            'exchange': self.exchange or '',
            'industry': self.industry or ''
        }


class StockData:
    """股票数据管理类"""
    
    def __init__(self, df: pd.DataFrame, stock_info: StockInfo):
        self.df = df.copy()
        self.stock_info = stock_info
        self._indicators_calculated = False
        self._validate_and_preprocess()
    
    def _validate_and_preprocess(self):
        """验证并预处理数据"""
        required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
        
        # 检查必要列
        for col in required_columns:
            if col not in self.df.columns:
                raise ValueError(f"缺少必要列: {col}")
        
        # 确保日期格式正确
        if not pd.api.types.is_datetime64_any_dtype(self.df['date']):
            self.df['date'] = pd.to_datetime(self.df['date'])
        
        # 按日期排序
        self.df = self.df.sort_values('date').reset_index(drop=True)
        
        # 计算技术指标
        self._calculate_indicators()
    
    def _calculate_indicators(self):
        """计算技术指标（带缓存）"""
        if self._indicators_calculated:
            return
        
        # 移动平均线
        self.df['ma10'] = self.df['close'].rolling(window=10, min_periods=1).mean()
        self.df['ma20'] = self.df['close'].rolling(window=20, min_periods=1).mean()
        
        # 成交量移动平均
        self.df['volume_ma10'] = self.df['volume'].rolling(window=10, min_periods=1).mean()
        
        # 涨跌幅
        self.df['change_pct'] = self.df['close'].pct_change() * 100
        
        # 振幅
        self.df['amplitude'] = (self.df['high'] - self.df['low']) / self.df['close'] * 100
        
        self._indicators_calculated = True
    
    @property
    def start_date(self) -> pd.Timestamp:
        """获取开始日期"""
        return self.df['date'].min()
    
    @property
    def end_date(self) -> pd.Timestamp:
        """获取结束日期"""
        return self.df['date'].max()
    
    @property
    def trading_days(self) -> int:
        """获取交易日数量"""
        return len(self.df)
    
    def get_data_in_range(self, start: Optional[pd.Timestamp] = None, 
                          end: Optional[pd.Timestamp] = None) -> pd.DataFrame:
        """获取指定日期范围的数据"""
        mask = pd.Series(True, index=self.df.index)
        if start is not None:
            mask &= self.df['date'] >= start
        if end is not None:
            mask &= self.df['date'] <= end
        return self.df[mask].copy()
    
    def get_latest_price(self) -> float:
        """获取最新价格"""
        return self.df['close'].iloc[-1]
    
    def get_price_at(self, date: pd.Timestamp) -> Optional[float]:
        """获取指定日期的价格"""
        row = self.df[self.df['date'] == date]
        if not row.empty:
            return row['close'].iloc[0]
        return None
    
    def is_bullish_arrangement(self, idx: int) -> bool:
        """检查指定位置是否为均线多头排列"""
        if idx < 0 or idx >= len(self.df):
            return False
        return self.df['ma10'].iloc[idx] > self.df['ma20'].iloc[idx]
    
    def is_bearish_arrangement(self, idx: int) -> bool:
        """检查指定位置是否为均线空头排列"""
        if idx < 0 or idx >= len(self.df):
            return False
        return self.df['ma10'].iloc[idx] < self.df['ma20'].iloc[idx]
    
    def get_consecutive_bearish_days(self, idx: int) -> int:
        """获取连续空头排列天数（截止到指定位置）"""
        if idx < 0 or idx >= len(self.df):
            return 0
        
        count = 0
        for i in range(idx, -1, -1):
            if self.is_bearish_arrangement(i):
                count += 1
            else:
                break
        return count
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'stock_info': self.stock_info.to_dict(),
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'trading_days': self.trading_days,
            'latest_price': self.get_latest_price()
        }
