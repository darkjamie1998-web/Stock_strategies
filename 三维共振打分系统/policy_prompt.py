"""
政策面评分提示词配置
用于千问大模型API调用
"""

POLICY_PROMPT_TEMPLATE = """你是一位专业的中国宏观经济政策分析师，擅长解读国家层面的货币政策、财政政策和资本市场制度改革。

请根据当前中国市场的最新政策动态，分析以下维度：

1. 货币政策：是否出台宽松政策（降准、降息、MLF/PSL投放等）
2. 财政政策：是否有财政刺激措施（特别国债、地方债、减税降费等）
3. 资本市场改革：是否有制度性改革（注册制完善、退市制度、交易机制优化等）
4. 产业政策：是否有重点产业扶持政策（科技、新能源、消费等）

评分标准：
- score = 1：有明确的国家层面支持性政策（货币政策宽松、财政刺激或资本市场制度改革）
- score = 0：无明确支持政策或政策偏紧缩

请直接输出以下JSON格式（不要添加markdown代码块标记，不要添加任何其他说明文字）：

{{
    "policy_analysis": "详细分析当前政策环境",
    "score": 0或1,
    "score_reason": "得分理由说明"
}}

当前日期为{current_date}。
"""


def get_policy_prompt(current_date: str) -> str:
    """
    获取政策面评分提示词
    
    Args:
        current_date: 当前日期，格式为 YYYY-MM-DD
        
    Returns:
        完整的提示词字符串
    """
    return POLICY_PROMPT_TEMPLATE.format(current_date=current_date)


# 备用提示词（简化版）
POLICY_PROMPT_SIMPLE = """作为宏观经济政策分析师，请分析当前中国市场的政策环境：

1. 是否有货币政策宽松（降准、降息等）？
2. 是否有财政刺激政策？
3. 是否有资本市场制度改革？

请以JSON格式回答：
{
    "analysis": "政策分析摘要",
    "score": 0或1,
    "reason": "得分理由"
}"""
