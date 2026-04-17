import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorers.base_scorer import BaseScorer
from models import PolicyData, DimensionScore


class PolicyScorer(BaseScorer):
    """政策面评分器"""
    
    def __init__(self):
        super().__init__("政策面")
    
    def score(self, policy_data: PolicyData, **kwargs) -> DimensionScore:
        """
        评估政策面
        
        评分规则：
        - 有支持性政策 且 有近期催化事件 → 1分
        - 无支持政策 或 无催化事件 → 0分
        
        Args:
            policy_data: 政策数据
            
        Returns:
            DimensionScore: 评分结果
        """
        if not isinstance(policy_data, PolicyData):
            return self._create_score(
                score=0,
                reason="无效的政策数据",
                details={'error': 'invalid_policy_data'}
            )
        
        details = {
            'has_support_policy': policy_data.has_support_policy,
            'policy_description': policy_data.policy_description,
            'has_catalyst_event': policy_data.has_catalyst_event,
            'catalyst_description': policy_data.catalyst_description
        }
        
        if policy_data.has_support_policy and policy_data.has_catalyst_event:
            reason_parts = []
            if policy_data.policy_description:
                reason_parts.append(f"有支持政策：{policy_data.policy_description}")
            else:
                reason_parts.append("有支持政策")
            
            if policy_data.catalyst_description:
                reason_parts.append(f"有催化事件：{policy_data.catalyst_description}")
            else:
                reason_parts.append("有催化事件")
            
            return self._create_score(
                score=1,
                reason=" & ".join(reason_parts),
                details=details
            )
        
        else:
            missing_parts = []
            if not policy_data.has_support_policy:
                missing_parts.append("无明确支持政策")
            if not policy_data.has_catalyst_event:
                missing_parts.append("无近期催化事件")
            
            return self._create_score(
                score=0,
                reason="；".join(missing_parts),
                details=details
            )
