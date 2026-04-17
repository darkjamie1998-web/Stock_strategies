import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scorers.base_scorer import BaseScorer
from models import TechnicalData, DimensionScore


class TechnicalScorer(BaseScorer):
    """技术面评分器"""
    
    SIGNAL_TYPES = ['意外大跌抄底', '1020起爆点', '龙回头']
    
    def __init__(self):
        super().__init__("技术面")
    
    def score(self, technical_data: TechnicalData, **kwargs) -> DimensionScore:
        """
        评估技术面
        
        评分规则：
        - 触发任一技术信号（意外大跌抄底、1020起爆点、龙回头）→ 1分
        - 无任何技术信号 → 0分
        
        Args:
            technical_data: 技术面数据
            
        Returns:
            DimensionScore: 评分结果
        """
        if not isinstance(technical_data, TechnicalData):
            return self._create_score(
                score=0,
                reason="无效的技术面数据",
                details={'error': 'invalid_technical_data'}
            )
        
        signals = technical_data.signals
        details = {
            'signal_count': len(signals),
            'signals': [
                {
                    'type': s.signal_type,
                    'description': s.description,
                    'stock_code': s.stock_code
                } for s in signals
            ]
        }
        
        if technical_data.has_signal:
            signal_descriptions = []
            for signal in signals:
                desc = signal.signal_type
                if signal.description:
                    desc += f"（{signal.description}）"
                if signal.stock_code:
                    desc += f"-{signal.stock_code}"
                signal_descriptions.append(desc)
            
            return self._create_score(
                score=1,
                reason=f"触发技术信号：{'、'.join(signal_descriptions)}",
                details=details
            )
        
        else:
            return self._create_score(
                score=0,
                reason="无技术信号触发",
                details=details
            )
