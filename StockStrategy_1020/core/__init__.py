"""
核心功能模块
"""
from .backtest_engine import BacktestEngine, BacktestMetrics, Trade
from .data_validator import DataValidator, validate_stock_data

__all__ = [
    'BacktestEngine',
    'BacktestMetrics',
    'Trade',
    'DataValidator',
    'validate_stock_data',
]
