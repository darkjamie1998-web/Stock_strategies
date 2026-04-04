"""
数据服务模块
负责股票数据的加载、缓存和管理
"""
import os
import pandas as pd
from typing import Dict, List, Optional, Callable
from functools import lru_cache
import logging

from config import PATH_CONFIG
from models import StockInfo, StockData

logger = logging.getLogger(__name__)


class StockDataManager:
    """股票数据管理器 - 单例模式"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._stock_files: Dict[str, str] = {}  # code -> filepath
        self._stock_info_map: Dict[str, StockInfo] = {}  # code -> StockInfo
        self._data_cache: Dict[str, StockData] = {}  # code -> StockData
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
        
        # 提取股票名称
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
    
    def load_stock_data(self, code: str) -> Optional[StockData]:
        """加载股票数据"""
        # 检查缓存
        if code in self._data_cache:
            logger.debug(f"从缓存加载股票数据: {code}")
            return self._data_cache[code]
        
        # 检查文件是否存在
        if code not in self._stock_files:
            logger.warning(f"股票代码不存在: {code}")
            return None
        
        try:
            filepath = self._stock_files[code]
            logger.info(f"从文件加载股票数据: {code}")
            df = pd.read_csv(filepath)
            
            # 数据验证
            if df.empty:
                logger.error(f"股票数据为空: {code}")
                return None
            
            stock_info = self._stock_info_map[code]
            stock_data = StockData(df, stock_info)
            
            # 缓存数据
            self._data_cache[code] = stock_data
            
            return stock_data
        except pd.errors.EmptyDataError:
            logger.error(f"股票数据文件为空: {code}")
            return None
        except pd.errors.ParserError as e:
            logger.error(f"股票数据文件解析失败 {code}: {e}")
            return None
        except KeyError as e:
            logger.error(f"股票数据缺少必要列 {code}: {e}")
            return None
        except Exception as e:
            logger.error(f"加载股票数据失败 {code}: {e}", exc_info=True)
            return None
    
    def clear_cache(self):
        """清除缓存"""
        self._data_cache.clear()
        logger.info("数据缓存已清除")
    
    def get_cache_stats(self) -> Dict:
        """获取缓存统计"""
        return {
            'cached_stocks': len(self._data_cache),
            'total_stocks': len(self._stock_files),
            'cache_ratio': len(self._data_cache) / len(self._stock_files) if self._stock_files else 0
        }


class DataService:
    """数据服务类"""
    
    def __init__(self):
        self.manager = StockDataManager()
    
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
