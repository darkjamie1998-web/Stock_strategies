"""
回测引擎模块
提供策略回测和性能评估功能
"""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import logging

from models import TradingSignal, SignalResult, StockData, TradingSignalType
from exceptions import StrategyExecutionError


logger = logging.getLogger(__name__)


@dataclass
class Trade:
    """交易记录"""
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    position_size: float = 1.0
    signal_type: str = ""
    
    @property
    def return_pct(self) -> Optional[float]:
        """计算收益率"""
        if self.exit_price and self.entry_price:
            return (self.exit_price - self.entry_price) / self.entry_price
        return None
    
    @property
    def is_closed(self) -> bool:
        """是否已平仓"""
        return self.exit_date is not None


@dataclass
class BacktestMetrics:
    """回测指标"""
    total_return: float = 0.0
    annual_return: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    profit_trades: int = 0
    loss_trades: int = 0
    avg_profit: float = 0.0
    avg_loss: float = 0.0
    profit_factor: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            '总收益率': f"{self.total_return * 100:.2f}%",
            '年化收益率': f"{self.annual_return * 100:.2f}%",
            '最大回撤': f"{self.max_drawdown * 100:.2f}%",
            '夏普比率': f"{self.sharpe_ratio:.2f}",
            '胜率': f"{self.win_rate * 100:.2f}%",
            '总交易次数': self.total_trades,
            '盈利次数': self.profit_trades,
            '亏损次数': self.loss_trades,
            '平均盈利': f"{self.avg_profit * 100:.2f}%",
            '平均亏损': f"{self.avg_loss * 100:.2f}%",
            '盈亏比': f"{self.profit_factor:.2f}",
        }


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.trades: List[Trade] = []
        self.equity_curve: List[float] = [initial_capital]
    
    def run_backtest(self, stock_data: StockData, signal_result: SignalResult) -> BacktestMetrics:
        """
        运行回测
        
        Args:
            stock_data: 股票数据
            signal_result: 信号结果
        
        Returns:
            回测指标
        """
        try:
            self.trades = []
            self.equity_curve = [self.initial_capital]
            
            current_trade: Optional[Trade] = None
            capital = self.initial_capital
            position = 0.0
            
            df = stock_data.df
            signals = signal_result.signals
            
            for signal in signals:
                if signal.action == '买入' and position == 0:
                    position = capital / signal.price
                    capital = 0
                    current_trade = Trade(
                        entry_date=signal.timestamp,
                        entry_price=signal.price,
                        signal_type=signal.signal_name
                    )
                
                elif signal.action in ['离场', '止盈'] and position > 0 and current_trade:
                    capital = position * signal.price
                    position = 0
                    current_trade.exit_date = signal.timestamp
                    current_trade.exit_price = signal.price
                    self.trades.append(current_trade)
                    current_trade = None
                
                self.equity_curve.append(capital + position * signal.price)
            
            if current_trade and position > 0:
                last_price = df['close'].iloc[-1]
                current_trade.exit_date = df['date'].iloc[-1]
                current_trade.exit_price = last_price
                self.trades.append(current_trade)
            
            return self._calculate_metrics()
        
        except Exception as e:
            logger.error(f"回测失败: {e}", exc_info=True)
            raise StrategyExecutionError("回测执行失败", str(e))
    
    def _calculate_metrics(self) -> BacktestMetrics:
        """计算回测指标"""
        if not self.trades:
            return BacktestMetrics()
        
        returns = [t.return_pct for t in self.trades if t.return_pct is not None]
        
        if not returns:
            return BacktestMetrics()
        
        total_return = sum(returns)
        avg_return = np.mean(returns)
        
        profit_trades = [r for r in returns if r > 0]
        loss_trades = [r for r in returns if r < 0]
        
        win_rate = len(profit_trades) / len(returns) if returns else 0
        avg_profit = np.mean(profit_trades) if profit_trades else 0
        avg_loss = np.mean(loss_trades) if loss_trades else 0
        
        profit_factor = abs(sum(profit_trades) / sum(loss_trades)) if loss_trades and sum(loss_trades) != 0 else 0
        
        if len(self.equity_curve) > 1:
            equity_series = pd.Series(self.equity_curve)
            cummax = equity_series.cummax()
            drawdown = (equity_series - cummax) / cummax
            max_drawdown = abs(drawdown.min())
            
            daily_returns = equity_series.pct_change().dropna()
            sharpe_ratio = self._calculate_sharpe_ratio(daily_returns)
            
            trading_days = len(self.equity_curve)
            annual_return = total_return * (252 / trading_days) if trading_days > 0 else 0
        else:
            max_drawdown = 0
            sharpe_ratio = 0
            annual_return = 0
        
        return BacktestMetrics(
            total_return=total_return,
            annual_return=annual_return,
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            win_rate=win_rate,
            total_trades=len(self.trades),
            profit_trades=len(profit_trades),
            loss_trades=len(loss_trades),
            avg_profit=avg_profit,
            avg_loss=avg_loss,
            profit_factor=profit_factor
        )
    
    def _calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.03) -> float:
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
        
        excess_returns = returns - risk_free_rate / 252
        
        if excess_returns.std() == 0:
            return 0.0
        
        return excess_returns.mean() / excess_returns.std() * np.sqrt(252)
    
    def get_trade_history(self) -> List[Dict[str, Any]]:
        """获取交易历史"""
        return [
            {
                'entry_date': t.entry_date.strftime('%Y-%m-%d'),
                'entry_price': t.entry_price,
                'exit_date': t.exit_date.strftime('%Y-%m-%d') if t.exit_date else None,
                'exit_price': t.exit_price,
                'return_pct': f"{t.return_pct * 100:.2f}%" if t.return_pct else None,
                'signal_type': t.signal_type
            }
            for t in self.trades
        ]
    
    def get_equity_curve_df(self) -> pd.DataFrame:
        """获取资金曲线DataFrame"""
        return pd.DataFrame({
            'equity': self.equity_curve
        })
