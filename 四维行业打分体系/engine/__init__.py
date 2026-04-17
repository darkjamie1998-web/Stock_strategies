from typing import Dict, List, Optional
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import (
    IndustryData,
    PolicyData,
    CapitalData,
    TechnicalData,
    TechnicalSignal,
    IndustryScoreResult
)
from scorers import (
    ProsperityScorer,
    PolicyScorer,
    CapitalScorer,
    TechnicalScorer
)


class IndustryScoringEngine:
    """四维行业打分引擎"""
    
    def __init__(self):
        """初始化评分引擎，加载四个维度的评分器"""
        self.prosperity_scorer = ProsperityScorer()
        self.policy_scorer = PolicyScorer()
        self.capital_scorer = CapitalScorer()
        self.technical_scorer = TechnicalScorer()
    
    def score_industry(
        self,
        industry_name: str,
        industry_data: IndustryData,
        policy_data: PolicyData,
        capital_data: CapitalData,
        technical_data: TechnicalData
    ) -> IndustryScoreResult:
        """
        对单个行业进行四维评分
        
        Args:
            industry_name: 行业名称
            industry_data: 行业景气度数据
            policy_data: 政策面数据
            capital_data: 资金面数据
            technical_data: 技术面数据
            
        Returns:
            IndustryScoreResult: 完整的评分结果
        """
        prosperity_score = self.prosperity_scorer.score(industry_data=industry_data)
        policy_score = self.policy_scorer.score(policy_data=policy_data)
        capital_score = self.capital_scorer.score(capital_data=capital_data)
        technical_score = self.technical_scorer.score(technical_data=technical_data)
        
        return IndustryScoreResult(
            industry_name=industry_name,
            prosperity_score=prosperity_score,
            policy_score=policy_score,
            capital_score=capital_score,
            technical_score=technical_score
        )
    
    def batch_score(self, industries_config: List[Dict]) -> List[IndustryScoreResult]:
        """
        批量评分多个行业
        
        Args:
            industries_config: 行业配置列表，每个元素包含四个维度的数据
            
        Returns:
            List[IndustryScoreResult]: 所有行业的评分结果列表
        """
        results = []
        
        for config in industries_config:
            industry_name = config.get('name', '未知行业')
            
            industry_data = IndustryData(
                name=industry_name,
                industry_type=config.get('industry_type', ''),
                cycle_phase=config.get('cycle_phase', ''),
                is_recommended=config.get('is_recommended', False)
            )
            
            policy_info = config.get('policy', {})
            policy_data = PolicyData(
                has_support_policy=policy_info.get('has_support_policy', False),
                policy_description=policy_info.get('policy_description', ''),
                has_catalyst_event=policy_info.get('has_catalyst_event', False),
                catalyst_description=policy_info.get('catalyst_description', '')
            )
            
            capital_info = config.get('capital', {})
            capital_data = CapitalData(
                etf_net_subscription=capital_info.get('etf_net_subscription', 0.0),
                fund_position_change=capital_info.get('fund_position_change', 0.0)
            )
            
            technical_info = config.get('technical', {})
            technical_data = TechnicalData()
            for signal in technical_info.get('signals', []):
                tech_signal = TechnicalSignal(
                    signal_type=signal.get('signal_type', ''),
                    description=signal.get('description', ''),
                    stock_code=signal.get('stock_code', '')
                )
                technical_data.add_signal(tech_signal)
            
            result = self.score_industry(
                industry_name=industry_name,
                industry_data=industry_data,
                policy_data=policy_data,
                capital_data=capital_data,
                technical_data=technical_data
            )
            
            results.append(result)
        
        return results
    
    def get_ranking(self, results: List[IndustryScoreResult]) -> List[IndustryScoreResult]:
        """
        对评分结果按总分排序
        
        Args:
            results: 评分结果列表
            
        Returns:
            List[IndustryScoreResult]: 按总分降序排列的结果
        """
        return sorted(results, key=lambda x: x.total_score, reverse=True)
    
    def filter_by_score(
        self,
        results: List[IndustryScoreResult],
        min_score: int = 3
    ) -> List[IndustryScoreResult]:
        """
        筛选达到最低分数的行业
        
        Args:
            results: 评分结果列表
            min_score: 最低分数阈值（默认3分）
            
        Returns:
            List[IndustryScoreResult]: 满足条件的行业列表
        """
        return [r for r in results if r.total_score >= min_score]
    
    def print_summary_report(self, results: List[IndustryScoreResult]):
        """打印汇总报告"""
        print(f"\n{'='*70}")
        print("【四维行业打分体系 - 汇总报告】")
        print(f"{'='*70}")
        print(f"\n共评估 {len(results)} 个行业\n")
        
        sorted_results = self.get_ranking(results)
        
        score_distribution = {4: [], 3: [], 2: [], 1: [], 0: []}
        for result in sorted_results:
            score_distribution[result.total_score].append(result.industry_name)
        
        print("【分数分布统计】")
        print("-" * 50)
        for score in [4, 3, 2, 1, 0]:
            industries = score_distribution[score]
            count = len(industries)
            level = "强买入信号" if score == 4 else "潜伏信号" if score == 3 else "观望/淘汰"
            print(f"{score}分（{level}）：{count}个行业")
            if industries and score >= 3:
                print(f"   → {', '.join(industries)}")
        
        print("\n【推荐配置行业】")
        print("-" * 50)
        recommended = self.filter_by_score(sorted_results, min_score=3)
        if recommended:
            for i, result in enumerate(recommended, 1):
                print(f"{i}. 【{result.industry_name}】{result.total_score}分 - {result.signal_level}")
        else:
            print("当前无达到3分以上的行业")
        
        print(f"\n{'='*70}\n")
