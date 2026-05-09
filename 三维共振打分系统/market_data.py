"""
中证全指市场数据获取模块
使用tushare作为数据源，支持本地CSV缓存
"""

import pandas as pd
import numpy as np
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import time

logger = logging.getLogger(__name__)


def load_tushare_token(file_path: str = "tushare_token.txt") -> Optional[str]:
    """
    从文件加载tushare token
    
    Args:
        file_path: 存储token的文件路径，默认为"tushare_token.txt"
        
    Returns:
        token字符串，如果文件不存在或无效则返回None
    """
    if not os.path.exists(file_path):
        return None
    
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    return line
    except Exception as e:
        logger.warning(f"读取tushare token文件失败: {e}")
    
    return None


class ZhongZhengData:
    """中证全指数据获取类"""
    
    def __init__(self, token: Optional[str] = None, cache_dir: str = "data"):
        """
        初始化
        
        Args:
            token: tushare token，如果不提供则尝试从tushare_token.txt读取
            cache_dir: 缓存目录，默认为"data"
        """
        self.index_code = "000985.SH"  # 中证全指代码（tushare格式）
        self.index_name = "中证全指"
        # 如果没有传入token，尝试从文件读取
        self.token = token or load_tushare_token()
        self.ts = None
        self.cache_dir = cache_dir
        
        # 确保缓存目录存在
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)
        
        # 尝试导入tushare
        try:
            import tushare as ts
            if self.token:
                ts.set_token(self.token)
                self.ts = ts.pro_api()
                logger.info("tushare已使用token初始化pro_api")
            else:
                self.ts = ts
                logger.info("tushare未使用token，将使用免费接口")
        except ImportError:
            logger.warning("tushare未安装，将使用备用方法")
            self.ts = None
        
        # 尝试导入akshare
        self.ak = None
        try:
            import akshare as ak
            self.ak = ak
            logger.info("akshare已成功导入")
        except Exception as e:
            logger.warning(f"akshare导入失败: {e}")
            self.ak = None
    
    def _get_cache_file_path(self) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, "zhongzheng_index_data.csv")
    
    def _load_from_cache(self) -> Optional[pd.DataFrame]:
        """
        从本地CSV缓存加载数据
        
        Returns:
            缓存的DataFrame或None
        """
        cache_file = self._get_cache_file_path()
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            df = pd.read_csv(cache_file)
            df['date'] = pd.to_datetime(df['date'])
            logger.info(f"从本地缓存加载了{len(df)}条数据")
            return df
        except Exception as e:
            logger.warning(f"读取缓存失败: {e}")
            return None
    
    def _save_to_cache(self, df: pd.DataFrame) -> bool:
        """
        保存数据到本地CSV缓存
        
        Args:
            df: 要保存的DataFrame
            
        Returns:
            是否保存成功
        """
        cache_file = self._get_cache_file_path()
        
        try:
            df.to_csv(cache_file, index=False)
            logger.info(f"数据已保存到本地缓存: {cache_file}")
            return True
        except Exception as e:
            logger.warning(f"保存缓存失败: {e}")
            return False
    
    def _get_latest_date_from_cache(self) -> Optional[str]:
        """
        获取缓存数据中的最新日期
        
        Returns:
            最新日期字符串(YYYY-MM-DD)或None
        """
        cache_file = self._get_cache_file_path()
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            df = pd.read_csv(cache_file)
            if df.empty:
                return None
            latest_date = pd.to_datetime(df['date']).max()
            return latest_date.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"获取缓存最新日期失败: {e}")
            return None
    
    def _is_today_data_available(self) -> bool:
        """
        检查本地缓存是否包含今天数据
        
        Returns:
            是否包含今天数据
        """
        latest_date = self._get_latest_date_from_cache()
        if latest_date is None:
            return False
        
        today = datetime.now().strftime('%Y-%m-%d')
        return latest_date == today
    
    def _fetch_data_from_akshare(self, days: int = 90) -> pd.DataFrame:
        """
        从akshare获取数据
        
        Args:
            days: 获取天数
            
        Returns:
            DataFrame
        """
        if self.ak is None:
            logger.warning("akshare未初始化")
            return pd.DataFrame()
        
        try:
            logger.info("尝试使用akshare接口获取数据...")
            
            # 计算日期范围
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days + 10)
            
            # 使用akshare东方财富接口获取中证全指数据（数据更新到最新）
            df = self.ak.stock_zh_index_daily_em(symbol="sh000985")
            
            if df is not None and not df.empty:
                # 转换日期格式
                df['date'] = pd.to_datetime(df['date'])
                
                # 筛选日期范围
                df = df[df['date'] >= pd.Timestamp(start_date)].reset_index(drop=True)
                
                # 确保列名一致
                df = df.rename(columns={
                    'open': 'open',
                    'high': 'high',
                    'low': 'low',
                    'close': 'close',
                    'volume': 'volume'
                })
                
                # 确保数值类型正确
                for col in ['open', 'high', 'low', 'close', 'volume']:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                
                # 添加amount列（如果不存在）
                if 'amount' not in df.columns:
                    df['amount'] = 0.0
                
                df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'amount']]
                
                # 计算涨跌幅
                df['pct_change'] = df['close'].pct_change() * 100
                df['change_amount'] = df['close'].diff()
                df['amplitude'] = (df['high'] - df['low']) / df['low'] * 100
                
                logger.info(f"成功从akshare获取{len(df)}条数据")
                return df
                
        except Exception as e:
            logger.warning(f"akshare接口失败: {e}")
        
        return pd.DataFrame()
    
    def _fetch_data_from_tushare(self, days: int = 90) -> pd.DataFrame:
        """
        从tushare获取数据
        
        Args:
            days: 获取天数
            
        Returns:
            DataFrame
        """
        # 尝试tushare pro接口 (query方式)
        if self.ts and hasattr(self.ts, 'query'):
            try:
                logger.info("尝试使用tushare pro接口获取数据...")
                
                # 计算日期范围
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days + 10)
                
                df = self.ts.query(
                    'index_daily',
                    ts_code=self.index_code,
                    start_date=start_date.strftime('%Y%m%d'),
                    end_date=end_date.strftime('%Y%m%d')
                )
                
                if df is not None and not df.empty:
                    df = df.sort_values('trade_date').reset_index(drop=True)
                    df['date'] = pd.to_datetime(df['trade_date'])
                    df = df.rename(columns={
                        'open': 'open',
                        'high': 'high',
                        'low': 'low',
                        'close': 'close',
                        'vol': 'volume',
                        'amount': 'amount'
                    })
                    
                    # 确保数值类型正确
                    for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                    
                    df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'amount']]
                    df['volume'] = df['volume'] * 100
                    
                    df['pct_change'] = df['close'].pct_change() * 100
                    df['change_amount'] = df['close'].diff()
                    df['amplitude'] = (df['high'] - df['low']) / df['low'] * 100
                    
                    logger.info(f"成功从API获取{len(df)}条数据")
                    return df
                    
            except Exception as e:
                logger.warning(f"tushare pro接口失败: {e}")
        
        # tushare失败，尝试使用akshare
        logger.info("tushare获取失败，尝试使用akshare...")
        return self._fetch_data_from_akshare(days=days)
    
    def get_index_data(self, days: int = 90, force_update: bool = False) -> pd.DataFrame:
        """
        获取中证全指历史数据，优先使用本地缓存
        
        Args:
            days: 获取天数，默认90天
            force_update: 是否强制更新数据
            
        Returns:
            DataFrame包含日期、开盘、收盘、最高、最低、成交量等数据
        """
        today = datetime.now().strftime('%Y-%m-%d')
        
        # 检查本地缓存
        if not force_update:
            cached_df = self._load_from_cache()
            if cached_df is not None and not cached_df.empty:
                latest_date = cached_df['date'].max().strftime('%Y-%m-%d')
                
                if latest_date == today:
                    logger.info(f"本地缓存已包含今天({today})的数据，直接使用缓存")
                    return cached_df.tail(days).reset_index(drop=True)
                else:
                    logger.info(f"本地缓存最新日期为{latest_date}，需要更新数据")
            else:
                logger.info("本地缓存不存在，需要从API获取数据")
        else:
            logger.info("强制更新模式，从API获取最新数据")
        
        # 从API获取数据
        df = self._fetch_data_from_tushare(days=days)
        
        if not df.empty:
            # 保存到缓存
            self._save_to_cache(df)
            return df.tail(days).reset_index(drop=True)
        
        # API获取失败，尝试使用缓存数据（即使不是最新的）
        cached_df = self._load_from_cache()
        if cached_df is not None and not cached_df.empty:
            logger.warning("API获取失败，使用本地缓存数据（可能不是最新的）")
            return cached_df.tail(days).reset_index(drop=True)
        
        # 所有方法都失败
        logger.error("所有数据源都失败，返回空数据")
        return pd.DataFrame()
    
    def calculate_ma(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        计算移动平均线
        
        Args:
            df: 指数数据DataFrame
            
        Returns:
            添加了MA10和MA20的DataFrame
        """
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        return df
    
    def analyze_capital_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析资金面得分
        
        判断依据：
        - 成交量明显放大且持续性良好得1分
        - 缩量或流出得0分
        
        Args:
            df: 指数数据DataFrame
            
        Returns:
            资金面分析结果
        """
        if df.empty or len(df) < 20:
            return {
                "score": 0,
                "analysis": "数据获取失败，无法判断",
                "details": {"error": "未能获取中证全指数据"}
            }
        
        # 计算近5日平均成交量
        recent_5_days = df.tail(5)
        recent_volume_mean = recent_5_days['volume'].mean()
        
        # 计算前5-10日平均成交量（作为对比基准）
        if len(df) >= 10:
            previous_5_days = df.iloc[-10:-5]
            previous_volume_mean = previous_5_days['volume'].mean()
        else:
            previous_volume_mean = df['volume'].mean()
        
        # 计算成交量变化率
        volume_change_ratio = (recent_volume_mean - previous_volume_mean) / previous_volume_mean * 100
        
        # 判断成交量趋势
        volume_trend = []
        for i in range(-5, 0):
            if i + 1 < 0:
                if df.iloc[i]['volume'] > df.iloc[i-1]['volume']:
                    volume_trend.append("up")
                else:
                    volume_trend.append("down")
        
        up_days = volume_trend.count("up")
        
        # 评分逻辑
        score = 0
        reasons = []
        
        # 条件1：成交量放大超过20%
        if volume_change_ratio > 20:
            score += 0.5
            reasons.append(f"近5日成交量较前5日放大{volume_change_ratio:.1f}%")
        
        # 条件2：成交量持续性良好（5天中至少3天放量）
        if up_days >= 3:
            score += 0.5
            reasons.append(f"近5个交易日有{up_days}天成交量上升，持续性良好")
        
        # 最终得分（0或1）
        final_score = 1 if score >= 0.5 else 0
        
        return {
            "score": final_score,
            "analysis": "成交量明显放大且持续性良好" if final_score == 1 else "成交量萎缩或缺乏持续性",
            "details": {
                "recent_5d_volume_mean": float(round(recent_volume_mean / 1e8, 2)),
                "previous_5d_volume_mean": float(round(previous_volume_mean / 1e8, 2)),
                "volume_change_ratio": float(round(volume_change_ratio, 2)),
                "up_days_in_5": int(up_days),
                "reasons": reasons,
                "raw_score": float(score)
            }
        }
    
    def analyze_technical_score(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        分析技术面得分
        
        判断依据：
        - 站稳双均线（10日和20日均线）得1分
        - 未突破或假突破得0分
        
        Args:
            df: 指数数据DataFrame
            
        Returns:
            技术面分析结果
        """
        if df.empty or len(df) < 20:
            return {
                "score": 0,
                "analysis": "数据获取失败，无法判断",
                "details": {"error": "未能获取中证全指数据"}
            }
        
        if 'MA10' not in df.columns or 'MA20' not in df.columns:
            df = self.calculate_ma(df)
        
        latest = df.iloc[-1]
        latest_close = latest['close']
        latest_ma10 = latest['MA10']
        latest_ma20 = latest['MA20']
        
        # 判断条件
        above_ma10 = latest_close > latest_ma10
        above_ma20 = latest_close > latest_ma20
        
        # 计算偏离度
        deviation_ma10 = (latest_close - latest_ma10) / latest_ma10 * 100
        deviation_ma20 = (latest_close - latest_ma20) / latest_ma20 * 100
        
        # 判断是否有效突破（连续站稳）
        consecutive_days_above = 0
        for i in range(-5, 0):
            if df.iloc[i]['close'] > df.iloc[i]['MA10'] and df.iloc[i]['close'] > df.iloc[i]['MA20']:
                consecutive_days_above += 1
        
        # 评分逻辑
        score = 0
        reasons = []
        
        # 条件1：收盘站稳双均线
        if above_ma10 and above_ma20:
            score += 0.5
            reasons.append(f"收盘价{latest_close:.2f}点站稳MA10({latest_ma10:.2f})和MA20({latest_ma20:.2f})")
        
        # 条件2：有效突破（至少连续2天站稳）
        if consecutive_days_above >= 2:
            score += 0.5
            reasons.append(f"已连续{consecutive_days_above}天站稳双均线，确认为有效突破")
        
        # 最终得分（0或1）
        final_score = 1 if score >= 0.5 else 0
        
        return {
            "score": final_score,
            "analysis": "指数站稳10日与20日均线，形成有效突破" if final_score == 1 else "指数未突破双均线或假突破",
            "details": {
                "latest_close": round(latest_close, 2),
                "ma10": round(latest_ma10, 2),
                "ma20": round(latest_ma20, 2),
                "deviation_ma10": round(deviation_ma10, 2),
                "deviation_ma20": round(deviation_ma20, 2),
                "above_ma10": bool(above_ma10),
                "above_ma20": bool(above_ma20),
                "consecutive_days_above": int(consecutive_days_above),
                "reasons": reasons,
                "raw_score": float(score)
            }
        }
    
    def get_full_analysis(self, force_update: bool = False) -> Dict[str, Any]:
        """
        获取完整的资金面和技术面分析
        
        Args:
            force_update: 是否强制更新数据
            
        Returns:
            包含资金面和技术面得分的完整分析结果
        """
        df = self.get_index_data(days=90, force_update=force_update)
        
        if df.empty:
            return {
                "success": False,
                "error": "未能获取中证全指数据，请检查网络连接或数据源配置"
            }
        
        df = self.calculate_ma(df)
        
        capital_analysis = self.analyze_capital_score(df)
        technical_analysis = self.analyze_technical_score(df)
        
        # 检查是否使用了缓存数据
        latest_date = df['date'].max().strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        from_cache = latest_date != today
        
        return {
            "success": True,
            "index_name": self.index_name,
            "index_code": self.index_code,
            "latest_date": latest_date,
            "latest_close": round(df.iloc[-1]['close'], 2),
            "capital": capital_analysis,
            "technical": technical_analysis,
            "total_score": capital_analysis["score"] + technical_analysis["score"],
            "from_cache": from_cache
        }


# 测试代码
if __name__ == "__main__":
    print("正在获取中证全指数据...")
    analyzer = ZhongZhengData()
    result = analyzer.get_full_analysis()
    
    if result["success"]:
        print(f"\n中证全指最新数据:")
        print(f"日期: {result['latest_date']}")
        print(f"收盘: {result['latest_close']}")
        print(f"数据来源: {'本地缓存' if result.get('from_cache') else 'API实时'}")
        print(f"\n资金面得分: {result['capital']['score']}")
        print(f"分析: {result['capital']['analysis']}")
        print(f"\n技术面得分: {result['technical']['score']}")
        print(f"分析: {result['technical']['analysis']}")
        print(f"\n市场数据总分: {result['total_score']}/2")
    else:
        print(f"获取数据失败: {result.get('error', '未知错误')}")
