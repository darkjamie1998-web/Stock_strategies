"""
优化后的策略服务模块
使用向量化计算和策略抽象基类
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

from config import TRADING_CONFIG
from models import TradingSignal, TradingSignalType, SignalResult, StockData
from strategies.base_strategy import BaseStrategy


logger = logging.getLogger(__name__)


@dataclass
class ConditionCheck:
    """条件检查结果"""
    passed: bool
    details: List[str]
    condition_id: int = 0


class VectorizedSignalChecker:
    """向量化信号检查器 - 提高性能"""
    
    def __init__(self, config=None):
        self.config = config or TRADING_CONFIG
    
    def check_all_conditions_vectorized(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        向量化检查所有条件
        
        Args:
            df: 股票数据DataFrame
        
        Returns:
            包含所有条件检查结果的DataFrame
        """
        result_df = df.copy()
        
        result_df['is_bullish'] = result_df['ma10'] > result_df['ma20']
        result_df['is_bearish'] = result_df['ma10'] < result_df['ma20']
        
        result_df['volume_surge'] = (
            (result_df['volume'] - result_df['volume_ma10']) / result_df['volume_ma10'] > self.config.VOLUME_THRESHOLD
        ) & (
            result_df['volume'] > result_df['volume'].shift(1) * (1 + self.config.VOLUME_THRESHOLD)
        )
        
        result_df['gap_up'] = result_df['low'] > result_df['high'].shift(1)
        
        result_df['stand_ma10'] = (
            (result_df['close'] > result_df['open']) &
            (result_df['close'] > result_df['ma10']) &
            (abs(result_df['close'] - result_df['ma10']) / result_df['ma10'] <= self.config.STAND_THRESHOLD)
        )
        
        result_df['stand_ma20'] = (
            (result_df['close'] > result_df['open']) &
            (result_df['close'] > result_df['ma20']) &
            (abs(result_df['close'] - result_df['ma20']) / result_df['ma20'] <= self.config.STAND_THRESHOLD)
        )
        
        result_df['pullback_ma10'] = (
            (result_df['close'] < result_df['open']) &
            (result_df['close'] > result_df['ma10']) &
            (abs(result_df['close'] - result_df['ma10']) / result_df['ma10'] <= self.config.PULLBACK_THRESHOLD)
        )
        
        result_df['pullback_ma20'] = (
            (result_df['close'] < result_df['open']) &
            (result_df['close'] > result_df['ma20']) &
            (abs(result_df['close'] - result_df['ma20']) / result_df['ma20'] <= self.config.PULLBACK_THRESHOLD)
        )
        
        result_df['first_above_ma10'] = result_df['close'].shift(1) <= result_df['ma10'].shift(1)
        result_df['first_above_ma20'] = result_df['close'].shift(1) <= result_df['ma20'].shift(1)
        
        result_df['below_ma20_2days'] = (
            (result_df['close'] < result_df['ma20']) &
            (result_df['close'].shift(1) < result_df['ma20'].shift(1))
        )
        
        result_df['bullish_cross'] = (
            (result_df['ma10'].shift(1) < result_df['ma20'].shift(1)) &
            (result_df['ma10'] > result_df['ma20'])
        )
        
        return result_df


class OptimizedStrategyService(BaseStrategy):
    """优化后的策略服务类"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.checker = VectorizedSignalChecker(config)
    
    def get_strategy_name(self) -> str:
        """获取策略名称"""
        return "1020双均线策略"
    
    def get_strategy_description(self) -> str:
        """获取策略描述"""
        return "基于10日和20日均线的交易信号策略，包括双龙出水、潜龙入渊、见龙在田、龙战于野等信号"
    
    def analyze(self, stock_data: StockData) -> SignalResult:
        """
        分析股票数据，生成交易信号（优化版）
        
        使用向量化计算提高性能
        """
        try:
            df = stock_data.df
            
            if not self.validate_data(df):
                return SignalResult(
                    signals=[],
                    statistics={'error': '数据不足'},
                    start_date=stock_data.start_date,
                    end_date=stock_data.end_date,
                    total_days=len(df) if df is not None else 0
                )
            
            result_df = self.checker.check_all_conditions_vectorized(df)
            
            signals = self._generate_signals_vectorized(result_df)
            
            logger.info(f"分析完成，生成 {len(signals)} 个信号")
            
            return SignalResult(
                signals=signals,
                statistics={},
                start_date=stock_data.start_date,
                end_date=stock_data.end_date,
                total_days=stock_data.trading_days
            )
        
        except Exception as e:
            logger.error(f"策略分析失败: {e}", exc_info=True)
            raise
    
    def _generate_signals_vectorized(self, df: pd.DataFrame) -> List[TradingSignal]:
        """
        向量化生成信号
        
        Args:
            df: 包含条件检查结果的DataFrame
        
        Returns:
            信号列表
        """
        signals = []
        
        last_buy_idx = -self.config.SIGNAL_WINDOW - 1
        last_exit_idx = -self.config.SIGNAL_WINDOW - 1
        has_position = False
        last_buy_price = 0.0
        
        bearish_count = 0
        
        for i in range(1, len(df)):
            current = df.iloc[i]
            
            if current['is_bearish']:
                bearish_count += 1
            else:
                bearish_count = 0
            
            skip_signals = bearish_count >= self.config.BEARISH_LIMIT
            
            signal = None
            
            if not skip_signals and not has_position:
                signal = self._check_buy_signal_vectorized(current, i, last_exit_idx)
            
            if signal is None and current['is_bullish'] and has_position:
                signal = self._check_add_signal_vectorized(current, i, last_buy_idx)
            
            if signal is None and has_position:
                signal = self._check_exit_signal_vectorized(current, i, last_buy_idx, last_buy_price)
            
            if signal is None and has_position:
                signal = self._check_take_profit_signal_vectorized(current, last_buy_price)
            
            if signal:
                signals.append(signal)
                
                if signal.action == '买入':
                    has_position = True
                    last_buy_idx = i
                    last_buy_price = signal.price
                elif signal.action == '加码':
                    last_buy_idx = i
                    last_buy_price = signal.price
                elif signal.action == '离场':
                    has_position = False
                    last_exit_idx = i
                elif signal.action == '止盈':
                    last_buy_idx = i
                    last_buy_price = signal.price
        
        return signals
    
    def _check_buy_signal_vectorized(self, current: pd.Series, idx: int, last_exit_idx: int) -> Optional[TradingSignal]:
        """检查买入信号（向量化版）"""
        if idx - last_exit_idx <= self.config.SIGNAL_WINDOW:
            return None
        
        conditions = []
        condition_id = 0
        
        if (current['first_above_ma10'] and current['stand_ma10'] and 
            current['stand_ma20'] and current['volume_surge']):
            conditions = ["首次放量站上双均线"]
            condition_id = 1
        
        elif condition_id == 0 and (current['gap_up'] and current['stand_ma10'] and 
                                     current['stand_ma20'] and current['volume_surge']):
            conditions = ["跳空且放量站上双均线"]
            condition_id = 2
        
        elif condition_id == 0 and (current['bullish_cross'] and current['volume_surge']):
            conditions = ["空头转多头排列且放量"]
            condition_id = 3
        
        if condition_id > 0:
            return TradingSignal(
                signal_type=TradingSignalType.DOUBLE_DRAGON_EMERGENCE,
                timestamp=current['date'],
                price=current['close'],
                conditions=conditions,
                condition_id=condition_id
            )
        
        return None
    
    def _check_add_signal_vectorized(self, current: pd.Series, idx: int, last_buy_idx: int) -> Optional[TradingSignal]:
        """检查加码信号（向量化版）"""
        if idx - last_buy_idx <= self.config.SIGNAL_WINDOW:
            return None
        
        if current['first_above_ma10'] and current['pullback_ma10']:
            return TradingSignal(
                signal_type=TradingSignalType.HIDDEN_DRAGON_DESCENT,
                timestamp=current['date'],
                price=current['close'],
                conditions=["首次回踩10日均线"]
            )
        
        if current['first_above_ma20'] and current['pullback_ma20']:
            return TradingSignal(
                signal_type=TradingSignalType.DRAGON_IN_FIELD,
                timestamp=current['date'],
                price=current['close'],
                conditions=["首次回踩20日均线"]
            )
        
        return None
    
    def _check_exit_signal_vectorized(self, current: pd.Series, idx: int, 
                                       last_buy_idx: int, last_buy_price: float) -> Optional[TradingSignal]:
        """检查离场信号（向量化版）"""
        if idx - last_buy_idx <= self.config.SIGNAL_WINDOW:
            return None
        
        conditions = []
        condition_id = 0
        
        if current['below_ma20_2days']:
            conditions = ["连续2个交易日收盘价低于20日均线"]
            condition_id = 1
        
        elif last_buy_price > 0:
            change_pct = (current['close'] - last_buy_price) / last_buy_price
            if change_pct < -self.config.STOP_LOSS_THRESHOLD:
                effective_break = current['close'] < current['ma20'] * (1 - self.config.BREAKDOWN_THRESHOLD)
                if effective_break:
                    conditions = [
                        f"跌幅{change_pct:.2%}超过止损阈值",
                        "有效破位"
                    ]
                    condition_id = 2
        
        if condition_id > 0:
            return TradingSignal(
                signal_type=TradingSignalType.DRAGON_BATTLE,
                timestamp=current['date'],
                price=current['close'],
                conditions=conditions,
                condition_id=condition_id
            )
        
        return None
    
    def _check_take_profit_signal_vectorized(self, current: pd.Series, last_buy_price: float) -> Optional[TradingSignal]:
        """检查止盈信号（向量化版）"""
        if last_buy_price <= 0:
            return None
        
        change_pct = (current['close'] - last_buy_price) / last_buy_price
        
        if change_pct >= self.config.TAKE_PROFIT_THRESHOLD:
            return TradingSignal(
                signal_type=TradingSignalType.TAKE_PROFIT,
                timestamp=current['date'],
                price=current['close'],
                conditions=[f"涨幅{change_pct:.2%}达到止盈阈值"]
            )
        
        return None


StrategyService = OptimizedStrategyService
