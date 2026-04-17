import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorers.base_scorer import BaseScorer
from models import IndustryData, DimensionScore


class ProsperityScorer(BaseScorer):
    """行业景气度评分器"""
    
    VALID_CYCLE_PHASES_CYCLICAL = ['底部', '底部反转']
    VALID_CYCLE_PHASES_NON_CYCLICAL = ['成长期', '成熟期']
    DECLINE_PHASES = ['衰退期', '下行周期']
    
    def __init__(self):
        super().__init__("行业景气度")
    
    def score(self, industry_data: IndustryData, **kwargs) -> DimensionScore:
        """
        评估行业景气度
        
        评分规则：
        - 周期性行业：处于底部或底部反转阶段得1分
        - 非周期性行业：处于成长期或成熟期得1分
        - 其他情况得0分
        
        Args:
            industry_data: 行业数据
            
        Returns:
            DimensionScore: 评分结果
        """
        if not isinstance(industry_data, IndustryData):
            return self._create_score(
                score=0,
                reason="无效的行业数据",
                details={'error': 'invalid_industry_data'}
            )
        
        cycle_phase = industry_data.cycle_phase
        industry_type = industry_data.industry_type
        
        details = {
            'industry_type': industry_type,
            'cycle_phase': cycle_phase
        }
        
        if industry_type == '周期性':
            if cycle_phase in self.VALID_CYCLE_PHASES_CYCLICAL:
                return self._create_score(
                    score=1,
                    reason=f"周期性行业，处于{cycle_phase}阶段",
                    details=details
                )
            else:
                advice = f"周期性行业，但处于{cycle_phase}阶段（非理想状态）"
                if cycle_phase in self.DECLINE_PHASES:
                    advice += " - 衰退型行业，建议回避"
                
                return self._create_score(
                    score=0,
                    reason=advice,
                    details=details
                )
        
        elif industry_type == '非周期性':
            if cycle_phase in self.VALID_CYCLE_PHASES_NON_CYCLICAL:
                return self._create_score(
                    score=1,
                    reason=f"非周期性行业，处于{cycle_phase}",
                    details=details
                )
            else:
                return self._create_score(
                    score=0,
                    reason=f"非周期性行业，但处于{cycle_phase}阶段",
                    details=details
                )
        
        else:
            return self._create_score(
                score=0,
                reason=f"未知行业类型：{industry_type}",
                details=details
            )
