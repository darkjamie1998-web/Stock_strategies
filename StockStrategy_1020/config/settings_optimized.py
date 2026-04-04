"""
配置管理器优化版
支持环境变量、配置验证和热重载
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from utils import get_project_root, get_exe_dir


logger = logging.getLogger(__name__)


@dataclass
class TradingConfig:
    """交易策略配置"""
    MA_SHORT: int = 10
    MA_LONG: int = 20
    VOLUME_THRESHOLD: float = 0.20
    VOLUME_SHRINK_THRESHOLD: float = -0.20
    STOP_LOSS_THRESHOLD: float = 0.05
    TAKE_PROFIT_THRESHOLD: float = 0.05
    PULLBACK_THRESHOLD: float = 0.02
    STAND_THRESHOLD: float = 0.02
    SIGNAL_WINDOW: int = 10
    BEARISH_LIMIT: int = 5
    VOLUME_LOOKBACK: int = 10
    
    def __post_init__(self):
        """验证配置参数"""
        self._validate()
    
    def _validate(self):
        """验证配置参数的有效性"""
        if self.MA_SHORT <= 0 or self.MA_LONG <= 0:
            raise ValueError("均线周期必须大于0")
        
        if self.MA_SHORT >= self.MA_LONG:
            raise ValueError("短期均线周期必须小于长期均线周期")
        
        if not (0 < self.VOLUME_THRESHOLD < 1):
            raise ValueError("放量阈值必须在0到1之间")
        
        if not (0 < self.STOP_LOSS_THRESHOLD < 1):
            raise ValueError("止损阈值必须在0到1之间")
        
        if not (0 < self.TAKE_PROFIT_THRESHOLD < 1):
            raise ValueError("止盈阈值必须在0到1之间")
        
        if self.SIGNAL_WINDOW < 0:
            raise ValueError("信号屏蔽窗口不能为负数")
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    def update(self, **kwargs):
        """更新配置"""
        for key, value in kwargs.items():
            if hasattr(self, key.upper()):
                setattr(self, key.upper(), value)
        self._validate()
    
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
    
    @classmethod
    def from_env(cls) -> 'TradingConfig':
        """从环境变量创建配置"""
        def get_env_float(key: str, default: float) -> float:
            value = os.getenv(key)
            return float(value) if value else default
        
        def get_env_int(key: str, default: int) -> int:
            value = os.getenv(key)
            return int(value) if value else default
        
        return cls(
            MA_SHORT=get_env_int('MA_SHORT', 10),
            MA_LONG=get_env_int('MA_LONG', 20),
            VOLUME_THRESHOLD=get_env_float('VOLUME_THRESHOLD', 0.20),
            VOLUME_SHRINK_THRESHOLD=get_env_float('VOLUME_SHRINK_THRESHOLD', -0.20),
            STOP_LOSS_THRESHOLD=get_env_float('STOP_LOSS_THRESHOLD', 0.05),
            TAKE_PROFIT_THRESHOLD=get_env_float('TAKE_PROFIT_THRESHOLD', 0.05),
            PULLBACK_THRESHOLD=get_env_float('PULLBACK_THRESHOLD', 0.02),
            STAND_THRESHOLD=get_env_float('STAND_THRESHOLD', 0.02),
            SIGNAL_WINDOW=get_env_int('SIGNAL_WINDOW', 10),
            BEARISH_LIMIT=get_env_int('BEARISH_LIMIT', 5),
            VOLUME_LOOKBACK=get_env_int('VOLUME_LOOKBACK', 10),
        )


@dataclass
class UIConfig:
    """UI界面配置"""
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
    CHART_HEIGHT: int = 500
    CHART_MARGIN: Dict[str, int] = field(default_factory=lambda: {
        'l': 50, 'r': 50, 't': 50, 'b': 50
    })
    DROPDOWN_BATCH_SIZE: int = 100
    DROPDOWN_SEARCH_THRESHOLD: int = 3


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


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, use_env: bool = True):
        self.trading = TradingConfig.from_env() if use_env else TradingConfig()
        self.ui = UIConfig()
        self.paths = PathConfig()
        
        self._load_from_file()
    
    def _load_from_file(self):
        """从文件加载配置"""
        try:
            if self.paths.CONFIG_FILE.exists():
                with open(self.paths.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
                
                if 'trading' in config_data:
                    self.trading = TradingConfig.from_dict(config_data['trading'])
                
                if 'ui' in config_data:
                    ui_data = config_data['ui']
                    if 'theme' in ui_data:
                        self.ui.THEME = ui_data['theme']
                    if 'chart_height' in ui_data:
                        self.ui.CHART_HEIGHT = ui_data['chart_height']
                
                logger.info("配置文件加载成功")
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
    
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
            
            logger.info("配置保存成功")
            return True
        except Exception as e:
            logger.error(f"保存配置失败: {e}")
            return False
    
    def reset_trading_config(self):
        """重置交易配置为默认值"""
        self.trading = TradingConfig()
        logger.info("交易配置已重置为默认值")
    
    def get_theme_colors(self) -> Dict[str, str]:
        """获取主题颜色"""
        return self.ui.THEME.copy()
    
    def update_trading_config(self, **kwargs):
        """更新交易配置"""
        self.trading.update(**kwargs)
        logger.info(f"交易配置已更新: {kwargs}")
    
    def export_config(self, filepath: Optional[Path] = None) -> bool:
        """
        导出配置到指定文件
        
        Args:
            filepath: 目标文件路径
        
        Returns:
            是否成功
        """
        try:
            if filepath is None:
                filepath = self.paths.EXE_DIR / 'config_export.json'
            
            config_data = {
                'trading': self.trading.to_dict(),
                'ui': {
                    'theme': self.ui.THEME,
                    'chart_height': self.ui.CHART_HEIGHT,
                }
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"配置已导出到: {filepath}")
            return True
        except Exception as e:
            logger.error(f"导出配置失败: {e}")
            return False
    
    def import_config(self, filepath: Path) -> bool:
        """
        从文件导入配置
        
        Args:
            filepath: 配置文件路径
        
        Returns:
            是否成功
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            if 'trading' in config_data:
                self.trading = TradingConfig.from_dict(config_data['trading'])
            
            if 'ui' in config_data:
                ui_data = config_data['ui']
                if 'theme' in ui_data:
                    self.ui.THEME = ui_data['theme']
                if 'chart_height' in ui_data:
                    self.ui.CHART_HEIGHT = ui_data['chart_height']
            
            logger.info(f"配置已从 {filepath} 导入")
            return True
        except Exception as e:
            logger.error(f"导入配置失败: {e}")
            return False


_config_instance = None


def get_config() -> ConfigManager:
    """获取配置单例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = ConfigManager()
    return _config_instance


TRADING_CONFIG = TradingConfig()
UI_CONFIG = UIConfig()
PATH_CONFIG = PathConfig()


class Settings:
    """配置管理器（兼容旧版本）"""
    
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
        return get_config().save_config()
    
    def load_config(self) -> bool:
        """从文件加载配置"""
        config = get_config()
        self.trading = config.trading
        self.ui = config.ui
        self.paths = config.paths
        return True


_settings_instance = None


def get_settings() -> Settings:
    """获取配置单例"""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings()
    return _settings_instance
