"""
常量定义模块
集中管理所有常量
"""
from enum import Enum


class SignalAction(Enum):
    """信号操作类型"""
    BUY = "买入"
    ADD = "加码"
    EXIT = "离场"
    TAKE_PROFIT = "止盈"


class SignalPriority(Enum):
    """信号优先级"""
    DOUBLE_DRAGON_EMERGENCE = 1
    HIDDEN_DRAGON_DESCENT = 2
    DRAGON_IN_FIELD = 3
    DRAGON_BATTLE = 4
    TAKE_PROFIT = 5


class ChartSymbol(Enum):
    """图表符号"""
    BUY = "triangle-up"
    ADD = "diamond"
    EXIT = "triangle-down"
    TAKE_PROFIT = "star"


DEFAULT_CONFIG = {
    'MA_SHORT': 10,
    'MA_LONG': 20,
    'VOLUME_THRESHOLD': 0.20,
    'VOLUME_SHRINK_THRESHOLD': -0.20,
    'STOP_LOSS_THRESHOLD': 0.05,
    'TAKE_PROFIT_THRESHOLD': 0.05,
    'PULLBACK_THRESHOLD': 0.02,
    'STAND_THRESHOLD': 0.02,
    'SIGNAL_WINDOW': 10,
    'BEARISH_LIMIT': 5,
    'VOLUME_LOOKBACK': 10,
}

REQUIRED_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']

SIGNAL_COLORS = {
    'DOUBLE_DRAGON_EMERGENCE': '#f56565',
    'HIDDEN_DRAGON_DESCENT': '#f6ad55',
    'DRAGON_IN_FIELD': '#f6ad55',
    'DRAGON_BATTLE': '#48bb78',
    'TAKE_PROFIT': '#9f7aea',
}

CHART_COLORS = {
    'INCREASING': '#f56565',
    'DECREASING': '#48bb78',
    'MA10': '#4a90e2',
    'MA20': '#f6ad55',
    'VOLUME_MA': '#9f7aea',
}

THEME_COLORS = {
    'BACKGROUND': '#1a1a2e',
    'CARD_BACKGROUND': '#16213e',
    'TEXT_COLOR': '#e0e0e0',
    'BORDER_COLOR': '#2d3748',
    'ACCENT_COLOR': '#4a90e2',
    'SUCCESS_COLOR': '#48bb78',
    'WARNING_COLOR': '#f6ad55',
    'DANGER_COLOR': '#f56565',
    'INFO_COLOR': '#63b3ed',
}

CACHE_CONFIG = {
    'MAX_CACHE_SIZE': 100,
    'CACHE_TTL': 3600,
}

ERROR_MESSAGES = {
    'DATA_NOT_FOUND': '股票数据未找到',
    'INVALID_DATA': '股票数据格式无效',
    'MISSING_COLUMNS': '缺少必要的列',
    'PARSE_ERROR': '数据解析失败',
    'STRATEGY_ERROR': '策略分析失败',
}
