# 快速开始指南

## 🚀 5分钟快速上手优化版本

本指南帮助你快速开始使用优化后的 StockStrategy_1020 项目。

## 📦 新增模块概览

优化后的项目新增了以下核心模块：

```
constants/      - 常量和枚举定义
exceptions/     - 自定义异常类
types/          - 类型定义和协议
strategies/     - 策略抽象层
core/           - 核心功能（回测引擎、数据验证）
```

## 🎯 三种使用方式

### 方式1: 基础使用（推荐新手）

继续使用原有代码，但享受性能优化：

```python
# 使用优化后的服务（自动替换）
from services import DataService, StrategyService
from config import TRADING_CONFIG

# 初始化服务
data_service = DataService()
strategy_service = StrategyService()

# 加载股票数据
stock_data = data_service.get_stock_data('000001.SZ')

# 分析信号
result = strategy_service.analyze(stock_data)

# 查看信号
for signal in result.signals:
    print(f"{signal.timestamp}: {signal.signal_name} @ {signal.price}")
```

### 方式2: 使用回测功能（推荐进阶用户）

评估策略的历史表现：

```python
from services import DataService, StrategyService
from core import BacktestEngine

# 加载数据和分析信号
data_service = DataService()
stock_data = data_service.get_stock_data('000001.SZ')

strategy_service = StrategyService()
signal_result = strategy_service.analyze(stock_data)

# 运行回测
engine = BacktestEngine(initial_capital=100000)
metrics = engine.run_backtest(stock_data, signal_result)

# 查看回测结果
print("=== 回测结果 ===")
for key, value in metrics.to_dict().items():
    print(f"{key}: {value}")

# 查看交易历史
trades = engine.get_trade_history()
print(f"\n总交易次数: {len(trades)}")
```

### 方式3: 自定义策略（推荐高级用户）

创建自己的交易策略：

```python
from strategies import BaseStrategy
from models import StockData, SignalResult, TradingSignal, TradingSignalType

class MyCustomStrategy(BaseStrategy):
    """自定义策略示例"""
    
    def get_strategy_name(self) -> str:
        return "我的自定义策略"
    
    def get_strategy_description(self) -> str:
        return "基于自定义指标的交易策略"
    
    def analyze(self, stock_data: StockData) -> SignalResult:
        """实现策略逻辑"""
        df = stock_data.df
        signals = []
        
        # 添加你的策略逻辑
        # 例如：简单的均线交叉策略
        for i in range(1, len(df)):
            if df['ma10'].iloc[i] > df['ma20'].iloc[i] and \
               df['ma10'].iloc[i-1] <= df['ma20'].iloc[i-1]:
                signal = TradingSignal(
                    signal_type=TradingSignalType.DOUBLE_DRAGON_EMERGENCE,
                    timestamp=df['date'].iloc[i],
                    price=df['close'].iloc[i],
                    conditions=["MA10上穿MA20"]
                )
                signals.append(signal)
        
        return SignalResult(
            signals=signals,
            statistics={},
            start_date=stock_data.start_date,
            end_date=stock_data.end_date,
            total_days=stock_data.trading_days
        )

# 使用自定义策略
strategy = MyCustomStrategy()
result = strategy.analyze(stock_data)
```

## 🔧 配置管理

### 使用环境变量

创建 `.env` 文件：

```bash
# .env
MA_SHORT=10
MA_LONG=20
VOLUME_THRESHOLD=0.20
STOP_LOSS_THRESHOLD=0.05
TAKE_PROFIT_THRESHOLD=0.05
```

### 使用配置管理器

```python
from config.settings_optimized import get_config

# 获取配置
config = get_config()

# 更新配置
config.update_trading_config(
    ma_short=15,
    ma_long=30,
    volume_threshold=0.25
)

# 保存配置
config.save_config()

# 导出/导入配置
config.export_config('my_config.json')
config.import_config('my_config.json')
```

## 📊 数据验证

确保数据质量：

```python
from core import validate_stock_data
import pandas as pd

# 加载数据
df = pd.read_csv('stock_data.csv')

# 验证并清洗数据
cleaned_df, is_valid, errors = validate_stock_data(df)

if not is_valid:
    print(f"数据验证失败: {errors}")
else:
    print("数据验证通过")
    print(f"清洗后数据行数: {len(cleaned_df)}")
```

## 🧪 运行测试

验证优化效果：

```bash
# 运行功能测试
python tests/test_optimizations.py

# 运行性能测试
python tests/test_performance.py

# 使用pytest运行所有测试
pytest tests/ -v
```

## 📈 性能优化建议

### 1. 预加载热门股票

```python
from services import DataService

data_service = DataService()
data_service.preload_data(count=50)  # 预加载前50只股票
```

### 2. 批量加载股票

```python
# 批量加载多只股票
codes = ['000001.SZ', '000002.SZ', '600000.SH']
stock_data_dict = data_service.manager.load_multiple_stocks(codes)
```

### 3. 使用缓存

```python
# 查看缓存统计
stats = data_service.get_cache_stats()
print(f"缓存股票数: {stats['cached_stocks']}")
print(f"缓存命中率: {stats['cache_ratio']:.2%}")

# 清除缓存
data_service.manager.clear_cache()
```

## 🎨 可视化示例

### 生成图表

```python
from services import ChartService

chart_service = ChartService()

# 生成价格图表
fig = chart_service.create_price_chart(
    stock_data.df,
    result.signals,
    stock_data.stock_info.display_name
)

# 显示图表
fig.show()
```

### 导出图表

```python
# 保存为HTML
fig.write_html('stock_chart.html')

# 保存为图片
fig.write_image('stock_chart.png')
```

## 📝 常见问题

### Q1: 如何从旧版本迁移？

A: 只需更新导入语句即可，API保持兼容：

```python
# 旧版本
from services import StrategyService

# 新版本（推荐）
from services.strategy_service_optimized import StrategyService
```

### Q2: 优化版本会影响现有功能吗？

A: 不会。优化版本完全兼容原有API，可以无缝切换。

### Q3: 如何查看性能提升？

A: 运行性能测试：

```bash
python tests/test_performance.py
```

### Q4: 缓存会占用太多内存吗？

A: 默认缓存限制为100只股票，可根据需要调整：

```python
# 在 data_service_optimized.py 中修改
self._max_cache_size = 200  # 调整为200
```

### Q5: 如何添加新的策略？

A: 继承 `BaseStrategy` 类并实现必要方法：

```python
from strategies import BaseStrategy

class MyStrategy(BaseStrategy):
    def analyze(self, stock_data):
        # 实现策略逻辑
        pass
    
    def get_strategy_name(self):
        return "策略名称"
    
    def get_strategy_description(self):
        return "策略描述"
```

## 🔗 相关文档

- [优化总结](OPTIMIZATION_SUMMARY.md) - 详细的优化内容说明
- [策略定义说明](1020策略定义说明.md) - 1020策略的详细定义
- [README](README.md) - 项目总体说明

## 💡 最佳实践

1. **使用缓存**: 预加载常用股票数据
2. **批量操作**: 使用批量加载代替单个加载
3. **数据验证**: 始终验证输入数据
4. **回测验证**: 使用回测引擎评估策略
5. **配置管理**: 使用配置文件和环境变量

## 🎉 开始使用

现在你已经了解了优化版本的主要功能，开始使用吧！

```python
# 快速开始
from services import DataService, StrategyService
from core import BacktestEngine

# 1. 加载数据
data_service = DataService()
stock_data = data_service.get_stock_data('000001.SZ')

# 2. 分析信号
strategy = StrategyService()
result = strategy.analyze(stock_data)

# 3. 回测评估
engine = BacktestEngine()
metrics = engine.run_backtest(stock_data, result)

# 4. 查看结果
print(metrics.to_dict())
```

祝你使用愉快！ 🚀
