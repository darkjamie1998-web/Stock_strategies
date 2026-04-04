# 1020双均线交易策略系统

基于历史数据的股票交易策略回测与信号分析系统。

## 功能特性

- 策略信号生成：双龙出水、潜龙入渊、见龙在田、龙战于野、收获果实
- 可视化图表：K线图、均线、成交量、信号标记
- 参数调优：实时调整策略参数并查看结果
- 数据管理：自动加载和缓存股票数据
- 配置持久化：保存和加载自定义配置
- 单元测试：完整的测试覆盖

## 策略说明

### 信号类型

1. 双龙出水（买入信号）
   - 首次放量站上双均线
   - 跳空且放量站上双均线
   - 空头转多头排列且放量

2. 潜龙入渊（加码信号）
   - 首次回踩10日均线

3. 见龙在田（加码信号）
   - 首次回踩20日均线

4. 龙战于野（离场信号）
   - 连续2个交易日收盘价低于20日均线
   - 单日跌幅超过止损阈值并有效破位

5. 收获果实（止盈信号）
   - 涨幅超过止盈阈值

### 约束条件

- 买入信号后无离场信号不产生新买入信号
- 离场信号后无买入信号不产生新离场信号
- 连续5日空头排列后不观测加码和买入信号
- 信号屏蔽窗口内不考虑离场信号

## 安装步骤

### 环境要求

- Python 3.8+
- pip

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置Tushare Token（可选）

如果需要更新股票数据，需要配置Tushare API Token：

1. 在项目根目录创建 `tushare_token.txt` 文件
2. 将你的Tushare Token写入文件

## 使用方法

### 启动应用

```bash
python main.py
```

应用将在 http://127.0.0.1:8050 启动

### 更新股票数据

```bash
python update_data.py
```

可选参数：
- `--delay`: 更新间隔延迟（秒），默认0.1秒

### 运行测试

```bash
python run_tests.py
```

或使用pytest：

```bash
pytest tests/ -v
```

## 项目结构

```
StockStrategy_1020/
├── main.py                 # 主入口文件
├── update_data.py          # 数据更新脚本
├── run_tests.py           # 测试运行脚本
├── requirements.txt       # 依赖包列表
├── .gitignore            # Git忽略文件
├── config/               # 配置模块
│   ├── __init__.py
│   └── settings.py       # 配置管理
├── models/               # 数据模型
│   ├── __init__.py
│   ├── stock.py         # 股票数据模型
│   └── signal.py        # 交易信号模型
├── services/            # 业务逻辑
│   ├── __init__.py
│   ├── data_service.py  # 数据服务
│   ├── strategy_service.py  # 策略服务
│   ├── chart_service.py    # 图表服务
│   └── data_updater.py     # 数据更新
├── views/               # 视图层
│   ├── __init__.py
│   └── app_view.py     # Dash应用视图
├── utils/               # 工具模块
│   ├── __init__.py
│   ├── logger.py       # 日志配置
│   ├── helpers.py      # 辅助函数
│   └── path_helper.py  # 路径管理
├── tests/               # 测试模块
│   ├── conftest.py
│   ├── test_models.py
│   └── test_strategy_service.py
├── assets/              # 静态资源
├── logs/                # 日志文件
├── A股上市公司数据/     # 股票数据目录
└── A股上市公司名单/     # 股票列表
```

## 配置说明

### 策略参数

- MA_SHORT: 短期均线（攻击线），默认10
- MA_LONG: 长期均线（生命线），默认20
- VOLUME_THRESHOLD: 放量阈值，默认20%
- STOP_LOSS_THRESHOLD: 止损阈值，默认5%
- TAKE_PROFIT_THRESHOLD: 止盈阈值，默认5%
- PULLBACK_THRESHOLD: 回踩/站上阈值，默认2%
- SIGNAL_WINDOW: 信号屏蔽窗口（天），默认10
- BEARISH_LIMIT: 空头排列连续限制（天），默认5

### 配置文件

配置会自动保存到 `config.json` 文件，下次启动时自动加载。

## 开发指南

### 代码规范

- 使用Black进行代码格式化
- 使用Flake8进行代码检查
- 使用MyPy进行类型检查

### 运行代码检查

```bash
# 格式化代码
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

### 添加新功能

1. 在相应的模块中添加功能代码
2. 添加单元测试
3. 更新文档
4. 运行测试确保功能正常

## 常见问题

### Q: 如何添加新的股票数据？

A: 将CSV文件放入 `A股上市公司数据` 目录，文件名格式为：`股票代码_股票名称_tushare_起始日期_结束日期.csv`

### Q: 如何修改策略参数？

A: 在应用界面的左侧控制面板中修改参数，点击"生成信号"按钮应用更改。

### Q: 配置文件在哪里？

A: 配置文件位于项目根目录的 `config.json`。

### Q: 如何查看日志？

A: 日志文件位于 `logs` 目录，按日期命名。

## 许可证

本项目仅供学习和研究使用。

## 联系方式

如有问题或建议，请提交Issue。

## 更新日志

### v1.0.0 (2024-03-27)

- 初始版本发布
- 实现1020双均线策略
- 添加可视化界面
- 添加配置持久化
- 添加单元测试
