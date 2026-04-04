"""
日志配置
"""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(
    level: int = logging.INFO,
    log_to_file: bool = True,
    log_dir: str = 'logs'
) -> logging.Logger:
    """
    配置日志
    
    Args:
        level: 日志级别
        log_to_file: 是否写入文件
        log_dir: 日志目录
        
    Returns:
        配置好的logger
    """
    # 创建logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # 清除已有handler
    logger.handlers.clear()
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 控制台输出
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # 文件输出
    if log_to_file:
        log_path = Path(log_dir)
        log_path.mkdir(exist_ok=True)
        
        log_file = log_path / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger
