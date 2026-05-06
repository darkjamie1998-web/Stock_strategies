"""
千问大模型API调用模块
用于获取政策面评分，支持本地缓存
"""

import json
import requests
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class QwenAPI:
    """千问API客户端"""
    
    def __init__(self, api_key: str, cache_dir: str = "data"):
        """
        初始化千问API客户端
        
        Args:
            api_key: 千问API密钥
            cache_dir: 缓存目录，默认为"data"
        """
        self.api_key = api_key
        self.base_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation"
        self.cache_dir = cache_dir
        
        # 确保缓存目录存在
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
    
    def _get_cache_file_path(self, date: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, f"policy_analysis_{date}.txt")
    
    def _load_from_cache(self, date: str) -> Optional[Dict[str, Any]]:
        """
        从本地缓存加载数据
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)
            
        Returns:
            缓存的数据或None
        """
        cache_file = self._get_cache_file_path(date)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析缓存内容
            lines = content.split('\n', 2)
            if len(lines) >= 3:
                score_line = lines[0]
                timestamp_line = lines[1]
                analysis_content = lines[2]
                
                # 解析得分
                score = int(score_line.split(':')[1].strip()) if score_line.startswith('score:') else 0
                
                # 尝试解析JSON内容，提取score_reason
                try:
                    analysis_json = json.loads(analysis_content)
                    return {
                        "success": True,
                        "raw_content": analysis_content,
                        "analysis": analysis_json,
                        "score": score,
                        "timestamp": timestamp_line.split(':')[1].strip() if timestamp_line.startswith('timestamp:') else datetime.now().isoformat(),
                        "from_cache": True
                    }
                except json.JSONDecodeError:
                    # 如果不是JSON格式，返回文本内容
                    return {
                        "success": True,
                        "raw_content": analysis_content,
                        "analysis": {"text": analysis_content},
                        "score": score,
                        "timestamp": timestamp_line.split(':')[1].strip() if timestamp_line.startswith('timestamp:') else datetime.now().isoformat(),
                        "from_cache": True
                    }
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def _save_to_cache(self, date: str, result: Dict[str, Any]) -> bool:
        """
        保存结果到本地缓存
        
        Args:
            date: 日期字符串 (YYYY-MM-DD)
            result: 分析结果
            
        Returns:
            是否保存成功
        """
        cache_file = self._get_cache_file_path(date)
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                f.write(f"score: {result['score']}\n")
                f.write(f"timestamp: {result['timestamp']}\n")
                f.write(result['raw_content'])
            return True
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
            return False
    
    def analyze_policy(self, prompt: str, current_date: Optional[str] = None) -> Dict[str, Any]:
        """
        调用千问API分析政策面，优先使用本地缓存
        
        Args:
            prompt: 提示词
            current_date: 当前日期，用于缓存
            
        Returns:
            包含分析结果和得分的字典
        """
        # 如果没有提供日期，使用今天
        if current_date is None:
            current_date = datetime.now().strftime("%Y-%m-%d")
        
        # 首先检查本地缓存
        cached_result = self._load_from_cache(current_date)
        if cached_result:
            logger.info(f"使用本地缓存的政策面分析数据 ({current_date})")
            return cached_result
        
        logger.info(f"本地缓存不存在，调用千问API获取政策面分析 ({current_date})")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "qwen-turbo",
            "input": {
                "messages": [
                    {
                        "role": "system",
                        "content": "你是一位专业的中国宏观经济政策分析师。请直接输出JSON格式，不要添加任何markdown标记或其他说明文字。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            },
            "parameters": {
                "result_format": "message",
                "max_tokens": 2000,
                "temperature": 0.3
            }
        }
        
        try:
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60
            )
            response.raise_for_status()
            
            result = response.json()
            
            # 解析API返回的内容
            if "output" in result and "choices" in result["output"]:
                content = result["output"]["choices"][0]["message"]["content"]
                
                # 尝试从内容中提取JSON
                try:
                    logger.info(f"API返回内容: {content[:200]}...")
                    
                    # 清理内容中的markdown代码块标记
                    cleaned_content = content.strip()
                    if cleaned_content.startswith("```json"):
                        cleaned_content = cleaned_content[7:]
                    elif cleaned_content.startswith("```"):
                        cleaned_content = cleaned_content[3:]
                    if cleaned_content.endswith("```"):
                        cleaned_content = cleaned_content[:-3]
                    cleaned_content = cleaned_content.strip()
                    
                    logger.info(f"清理后内容: {cleaned_content[:200]}...")
                    
                    # 查找JSON格式的内容
                    json_start = cleaned_content.find("{")
                    json_end = cleaned_content.rfind("}") + 1
                    
                    if json_start >= 0 and json_end > json_start:
                        json_str = cleaned_content[json_start:json_end]
                        logger.info(f"提取的JSON: {json_str[:200]}...")
                        
                        try:
                            analysis_result = json.loads(json_str)
                            
                            # 尝试多种可能的score字段名
                            score = 0
                            if "score" in analysis_result:
                                score_value = analysis_result["score"]
                                score = 1 if score_value in [1, "1", 1.0, "1.0"] else 0
                            
                            result_data = {
                                "success": True,
                                "raw_content": content,
                                "analysis": analysis_result,
                                "score": score,
                                "timestamp": datetime.now().isoformat(),
                                "from_cache": False
                            }
                            
                            # 保存到缓存
                            self._save_to_cache(current_date, result_data)
                            
                            return result_data
                        except json.JSONDecodeError as json_err:
                            logger.warning(f"JSON解析错误: {json_err}")
                            # 尝试从文本中提取得分
                            score = 0
                            if '"score": 1' in json_str or '"score":1' in json_str:
                                score = 1
                            elif '"score": 0' in json_str or '"score":0' in json_str:
                                score = 0
                            
                            result_data = {
                                "success": True,
                                "raw_content": content,
                                "analysis": {"text": cleaned_content, "json_error": str(json_err)},
                                "score": score,
                                "timestamp": datetime.now().isoformat(),
                                "from_cache": False
                            }
                            
                            # 保存到缓存
                            self._save_to_cache(current_date, result_data)
                            
                            return result_data
                    else:
                        # 如果没有JSON格式，尝试解析文本
                        score = 1 if ("支持" in content or "宽松" in content or "利好" in content) and "不" not in content[:50] else 0
                        
                        result_data = {
                            "success": True,
                            "raw_content": content,
                            "analysis": {"text": cleaned_content},
                            "score": score,
                            "timestamp": datetime.now().isoformat(),
                            "from_cache": False
                        }
                        
                        # 保存到缓存
                        self._save_to_cache(current_date, result_data)
                        
                        return result_data
                        
                except Exception as e:
                    logger.warning(f"处理异常: {e}")
                    # 任何异常都返回文本分析结果
                    score = 1 if ("支持" in content or "宽松" in content) else 0
                    
                    result_data = {
                        "success": True,
                        "raw_content": content,
                        "analysis": {"text": cleaned_content, "error": str(e)},
                        "score": score,
                        "timestamp": datetime.now().isoformat(),
                        "from_cache": False
                    }
                    
                    # 保存到缓存
                    self._save_to_cache(current_date, result_data)
                    
                    return result_data
            else:
                return {
                    "success": False,
                    "error": "API返回格式异常",
                    "raw_response": result
                }
                
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API请求失败: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"未知错误: {str(e)}"
            }
    
    def get_policy_score(self, current_date: Optional[str] = None) -> Dict[str, Any]:
        """
        获取政策面评分（便捷方法）
        
        Args:
            current_date: 当前日期，默认为今天
            
        Returns:
            政策面评分结果
        """
        from policy_prompt import get_policy_prompt
        
        if current_date is None:
            current_date = datetime.now().strftime("%Y-%m-%d")
            
        prompt = get_policy_prompt(current_date)
        return self.analyze_policy(prompt, current_date)


def load_api_key_from_file(file_path: str = "qwen_token.txt") -> str:
    """
    从文件加载API密钥
    
    Args:
        file_path: 存储API密钥的文件路径，默认为"qwen_token.txt"
        
    Returns:
        API密钥字符串
        
    Raises:
        FileNotFoundError: 当文件不存在时
        ValueError: 当文件内容为空时
    """
    # 获取当前脚本所在目录，确保从正确的位置查找文件
    script_dir = os.path.dirname(os.path.abspath(__file__))
    full_path = os.path.join(script_dir, file_path)
    
    if not os.path.exists(full_path):
        raise FileNotFoundError(f"API密钥文件不存在: {full_path}")
    
    with open(full_path, 'r', encoding='utf-8') as f:
        api_key = f.read().strip()
    
    if not api_key:
        raise ValueError(f"API密钥文件为空: {full_path}")
    
    return api_key


# 测试代码
if __name__ == "__main__":
    # 测试API调用
    api_key = load_api_key_from_file()
    client = QwenAPI(api_key)
    
    print("正在调用千问API分析政策面...")
    result = client.get_policy_score()
    
    if result["success"]:
        print(f"\n分析成功！")
        print(f"得分: {result['score']}")
        print(f"来源: {'本地缓存' if result.get('from_cache') else 'API调用'}")
        print(f"\n原始内容:\n{result['raw_content'][:500]}...")
    else:
        print(f"分析失败: {result.get('error', '未知错误')}")
