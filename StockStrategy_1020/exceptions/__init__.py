"""
自定义异常类
提供统一的异常处理机制
"""


class StockStrategyError(Exception):
    """股票策略基础异常"""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def __str__(self):
        if self.details:
            return f"{self.message} - 详情: {self.details}"
        return self.message


class DataLoadError(StockStrategyError):
    """数据加载异常"""
    pass


class DataValidationError(StockStrategyError):
    """数据验证异常"""
    pass


class StrategyExecutionError(StockStrategyError):
    """策略执行异常"""
    pass


class ConfigurationError(StockStrategyError):
    """配置异常"""
    pass


class CacheError(StockStrategyError):
    """缓存异常"""
    pass


class ChartGenerationError(StockStrategyError):
    """图表生成异常"""
    pass


def handle_exception(exc: Exception, logger=None):
    """
    统一异常处理
    
    Args:
        exc: 异常对象
        logger: 日志记录器
    
    Returns:
        错误信息字典
    """
    error_info = {
        'type': type(exc).__name__,
        'message': str(exc),
        'details': getattr(exc, 'details', None)
    }
    
    if logger:
        if isinstance(exc, StockStrategyError):
            logger.error(f"{exc.message}", exc_info=True)
        else:
            logger.error(f"未预期的错误: {exc}", exc_info=True)
    
    return error_info
