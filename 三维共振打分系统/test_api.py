"""
测试千问API调用
"""

from qwen_api import QwenAPI
from policy_prompt import get_policy_prompt
from datetime import datetime

API_KEY = "sk-4613f6b3b3664049b0b7d808bd3c9b9a"

print("=" * 50)
print("测试千问API调用")
print("=" * 50)

# 创建客户端
client = QwenAPI(API_KEY)

# 获取提示词
current_date = datetime.now().strftime("%Y-%m-%d")
prompt = get_policy_prompt(current_date)

print(f"\n提示词:\n{prompt[:300]}...")
print("\n" + "=" * 50)

# 调用API
print("\n正在调用API...")
result = client.analyze_policy(prompt)

print("\n" + "=" * 50)
print("返回结果:")
print("=" * 50)

if result["success"]:
    print(f"\n✓ 调用成功")
    print(f"得分: {result['score']}")
    print(f"\n原始内容:\n{result['raw_content']}")
    print(f"\n解析结果:\n{result['analysis']}")
else:
    print(f"\n✗ 调用失败")
    print(f"错误: {result.get('error', '未知错误')}")
    if 'raw_response' in result:
        print(f"\n原始响应:\n{result['raw_response']}")
