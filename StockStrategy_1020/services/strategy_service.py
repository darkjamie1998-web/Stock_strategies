"""
策略服务模块
封装1020策略的核心逻辑
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple, Dict, Any, Union
from dataclasses import dataclass
import logging

from config import TRADING_CONFIG
from models import TradingSignal, TradingSignalType, SignalResult, StockData

logger = logging.getLogger(__name__)


@dataclass
class ConditionCheck:
    """条件检查结果"""
    passed: bool
    details: List[str]
    condition_id: int = 0


class SignalConditionChecker:
    """信号条件检查器"""
    
    def __init__(self, config=None):
        self.config = config or TRADING_CONFIG
    
    def _get_value(self, row, col: str) -> float:
        """安全获取数值"""
        val = row[col]
        if isinstance(val, pd.Series):
            val = val.iloc[0] if len(val) > 0 else np.nan
        return float(val) if pd.notna(val) else np.nan
    
    def check_volume_surge(self, current: pd.Series, prev: pd.Series) -> ConditionCheck:
        """检查是否放量"""
        current_vol = self._get_value(current, 'volume')
        prev_vol = self._get_value(prev, 'volume')
        vol_ma10 = self._get_value(current, 'volume_ma10')
        
        if any(np.isnan([current_vol, prev_vol, vol_ma10])):
            return ConditionCheck(False, ["成交量数据缺失"])
        
        if vol_ma10 <= 0 or prev_vol <= 0:
            return ConditionCheck(False, ["成交量数据无效"])
        
        vs_ma10 = (current_vol - vol_ma10) / vol_ma10 > self.config.VOLUME_THRESHOLD
        vs_prev = (current_vol - prev_vol) / prev_vol > self.config.VOLUME_THRESHOLD
        
        passed = vs_ma10 and vs_prev
        details = [
            f"成交量vs10日均值: {vs_ma10} ({current_vol/vol_ma10:.2%})",
            f"成交量vs前一日: {vs_prev} ({current_vol/prev_vol:.2%})"
        ]
        
        return ConditionCheck(passed, details)
    
    def check_gap_up(self, current: pd.Series, prev: pd.Series) -> ConditionCheck:
        """检查是否跳空"""
        current_low = self._get_value(current, 'low')
        prev_high = self._get_value(prev, 'high')
        
        if any(np.isnan([current_low, prev_high])):
            return ConditionCheck(False, ["价格数据缺失"])
        
        passed = current_low > prev_high
        return ConditionCheck(passed, [f"跳空: {passed} (当日最低{current_low:.2f} > 前日最高{prev_high:.2f})"])
    
    def check_stand_on_ma(self, current: pd.Series, ma_col: str) -> ConditionCheck:
        """检查是否站上均线"""
        close = self._get_value(current, 'close')
        open_price = self._get_value(current, 'open')
        ma = self._get_value(current, ma_col)
        
        if any(np.isnan([close, open_price, ma])):
            return ConditionCheck(False, ["价格数据缺失"])
        
        close_above_open = close > open_price
        close_above_ma = close > ma
        deviation = abs(close - ma) / ma <= self.config.STAND_THRESHOLD
        
        passed = close_above_open and close_above_ma and deviation
        details = [
            f"收盘价>开盘价: {close_above_open}",
            f"收盘价>均线: {close_above_ma}",
            f"偏差≤阈值: {deviation} ({abs(close-ma)/ma:.2%})"
        ]
        
        return ConditionCheck(passed, details)
    
    def check_pullback_to_ma(self, current: pd.Series, ma_col: str) -> ConditionCheck:
        """检查是否回踩均线"""
        close = self._get_value(current, 'close')
        open_price = self._get_value(current, 'open')
        ma = self._get_value(current, ma_col)
        
        if any(np.isnan([close, open_price, ma])):
            return ConditionCheck(False, ["价格数据缺失"])
        
        close_below_open = close < open_price
        close_above_ma = close > ma
        deviation = abs(close - ma) / ma <= self.config.PULLBACK_THRESHOLD
        
        passed = close_below_open and close_above_ma and deviation
        details = [
            f"收盘价<开盘价: {close_below_open}",
            f"收盘价>均线: {close_above_ma}",
            f"偏差≤阈值: {deviation} ({abs(close-ma)/ma:.2%})"
        ]
        
        return ConditionCheck(passed, details)
    
    def check_first_time_above_ma(self, current: pd.Series, prev: pd.Series, ma_col: str) -> ConditionCheck:
        """检查是否首次站上均线"""
        prev_close = self._get_value(prev, 'close')
        prev_ma = self._get_value(prev, ma_col)
        
        if any(np.isnan([prev_close, prev_ma])):
            return ConditionCheck(False, ["前日数据缺失"])
        
        passed = prev_close <= prev_ma
        return ConditionCheck(passed, [f"首次站上: {passed} (前日收盘{prev_close:.2f} ≤ 前日均线{prev_ma:.2f})"])


class StrategyService:
    """策略服务类"""
    
    def __init__(self, config=None):
        self.config = config or TRADING_CONFIG
        self.checker = SignalConditionChecker(config)
    
    def analyze(self, stock_data: StockData) -> SignalResult:
        """分析股票数据，生成交易信号"""
        try:
            df = stock_data.df
            signals = []
            
            # 验证数据
            if df is None or len(df) < 2:
                logger.warning("数据不足，无法进行分析")
                return SignalResult(
                    signals=[],
                    statistics={'error': '数据不足'},
                    start_date=stock_data.start_date if hasattr(stock_data, 'start_date') else pd.Timestamp.now(),
                    end_date=stock_data.end_date if hasattr(stock_data, 'end_date') else pd.Timestamp.now(),
                    total_days=len(df) if df is not None else 0
                )
            
            # 状态追踪
            last_buy_idx = -self.config.SIGNAL_WINDOW - 1
            last_exit_idx = -self.config.SIGNAL_WINDOW - 1
            has_position = False
            last_buy_price = 0.0
            
            for i in range(1, len(df)):
                current = df.iloc[i]
                prev = df.iloc[i-1]
                
                # 检查均线排列
                is_bullish = stock_data.is_bullish_arrangement(i)
                is_bearish = stock_data.is_bearish_arrangement(i)
                
                # 连续空头排列天数
                bearish_days = stock_data.get_consecutive_bearish_days(i)
                skip_signals = bearish_days >= self.config.BEARISH_LIMIT
                
                signal = None
                
                # 1. 检查买入信号（双龙出水）
                if not skip_signals:
                    signal = self._check_buy_signal(
                        current, prev, df, i, 
                        has_position, last_buy_idx, last_exit_idx
                    )
                
                # 2. 检查加码信号（多头排列时）
                if signal is None and is_bullish and has_position:
                    signal = self._check_add_signals(
                        current, prev, df, i, last_buy_idx
                    )
                
                # 3. 检查离场信号
                if signal is None and has_position:
                    signal = self._check_exit_signal(
                        current, prev, df, i,
                        has_position, last_buy_idx, last_buy_price
                    )
                
                # 4. 检查止盈信号
                if signal is None and has_position:
                    signal = self._check_take_profit(
                        current, last_buy_price
                    )
                
                # 记录信号
                if signal:
                    signals.append(signal)
                    
                    # 更新状态
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
                        # 止盈信号不清仓，保持持仓状态，只更新买入索引和价格
                        last_buy_idx = i
                        last_buy_price = signal.price
            
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
    
    def _check_buy_signal(self, current, prev, df, i, has_position, last_buy_idx, last_exit_idx) -> Optional[TradingSignal]:
        """检查买入信号（双龙出水）"""
        try:
            timestamp = current['date']
            price = self.checker._get_value(current, 'close')
            
            # 约束：买入信号后无离场信号不产生新买入信号
            if has_position:
                return None
            
            # 约束：离场信号后无买入信号不产生新离场信号（这里检查是否可以产生买入）
            if i - last_exit_idx <= self.config.SIGNAL_WINDOW:
                return None
            
            conditions = []
            condition_id = 0
            
            # 条件1：首次放量站上双均线
            is_first_above = self.checker.check_first_time_above_ma(current, prev, 'ma10')
            stand_ma10 = self.checker.check_stand_on_ma(current, 'ma10')
            stand_ma20 = self.checker.check_stand_on_ma(current, 'ma20')
            volume_surge = self.checker.check_volume_surge(current, prev)
            
            if is_first_above.passed and stand_ma10.passed and stand_ma20.passed and volume_surge.passed:
                conditions.extend(is_first_above.details + stand_ma10.details + stand_ma20.details + volume_surge.details)
                condition_id = 1
            
            # 条件2：跳空且放量站上双均线
            if condition_id == 0:
                gap_up = self.checker.check_gap_up(current, prev)
                if gap_up.passed and stand_ma10.passed and stand_ma20.passed and volume_surge.passed:
                    conditions.extend(gap_up.details + stand_ma10.details + stand_ma20.details + volume_surge.details)
                    condition_id = 2
            
            # 条件3：空头转多头排列且放量
            if condition_id == 0 and i > 1:
                prev_prev = df.iloc[i-2]
                prev_ma10 = self.checker._get_value(prev, 'ma10')
                prev_ma20 = self.checker._get_value(prev, 'ma20')
                curr_ma10 = self.checker._get_value(current, 'ma10')
                curr_ma20 = self.checker._get_value(current, 'ma20')
                
                if prev_ma10 < prev_ma20 and curr_ma10 > curr_ma20:
                    prev_volume_surge = self.checker.check_volume_surge(prev, prev_prev)
                    if volume_surge.passed or prev_volume_surge.passed:
                        conditions.append(f"空头转多头: {prev_ma10:.2f}<{prev_ma20:.2f} -> {curr_ma10:.2f}>{curr_ma20:.2f}")
                        conditions.extend(volume_surge.details)
                        condition_id = 3
            
            if condition_id > 0:
                logger.debug(f"检测到买入信号（条件{condition_id}）: {timestamp}")
                return TradingSignal(
                    signal_type=TradingSignalType.DOUBLE_DRAGON_EMERGENCE,
                    timestamp=timestamp,
                    price=price,
                    conditions=conditions,
                    condition_id=condition_id
                )
            
            return None
        except Exception as e:
            logger.warning(f"检查买入信号时出错: {e}")
            return None
    
    def _check_add_signals(self, current, prev, df, i, last_buy_idx) -> Optional[TradingSignal]:
        """检查加码信号"""
        try:
            timestamp = current['date']
            price = self.checker._get_value(current, 'close')
            
            # 约束：信号屏蔽窗口
            if i - last_buy_idx <= self.config.SIGNAL_WINDOW:
                return None
            
            prev_close = self.checker._get_value(prev, 'close')
            prev_ma10 = self.checker._get_value(prev, 'ma10')
            prev_ma20 = self.checker._get_value(prev, 'ma20')
            
            # 潜龙入渊：首次回踩10日均线
            if prev_close > prev_ma10:
                pullback = self.checker.check_pullback_to_ma(current, 'ma10')
                if pullback.passed:
                    logger.debug(f"检测到潜龙入渊信号: {timestamp}")
                    return TradingSignal(
                        signal_type=TradingSignalType.HIDDEN_DRAGON_DESCENT,
                        timestamp=timestamp,
                        price=price,
                        conditions=pullback.details
                    )
            
            # 见龙在田：首次回踩20日均线
            if prev_close > prev_ma20:
                pullback = self.checker.check_pullback_to_ma(current, 'ma20')
                if pullback.passed:
                    logger.debug(f"检测到见龙在田信号: {timestamp}")
                    return TradingSignal(
                        signal_type=TradingSignalType.DRAGON_IN_FIELD,
                        timestamp=timestamp,
                        price=price,
                        conditions=pullback.details
                    )
            
            return None
        except Exception as e:
            logger.warning(f"检查加码信号时出错: {e}")
            return None
    
    def _check_exit_signal(self, current, prev, df, i, has_position, last_buy_idx, last_buy_price) -> Optional[TradingSignal]:
        """检查离场信号（龙战于野）"""
        try:
            # 约束：信号屏蔽窗口内不考虑离场信号
            if i - last_buy_idx <= self.config.SIGNAL_WINDOW:
                return None
            
            timestamp = current['date']
            close = self.checker._get_value(current, 'close')
            ma20 = self.checker._get_value(current, 'ma20')
            
            conditions = []
            condition_id = 0
            
            # 条件1：连续2个交易日收盘价低于20日均线
            if i > 0:
                prev_close = self.checker._get_value(prev, 'close')
                prev_ma20 = self.checker._get_value(prev, 'ma20')
                
                if close < ma20 and prev_close < prev_ma20:
                    conditions.append(f"连续2日低于MA20: 前日{prev_close:.2f}<{prev_ma20:.2f}, 当日{close:.2f}<{ma20:.2f}")
                    condition_id = 1
            
            # 条件2：单日跌幅超过止损阈值并有效破位
            if condition_id == 0 and last_buy_price > 0:
                change_pct = (close - last_buy_price) / last_buy_price
                if change_pct < -self.config.STOP_LOSS_THRESHOLD:
                    effective_break = close < ma20 * (1 - self.config.BREAKDOWN_THRESHOLD)
                    if effective_break:
                        conditions.append(f"跌幅{change_pct:.2%}超过止损阈值{self.config.STOP_LOSS_THRESHOLD:.0%}")
                        conditions.append(f"有效破位: {close:.2f} < {ma20 * (1 - self.config.BREAKDOWN_THRESHOLD):.2f}")
                        condition_id = 2
            
            if condition_id > 0:
                logger.debug(f"检测到离场信号（条件{condition_id}）: {timestamp}")
                return TradingSignal(
                    signal_type=TradingSignalType.DRAGON_BATTLE,
                    timestamp=timestamp,
                    price=close,
                    conditions=conditions,
                    condition_id=condition_id
                )
            
            return None
        except Exception as e:
            logger.warning(f"检查离场信号时出错: {e}")
            return None
    
    def _check_take_profit(self, current, last_buy_price) -> Optional[TradingSignal]:
        """检查止盈信号（收获果实）"""
        try:
            if last_buy_price <= 0:
                return None
            
            close = self.checker._get_value(current, 'close')
            change_pct = (close - last_buy_price) / last_buy_price
            
            if change_pct >= self.config.TAKE_PROFIT_THRESHOLD:
                logger.debug(f"检测到止盈信号: {current['date']}, 涨幅: {change_pct:.2%}")
                return TradingSignal(
                    signal_type=TradingSignalType.TAKE_PROFIT,
                    timestamp=current['date'],
                    price=close,
                    conditions=[f"涨幅{change_pct:.2%}达到止盈阈值{self.config.TAKE_PROFIT_THRESHOLD:.0%}"]
                )
            
            return None
        except Exception as e:
            logger.warning(f"检查止盈信号时出错: {e}")
            return None
    
    def update_config(self, **kwargs):
        """更新策略配置"""
        self.config.update(**kwargs)
        logger.info(f"策略配置已更新: {kwargs}")
