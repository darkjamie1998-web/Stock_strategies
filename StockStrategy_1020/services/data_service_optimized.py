"""
优化后的数据服务模块
提供懒加载、批量加载和智能缓存功能
"""
import os
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
import threading

from config import PATH_CONFIG
from models import StockInfo, StockData
from core.data_validator import DataValidator, validate_stock_data
from exceptions import DataLoadError, DataValidationError


logger = logging.getLogger(__name__)


class OptimizedStockDataManager:
    """优化的股票数据管理器 - 单例模式"""
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._stock_files: Dict[str, str] = {}
        self._stock_info_map: Dict[str, StockInfo] = {}
        self._data_cache: Dict[str, StockData] = {}
        self._cache_lock = threading.Lock()
        self._validator = DataValidator()
        self._max_cache_size = 100
        
        self._load_stock_list()
        self._initialized = True
    
    def _load_stock_list(self):
        """加载股票列表"""
        data_dir = str(PATH_CONFIG.DATA_DIR)
        
        if not os.path.exists(data_dir):
            logger.warning(f"数据目录不存在: {data_dir}")
            return
        
        for filename in sorted(os.listdir(data_dir)):
            if filename.endswith('.csv') and 'tushare' in filename:
                self._parse_filename(filename, data_dir)
        
        logger.info(f"加载了 {len(self._stock_files)} 只股票")
    
    def reload_stock_list(self):
        """重新加载股票列表"""
        with self._cache_lock:
            self._stock_files.clear()
            self._stock_info_map.clear()
            self._data_cache.clear()
        self._load_stock_list()
        logger.info("股票列表已重新加载")
    
    def _parse_filename(self, filename: str, data_dir: str):
        """解析文件名获取股票信息"""
        parts = filename.split('_')
        if len(parts) < 2:
            return
        
        stock_code = parts[0]
        filepath = os.path.join(data_dir, filename)
        
        stock_name = self._extract_stock_name(parts)
        
        self._stock_files[stock_code] = filepath
        self._stock_info_map[stock_code] = StockInfo(
            code=stock_code,
            name=stock_name
        )
    
    def _extract_stock_name(self, parts: List[str]) -> str:
        """从文件名部分提取股票名称"""
        try:
            tushare_idx = parts.index('tushare')
            if tushare_idx > 1:
                name = '_'.join(parts[1:tushare_idx])
                return name.lstrip('_')
        except ValueError:
            pass
        return ''
    
    def get_stock_codes(self) -> List[str]:
        """获取所有股票代码"""
        return list(self._stock_files.keys())
    
    def get_stock_info(self, code: str) -> Optional[StockInfo]:
        """获取股票信息"""
        return self._stock_info_map.get(code)
    
    def get_all_stock_info(self) -> List[StockInfo]:
        """获取所有股票信息"""
        return list(self._stock_info_map.values())
    
    def search_stocks(self, query: str) -> List[StockInfo]:
        """搜索股票"""
        query = query.lower()
        results = []
        
        for code, info in self._stock_info_map.items():
            if query in code.lower() or query in info.name.lower():
                results.append(info)
        
        return results
    
    def load_stock_data(self, code: str, use_cache: bool = True) -> Optional[StockData]:
        """
        加载股票数据（带缓存和验证）
        
        Args:
            code: 股票代码
            use_cache: 是否使用缓存
        
        Returns:
            股票数据对象
        """
        if use_cache:
            with self._cache_lock:
                if code in self._data_cache:
                    logger.debug(f"从缓存加载股票数据: {code}")
                    return self._data_cache[code]
        
        if code not in self._stock_files:
            logger.warning(f"股票代码不存在: {code}")
            return None
        
        try:
            filepath = self._stock_files[code]
            logger.info(f"从文件加载股票数据: {code}")
            
            df = pd.read_csv(filepath)
            
            df, is_valid, errors = validate_stock_data(df)
            
            if not is_valid:
                logger.error(f"股票数据验证失败 {code}: {errors}")
                return None
            
            stock_info = self._stock_info_map[code]
            stock_data = StockData(df, stock_info)
            
            if use_cache:
                self._add_to_cache(code, stock_data)
            
            return stock_data
        
        except pd.errors.EmptyDataError:
            logger.error(f"股票数据文件为空: {code}")
            return None
        except pd.errors.ParserError as e:
            logger.error(f"股票数据文件解析失败 {code}: {e}")
            return None
        except Exception as e:
            logger.error(f"加载股票数据失败 {code}: {e}", exc_info=True)
            return None
    
    def _add_to_cache(self, code: str, stock_data: StockData):
        """添加到缓存（LRU策略）"""
        with self._cache_lock:
            if len(self._data_cache) >= self._max_cache_size:
                oldest_key = next(iter(self._data_cache))
                del self._data_cache[oldest_key]
                logger.debug(f"缓存已满，移除最旧数据: {oldest_key}")
            
            self._data_cache[code] = stock_data
    
    def load_multiple_stocks(self, codes: List[str], max_workers: int = 4) -> Dict[str, StockData]:
        """
        批量加载股票数据（并行）
        
        Args:
            codes: 股票代码列表
            max_workers: 最大线程数
        
        Returns:
            股票数据字典
        """
        results = {}
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_code = {
                executor.submit(self.load_stock_data, code): code 
                for code in codes
            }
            
            for future in future_to_code:
                code = future_to_code[future]
                try:
                    stock_data = future.result()
                    if stock_data:
                        results[code] = stock_data
                except Exception as e:
                    logger.error(f"加载股票 {code} 失败: {e}")
        
        return results
    
    def clear_cache(self):
        """清除缓存"""
        with self._cache_lock:
            self._data_cache.clear()
        logger.info("数据缓存已清除")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        with self._cache_lock:
            return {
                'cached_stocks': len(self._data_cache),
                'total_stocks': len(self._stock_files),
                'cache_ratio': len(self._data_cache) / len(self._stock_files) if self._stock_files else 0,
                'max_cache_size': self._max_cache_size
            }
    
    def preload_popular_stocks(self, count: int = 50):
        """
        预加载热门股票
        
        Args:
            count: 预加载数量
        """
        codes = self.get_stock_codes()[:count]
        logger.info(f"开始预加载 {len(codes)} 只热门股票")
        
        self.load_multiple_stocks(codes)
        
        logger.info(f"预加载完成，缓存了 {len(self._data_cache)} 只股票")


class OptimizedDataService:
    """优化的数据服务类"""
    
    def __init__(self):
        self.manager = OptimizedStockDataManager()
    
    def reload_data(self):
        """重新加载数据"""
        self.manager.reload_stock_list()
    
    def get_stock_list(self, limit: Optional[int] = None) -> List[Dict]:
        """获取股票列表"""
        stocks = self.manager.get_all_stock_info()
        
        result = []
        for stock in stocks:
            result.append({
                'label': stock.display_name,
                'value': stock.code
            })
        
        if limit:
            result = result[:limit]
        
        return result
    
    def get_stock_data(self, code: str) -> Optional[StockData]:
        """获取股票数据"""
        return self.manager.load_stock_data(code)
    
    def search_stocks(self, query: str) -> List[Dict]:
        """搜索股票"""
        stocks = self.manager.search_stocks(query)
        return [{'label': s.display_name, 'value': s.code} for s in stocks]
    
    def get_price_history(self, code: str, days: Optional[int] = None) -> Optional[pd.DataFrame]:
        """获取价格历史"""
        stock_data = self.get_stock_data(code)
        if stock_data is None:
            return None
        
        df = stock_data.df
        if days:
            df = df.tail(days)
        
        return df.copy()
    
    def preload_data(self, count: int = 50):
        """预加载数据"""
        self.manager.preload_popular_stocks(count)
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return self.manager.get_cache_stats()


DataService = OptimizedDataService
