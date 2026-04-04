"""
类型定义模块
提供类型别名和协议定义
"""
from typing import Protocol, Dict, List, Any, Optional, Union, Callable, TypeVar
import pandas as pd
import numpy as np
from datetime import datetime


T = TypeVar('T')


class DataValidator(Protocol):
    """数据验证器协议"""
    
    def validate(self, data: pd.DataFrame) -> bool:
        """验证数据"""
        ...


class Strategy(Protocol):
    """策略协议"""
    
    def analyze(self, data: pd.DataFrame) -> List[Dict[str, Any]]:
        """分析数据并生成信号"""
        ...


class ChartGenerator(Protocol):
    """图表生成器协议"""
    
    def generate(self, data: pd.DataFrame, signals: List[Any]) -> Any:
        """生成图表"""
        ...


StockCode = str
StockName = str
Price = float
Volume = int
Percentage = float
Timestamp = Union[pd.Timestamp, datetime, str]

StockDataDict = Dict[str, Union[str, int, float]]
SignalDict = Dict[str, Any]
ConfigDict = Dict[str, Union[int, float, str, bool]]
StatisticsDict = Dict[str, Union[int, float, str]]

PriceSeries = pd.Series
VolumeSeries = pd.Series
IndicatorSeries = pd.Series

DataFrameTransformer = Callable[[pd.DataFrame], pd.DataFrame]
SignalFilter = Callable[[List[Dict]], List[Dict]]


class MarketData:
    """市场数据类型"""
    open: PriceSeries
    high: PriceSeries
    low: PriceSeries
    close: PriceSeries
    volume: VolumeSeries
    date: pd.Series


class TechnicalIndicators:
    """技术指标类型"""
    ma_short: IndicatorSeries
    ma_long: IndicatorSeries
    volume_ma: IndicatorSeries
    change_pct: IndicatorSeries
    amplitude: IndicatorSeries


class SignalCondition:
    """信号条件类型"""
    passed: bool
    details: List[str]
    condition_id: int


class BacktestResult:
    """回测结果类型"""
    total_return: float
    annual_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades: int
    profit_trades: int
    loss_trades: int
