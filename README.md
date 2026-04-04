# 三维共振+1020双线交易策略

基于高志强提出的"三维共振+1020双线"交易策略的Python实现。该策略构建了一套完整的"宏观判断—行业筛选—择时交易—风险控制"四层闭环逻辑，通过系统化规则实现顺势而为、截断亏损、让利润奔跑的交易目标。

## 策略核心组件

### 1. 三维共振系统
- **政策面评估**：判断是否有明确的利好政策支持
- **资金面评估**：判断资金是否持续流入市场
- **技术面评估**：判断是否站上10日和20日均线
- **仓位建议**：根据三维得分确定市场趋势和仓位比例

### 2. 行业四维打分体系
- **景气度评分**：评估行业成长性和前景
- **政策面评分**：判断行业政策支持程度
- **资金面评分**：分析资金流向和成交量
- **技术面评分**：检测技术买入信号

### 3. 1020双均线策略
- **双龙出水**：首次放量站上双均线的买入信号
- **潜龙入渊**：回踩10日均线企稳的加码信号
- **见龙在田**：回踩20日均线企稳的加码信号
- **龙战于野**：连续破位或大幅下跌的离场信号

## 安装要求

```bash
pip install pandas numpy
```

## 快速开始

### 基础使用示例

```python
from three_d_resonance_strategy import ThreeDResonanceStrategy

# 初始化策略
strategy = ThreeDResonanceStrategy()

# 1. 三维共振分析
policy_data = {'has_supportive_policy': True, 'has_recent_catalyst': True}
capital_data = {'volume_increase': True, 'capital_inflow': True}
technical_data = {'above_ma10': True, 'above_ma20': True}

resonance_result = strategy.three_d_resonance_analysis(policy_data, capital_data, technical_data)
print(f"市场趋势: {resonance_result.market_trend.value}")
print(f"建议仓位: {resonance_result.suggested_position[0]*100:.0f}%-{resonance_result.suggested_position[1]*100:.0f}%")

# 2. 行业打分
industry_data = {
    'name': '芯片行业',
    'is_growth_industry': True,
    'has_positive_outlook': True,
    'has_supportive_policy': True,
    'has_recent_catalyst': True,
    'volume_gap_up': True,
    'volume_increase': True,
    'has_buying_opportunity': False,
    'has_1020_breakout': True,
    'has_dragon_return': False
}

industry_result = strategy.industry_scoring(industry_data)
print(f"行业得分: {industry_result.total_score}/4")
print(f"推荐建议: {industry_result.recommendation}")

# 3. 计算仓位
position_size = strategy.calculate_position_size(
    resonance_result.market_trend,
    industry_result.total_score,
    100000  # 10万元可用资金
)
print(f"建议投资金额: ¥{position_size:,.0f}")
```

## 输入数据格式要求

### 1. 三维共振系统输入数据

#### 政策面数据 (policy_data)
```python
{
    'has_supportive_policy': True/False,  # 是否有明确的利好政策支持
    'has_recent_catalyst': True/False     # 是否有近期催化事件
}
```

**判断标准：**
- `has_supportive_policy`：关注国家层面政策文件、行业发展规划
- `has_recent_catalyst`：关注重大会议、政策落地、行业事件

#### 资金面数据 (capital_data)
```python
{
    'volume_increase': True/False,        # 成交量是否明显放大
    'capital_inflow': True/False          # 资金是否持续流入
}
```

**判断标准：**
- `volume_increase`：成交量较前5日均值增长20%以上
- `capital_inflow`：北向资金/主力资金连续3日净流入

#### 技术面数据 (technical_data)
```python
{
    'above_ma10': True/False,             # 是否站上10日均线
    'above_ma20': True/False              # 是否站上20日均线
}
```

**判断标准：**
- 收盘价连续2日站稳在均线之上视为有效突破

### 2. 行业打分体系输入数据

```python
{
    'name': '行业名称',                    # 字符串类型
    'is_growth_industry': True/False,     # 是否为成长性行业
    'has_positive_outlook': True/False,   # 是否有积极前景
    'has_supportive_policy': True/False,  # 是否有政策支持
    'has_recent_catalyst': True/False,    # 是否有近期催化
    'volume_gap_up': True/False,          # 是否跳空放量
    'volume_increase': True/False,        # 成交量是否放大
    'has_buying_opportunity': True/False, # 是否有抄底机会
    'has_1020_breakout': True/False,      # 是否有1020起爆点
    'has_dragon_return': True/False       # 是否有龙回头信号
}
```

**各维度评分标准：**

| 维度 | 评分条件 | 得分 |
|------|----------|------|
| 景气度 | 处于成长期产业，有积极前景 | 1分 |
| 政策面 | 有支持性政策+近期催化 | 1分 |
| 资金面 | 跳空放量或成交量放大 | 1分 |
| 技术面 | 有抄底机会/1020起爆点/龙回头 | 1分 |

**推荐标准：**
- 总分≥3分：具备配置价值（潜伏信号）
- 总分=4分：强买入信号

### 3. 1020双均线策略输入数据

**价格数据DataFrame格式：**
```python
import pandas as pd

# 必需的数据列
price_data = pd.DataFrame({
    'open': [开盘价列表],      # 开盘价
    'high': [最高价列表],      # 最高价  
    'low': [最低价列表],       # 最低价
    'close': [收盘价列表],     # 收盘价（最重要的价格数据）
    'volume': [成交量列表]     # 成交量
}, index=日期索引)
```

**数据要求：**
- 至少需要20个交易日的数据（用于计算20日均线）
- 日期索引应为pandas的DatetimeIndex
- 价格数据应为数值类型

## 详细使用指南

### 步骤1：数据准备

#### 获取实时数据（推荐使用akshare）
```python
import akshare as ak

# 获取股票数据
stock_data = ak.stock_zh_a_hist(symbol="000001", period="daily", adjust="qfq")

# 转换为标准格式
price_data = stock_data[['开盘', '最高', '最低', '收盘', '成交量']]
price_data.columns = ['open', 'high', 'low', 'close', 'volume']
price_data.index = pd.to_datetime(stock_data['日期'])
```

#### 手动准备数据
```python
import pandas as pd
import numpy as np

# 创建示例数据
dates = pd.date_range('2024-01-01', periods=50, freq='D')
price_data = pd.DataFrame({
    'open': np.random.normal(100, 5, 50),
    'high': np.random.normal(105, 5, 50),
    'low': np.random.normal(95, 5, 50),
    'close': np.random.normal(100, 5, 50),
    'volume': np.random.normal(1000000, 200000, 50)
}, index=dates)
```

### 步骤2：策略执行流程

```python
from three_d_resonance_strategy import ThreeDResonanceStrategy

# 初始化策略
strategy = ThreeDResonanceStrategy()

# 1. 宏观趋势判断（三维共振）
def get_market_analysis():
    """根据当前市场情况获取三维共振分析"""
    # 这里需要根据实际市场数据设置布尔值
    policy_data = {
        'has_supportive_policy': True,  # 例如：近期有降准降息
        'has_recent_catalyst': True     # 例如：重要经济会议召开
    }
    
    capital_data = {
        'volume_increase': True,        # 例如：成交量放大
        'capital_inflow': True          # 例如：外资流入
    }
    
    technical_data = {
        'above_ma10': True,             # 例如：指数站上10日线
        'above_ma20': True              # 例如：指数站上20日线
    }
    
    return strategy.three_d_resonance_analysis(policy_data, capital_data, technical_data)

# 2. 行业筛选（四维打分）
def score_industry(industry_name):
    """对特定行业进行打分"""
    industry_data = {
        'name': industry_name,
        'is_growth_industry': True,     # 是否为成长行业
        'has_positive_outlook': True,   # 行业前景
        'has_supportive_policy': True,  # 政策支持
        'has_recent_catalyst': True,    # 近期催化
        'volume_gap_up': False,         # 跳空放量
        'volume_increase': True,        # 成交量放大
        'has_buying_opportunity': False,
        'has_1020_breakout': True,      # 1020起爆点
        'has_dragon_return': False
    }
    
    return strategy.industry_scoring(industry_data)

# 3. 交易信号生成
def generate_trading_signals(price_data):
    """生成1020双均线交易信号"""
    return strategy.generate_1020_signals(price_data)

# 4. 仓位计算
def calculate_investment_amount(market_trend, industry_score, available_capital):
    """计算建议投资金额"""
    return strategy.calculate_position_size(market_trend, industry_score, available_capital)

# 执行完整策略
market_analysis = get_market_analysis()
industry_score = score_industry("芯片行业")
signals = generate_trading_signals(price_data)
investment_amount = calculate_investment_amount(
    market_analysis.market_trend, 
    industry_score.total_score, 
    100000
)

print("策略执行结果:")
print(f"- 市场趋势: {market_analysis.market_trend.value}")
print(f"- 行业得分: {industry_score.total_score}/4")
print(f"- 检测到信号: {len(signals)}个")
print(f"- 建议投资: ¥{investment_amount:,.0f}")
```

### 步骤3：信号解读和交易执行

#### 交易信号类型说明

| 信号类型 | 信号名称 | 触发条件 | 操作建议 |
|----------|----------|----------|----------|
| 买入信号 | 双龙出水 | 首次放量站上双均线 | 初始建仓 |
| 加码信号 | 潜龙入渊 | 回踩10日线企稳 | 增加持仓 |
| 加码信号 | 见龙在田 | 回踩20日线企稳 | 二次加仓 |
| 离场信号 | 龙战于野 | 连续破位或大跌 | 立即止损 |

#### 仓位管理原则

根据三维共振结果确定总仓位：
- **单边上行行情**（三维共振）：70-100%仓位
- **横盘震荡行情**（二维共振）：30-70%仓位  
- **单边下跌行情**（二维以下）：0-30%仓位

## 数据获取工具推荐

### 1. 政策面数据源
- 中国政府网：http://www.gov.cn
- 新华社：http://www.xinhuanet.com
- 财经新闻：新浪财经、东方财富

### 2. 资金面数据源
- 北向资金：通过akshare获取
- 成交量数据：股票API
- 资金流向：同花顺、东方财富

### 3. 技术面数据源
- 股票数据：akshare、tushare
- 均线计算：pandas rolling函数

### 4. 行业数据源
- 行业研报：券商研究报告
- 行业数据：国家统计局、行业协会

## 参数调整指南

### 可调整参数
```python
strategy = ThreeDResonanceStrategy()

# 修改均线周期
strategy.ma_short = 5    # 短期均线（默认10）
strategy.ma_long = 30    # 长期均线（默认20）

# 修改止损阈值
strategy.stop_loss_threshold = 0.03  # 3%止损（默认5%）

# 修改成交量比较周期
strategy.volume_lookback = 10  # 10日成交量均值（默认5）
```

### 参数调整建议

1. **激进型投资者**：
   - 缩短均线周期（如5-15）
   - 降低止损阈值（如3%）
   - 提高仓位上限

2. **保守型投资者**：
   - 延长均线周期（如20-60）
   - 提高止损阈值（如7%）
   - 降低仓位上限

## 常见问题解答

### Q1: 如何判断政策面是否支持？
A: 关注国家层面的政策文件、行业发展规划、重要会议决议等。有明显利好政策且近期有催化事件时设为True。

### Q2: 成交量"明显放大"的标准是什么？
A: 通常指成交量较前5日均值增长20%以上，且具有持续性。

### Q3: 什么是"有效站上"均线？
A: 收盘价连续2个交易日站在均线之上，且成交量配合放大。

### Q4: 行业打分中哪些行业值得关注？
A: 优先关注机器人、芯片、电池、创新药等科技成长行业，规避钢铁、房地产等衰退行业。

### Q5: 如何处理信号冲突？
A: 以离场信号（龙战于野）为最高优先级，出现离场信号时立即执行，不考虑其他信号。

## 风险提示

1. **市场风险**：任何交易策略都存在亏损风险
2. **数据风险**：输入数据质量直接影响策略效果
3. **参数风险**：不同市场环境下可能需要调整参数
4. **执行风险**：实际交易中可能存在滑点等问题

## 更新日志

- v1.0.0 (2024-03-13)：初始版本，实现基本策略功能
- 包含三维共振、行业打分、1020双均线策略

## 联系我们

如有问题或建议，请通过以下方式联系：
- 邮箱：example@email.com
- GitHub：提交Issue或Pull Request

---

**免责声明**：本策略仅供参考学习，不构成投资建议。投资有风险，入市需谨慎。