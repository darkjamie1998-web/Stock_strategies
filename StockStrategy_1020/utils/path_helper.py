import os
import sys
from pathlib import Path
from typing import Optional


def is_frozen():
    return getattr(sys, 'frozen', False)


def get_base_path():
    if is_frozen():
        return Path(sys._MEIPASS)
    current = Path(__file__).resolve()
    return current.parent.parent


def get_exe_dir():
    if is_frozen():
        exe_dir = Path(sys.executable).parent
        if exe_dir.name == 'DataUpdater':
            parent_dir = exe_dir.parent
            if (parent_dir / 'A股上市公司数据').exists():
                return parent_dir
        return exe_dir
    return get_base_path()


def get_project_root():
    return get_base_path()


def ensure_project_root_in_path():
    root = str(get_project_root())
    if root not in sys.path:
        sys.path.insert(0, root)


def get_data_dir():
    return get_exe_dir() / 'A股上市公司数据'


def get_stock_list_path():
    return get_exe_dir() / 'A股上市公司名单' / 'A股上市公司名单.csv'


def get_assets_dir():
    return get_base_path() / 'assets'


def get_cache_dir():
    cache_dir = get_exe_dir() / '.cache'
    cache_dir.mkdir(exist_ok=True)
    return cache_dir


def get_logs_dir():
    logs_dir = get_exe_dir() / 'logs'
    logs_dir.mkdir(exist_ok=True)
    return logs_dir


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


__all__ = [
    'is_frozen',
    'get_base_path',
    'get_exe_dir',
    'get_project_root',
    'ensure_project_root_in_path',
    'get_data_dir',
    'get_stock_list_path',
    'get_assets_dir',
    'get_cache_dir',
    'get_logs_dir',
    'ensure_dir',
]
