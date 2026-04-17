from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime


@dataclass
class IndustryData:
    """行业基础数据模型"""
    name: str                          # 行业名称
    industry_type: str                 # 行业类型：周期性/非周期性
    cycle_phase: str                   # 周期阶段：底部/底部反转/成长期/成熟期/衰退期
    is_recommended: bool = False       # 是否为推荐行业
    
    def to_dict(self) -> Dict:
        return {
            'name': self.name,
            'industry_type': self.industry_type,
            'cycle_phase': self.cycle_phase,
            'is_recommended': self.is_recommended
        }


@dataclass
class PolicyData:
    """政策面数据"""
    has_support_policy: bool = False           # 是否有支持性政策
    policy_description: str = ""               # 政策描述
    has_catalyst_event: bool = False           # 是否有催化事件
    catalyst_description: str = ""             # 催化事件描述
    policy_date: Optional[datetime] = None     # 政策发布日期
    
    def to_dict(self) -> Dict:
        return {
            'has_support_policy': self.has_support_policy,
            'policy_description': self.policy_description,
            'has_catalyst_event': self.has_catalyst_event,
            'catalyst_description': self.catalyst_description,
            'policy_date': self.policy_date.isoformat() if self.policy_date else None
        }


@dataclass
class CapitalData:
    """资金面数据"""
    etf_net_subscription: float = 0.0         # ETF月度净申购金额（亿元）
    fund_position_change: float = 0.0         # 公募基金季度仓位变化（%）
    
    @property
    def etf_positive(self) -> bool:
        return self.etf_net_subscription > 0
    
    @property
    def fund_position_not_declining(self) -> bool:
        return self.fund_position_change >= 0
    
    def to_dict(self) -> Dict:
        return {
            'etf_net_subscription': self.etf_net_subscription,
            'fund_position_change': self.fund_position_change,
            'etf_positive': self.etf_positive,
            'fund_position_not_declining': self.fund_position_not_declining
        }


@dataclass
class TechnicalSignal:
    """技术信号类型"""
    signal_type: str                           # 信号类型：意外大跌抄底/1020起爆点/龙回头
    description: str = ""                      # 信号描述
    trigger_date: Optional[datetime] = None    # 触发日期
    stock_code: str = ""                       # 相关股票代码（龙头股）


@dataclass
class TechnicalData:
    """技术面数据"""
    signals: List[TechnicalSignal] = field(default_factory=list)
    
    @property
    def has_signal(self) -> bool:
        return len(self.signals) > 0
    
    def add_signal(self, signal: TechnicalSignal):
        self.signals.append(signal)
    
    def to_dict(self) -> Dict:
        return {
            'signals': [
                {
                    'signal_type': s.signal_type,
                    'description': s.description,
                    'trigger_date': s.trigger_date.isoformat() if s.trigger_date else None,
                    'stock_code': s.stock_code
                }
                for s in self.signals
            ],
            'has_signal': self.has_signal
        }


@dataclass
class DimensionScore:
    """维度评分结果"""
    dimension_name: str                        # 维度名称
    score: int                                 # 得分（0或1）
    reason: str = ""                           # 评分理由
    details: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            'dimension_name': self.dimension_name,
            'score': self.score,
            'reason': self.reason,
            'details': self.details
        }


@dataclass
class IndustryScoreResult:
    """行业评分总结果"""
    industry_name: str                         # 行业名称
    prosperity_score: DimensionScore           # 景气度得分
    policy_score: DimensionScore               # 政策面得分
    capital_score: DimensionScore              # 资金面得分
    technical_score: DimensionScore            # 技术面得分
    
    @property
    def total_score(self) -> int:
        """计算总分"""
        return (self.prosperity_score.score + 
                self.policy_score.score + 
                self.capital_score.score + 
                self.technical_score.score)
    
    @property
    def signal_level(self) -> str:
        """获取信号等级"""
        if self.total_score >= 4:
            return "强买入信号"
        elif self.total_score >= 3:
            return "潜伏信号"
        else:
            return "观望/淘汰"
    
    @property
    def action_advice(self) -> str:
        """获取操作建议"""
        if self.total_score >= 4:
            return "优先配置，可重仓参与"
        elif self.total_score >= 3:
            return "具备配置价值，可适度建仓"
        else:
            return "不具备配置价值，应回避或减仓"
    
    def to_dict(self) -> Dict:
        return {
            'industry_name': self.industry_name,
            'prosperity_score': self.prosperity_score.to_dict(),
            'policy_score': self.policy_score.to_dict(),
            'capital_score': self.capital_score.to_dict(),
            'technical_score': self.technical_score.to_dict(),
            'total_score': self.total_score,
            'signal_level': self.signal_level,
            'action_advice': self.action_advice
        }
    
    def print_report(self):
        """打印评分报告"""
        print(f"\n{'='*60}")
        print(f"【{self.industry_name}】四维行业打分报告")
        print(f"{'='*60}")
        print(f"\n维度一：行业景气度")
        print(f"  得分：{self.prosperity_score.score}分 | {self.prosperity_score.reason}")
        
        print(f"\n维度二：政策面")
        print(f"  得分：{self.policy_score.score}分 | {self.policy_score.reason}")
        
        print(f"\n维度三：资金面")
        print(f"  得分：{self.capital_score.score}分 | {self.capital_score.reason}")
        
        print(f"\n维度四：技术面")
        print(f"  得分：{self.technical_score.score}分 | {self.technical_score.reason}")
        
        print(f"\n{'-'*60}")
        print(f"总分：{self.total_score}/4分")
        print(f"信号等级：{self.signal_level}")
        print(f"操作建议：{self.action_advice}")
        print(f"{'='*60}\n")
