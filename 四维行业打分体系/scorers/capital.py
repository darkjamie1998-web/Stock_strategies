import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorers.base_scorer import BaseScorer
from models import CapitalData, DimensionScore


class CapitalScorer(BaseScorer):
    """资金面评分器"""
    
    def __init__(self):
        super().__init__("资金面")
    
    def score(self, capital_data: CapitalData, **kwargs) -> DimensionScore:
        """
        评估资金面
        
        评分规则：
        - ETF月度净申购金额 > 0 且 公募基金季度仓位未下降 → 1分
        - 任一条件不满足 → 0分
        
        Args:
            capital_data: 资金面数据
            
        Returns:
            DimensionScore: 评分结果
        """
        if not isinstance(capital_data, CapitalData):
            return self._create_score(
                score=0,
                reason="无效的资金面数据",
                details={'error': 'invalid_capital_data'}
            )
        
        etf_positive = capital_data.etf_positive
        fund_stable = capital_data.fund_position_not_declining
        
        details = {
            'etf_net_subscription': capital_data.etf_net_subscription,
            'etf_positive': etf_positive,
            'fund_position_change': capital_data.fund_position_change,
            'fund_position_not_declining': fund_stable
        }
        
        if etf_positive and fund_stable:
            reasons = []
            reasons.append(f"ETF净申购>0（{capital_data.etf_net_subscription:.2f}亿元）")
            reasons.append("公募仓位未降" if capital_data.fund_position_change == 0 
                          else f"公募仓位上升（+{capital_data.fund_position_change:.2f}%）")
            
            return self._create_score(
                score=1,
                reason="，".join(reasons),
                details=details
            )
        
        else:
            problems = []
            if not etf_positive:
                problems.append(f"ETF净申购≤0（{capital_data.etf_net_subscription:.2f}亿元）")
            if not fund_stable:
                problems.append(f"公募仓位下降（{capital_data.fund_position_change:.2f}%）")
            
            return self._create_score(
                score=0,
                reason="；".join(problems),
                details=details
            )
