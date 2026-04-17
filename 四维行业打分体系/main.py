#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
四维行业打分系统 - 主程序入口

本程序实现基于四维行业打分体系的行业评估系统，
从行业景气度、政策面、资金面、技术面四个维度进行综合评分。
"""

import os
import sys
import webbrowser
import threading
from datetime import datetime
from http.server import HTTPServer, SimpleHTTPRequestHandler

from engine import IndustryScoringEngine
from models import (
    IndustryData,
    PolicyData,
    CapitalData,
    TechnicalData,
    TechnicalSignal
)
from utils import (
    load_yaml_config,
    get_industries_from_config,
    format_score_table,
    save_results_to_json,
    save_results_to_csv
)


def run_example_with_config():
    """使用配置文件运行示例"""
    print("=" * 70)
    print("【四维行业打分体系】基于配置文件的批量评估示例")
    print("=" * 70)
    
    config_path = os.path.join(os.path.dirname(__file__), 'config', 'industries.yaml')
    config = load_yaml_config(config_path)
    
    if not config:
        print("无法加载配置文件，退出")
        return
    
    industries = get_industries_from_config(config)
    
    engine = IndustryScoringEngine()
    results = engine.batch_score(industries)
    
    print("\n【详细评分表格】")
    print(format_score_table(results))
    
    for result in results:
        result.print_report()
    
    engine.print_summary_report(results)
    
    output_dir = os.path.join(os.path.dirname(__file__), 'output')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    save_results_to_json(
        results,
        os.path.join(output_dir, f'score_results_{timestamp}.json')
    )
    save_results_to_csv(
        results,
        os.path.join(output_dir, f'score_results_{timestamp}.csv')
    )


def run_single_industry_example():
    """单行业手动输入示例"""
    print("=" * 70)
    print("【四维行业打分体系】单行业评估示例 - 芯片行业")
    print("=" * 70)
    
    engine = IndustryScoringEngine()
    
    industry_data = IndustryData(
        name="芯片",
        industry_type="周期性",
        cycle_phase="底部反转",
        is_recommended=True
    )
    
    policy_data = PolicyData(
        has_support_policy=True,
        policy_description="国产替代政策支持",
        has_catalyst_event=True,
        catalyst_description="近期半导体产业政策发布"
    )
    
    capital_data = CapitalData(
        etf_net_subscription=150.5,
        fund_position_change=2.3
    )
    
    technical_data = TechnicalData()
    technical_data.add_signal(TechnicalSignal(
        signal_type="1020起爆点",
        description="站上10日与20日均线"
    ))
    
    result = engine.score_industry(
        industry_name="芯片",
        industry_data=industry_data,
        policy_data=policy_data,
        capital_data=capital_data,
        technical_data=technical_data
    )
    
    result.print_report()


def run_comparison_example():
    """对比示例：高分行业 vs 低分行业"""
    print("=" * 70)
    print("【四维行业打分体系】对比分析示例")
    print("=" * 70)
    
    engine = IndustryScoringEngine()
    
    test_cases = [
        {
            "name": "芯片（假设）",
            "industry_type": "周期性",
            "cycle_phase": "底部反转",
            "policy": {
                "has_support_policy": True,
                "policy_description": "国产替代+政策驱动",
                "has_catalyst_event": True,
                "catalyst_description": "近期催化事件"
            },
            "capital": {
                "etf_net_subscription": 150.5,
                "fund_position_change": 2.3
            },
            "technical": {
                "signals": [
                    {"signal_type": "1020起爆点", "description": "出现1020起爆点信号"}
                ]
            }
        },
        {
            "name": "钢铁（假设）",
            "industry_type": "周期性",
            "cycle_phase": "衰退期",
            "policy": {
                "has_support_policy": False,
                "policy_description": "",
                "has_catalyst_event": False,
                "catalyst_description": ""
            },
            "capital": {
                "etf_net_subscription": -25.3,
                "fund_position_change": -3.5
            },
            "technical": {
                "signals": []
            }
        }
    ]
    
    results = engine.batch_score(test_cases)
    
    print("\n【对比分析结果】")
    print(format_score_table(results))
    
    for result in results:
        result.print_report()
    
    print("\n【关键差异分析】")
    print("-" * 50)
    chip_result = results[0]
    steel_result = results[1]
    
    print(f"\n{chip_result.industry_name}（{chip_result.total_score}分 - {chip_result.signal_level}）：")
    print(f"  ✓ 科技类成长产业，符合核心理念")
    print(f"  ✓ 四个维度均满足条件")
    print(f"  → 建议：{chip_result.action_advice}")
    
    print(f"\n{steel_result.industry_name}（{steel_result.total_score}分 - {steel_result.signal_level}）：")
    print(f"  ✗ 衰退型行业，处于下行周期")
    print(f"  ✗ 无政策支持、资金流出、无技术信号")
    print(f"  → 建议：{steel_result.action_advice}")


def start_web_server(port=8080):
    """启动Web服务器"""
    web_dir = os.path.join(os.path.dirname(__file__), 'web')
    os.chdir(web_dir)
    
    handler = SimpleHTTPRequestHandler
    server = HTTPServer(('localhost', port), handler)
    
    print(f"\nWeb服务器已启动：http://localhost:{port}")
    print("正在自动打开浏览器...\n")
    
    webbrowser.open(f'http://localhost:{port}')
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\nWeb服务器已停止")
        server.shutdown()


def main():
    """主函数"""
    print("\n" + "=" * 70)
    print("       四维行业打分体系 - 行业选择核心工具")
    print("=" * 70)
    print("\n正在启动 Web 交互界面...")
    print("系统概述：")
    print("  - 从行业景气度、政策面、资金面、技术面四个维度进行独立评估")
    print("  - 每项满分为 1 分，总分达到 3 分及以上视为具备配置价值")
    print("  - 4 分为强买入信号，<=2 分为观望/淘汰")
    print()
    
    try:
        start_web_server()
    except Exception as e:
        print(f"\n程序运行出错：{e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
