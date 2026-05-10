"""
信号扫描模块
批量扫描所有股票在指定时间段内的交易信号
"""
import pandas as pd
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass, field
import logging

from config import TRADING_CONFIG
from models import TradingSignal, TradingSignalType
from services.data_service import DataService
from services.strategy_service import StrategyService

logger = logging.getLogger(__name__)


@dataclass
class ScanResult:
    """单只股票的扫描结果"""
    stock_code: str
    stock_name: str
    buy_count: int = 0
    add_count: int = 0
    exit_count: int = 0
    profit_count: int = 0
    total_signals: int = 0
    signals: List[TradingSignal] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def has_signals(self) -> bool:
        return self.total_signals > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'stock_code': self.stock_code,
            'stock_name': self.stock_name,
            'buy_count': self.buy_count,
            'add_count': self.add_count,
            'exit_count': self.exit_count,
            'profit_count': self.profit_count,
            'total_signals': self.total_signals,
            'error': self.error
        }


class SignalScanner:
    """信号扫描器"""

    def __init__(self, config=None):
        self.config = config or TRADING_CONFIG
        self.data_service = DataService()
        self.strategy_service = StrategyService(config)
        self._stop_requested = False

    def request_stop(self):
        self._stop_requested = True

    def scan_all_stocks(self, start_date: str, end_date: str,
                        progress_callback: Optional[Callable[[int, int, str, str], None]] = None
                        ) -> List[ScanResult]:
        """扫描所有股票在指定时间段内的信号"""
        start_dt = pd.Timestamp(start_date)
        end_dt = pd.Timestamp(end_date)

        stock_codes = self.data_service.manager.get_stock_codes()
        total = len(stock_codes)
        results = []

        logger.info(f"开始扫描 {total} 只股票，时间范围: {start_date} ~ {end_date}")

        for idx, code in enumerate(stock_codes):
            if self._stop_requested:
                logger.info("用户请求停止扫描")
                break

            stock_info = self.data_service.manager.get_stock_info(code)
            stock_name = stock_info.name if stock_info else ''

            if progress_callback:
                progress_callback(idx + 1, total, code, stock_name)

            try:
                stock_data = self.data_service.get_stock_data(code)
                if stock_data is None:
                    continue

                result = self.strategy_service.analyze(stock_data)

                filtered_signals = [
                    s for s in result.signals
                    if start_dt <= s.timestamp <= end_dt
                ]

                if filtered_signals:
                    scan_result = ScanResult(
                        stock_code=code,
                        stock_name=stock_name,
                        signals=filtered_signals
                    )
                    scan_result.buy_count = len([
                        s for s in filtered_signals
                        if s.signal_type == TradingSignalType.DOUBLE_DRAGON_EMERGENCE
                    ])
                    scan_result.add_count = len([
                        s for s in filtered_signals
                        if s.signal_type in [
                            TradingSignalType.HIDDEN_DRAGON_DESCENT,
                            TradingSignalType.DRAGON_IN_FIELD
                        ]
                    ])
                    scan_result.exit_count = len([
                        s for s in filtered_signals
                        if s.signal_type == TradingSignalType.DRAGON_BATTLE
                    ])
                    scan_result.profit_count = len([
                        s for s in filtered_signals
                        if s.signal_type == TradingSignalType.TAKE_PROFIT
                    ])
                    scan_result.total_signals = len(filtered_signals)
                    results.append(scan_result)

            except Exception as e:
                logger.warning(f"扫描 {code} {stock_name} 时出错: {e}")
                results.append(ScanResult(
                    stock_code=code,
                    stock_name=stock_name,
                    error=str(e)
                ))

        results.sort(key=lambda r: r.total_signals, reverse=True)
        logger.info(f"扫描完成，共 {len(results)} 只股票触发信号")
        return results