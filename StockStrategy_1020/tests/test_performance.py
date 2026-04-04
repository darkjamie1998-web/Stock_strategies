"""
性能对比测试
比较优化前后的性能差异
"""
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def generate_test_data(days: int = 500) -> pd.DataFrame:
    """生成测试数据"""
    dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
    
    np.random.seed(42)
    base_price = 100
    prices = [base_price]
    
    for _ in range(days - 1):
        change = np.random.normal(0, 0.02)
        new_price = prices[-1] * (1 + change)
        prices.append(new_price)
    
    df = pd.DataFrame({
        'date': dates,
        'open': prices,
        'high': [p * (1 + np.random.uniform(0, 0.03)) for p in prices],
        'low': [p * (1 - np.random.uniform(0, 0.03)) for p in prices],
        'close': [p * (1 + np.random.normal(0, 0.01)) for p in prices],
        'volume': np.random.randint(1000000, 10000000, days)
    })
    
    df['high'] = df[['open', 'close', 'high']].max(axis=1)
    df['low'] = df[['open', 'close', 'low']].min(axis=1)
    
    return df


def test_strategy_performance():
    """测试策略性能"""
    from models import StockData, StockInfo
    from config import TRADING_CONFIG
    
    print("\n" + "="*60)
    print("策略性能测试")
    print("="*60)
    
    df = generate_test_data(500)
    stock_info = StockInfo(code='TEST', name='测试股票')
    stock_data = StockData(df, stock_info)
    
    print("\n测试原始策略服务...")
    from services.strategy_service import StrategyService as OriginalStrategy
    original_strategy = OriginalStrategy()
    
    start_time = time.time()
    for _ in range(10):
        result = original_strategy.analyze(stock_data)
    original_time = time.time() - start_time
    
    print(f"原始策略 - 10次分析耗时: {original_time:.4f}秒")
    print(f"生成信号数: {len(result.signals)}")
    
    print("\n测试优化策略服务...")
    from services.strategy_service_optimized import StrategyService as OptimizedStrategy
    optimized_strategy = OptimizedStrategy()
    
    start_time = time.time()
    for _ in range(10):
        result = optimized_strategy.analyze(stock_data)
    optimized_time = time.time() - start_time
    
    print(f"优化策略 - 10次分析耗时: {optimized_time:.4f}秒")
    print(f"生成信号数: {len(result.signals)}")
    
    improvement = (original_time - optimized_time) / original_time * 100
    print(f"\n性能提升: {improvement:.2f}%")
    print(f"速度提升: {original_time/optimized_time:.2f}倍")


def test_data_loading_performance():
    """测试数据加载性能"""
    print("\n" + "="*60)
    print("数据加载性能测试")
    print("="*60)
    
    print("\n测试原始数据服务...")
    from services.data_service import DataService as OriginalDataService
    original_service = OriginalDataService()
    
    codes = original_service.get_stock_list(limit=10)
    codes_to_load = [c['value'] for c in codes]
    
    start_time = time.time()
    for code in codes_to_load:
        stock_data = original_service.get_stock_data(code)
    original_time = time.time() - start_time
    
    print(f"原始服务 - 加载10只股票耗时: {original_time:.4f}秒")
    
    original_service.manager.clear_cache()
    
    print("\n测试优化数据服务...")
    from services.data_service_optimized import DataService as OptimizedDataService
    optimized_service = OptimizedDataService()
    
    start_time = time.time()
    for code in codes_to_load:
        stock_data = optimized_service.get_stock_data(code)
    first_load_time = time.time() - start_time
    
    print(f"优化服务 - 首次加载10只股票耗时: {first_load_time:.4f}秒")
    
    start_time = time.time()
    for code in codes_to_load:
        stock_data = optimized_service.get_stock_data(code)
    cached_load_time = time.time() - start_time
    
    print(f"优化服务 - 缓存加载10只股票耗时: {cached_load_time:.4f}秒")
    
    cache_improvement = (first_load_time - cached_load_time) / first_load_time * 100
    print(f"\n缓存性能提升: {cache_improvement:.2f}%")
    print(f"缓存速度提升: {first_load_time/cached_load_time:.2f}倍")
    
    print("\n测试批量加载...")
    start_time = time.time()
    results = optimized_service.manager.load_multiple_stocks(codes_to_load, max_workers=4)
    batch_load_time = time.time() - start_time
    
    print(f"批量并行加载10只股票耗时: {batch_load_time:.4f}秒")
    
    parallel_improvement = (first_load_time - batch_load_time) / first_load_time * 100
    print(f"并行加载性能提升: {parallel_improvement:.2f}%")


def test_backtest_performance():
    """测试回测性能"""
    print("\n" + "="*60)
    print("回测引擎性能测试")
    print("="*60)
    
    from models import StockData, StockInfo
    from services.strategy_service_optimized import StrategyService
    from core import BacktestEngine
    
    df = generate_test_data(500)
    stock_info = StockInfo(code='TEST', name='测试股票')
    stock_data = StockData(df, stock_info)
    
    strategy = StrategyService()
    signal_result = strategy.analyze(stock_data)
    
    engine = BacktestEngine(initial_capital=100000)
    
    start_time = time.time()
    metrics = engine.run_backtest(stock_data, signal_result)
    backtest_time = time.time() - start_time
    
    print(f"回测耗时: {backtest_time:.4f}秒")
    print(f"总交易次数: {metrics.total_trades}")
    print(f"总收益率: {metrics.total_return*100:.2f}%")
    print(f"最大回撤: {metrics.max_drawdown*100:.2f}%")
    print(f"夏普比率: {metrics.sharpe_ratio:.2f}")
    print(f"胜率: {metrics.win_rate*100:.2f}%")


def test_data_validation_performance():
    """测试数据验证性能"""
    print("\n" + "="*60)
    print("数据验证性能测试")
    print("="*60)
    
    from core import DataValidator
    
    df = generate_test_data(1000)
    validator = DataValidator()
    
    start_time = time.time()
    for _ in range(100):
        is_valid, errors = validator.validate(df)
    validation_time = time.time() - start_time
    
    print(f"验证1000条数据100次耗时: {validation_time:.4f}秒")
    print(f"平均每次验证耗时: {validation_time/100*1000:.2f}毫秒")
    
    start_time = time.time()
    for _ in range(100):
        cleaned_df = validator.clean_data(df)
    cleaning_time = time.time() - start_time
    
    print(f"清洗1000条数据100次耗时: {cleaning_time:.4f}秒")
    print(f"平均每次清洗耗时: {cleaning_time/100*1000:.2f}毫秒")


def run_all_performance_tests():
    """运行所有性能测试"""
    print("\n" + "="*60)
    print("开始性能测试")
    print("="*60)
    
    try:
        test_strategy_performance()
    except Exception as e:
        print(f"策略性能测试失败: {e}")
    
    try:
        test_data_loading_performance()
    except Exception as e:
        print(f"数据加载性能测试失败: {e}")
    
    try:
        test_backtest_performance()
    except Exception as e:
        print(f"回测性能测试失败: {e}")
    
    try:
        test_data_validation_performance()
    except Exception as e:
        print(f"数据验证性能测试失败: {e}")
    
    print("\n" + "="*60)
    print("性能测试完成")
    print("="*60)


if __name__ == '__main__':
    run_all_performance_tests()
