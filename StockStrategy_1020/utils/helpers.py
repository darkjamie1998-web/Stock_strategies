"""
通用辅助函数
"""
import pandas as pd
import numpy as np
from typing import Union, Optional
import re


def safe_get_value(row: Union[pd.Series, pd.DataFrame], col: str) -> float:
    """
    安全地从Series或DataFrame行中获取数值
    
    Args:
        row: 数据行
        col: 列名
        
    Returns:
        浮点数值，如果失败返回nan
    """
    try:
        val = row[col]
        if isinstance(val, pd.Series):
            val = val.iloc[0] if len(val) > 0 else np.nan
        return float(val) if pd.notna(val) else np.nan
    except (KeyError, IndexError, TypeError, ValueError):
        return np.nan


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    格式化百分比
    
    Args:
        value: 小数值（如0.05表示5%）
        decimals: 小数位数
        
    Returns:
        格式化后的字符串
    """
    return f"{value * 100:.{decimals}f}%"


def validate_stock_code(code: str) -> bool:
    """
    验证股票代码格式
    
    Args:
        code: 股票代码
        
    Returns:
        是否有效
    """
    if not code or not isinstance(code, str):
        return False
    
    # 支持格式：000001.SZ, 600000.SH, 000001 等
    pattern = r'^(\d{6})(\.([A-Z]{2}))?$'
    return bool(re.match(pattern, code))


def clean_stock_name(name: str) -> str:
    """
    清理股票名称
    
    Args:
        name: 原始名称
        
    Returns:
        清理后的名称
    """
    if not name:
        return ''
    
    # 移除特殊字符
    name = name.strip()
    name = name.lstrip('_')
    
    return name


def calculate_drawdown(prices: pd.Series) -> pd.Series:
    """
    计算回撤
    
    Args:
        prices: 价格序列
        
    Returns:
        回撤序列
    """
    cummax = prices.cummax()
    drawdown = (prices - cummax) / cummax
    return drawdown


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.03) -> float:
    """
    计算夏普比率
    
    Args:
        returns: 收益率序列
        risk_free_rate: 无风险利率（年化）
        
    Returns:
        夏普比率
    """
    if len(returns) < 2:
        return 0.0
    
    # 假设returns是日收益率
    excess_returns = returns - risk_free_rate / 252
    
    if excess_returns.std() == 0:
        return 0.0
    
    sharpe = excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    return sharpe


def resample_data(df: pd.DataFrame, rule: str = 'W') -> pd.DataFrame:
    """
    重采样数据
    
    Args:
        df: 原始数据，需要包含date, open, high, low, close, volume列
        rule: 重采样规则，'W'为周，'M'为月
        
    Returns:
        重采样后的数据
    """
    df = df.copy()
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    
    resampled = df.resample(rule).agg({
        'open': 'first',
        'high': 'max',
        'low': 'min',
        'close': 'last',
        'volume': 'sum'
    }).dropna()
    
    resampled.reset_index(inplace=True)
    return resampled
