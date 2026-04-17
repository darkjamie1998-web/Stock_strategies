from abc import ABC, abstractmethod
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import DimensionScore


class BaseScorer(ABC):
    """基础评分器抽象类"""
    
    def __init__(self, dimension_name: str):
        """
        初始化评分器
        
        Args:
            dimension_name: 维度名称
        """
        self.dimension_name = dimension_name
    
    @abstractmethod
    def score(self, **kwargs) -> DimensionScore:
        """
        执行评分逻辑
        
        Returns:
            DimensionScore: 评分结果
        """
        pass
    
    def _create_score(self, score: int, reason: str, details: dict = None) -> DimensionScore:
        """创建评分结果"""
        return DimensionScore(
            dimension_name=self.dimension_name,
            score=score,
            reason=reason,
            details=details or {}
        )
