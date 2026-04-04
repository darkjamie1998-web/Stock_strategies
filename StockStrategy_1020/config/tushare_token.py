"""
Tushare API Token配置
用于管理tushare数据接口的访问令牌
"""
import os
from pathlib import Path
from typing import Optional

from utils import get_project_root, get_exe_dir


def get_token_file_path() -> Path:
    """获取token文件路径"""
    if getattr(__import__('sys'), 'frozen', False):
        exe_dir = Path(__import__('sys').executable).parent
        return exe_dir / 'tushare_token.txt'
    exe_dir = get_exe_dir()
    return exe_dir / 'tushare_token.txt'


def load_tushare_token() -> Optional[str]:
    """
    加载tushare token
    优先从环境变量TUSHARE_TOKEN读取，其次从tushare_token.txt文件读取
    """
    token = os.environ.get('TUSHARE_TOKEN')
    if token:
        return token.strip()

    token_file = get_token_file_path()
    if token_file.exists():
        with open(token_file, 'r', encoding='utf-8') as f:
            token = f.read().strip()
        if token:
            return token
    return None


def save_tushare_token(token: str) -> bool:
    """
    保存tushare token到文件
    返回是否保存成功
    """
    try:
        token_file = get_token_file_path()
        with open(token_file, 'w', encoding='utf-8') as f:
            f.write(token.strip())
        return True
    except Exception:
        return False


TUSHARE_TOKEN = load_tushare_token()