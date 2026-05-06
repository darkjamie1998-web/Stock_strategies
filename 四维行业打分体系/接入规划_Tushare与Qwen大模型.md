# 四维行业打分体系 —— Tushare 数据源 & Qwen 大模型接入规划

---

## 一、项目现状分析

### 1.1 当前架构

```
四维行业打分体系/
├── main.py                    # 入口：CLI示例 / Web服务器
├── config/
│   └── industries.yaml        # 行业配置（用户手动填写）
├── models/
│   └── __init__.py            # 数据模型定义
├── engine/
│   └── __init__.py            # 评分引擎（编排四个评分器）
├── scorers/
│   ├── base_scorer.py         # 评分器抽象基类
│   ├── prosperity.py          # 维度一：行业景气度
│   ├── policy.py              # 维度二：政策面
│   ├── capital.py             # 维度三：资金面
│   └── technical.py           # 维度四：技术面
├── utils/
│   └── helpers.py             # YAML加载、格式化、导出
├── web/
│   ├── index.html
│   └── static/
│       ├── app.js
│       ├── scoring-engine.js  # 前端评分引擎（JS复刻）
│       └── styles.css
└── output/                    # 评分结果输出
```

### 1.2 当前数据流

```
用户手动填写 industries.yaml
        │
        ▼
  main.py 加载配置
        │
        ▼
  IndustryScoringEngine.batch_score()
        │
        ├── ProsperityScorer  ← IndustryData（行业类型、周期阶段）
        ├── PolicyScorer      ← PolicyData（是否有政策、是否有催化事件）
        ├── CapitalScorer     ← CapitalData（ETF净申购、公募仓位变化）
        └── TechnicalScorer   ← TechnicalData（技术信号列表）
        │
        ▼
  IndustryScoreResult（总分、信号等级、操作建议）
```

### 1.3 当前"待用户填写"的数据字段

| 维度 | 字段 | 类型 | 当前来源 |
|------|------|------|----------|
| 行业景气度 | `industry_type`（周期性/非周期性） | 定性 | 用户主观判断 |
| 行业景气度 | `cycle_phase`（底部/成长期/衰退期等） | 定性 | 用户主观判断 |
| 政策面 | `has_support_policy` | 定性 | 用户主观判断 |
| 政策面 | `policy_description` | 定性 | 用户手动填写 |
| 政策面 | `has_catalyst_event` | 定性 | 用户主观判断 |
| 政策面 | `catalyst_description` | 定性 | 用户手动填写 |
| 资金面 | `etf_net_subscription` | 定量 | 用户手动输入 |
| 资金面 | `fund_position_change` | 定量 | 用户手动输入 |
| 技术面 | `signals`（技术信号） | 定量+定性 | 用户手动判断 |

**核心问题**：所有数据依赖用户手动填写，主观性强、时效性差、无法批量自动化。

---

## 二、Tushare 数据源接入方案

### 2.1 Tushare 简介

Tushare 是一个免费、开源的 Python 金融数据接口包，提供股票、基金、指数、宏观经济等全品类金融数据。需要注册获取 API Token，基础接口免费，高频/高级接口需积分。

- 官网：https://tushare.pro
- Python SDK：`pip install tushare`
- 认证方式：`ts.set_token('your_token')` → `ts.pro_api()`

### 2.2 各维度数据映射

#### 维度一：行业景气度 —— 定量数据替代定性判断

当前 `ProsperityScorer` 依赖用户手动判断 `industry_type` 和 `cycle_phase`。可通过 Tushare 获取行业基本面数据，用规则引擎自动判定。

| 需要的判断 | Tushare 接口 | 可用字段 | 自动判定逻辑 |
|-----------|-------------|---------|-------------|
| 行业分类（周期性/非周期性） | `ths_index` / 预置映射表 | `ts_code`, `name` | 建立申万行业→周期属性映射表 |
| 行业景气阶段 | `index_daily` + 财务数据 | 行业指数走势、PE/PB分位 | 基于价格趋势+估值分位判定 |
| 行业营收/利润增速 | `ths_daily` / `ths_index` | 同花顺行业指数 | 趋势分析判定景气方向 |

**推荐方案**：

```
Tushare API
    │
    ▼
industry_data_fetcher.py（新增模块）
    │
    ├── 获取申万行业分类 → 映射周期性/非周期性
    ├── 获取行业指数历史K线 → 计算趋势（MA20/MA60斜率）
    ├── 获取行业PE/PB分位数 → 判断估值位置
    └── 综合判定 cycle_phase（底部/底部反转/成长期/成熟期/衰退期）
    │
    ▼
自动填充 IndustryData
```

**具体 Tushare 接口调用**：

```python
import tushare as ts

pro = ts.pro_api()

# 1. 获取申万行业分类
# pro.index_classify(level='L1', src='SW')  → 一级行业列表

# 2. 获取行业指数日线
# pro.index_daily(ts_code='801080.SI', start_date='20240101')
# → 用于计算均线趋势、阶段判定

# 3. 获取行业指数估值
# pro.index_dailybasic(ts_code='801080.SI')
# → pe, pb 用于分位数计算
```

#### 维度二：政策面 —— 暂不适用（见 Qwen 方案）

政策面数据属于非结构化文本信息，Tushare 不直接提供政策新闻数据。此维度更适合接入 Qwen 大模型处理（见第三章）。

#### 维度三：资金面 —— 定量数据直接替代

当前 `CapitalScorer` 需要的两个字段均可从 Tushare 获取：

| 字段 | Tushare 接口 | 说明 |
|------|-------------|------|
| `etf_net_subscription`（ETF月度净申购） | `fund_daily` | 获取行业ETF的日净值+份额，计算月度净申购 |
| `fund_position_change`（公募仓位变化） | `fund_portfolio` | 获取公募基金季度持仓，计算仓位变化 |

**推荐方案**：

```python
# 1. ETF净申购
# 步骤：
#   a. 通过 fund_basic 筛选行业ETF（如芯片ETF、新能源ETF等）
#   b. 通过 fund_daily 获取日份额数据
#   c. 计算月度净申购 = 月末份额 - 月初份额

# 2. 公募基金仓位
# 步骤：
#   a. 通过 fund_portfolio 获取季度持仓
#   b. 汇总特定行业基金的股票仓位
#   c. 计算环比变化
```

**行业ETF映射表**（需预置）：

| 行业 | 对应ETF代码 | ETF名称 |
|------|-----------|---------|
| 芯片 | 159995.SZ | 芯片ETF |
| 机器人 | 562500.SH | 机器人ETF |
| 电池 | 159755.SZ | 电池ETF |
| 创新药 | 159992.SZ | 创新药ETF |
| ... | ... | ... |

#### 维度四：技术面 —— 定量计算替代人工判断

当前 `TechnicalScorer` 的三种信号均可通过价格数据自动检测：

| 信号类型 | 计算逻辑 | Tushare 接口 |
|---------|---------|-------------|
| 1020起爆点 | 收盘价站上10日&20日均线，且前一日在均线下方 | `index_daily` |
| 龙回头 | 前期大涨→回调至关键均线→再度放量走强 | `index_daily` |
| 意外大跌抄底 | 单日跌幅>3%且偏离20日均线>5%，成交量放大 | `index_daily` |

**推荐方案**：

```python
# 获取行业指数日线数据
df = pro.index_daily(ts_code='801080.SI', start_date='20240101')

# 计算技术指标
df['ma10'] = df['close'].rolling(10).mean()
df['ma20'] = df['close'].rolling(20).mean()
df['ma60'] = df['close'].rolling(60).mean()

# 检测1020起爆点
df['signal_1020'] = (df['close'] > df['ma10']) & (df['close'] > df['ma20']) & \
                     (df['close'].shift(1) <= df['ma10'].shift(1))

# 检测意外大跌抄底
df['pct_change'] = df['close'].pct_change()
df['deviation'] = (df['close'] - df['ma20']) / df['ma20']
df['signal_dip'] = (df['pct_change'] < -0.03) & (df['deviation'] < -0.05) & \
                    (df['vol'] > df['vol'].rolling(20).mean() * 1.5)

# 检测龙回头
# 前期涨幅>15%（过去20日）→ 回调至MA20附近（偏离<3%）→ 当日涨幅>2%且放量
```

### 2.3 新增模块结构

```
四维行业打分体系/
├── data_sources/                  # 新增：数据源层
│   ├── __init__.py
│   ├── tushare_client.py          # Tushare API 客户端封装
│   ├── industry_fetcher.py        # 行业景气度数据获取
│   ├── capital_fetcher.py         # 资金面数据获取
│   ├── technical_fetcher.py       # 技术面数据获取+信号检测
│   └── etf_mapping.yaml           # 行业→ETF映射配置
├── config/
│   └── industries.yaml            # 保留，作为行业列表+覆盖配置
├── ...（其余不变）
```

### 2.4 Tushare 接入配置

在 `config/` 下新增 `tushare_config.yaml`：

```yaml
tushare:
  token: "your_tushare_token"      # 用户需自行注册获取
  cache_dir: "./data_cache"        # 数据缓存目录
  cache_ttl_hours: 6               # 缓存有效期（小时）

industries:
  - name: "芯片"
    sw_code: "801080.SI"           # 申万行业代码
    etf_codes:                     # 关联ETF
      - "159995.SZ"
      - "512760.SH"
  - name: "机器人"
    sw_code: "850711.SI"
    etf_codes:
      - "562500.SH"
  # ...
```

---

## 三、Qwen 大模型接入方案

### 3.1 Qwen（通义千问）简介

Qwen 是阿里云推出的开源大语言模型系列，通过阿里云 DashScope API 或本地部署均可调用。对于本项目，推荐使用 **DashScope API**（云端调用，无需GPU），成本低、接入简单。

- 官网：https://dashscope.aliyun.com
- Python SDK：`pip install dashscope`
- 推荐模型：`qwen-plus`（性价比高）或 `qwen-max`（效果最好）

### 3.2 适用场景分析

在本项目中，Qwen 大模型最适合处理以下**定性分析**任务：

| 维度 | 任务 | 输入 | 输出 |
|------|------|------|------|
| 政策面 | 判断是否有支持性政策 | 行业名称 + 近期新闻标题/摘要 | `has_support_policy: bool` + `policy_description` |
| 政策面 | 判断是否有催化事件 | 行业名称 + 近期新闻标题/摘要 | `has_catalyst_event: bool` + `catalyst_description` |
| 行业景气度 | 辅助判断周期阶段 | 行业基本面数据 + 近期新闻 | `cycle_phase` 建议 + 分析理由 |
| 综合 | 生成行业分析摘要 | 四维评分结果 | 自然语言分析报告 |

### 3.3 政策面分析 —— 核心应用场景

这是 Qwen 最直接的应用场景。当前 `PolicyScorer` 完全依赖用户手动判断，接入 Qwen 后可实现自动化。

**方案设计**：

```
新闻数据源（新浪财经/东方财富/同花顺等）
    │
    ▼
news_fetcher.py（新增模块）
    │  获取行业相关近期新闻
    │
    ▼
policy_analyzer.py（新增模块）
    │  构造 Prompt → 调用 Qwen API
    │
    ▼
PolicyData（自动填充）
    ├── has_support_policy: true/false
    ├── policy_description: "国产替代政策支持..."
    ├── has_catalyst_event: true/false
    └── catalyst_description: "近期半导体产业政策发布..."
```

**Prompt 设计**：

```python
POLICY_ANALYSIS_PROMPT = """
你是一位专业的A股行业研究员。请根据以下行业近期新闻，分析该行业的政策面情况。

行业名称：{industry_name}

近期相关新闻：
{news_list}

请按以下JSON格式输出分析结果（仅输出JSON，不要其他内容）：
{{
    "has_support_policy": true/false,
    "policy_description": "如有支持政策，简要描述（不超过50字）；如无，留空",
    "has_catalyst_event": true/false,
    "catalyst_description": "如有催化事件，简要描述（不超过50字）；如无，留空",
    "analysis_summary": "综合分析（不超过100字）",
    "confidence": 0.0-1.0
}}

判断标准：
- has_support_policy: 国家层面或部委层面出台了明确支持该行业发展的政策文件、规划、意见等
- has_catalyst_event: 近期发生了可能推动行业上涨的具体事件（政策发布、技术突破、行业大会、龙头企业重大利好等）
"""
```

**DashScope API 调用示例**：

```python
from dashscope import Generation
import json

def analyze_policy(industry_name: str, news_list: list[str]) -> dict:
    prompt = POLICY_ANALYSIS_PROMPT.format(
        industry_name=industry_name,
        news_list="\n".join(f"- {n}" for n in news_list)
    )
    
    response = Generation.call(
        model='qwen-plus',
        messages=[{'role': 'user', 'content': prompt}],
        result_format='message'
    )
    
    result_text = response.output.choices[0].message.content
    # 提取JSON
    return json.loads(result_text)
```

### 3.4 行业景气度辅助判断

Qwen 可作为景气度判断的**辅助增强**，结合 Tushare 定量数据给出更准确的周期阶段判定。

```python
PROSPERITY_ANALYSIS_PROMPT = """
你是一位专业的A股行业研究员。请根据以下行业数据，判断该行业当前所处的周期阶段。

行业名称：{industry_name}
行业类型：{industry_type}

定量数据：
- 行业指数近3月涨跌幅：{pct_3m}%
- 行业指数近6月涨跌幅：{pct_6m}%
- PE当前值：{pe_current}，历史分位：{pe_percentile}%
- PB当前值：{pb_current}，历史分位：{pb_percentile}%
- 行业营收增速（同比）：{revenue_growth}%
- 行业净利润增速（同比）：{profit_growth}%

近期行业新闻摘要：
{news_summary}

请判断该行业当前处于以下哪个阶段（仅输出阶段名称）：
- 底部：价格长期下跌后企稳，估值处于历史低位，基本面尚未改善
- 底部反转：价格开始从底部回升，基本面出现改善迹象
- 成长期：价格持续上行，基本面强劲，行业景气度高
- 成熟期：增速放缓，估值合理，行业格局稳定
- 衰退期：价格持续下行，基本面恶化，行业景气度低
"""
```

### 3.5 综合报告生成

在评分完成后，可调用 Qwen 生成自然语言分析报告：

```python
REPORT_PROMPT = """
你是一位专业的A股行业研究员。请根据以下四维评分结果，生成一份简洁的行业配置建议报告。

评分结果：
{score_summary}

请生成一份不超过300字的分析报告，包含：
1. 总体评价
2. 各维度亮点/风险
3. 操作建议
"""
```

### 3.6 新增模块结构

```
四维行业打分体系/
├── ai_analysis/                       # 新增：AI分析层
│   ├── __init__.py
│   ├── qwen_client.py                 # Qwen API 客户端封装
│   ├── policy_analyzer.py             # 政策面AI分析
│   ├── prosperity_analyzer.py         # 景气度AI辅助分析
│   ├── report_generator.py            # 综合报告生成
│   └── prompts.py                     # Prompt模板管理
├── data_sources/
│   ├── news_fetcher.py                # 新增：新闻数据获取
│   └── ...
├── config/
│   └── qwen_config.yaml               # 新增：Qwen配置
├── ...（其余不变）
```

### 3.7 Qwen 接入配置

在 `config/` 下新增 `qwen_config.yaml`：

```yaml
qwen:
  api_key: "your_dashscope_api_key"    # 用户需自行注册获取
  model: "qwen-plus"                   # qwen-plus / qwen-max / qwen-turbo
  max_tokens: 1000
  temperature: 0.3                     # 低温度保证输出稳定
  enable_policy_analysis: true         # 是否启用政策面AI分析
  enable_prosperity_analysis: false    # 是否启用景气度AI辅助（可选）
  enable_report_generation: true       # 是否启用AI报告生成

news:
  sources:
    - "eastmoney"                      # 东方财富
    - "sina"                           # 新浪财经
  max_articles_per_industry: 10
  lookback_days: 30                    # 回溯天数
```

---

## 四、整体架构演进

### 4.1 目标架构

```
                        ┌──────────────────────┐
                        │   config/             │
                        │   ├── industries.yaml │  ← 行业列表+手动覆盖
                        │   ├── tushare_config  │  ← Tushare Token
                        │   └── qwen_config     │  ← Qwen API Key
                        └──────┬───────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          │                    │                    │
          ▼                    ▼                    ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  data_sources/  │  │  ai_analysis/   │  │  scorers/       │
│                 │  │                 │  │  (保持不变)      │
│ tushare_client  │  │ qwen_client     │  │                 │
│ industry_fetcher│  │ policy_analyzer │  │ ProsperityScorer│
│ capital_fetcher │  │ prosperity_     │  │ PolicyScorer    │
│ technical_fetcher│ │   analyzer      │  │ CapitalScorer   │
│ news_fetcher    │  │ report_generator│  │ TechnicalScorer │
└────────┬────────┘  └────────┬────────┘  └────────┬────────┘
         │                    │                    │
         └────────────────────┼────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │  engine/        │
                    │  (增强版)        │
                    │  编排数据获取→   │
                    │  AI分析→评分     │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  IndustryScore  │
                    │  Result +       │
                    │  AI分析报告     │
                    └─────────────────┘
```

### 4.2 增强后的数据流

```
1. 加载 industries.yaml（行业列表）
        │
2. 对每个行业：
   ├── data_sources/industry_fetcher   → Tushare获取行业指数+估值 → 判定cycle_phase
   ├── data_sources/capital_fetcher    → Tushare获取ETF净申购+公募仓位
   ├── data_sources/technical_fetcher  → Tushare获取K线 → 检测技术信号
   ├── data_sources/news_fetcher       → 获取行业近期新闻
   └── ai_analysis/policy_analyzer     → Qwen分析新闻 → 判定政策面
        │
3. engine/IndustryScoringEngine → 汇总数据 → 执行四维评分
        │
4. ai_analysis/report_generator → Qwen生成综合分析报告
        │
5. 输出：评分结果 + AI分析报告
```

### 4.3 降级策略

当外部服务不可用时，系统应能优雅降级：

| 场景 | 降级策略 |
|------|---------|
| Tushare API 不可用 | 回退到 `industries.yaml` 中的手动配置数据 |
| Qwen API 不可用 | 政策面回退到 `industries.yaml` 中的手动配置 |
| 新闻源不可用 | 政策面回退到手动配置，其他维度不受影响 |
| 全部外部服务不可用 | 完全回退到当前纯手动模式 |

---

## 五、实施路线图

### Phase 1：基础设施搭建（预计改动 3~4 个文件）

- [ ] 新增 `data_sources/tushare_client.py`：Tushare API 客户端封装（Token管理、请求限流、缓存）
- [ ] 新增 `config/tushare_config.yaml`：Tushare 配置模板
- [ ] 更新 `requirements.txt`：添加 `tushare` 依赖

### Phase 2：定量数据接入（预计改动 4~5 个文件）

- [ ] 新增 `data_sources/capital_fetcher.py`：ETF净申购 + 公募仓位获取
- [ ] 新增 `data_sources/technical_fetcher.py`：技术信号自动检测
- [ ] 新增 `data_sources/industry_fetcher.py`：行业分类 + 周期阶段判定
- [ ] 新增 `data_sources/etf_mapping.yaml`：行业→ETF映射表
- [ ] 修改 `engine/__init__.py`：支持从 Tushare 自动获取数据

### Phase 3：AI 定性分析接入（预计改动 4~5 个文件）

- [ ] 新增 `ai_analysis/qwen_client.py`：DashScope API 客户端封装
- [ ] 新增 `ai_analysis/prompts.py`：Prompt 模板
- [ ] 新增 `ai_analysis/policy_analyzer.py`：政策面 AI 分析
- [ ] 新增 `data_sources/news_fetcher.py`：行业新闻获取
- [ ] 新增 `config/qwen_config.yaml`：Qwen 配置模板
- [ ] 更新 `requirements.txt`：添加 `dashscope` 依赖

### Phase 4：综合增强（预计改动 2~3 个文件）

- [ ] 新增 `ai_analysis/report_generator.py`：AI 综合报告生成
- [ ] 新增 `ai_analysis/prosperity_analyzer.py`：景气度 AI 辅助
- [ ] 修改 `main.py`：新增 `--auto` 模式（自动获取数据+AI分析）

### Phase 5：Web 前端适配（预计改动 2~3 个文件）

- [ ] 修改 `web/static/app.js`：增加"自动获取数据"按钮
- [ ] 修改 `web/static/scoring-engine.js`：支持展示 AI 分析结果
- [ ] 修改 `web/index.html`：增加 AI 分析报告展示区域

---

## 六、关键注意事项

### 6.1 安全性

- **API Key 管理**：Tushare Token 和 DashScope API Key 存储在配置文件中，**不要提交到 Git**。建议在 `.gitignore` 中添加 `*_config.yaml`（或提供 `.example` 模板文件）
- **请求频率控制**：Tushare 免费版有请求频率限制（通常 200次/分钟），需在 `tushare_client.py` 中实现限流

### 6.2 成本控制

| 服务 | 费用模式 | 预估月成本 |
|------|---------|-----------|
| Tushare | 基础接口免费，高级接口需积分（可通过签到获取） | ¥0 |
| DashScope Qwen-Plus | 按 Token 计费（输入 ¥0.004/千token，输出 ¥0.012/千token） | 约 ¥5~20/月（取决于分析频率） |

### 6.3 数据缓存

为避免重复请求和降低成本，建议实现两级缓存：

1. **Tushare 数据缓存**：K线/估值数据缓存 6 小时（交易日内不变）
2. **Qwen 分析缓存**：同一行业+同一批新闻的分析结果缓存 24 小时

### 6.4 新闻数据源选择

政策面分析需要行业新闻作为 Qwen 的输入。推荐方案（按优先级）：

1. **东方财富行业板块新闻**：免费、覆盖面广、更新及时
2. **同花顺行业新闻**：行业分类清晰
3. **新浪财经**：API 相对稳定

建议实现一个抽象的 `NewsFetcher` 基类，支持多个新闻源切换。

### 6.5 向后兼容

- `industries.yaml` 中的手动配置字段**全部保留**，作为 Tushare/Qwen 不可用时的 fallback
- 如果用户在 YAML 中填写了数据，优先使用用户填写的数据（手动覆盖 > 自动获取）
- 新增的自动获取功能通过命令行参数 `--auto` 或配置文件开关控制，默认关闭

---

## 七、依赖更新

更新后的 `requirements.txt`：

```
pandas>=2.0.0
pyyaml>=6.0
tushare>=1.4.0
dashscope>=1.20.0
requests>=2.31.0
```

---

> **文档版本**：v1.0  
> **创建日期**：2026-05-03  
> **适用范围**：`d:\trae_projects\Stock_strategies\四维行业打分体系`
