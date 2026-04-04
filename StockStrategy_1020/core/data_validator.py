"""
数据验证器模块
提供数据验证和清洗功能
"""
import pandas as pd
import numpy as np
from typing import List, Optional, Tuple
import logging

from constants import REQUIRED_COLUMNS
from exceptions import DataValidationError


logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""
    
    def __init__(self, required_columns: List[str] = None):
        self.required_columns = required_columns or REQUIRED_COLUMNS
    
    def validate(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        验证数据
        
        Args:
            df: 股票数据DataFrame
        
        Returns:
            (是否有效, 错误信息列表)
        """
        errors = []
        
        if df is None or df.empty:
            errors.append("数据为空")
            return False, errors
        
        missing_columns = self._check_required_columns(df)
        if missing_columns:
            errors.append(f"缺少必要列: {', '.join(missing_columns)}")
        
        if not self._check_date_column(df):
            errors.append("日期列格式无效")
        
        if not self._check_price_columns(df):
            errors.append("价格列包含无效数据")
        
        if not self._check_volume_column(df):
            errors.append("成交量列包含无效数据")
        
        return len(errors) == 0, errors
    
    def _check_required_columns(self, df: pd.DataFrame) -> List[str]:
        """检查必要列"""
        missing = []
        for col in self.required_columns:
            if col not in df.columns:
                missing.append(col)
        return missing
    
    def _check_date_column(self, df: pd.DataFrame) -> bool:
        """检查日期列"""
        if 'date' not in df.columns:
            return False
        
        try:
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                pd.to_datetime(df['date'])
            return True
        except (ValueError, TypeError):
            return False
    
    def _check_price_columns(self, df: pd.DataFrame) -> bool:
        """检查价格列"""
        price_cols = ['open', 'high', 'low', 'close']
        
        for col in price_cols:
            if col not in df.columns:
                return False
            
            if not pd.api.types.is_numeric_dtype(df[col]):
                return False
            
            if (df[col] <= 0).any():
                logger.warning(f"价格列 {col} 包含非正值")
        
        if not self._check_price_consistency(df):
            logger.warning("价格数据不一致（high < low 或其他异常）")
        
        return True
    
    def _check_price_consistency(self, df: pd.DataFrame) -> bool:
        """检查价格一致性"""
        if not all(col in df.columns for col in ['high', 'low', 'open', 'close']):
            return False
        
        consistent = (
            (df['high'] >= df['low']) &
            (df['high'] >= df['open']) &
            (df['high'] >= df['close']) &
            (df['low'] <= df['open']) &
            (df['low'] <= df['close'])
        )
        
        return consistent.all()
    
    def _check_volume_column(self, df: pd.DataFrame) -> bool:
        """检查成交量列"""
        if 'volume' not in df.columns:
            return False
        
        if not pd.api.types.is_numeric_dtype(df['volume']):
            return False
        
        if (df['volume'] < 0).any():
            logger.warning("成交量列包含负值")
        
        return True
    
    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        清洗数据
        
        Args:
            df: 原始数据
        
        Returns:
            清洗后的数据
        """
        df = df.copy()
        
        df = self._remove_duplicates(df)
        df = self._handle_missing_values(df)
        df = self._sort_by_date(df)
        df = self._remove_outliers(df)
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """移除重复数据"""
        if 'date' in df.columns:
            duplicates = df.duplicated(subset=['date'], keep='first')
            if duplicates.any():
                logger.info(f"移除 {duplicates.sum()} 条重复数据")
                df = df[~duplicates]
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        
        for col in numeric_cols:
            missing_count = df[col].isna().sum()
            if missing_count > 0:
                logger.info(f"列 {col} 有 {missing_count} 个缺失值，使用前值填充")
                df[col] = df[col].fillna(method='ffill')
        
        df = df.dropna(subset=self.required_columns)
        
        return df
    
    def _sort_by_date(self, df: pd.DataFrame) -> pd.DataFrame:
        """按日期排序"""
        if 'date' in df.columns:
            if not pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date').reset_index(drop=True)
        return df
    
    def _remove_outliers(self, df: pd.DataFrame, threshold: float = 3.0) -> pd.DataFrame:
        """移除异常值"""
        price_cols = ['open', 'high', 'low', 'close']
        
        for col in price_cols:
            if col in df.columns:
                z_scores = np.abs((df[col] - df[col].mean()) / df[col].std())
                outliers = z_scores > threshold
                if outliers.any():
                    logger.info(f"列 {col} 发现 {outliers.sum()} 个异常值")
        
        return df
    
    def validate_and_clean(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, bool, List[str]]:
        """
        验证并清洗数据
        
        Args:
            df: 原始数据
        
        Returns:
            (清洗后的数据, 是否有效, 错误信息列表)
        """
        is_valid, errors = self.validate(df)
        
        if not is_valid:
            return df, False, errors
        
        cleaned_df = self.clean_data(df)
        
        is_valid_after, errors_after = self.validate(cleaned_df)
        
        return cleaned_df, is_valid_after, errors_after


def validate_stock_data(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool, List[str]]:
    """
    便捷函数：验证股票数据
    
    Args:
        df: 股票数据DataFrame
    
    Returns:
        (清洗后的数据, 是否有效, 错误信息列表)
    """
    validator = DataValidator()
    return validator.validate_and_clean(df)
