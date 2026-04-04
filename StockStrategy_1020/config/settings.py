"""
应用配置管理
集中管理所有配置参数
"""
from dataclasses import dataclass, field
from typing import Dict, Any
import json
from pathlib import Path

from utils import get_project_root, get_exe_dir, ensure_project_root_in_path

ensure_project_root_in_path()


@dataclass
class TradingConfig:
    """交易策略配置"""
    # 均线参数
    MA_SHORT: int = 10  # 短期均线（攻击线）
    MA_LONG: int = 20   # 长期均线（生命线）
    
    # 阈值参数（百分比）
    VOLUME_THRESHOLD: float = 0.20      # 放量阈值 20%
    VOLUME_SHRINK_THRESHOLD: float = -0.20  # 缩量阈值 -20%
    STOP_LOSS_THRESHOLD: float = 0.05   # 止损阈值 5%
    TAKE_PROFIT_THRESHOLD: float = 0.05 # 止盈阈值 5%
    PULLBACK_THRESHOLD: float = 0.02    # 回踩阈值 2%
    STAND_THRESHOLD: float = 0.02       # 站上阈值 2%
    
    # 信号参数
    SIGNAL_WINDOW: int = 10     # 信号屏蔽窗口（天）
    BEARISH_LIMIT: int = 5      # 空头排列连续限制（天）
    VOLUME_LOOKBACK: int = 10   # 成交量回看周期（天）
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'ma_short': self.MA_SHORT,
            'ma_long': self.MA_LONG,
            'volume_threshold': self.VOLUME_THRESHOLD,
            'volume_shrink_threshold': self.VOLUME_SHRINK_THRESHOLD,
            'stop_loss_threshold': self.STOP_LOSS_THRESHOLD,
            'take_profit_threshold': self.TAKE_PROFIT_THRESHOLD,
            'pullback_threshold': self.PULLBACK_THRESHOLD,
            'stand_threshold': self.STAND_THRESHOLD,
            'signal_window': self.SIGNAL_WINDOW,
            'bearish_limit': self.BEARISH_LIMIT,
            'volume_lookback': self.VOLUME_LOOKBACK,
        }
    
    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key.upper()):
                setattr(self, key.upper(), value)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TradingConfig':
        """从字典创建配置"""
        return cls(
            MA_SHORT=data.get('ma_short', 10),
            MA_LONG=data.get('ma_long', 20),
            VOLUME_THRESHOLD=data.get('volume_threshold', 0.20),
            VOLUME_SHRINK_THRESHOLD=data.get('volume_shrink_threshold', -0.20),
            STOP_LOSS_THRESHOLD=data.get('stop_loss_threshold', 0.05),
            TAKE_PROFIT_THRESHOLD=data.get('take_profit_threshold', 0.05),
            PULLBACK_THRESHOLD=data.get('pullback_threshold', 0.02),
            STAND_THRESHOLD=data.get('stand_threshold', 0.02),
            SIGNAL_WINDOW=data.get('signal_window', 10),
            BEARISH_LIMIT=data.get('bearish_limit', 5),
            VOLUME_LOOKBACK=data.get('volume_lookback', 10),
        )


@dataclass
class UIConfig:
    """UI界面配置"""
    # 深色主题配色
    THEME: Dict[str, str] = field(default_factory=lambda: {
        'background_color': '#1a1a2e',
        'card_background': '#16213e',
        'text_color': '#e0e0e0',
        'border_color': '#2d3748',
        'accent_color': '#4a90e2',
        'success_color': '#48bb78',
        'warning_color': '#f6ad55',
        'danger_color': '#f56565',
        'info_color': '#63b3ed'
    })
    
    # 图表配置
    CHART_HEIGHT: int = 500
    CHART_MARGIN: Dict[str, int] = field(default_factory=lambda: {
        'l': 50, 'r': 50, 't': 50, 'b': 50
    })
    
    # 下拉框配置
    DROPDOWN_BATCH_SIZE: int = 100  # 初始加载数量
    DROPDOWN_SEARCH_THRESHOLD: int = 3  # 触发搜索的最小字符数


@dataclass
class PathConfig:
    """路径配置"""
    BASE_DIR: Path = field(default_factory=get_project_root)
    EXE_DIR: Path = field(default_factory=get_exe_dir)
    
    @property
    def DATA_DIR(self) -> Path:
        return self.EXE_DIR / 'A股上市公司数据'
    
    @property
    def STOCK_LIST_PATH(self) -> Path:
        return self.EXE_DIR / 'A股上市公司名单' / 'A股上市公司名单.csv'
    
    @property
    def ASSETS_DIR(self) -> Path:
        return self.BASE_DIR / 'assets'
    
    @property
    def CACHE_DIR(self) -> Path:
        cache_dir = self.EXE_DIR / '.cache'
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    
    @property
    def LOGS_DIR(self) -> Path:
        logs_dir = self.EXE_DIR / 'logs'
        logs_dir.mkdir(exist_ok=True)
        return logs_dir
    
    @property
    def CONFIG_FILE(self) -> Path:
        return self.EXE_DIR / 'config.json'


# 全局配置实例
TRADING_CONFIG = TradingConfig()
UI_CONFIG = UIConfig()
PATH_CONFIG = PathConfig()


class Settings:
    """配置管理器"""
    
    def __init__(self):
        self.trading = TRADING_CONFIG
        self.ui = UI_CONFIG
        self.paths = PATH_CONFIG
    
    def reset_trading_config(self):
        """重置交易配置为默认值"""
        self.trading = TradingConfig()
    
    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色"""
        return self.ui.THEME.copy()
    
    def save_config(self) -> bool:
        """保存配置到文件"""
        try:
            config_data = {
                'trading': self.trading.to_dict(),
                'ui': {
                    'theme': self.ui.THEME,
                    'chart_height': self.ui.CHART_HEIGHT,
                    'chart_margin': self.ui.CHART_MARGIN,
                    'dropdown_batch_size': self.ui.DROPDOWN_BATCH_SIZE,
                    'dropdown_search_threshold': self.ui.DROPDOWN_SEARCH_THRESHOLD,
                }
            }
            
            with open(self.paths.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            return True
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
    
    def load_config(self) -> bool:
        """从文件加载配置"""
        try:
            if not self.paths.CONFIG_FILE.exists():
                return False
            
            with open(self.paths.CONFIG_FILE, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 加载交易配置
            if 'trading' in config_data:
                self.trading = TradingConfig.from_dict(config_data['trading'])
            
            # 加载UI配置
            if 'ui' in config_data:
                ui_data = config_data['ui']
                if 'theme' in ui_data:
                    self.ui.THEME = ui_data['theme']
                if 'chart_height' in ui_data:
                    self.ui.CHART_HEIGHT = ui_data['chart_height']
                if 'chart_margin' in ui_data:
                    self.ui.CHART_MARGIN = ui_data['chart_margin']
                if 'dropdown_batch_size' in ui_data:
                    self.ui.DROPDOWN_BATCH_SIZE = ui_data['dropdown_batch_size']
                if 'dropdown_search_threshold' in ui_data:
                    self.ui.DROPDOWN_SEARCH_THRESHOLD = ui_data['dropdown_search_threshold']
            
            return True
        except Exception as e:
            print(f"加载配置失败: {e}")
            return False


# 单例模式
_settings_instance = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
