"""
优化模块测试
验证新增模块的功能（无需pytest版本）
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestRunner:
    """测试运行器"""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def run_test(self, test_name, test_func):
        """运行单个测试"""
        try:
            test_func()
            self.passed += 1
            print(f"✅ {test_name}")
        except AssertionError as e:
            self.failed += 1
            self.errors.append((test_name, str(e)))
            print(f"❌ {test_name}: {e}")
        except Exception as e:
            self.failed += 1
            import traceback
            error_detail = f"{str(e)}\n{traceback.format_exc()}"
            self.errors.append((test_name, error_detail))
            print(f"❌ {test_name}: 异常 - {e}")
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "="*60)
        print(f"测试完成: {self.passed} 通过, {self.failed} 失败")
        print("="*60)
        
        if self.errors:
            print("\n失败的测试:")
            for name, error in self.errors:
                print(f"\n  【{name}】:")
                print(f"    {error}")


def test_signal_action_enum():
    """测试信号操作枚举"""
    from constants import SignalAction
    
    assert SignalAction.BUY.value == "买入"
    assert SignalAction.ADD.value == "加码"
    assert SignalAction.EXIT.value == "离场"
    assert SignalAction.TAKE_PROFIT.value == "止盈"


def test_default_config():
    """测试默认配置"""
    from constants import DEFAULT_CONFIG
    
    assert 'MA_SHORT' in DEFAULT_CONFIG
    assert 'MA_LONG' in DEFAULT_CONFIG
    assert DEFAULT_CONFIG['MA_SHORT'] == 10
    assert DEFAULT_CONFIG['MA_LONG'] == 20


def test_signal_colors():
    """测试信号颜色"""
    from constants import SIGNAL_COLORS
    
    assert 'DOUBLE_DRAGON_EMERGENCE' in SIGNAL_COLORS
    assert SIGNAL_COLORS['DOUBLE_DRAGON_EMERGENCE'] == '#f56565'


def test_base_exception():
    """测试基础异常"""
    from exceptions import StockStrategyError
    
    exc = StockStrategyError("测试错误", "详细信息")
    assert exc.message == "测试错误"
    assert exc.details == "详细信息"
    assert "测试错误" in str(exc)


def test_data_load_error():
    """测试数据加载异常"""
    from exceptions import DataLoadError, StockStrategyError
    
    exc = DataLoadError("加载失败")
    assert isinstance(exc, StockStrategyError)
    assert exc.message == "加载失败"


def test_handle_exception():
    """测试异常处理函数"""
    from exceptions import handle_exception, StockStrategyError
    
    exc = StockStrategyError("测试", "详情")
    error_info = handle_exception(exc)
    
    assert error_info['type'] == 'StockStrategyError'
    assert "测试" in error_info['message']
    assert error_info['details'] == "详情"


def test_validate_valid_data():
    """测试有效数据验证"""
    from core import DataValidator
    
    validator = DataValidator()
    
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'open': np.random.uniform(10, 20, 10),
        'high': np.random.uniform(20, 30, 10),
        'low': np.random.uniform(5, 10, 10),
        'close': np.random.uniform(10, 20, 10),
        'volume': np.random.randint(1000, 10000, 10)
    })
    
    df['high'] = df[['open', 'close', 'low']].max(axis=1) + 1
    df['low'] = df[['open', 'close']].min(axis=1) - 1
    
    is_valid, errors = validator.validate(df)
    
    assert is_valid
    assert len(errors) == 0


def test_validate_missing_columns():
    """测试缺少列的数据"""
    from core import DataValidator
    
    validator = DataValidator()
    
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'close': np.random.uniform(10, 20, 10)
    })
    
    is_valid, errors = validator.validate(df)
    
    assert not is_valid
    assert len(errors) > 0
    assert any('缺少必要列' in err for err in errors)


def test_clean_data():
    """测试数据清洗"""
    from core import DataValidator
    
    validator = DataValidator()
    
    df = pd.DataFrame({
        'date': pd.date_range('2024-01-01', periods=10),
        'open': [10, 11, 12, 13, 14, 15, 16, 17, 18, 19],
        'high': [12, 13, 14, 15, 16, 17, 18, 19, 20, 21],
        'low': [9, 10, 11, 12, 13, 14, 15, 16, 17, 18],
        'close': [11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    })
    
    cleaned_df = validator.clean_data(df)
    
    assert len(cleaned_df) == 10
    assert cleaned_df['date'].is_monotonic_increasing


def test_backtest_metrics_creation():
    """测试回测指标创建"""
    from core import BacktestMetrics
    
    metrics = BacktestMetrics(
        total_return=0.15,
        annual_return=0.20,
        max_drawdown=0.10,
        sharpe_ratio=1.5,
        win_rate=0.6,
        total_trades=10,
        profit_trades=6,
        loss_trades=4
    )
    
    metrics_dict = metrics.to_dict()
    
    assert '总收益率' in metrics_dict
    assert metrics_dict['总收益率'] == "15.00%"


def test_backtest_engine_initialization():
    """测试回测引擎初始化"""
    from core import BacktestEngine
    
    engine = BacktestEngine(initial_capital=100000)
    
    assert engine.initial_capital == 100000
    assert len(engine.trades) == 0
    assert len(engine.equity_curve) == 1


def test_config_validation():
    """测试配置验证"""
    from config.settings_optimized import TradingConfig
    
    config = TradingConfig(
        MA_SHORT=10,
        MA_LONG=20,
        VOLUME_THRESHOLD=0.20
    )
    
    assert config.MA_SHORT == 10
    assert config.MA_LONG == 20


def test_invalid_config():
    """测试无效配置"""
    from config.settings_optimized import TradingConfig
    
    try:
        TradingConfig(MA_SHORT=20, MA_LONG=10)
        assert False, "应该抛出异常"
    except ValueError:
        pass
    
    try:
        TradingConfig(VOLUME_THRESHOLD=1.5)
        assert False, "应该抛出异常"
    except ValueError:
        pass


def test_config_update():
    """测试配置更新"""
    from config.settings_optimized import TradingConfig
    
    config = TradingConfig()
    config.update(ma_short=15)
    
    assert config.MA_SHORT == 15


def test_strategy_manager():
    """测试策略管理器"""
    from strategies import StrategyManager
    
    manager = StrategyManager()
    
    strategies = manager.list_strategies()
    assert isinstance(strategies, list)


def run_all_tests():
    """运行所有测试"""
    print("\n" + "="*60)
    print("开始运行优化模块测试")
    print("="*60 + "\n")
    
    runner = TestRunner()
    
    print("测试常量模块:")
    runner.run_test("信号操作枚举", test_signal_action_enum)
    runner.run_test("默认配置", test_default_config)
    runner.run_test("信号颜色", test_signal_colors)
    
    print("\n测试异常模块:")
    runner.run_test("基础异常", test_base_exception)
    runner.run_test("数据加载异常", test_data_load_error)
    runner.run_test("异常处理函数", test_handle_exception)
    
    print("\n测试数据验证器:")
    runner.run_test("有效数据验证", test_validate_valid_data)
    runner.run_test("缺少列验证", test_validate_missing_columns)
    runner.run_test("数据清洗", test_clean_data)
    
    print("\n测试回测引擎:")
    runner.run_test("回测指标创建", test_backtest_metrics_creation)
    runner.run_test("回测引擎初始化", test_backtest_engine_initialization)
    
    print("\n测试配置管理:")
    runner.run_test("配置验证", test_config_validation)
    runner.run_test("无效配置", test_invalid_config)
    runner.run_test("配置更新", test_config_update)
    
    print("\n测试策略模块:")
    runner.run_test("策略管理器", test_strategy_manager)
    
    runner.print_summary()
    
    return runner.failed == 0


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
