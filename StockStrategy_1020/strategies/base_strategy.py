"""
策略抽象基类
提供策略接口定义和通用功能
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
import pandas as pd
import logging

from models import TradingSignal, SignalResult, StockData
from config import TRADING_CONFIG


class BaseStrategy(ABC):
    """策略抽象基类"""
    
    def __init__(self, config=None):
        self.config = config or TRADING_CONFIG
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def analyze(self, stock_data: StockData) -> SignalResult:
        """
        分析股票数据，生成交易信号
        
        Args:
            stock_data: 股票数据对象
        
        Returns:
            信号分析结果
        """
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        pass
    
    @abstractmethod
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        pass
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """
        验证数据是否满足策略要求
        
        Args:
            df: 股票数据DataFrame
        
        Returns:
            是否有效
        """
        if df is None or len(df) < 2:
            self.logger.warning("数据不足，无法进行分析")
            return False
        return True
    
    def update_config(self, **kwargs):
        """
        更新策略配置
        
        Args:
            **kwargs: 配置参数
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key.upper()):
                setattr(self.config, key.upper(), value)
        self.logger.info(f"策略配置已更新: {kwargs}")
    
    def get_config_dict(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.config.to_dict() if hasattr(self.config, 'to_dict') else {}
    
    def _safe_get_value(self, row: pd.Series, col: str) -> float:
        """
        安全获取数值
        
        Args:
            row: 数据行
            col: 列名
        
        Returns:
            浮点数值
        """
        import numpy as np
        try:
            val = row[col]
            if isinstance(val, pd.Series):
                val = val.iloc[0] if len(val) > 0 else np.nan
            return float(val) if pd.notna(val) else np.nan
        except (KeyError, IndexError, TypeError, ValueError):
            return np.nan


class StrategyManager:
    """策略管理器"""
    
    def __init__(self):
        self._strategies: Dict[str, BaseStrategy] = {}
    
    def register(self, name: str, strategy: BaseStrategy):
        """注册策略"""
        self._strategies[name] = strategy
    
    def get(self, name: str) -> Optional[BaseStrategy]:
        """获取策略"""
        return self._strategies.get(name)
    
    def list_strategies(self) -> List[str]:
        """列出所有策略"""
        return list(self._strategies.keys())
    
    def get_strategy_info(self, name: str) -> Optional[Dict[str, str]]:
        """获取策略信息"""
        strategy = self.get(name)
        if strategy:
            return {
                'name': strategy.get_strategy_name(),
                'description': strategy.get_strategy_description()
            }
        return None
