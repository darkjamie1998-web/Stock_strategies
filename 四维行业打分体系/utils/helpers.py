import yaml
import os
from typing import List, Dict, Optional


def load_yaml_config(file_path: str) -> Optional[Dict]:
    """
    加载YAML配置文件
    
    Args:
        file_path: YAML文件路径
        
    Returns:
        Dict: 配置内容，加载失败返回None
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    except Exception as e:
        print(f"加载配置文件失败：{file_path}")
        print(f"错误信息：{e}")
        return None


def get_industries_from_config(config: Dict) -> List[Dict]:
    """
    从配置中获取行业列表
    
    Args:
        config: 配置字典
        
    Returns:
        List[Dict]: 行业配置列表
    """
    return config.get('industries', [])


def ensure_dir_exists(file_path: str):
    """
    确保目录存在
    
    Args:
        file_path: 文件路径
    """
    dir_path = os.path.dirname(file_path)
    if dir_path and not os.path.exists(dir_path):
        os.makedirs(dir_path)


def format_score_table(results: list) -> str:
    """
    格式化评分结果为表格形式
    
    Args:
        results: IndustryScoreResult列表
        
    Returns:
        str: 格式化的表格字符串
    """
    header = f"{'行业':<10} {'景气度':<6} {'政策面':<6} {'资金面':<6} {'技术面':<6} {'总分':<4} {'信号等级':<12}"
    separator = "-" * len(header)
    
    lines = [header, separator]
    
    for r in results:
        line = (f"{r.industry_name:<10} "
               f"{r.prosperity_score.score:<6} "
               f"{r.policy_score.score:<6} "
               f"{r.capital_score.score:<6} "
               f"{r.technical_score.score:<6} "
               f"{r.total_score:<4} "
               f"{r.signal_level:<12}")
        lines.append(line)
    
    return "\n".join(lines)


def save_results_to_json(results: list, output_path: str):
    """
    将评分结果保存为JSON格式
    
    Args:
        results: IndustryScoreResult列表
        output_path: 输出文件路径
    """
    import json
    
    data = [r.to_dict() for r in results]
    
    ensure_dir_exists(output_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"评分结果已保存至：{output_path}")


def save_results_to_csv(results: list, output_path: str):
    """
    将评分结果保存为CSV格式
    
    Args:
        results: IndustryScoreResult列表
        output_path: 输出文件路径
    """
    import csv
    
    ensure_dir_exists(output_path)
    
    fieldnames = [
        '行业名称', '景气度得分', '政策面得分', '资金面得分', '技术面得分',
        '总分', '信号等级', '操作建议'
    ]
    
    with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for r in results:
            writer.writerow({
                '行业名称': r.industry_name,
                '景气度得分': r.prosperity_score.score,
                '政策面得分': r.policy_score.score,
                '资金面得分': r.capital_score.score,
                '技术面得分': r.technical_score.score,
                '总分': r.total_score,
                '信号等级': r.signal_level,
                '操作建议': r.action_advice
            })
    
    print(f"评分结果已保存至：{output_path}")
