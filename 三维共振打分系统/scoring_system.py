"""
三维共振打分系统主程序
整合政策面（千问API）、资金面、技术面（中证全指数据）的打分逻辑
支持本地缓存，优先使用本地数据
"""

import json
import os
from typing import Dict, Any, Optional
from datetime import datetime
from policy_prompt import get_policy_prompt
from qwen_api import QwenAPI
from market_data import ZhongZhengData


class ThreeDimensionalScoringSystem:
    """三维共振打分系统"""
    
    def __init__(self, api_key: str, cache_dir: str = "data"):
        """
        初始化打分系统
        
        Args:
            api_key: 千问API密钥
            cache_dir: 缓存目录，默认为"data"
        """
        self.api_key = api_key
        self.cache_dir = cache_dir
        
        # 确保缓存目录存在
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # 初始化客户端（会自动使用缓存）
        self.qwen_client = QwenAPI(api_key, cache_dir=cache_dir)
        self.market_analyzer = ZhongZhengData(cache_dir=cache_dir)
        
    def calculate_policy_score(self) -> Dict[str, Any]:
        """
        计算政策面得分（自动使用本地缓存）
        
        Returns:
            政策面评分结果
        """
        print("正在分析政策面...")
        result = self.qwen_client.get_policy_score()
        
        if result["success"]:
            return {
                "dimension": "政策面",
                "score": result["score"],
                "max_score": 1,
                "analysis": result["analysis"],
                "raw_content": result["raw_content"],
                "timestamp": result["timestamp"],
                "from_cache": result.get("from_cache", False)
            }
        else:
            return {
                "dimension": "政策面",
                "score": 0,
                "max_score": 1,
                "analysis": f"分析失败: {result.get('error', '未知错误')}",
                "error": result.get('error', '未知错误'),
                "timestamp": datetime.now().isoformat(),
                "from_cache": False
            }
    
    def calculate_capital_score(self) -> Dict[str, Any]:
        """
        计算资金面得分（自动使用本地缓存）
        
        Returns:
            资金面评分结果
        """
        print("正在分析资金面...")
        market_result = self.market_analyzer.get_full_analysis()
        
        if market_result["success"]:
            capital = market_result["capital"]
            return {
                "dimension": "资金面",
                "score": capital["score"],
                "max_score": 1,
                "analysis": capital["analysis"],
                "details": capital["details"],
                "index_name": market_result["index_name"],
                "latest_close": market_result["latest_close"],
                "timestamp": datetime.now().isoformat(),
                "from_cache": market_result.get("from_cache", False)
            }
        else:
            return {
                "dimension": "资金面",
                "score": 0,
                "max_score": 1,
                "analysis": f"分析失败: {market_result.get('error', '未知错误')}",
                "error": market_result.get('error', '未知错误'),
                "timestamp": datetime.now().isoformat(),
                "from_cache": False
            }
    
    def calculate_technical_score(self) -> Dict[str, Any]:
        """
        计算技术面得分（自动使用本地缓存）
        
        Returns:
            技术面评分结果
        """
        print("正在分析技术面...")
        market_result = self.market_analyzer.get_full_analysis()
        
        if market_result["success"]:
            technical = market_result["technical"]
            return {
                "dimension": "技术面",
                "score": technical["score"],
                "max_score": 1,
                "analysis": technical["analysis"],
                "details": technical["details"],
                "index_name": market_result["index_name"],
                "latest_close": market_result["latest_close"],
                "timestamp": datetime.now().isoformat(),
                "from_cache": market_result.get("from_cache", False)
            }
        else:
            return {
                "dimension": "技术面",
                "score": 0,
                "max_score": 1,
                "analysis": f"分析失败: {market_result.get('error', '未知错误')}",
                "error": market_result.get('error', '未知错误'),
                "timestamp": datetime.now().isoformat(),
                "from_cache": False
            }
    
    def calculate_total_score(self, policy_score: int, capital_score: int, technical_score: int) -> Dict[str, Any]:
        """
        计算总分并判断市场状态
        
        Args:
            policy_score: 政策面得分
            capital_score: 资金面得分
            technical_score: 技术面得分
            
        Returns:
            总分和市场状态判断
        """
        total_score = policy_score + capital_score + technical_score
        
        # 判断市场状态
        if total_score == 3:
            market_status = "单边上行行情"
            position_suggestion = "70-100%"
            description = "三维共振成立，政策利好释放、资金大规模流入、技术形态突破并站稳均线"
        elif total_score == 2:
            market_status = "横盘震荡行情"
            position_suggestion = "30-70%"
            description = "二维共振，存在政策或技术支撑，但资金未明显跟进"
        else:
            market_status = "单边下跌行情"
            position_suggestion = "0-30%"
            description = "二维以下，政策无响应、资金持续流出、技术走势破位下行"
        
        return {
            "total_score": total_score,
            "max_score": 3,
            "market_status": market_status,
            "position_suggestion": position_suggestion,
            "description": description
        }
    
    def run_full_analysis(self, force_update: bool = False) -> Dict[str, Any]:
        """
        运行完整的打分分析
        
        Args:
            force_update: 是否强制更新数据（忽略缓存）
            
        Returns:
            完整的三维共振打分结果
        """
        print("=" * 50)
        print("开始三维共振打分分析")
        if force_update:
            print("【强制更新模式 - 忽略本地缓存】")
        print("=" * 50)
        
        # 计算各维度得分
        policy_result = self.calculate_policy_score()
        
        # 资金和技术面使用相同的市场数据，避免重复获取
        print("正在获取市场数据...")
        market_result = self.market_analyzer.get_full_analysis(force_update=force_update)
        
        if market_result["success"]:
            # 资金面
            capital = market_result["capital"]
            capital_result = {
                "dimension": "资金面",
                "score": capital["score"],
                "max_score": 1,
                "analysis": capital["analysis"],
                "details": capital["details"],
                "index_name": market_result["index_name"],
                "latest_close": market_result["latest_close"],
                "timestamp": datetime.now().isoformat(),
                "from_cache": market_result.get("from_cache", False)
            }
            
            # 技术面
            technical = market_result["technical"]
            technical_result = {
                "dimension": "技术面",
                "score": technical["score"],
                "max_score": 1,
                "analysis": technical["analysis"],
                "details": technical["details"],
                "index_name": market_result["index_name"],
                "latest_close": market_result["latest_close"],
                "timestamp": datetime.now().isoformat(),
                "from_cache": market_result.get("from_cache", False)
            }
        else:
            # 市场数据获取失败
            capital_result = {
                "dimension": "资金面",
                "score": 0,
                "max_score": 1,
                "analysis": f"分析失败: {market_result.get('error', '未知错误')}",
                "error": market_result.get('error', '未知错误'),
                "timestamp": datetime.now().isoformat(),
                "from_cache": False
            }
            technical_result = {
                "dimension": "技术面",
                "score": 0,
                "max_score": 1,
                "analysis": f"分析失败: {market_result.get('error', '未知错误')}",
                "error": market_result.get('error', '未知错误'),
                "timestamp": datetime.now().isoformat(),
                "from_cache": False
            }
        
        # 计算总分
        total_result = self.calculate_total_score(
            policy_result["score"],
            capital_result["score"],
            technical_result["score"]
        )
        
        # 组装完整结果
        full_result = {
            "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data_date": market_result.get("latest_date", datetime.now().strftime("%Y-%m-%d")),
            "dimensions": [
                policy_result,
                capital_result,
                technical_result
            ],
            "summary": total_result
        }
        
        return full_result
    
    def print_report(self, result: Dict[str, Any]):
        """
        打印分析报告
        
        Args:
            result: 打分结果字典
        """
        print("\n" + "=" * 50)
        print("三维共振打分报告")
        print("=" * 50)
        print(f"分析时间: {result['analysis_time']}")
        print(f"数据日期: {result.get('data_date', 'N/A')}\n")
        
        # 打印各维度得分
        for dim in result["dimensions"]:
            print(f"\n【{dim['dimension']}】")
            print(f"  得分: {dim['score']}/{dim['max_score']}")
            
            # 显示数据来源
            if dim.get("from_cache"):
                print(f"  数据来源: 本地缓存")
            else:
                print(f"  数据来源: API实时")
            
            print(f"  分析: {dim['analysis']}")
            
            # 打印详细信息
            if "details" in dim and dim["details"]:
                print(f"  详细信息:")
                for key, value in dim["details"].items():
                    if key != "reasons":
                        print(f"    - {key}: {value}")
                if "reasons" in dim["details"] and dim["details"]["reasons"]:
                    print(f"    - 理由:")
                    for reason in dim["details"]["reasons"]:
                        print(f"      * {reason}")
        
        # 打印总结
        summary = result["summary"]
        print("\n" + "=" * 50)
        print("综合评估")
        print("=" * 50)
        print(f"总分: {summary['total_score']}/{summary['max_score']}")
        print(f"市场状态: {summary['market_status']}")
        print(f"建议仓位: {summary['position_suggestion']}")
        print(f"判断依据: {summary['description']}")
        print("=" * 50)


# 测试代码
if __name__ == "__main__":
    API_KEY = "sk-4613f6b3b3664049b0b7d808bd3c9b9a"
    
    # 创建打分系统实例
    scoring_system = ThreeDimensionalScoringSystem(API_KEY)
    
    # 运行完整分析（优先使用缓存）
    result = scoring_system.run_full_analysis()
    
    # 打印报告
    scoring_system.print_report(result)
    
    # 保存结果到JSON文件
    result_file = os.path.join("data", "scoring_result.json")
    with open(result_file, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n结果已保存到 {result_file}")
