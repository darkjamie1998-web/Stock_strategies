"""
交易信号模型
定义信号类型和数据结构
"""
from enum import Enum, auto
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime
import pandas as pd


class TradingSignalType(Enum):
    """交易信号类型枚举"""
    DOUBLE_DRAGON_EMERGENCE = ("双龙出水", "买入", "#f56565", 1, [
        "首次放量站上双均线（收盘价>开盘价，收盘价>均线，偏差≤阈值）",
        "跳空且放量站上双均线",
        "空头转多头排列且放量"
    ])
    HIDDEN_DRAGON_DESCENT = ("潜龙入渊", "加码", "#f6ad55", 2, [
        "首次回踩10日均线（均线多头排列时，收盘价<开盘价，收盘价>均线，偏差≤阈值）"
    ])
    DRAGON_IN_FIELD = ("见龙在田", "加码", "#f6ad55", 3, [
        "首次回踩20日均线（均线多头排列时，收盘价<开盘价，收盘价>均线，偏差≤阈值）"
    ])
    DRAGON_BATTLE = ("龙战于野", "离场", "#48bb78", 4, [
        "连续2个交易日收盘价低于20日均线",
        "单日跌幅超过止损阈值并有效破位（收盘价低于20日均线止损阈值以上）"
    ])
    TAKE_PROFIT = ("收获果实", "止盈", "#9f7aea", 5, [
        "当日收盘价较买入或加码信号涨幅超过止盈阈值"
    ])
    
    def __init__(self, cn_name: str, action: str, color: str, priority: int, conditions: List[str]):
        self.cn_name = cn_name
        self.action = action
        self.color = color
        self.priority = priority
        self.conditions = conditions
    
    @property
    def display_name(self) -> str:
        """获取显示名称"""
        return f"{self.cn_name}（{self.action}）"


@dataclass
class TradingSignal:
    """交易信号数据类"""
    signal_type: TradingSignalType
    timestamp: pd.Timestamp
    price: float
    conditions: List[str]
    condition_id: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
    
    @property
    def signal_name(self) -> str:
        """获取信号名称"""
        return self.signal_type.cn_name
    
    @property
    def action(self) -> str:
        """获取操作类型"""
        return self.signal_type.action
    
    @property
    def color(self) -> str:
        """获取信号颜色"""
        return self.signal_type.color
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'signal_type': self.signal_type.name,
            'signal_name': self.signal_name,
            'action': self.action,
            'timestamp': self.timestamp.isoformat() if isinstance(self.timestamp, pd.Timestamp) else str(self.timestamp),
            'price': self.price,
            'conditions': self.conditions,
            'condition_id': self.condition_id,
            'color': self.color,
            'metadata': self.metadata
        }
    
    def __str__(self) -> str:
        return f"{self.signal_name} @ {self.timestamp.strftime('%Y-%m-%d')} - {self.price:.2f}"


@dataclass
class SignalResult:
    """信号分析结果"""
    signals: List[TradingSignal]
    statistics: Dict[str, Any]
    start_date: pd.Timestamp
    end_date: pd.Timestamp
    total_days: int
    
    def __post_init__(self):
        if not self.signals:
            self.signals = []
        if not self.statistics:
            self.statistics = self._calculate_statistics()
    
    def _calculate_statistics(self) -> Dict[str, Any]:
        """计算统计信息"""
        stats = {
            'total_signals': len(self.signals),
            'buy_signals': len([s for s in self.signals if s.signal_type == TradingSignalType.DOUBLE_DRAGON_EMERGENCE]),
            'add_signals': len([s for s in self.signals if s.signal_type in [
                TradingSignalType.HIDDEN_DRAGON_DESCENT, TradingSignalType.DRAGON_IN_FIELD
            ]]),
            'exit_signals': len([s for s in self.signals if s.signal_type == TradingSignalType.DRAGON_BATTLE]),
            'profit_signals': len([s for s in self.signals if s.signal_type == TradingSignalType.TAKE_PROFIT]),
        }
        
        # 计算收益率（简化版）
        if len(self.signals) >= 2:
            buy_signals = [s for s in self.signals if s.action in ['买入', '加码']]
            sell_signals = [s for s in self.signals if s.action in ['离场', '止盈']]
            
            if buy_signals and sell_signals:
                total_return = sum(s.price for s in sell_signals) / sum(s.price for s in buy_signals) - 1
                stats['estimated_return'] = f"{total_return * 100:.2f}%"
        
        return stats
    
    def get_signals_by_type(self, signal_type: TradingSignalType) -> List[TradingSignal]:
        """按类型获取信号"""
        return [s for s in self.signals if s.signal_type == signal_type]
    
    def get_signals_in_range(self, start: pd.Timestamp, end: pd.Timestamp) -> List[TradingSignal]:
        """获取时间范围内的信号"""
        return [s for s in self.signals if start <= s.timestamp <= end]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'signals': [s.to_dict() for s in self.signals],
            'statistics': self.statistics,
            'start_date': str(self.start_date),
            'end_date': str(self.end_date),
            'total_days': self.total_days
        }
