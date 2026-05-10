"""
股票数据自动更新模块
用于批量更新A股上市公司数据到最新日期
"""
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Callable
import logging
import time
from pathlib import Path

from config import PATH_CONFIG, load_tushare_token

logger = logging.getLogger(__name__)


class StockDataUpdater:
    """股票数据更新器"""
    
    def __init__(self, data_dir: Optional[str] = None, custom_start_date: Optional[str] = None):
        self.data_dir = data_dir or PATH_CONFIG.DATA_DIR
        self.today = datetime.now().strftime('%Y%m%d')
        self.custom_start_date = custom_start_date
        self.updated_count = 0
        self.failed_stocks = []
        self._stop_requested = False
        self._progress_callback: Optional[Callable] = None
        self._should_stop_callback: Optional[Callable] = None
        
        self.token = load_tushare_token()
        if self.token:
            import tushare as ts
            ts.set_token(self.token)
            self.pro = ts.pro_api()
            logger.info("Tushare API 初始化成功")
        else:
            self.pro = None
            logger.warning("未找到tushare token，将使用模拟数据")
    
    def set_progress_callback(self, callback: Callable[[int, int, str, str, bool], None]):
        self._progress_callback = callback
    
    def set_should_stop_callback(self, callback: Callable[[], bool]):
        self._should_stop_callback = callback
    
    def request_stop(self):
        self._stop_requested = True
    
    def _should_stop(self) -> bool:
        if self._stop_requested:
            return True
        if self._should_stop_callback:
            return self._should_stop_callback()
        return False
    
    def parse_filename(self, filename: str) -> Optional[Dict]:
        """解析文件名获取股票信息"""
        if not filename.endswith('.csv') or 'tushare' not in filename:
            return None
        
        parts = filename.replace('.csv', '').split('_')
        if len(parts) < 4:
            return None
        
        try:
            stock_code = parts[0]
            tushare_idx = parts.index('tushare')
            stock_name = '_'.join(parts[1:tushare_idx])
            start_date = parts[tushare_idx + 1]
            end_date = parts[tushare_idx + 2]
            
            return {
                'code': stock_code,
                'name': stock_name,
                'start_date': start_date,
                'end_date': end_date,
                'filename': filename,
                'filepath': os.path.join(self.data_dir, filename)
            }
        except (ValueError, IndexError):
            return None
    
    def get_all_stock_files(self) -> List[Dict]:
        """获取所有股票文件信息"""
        stocks = []
        if not os.path.exists(self.data_dir):
            logger.warning(f"数据目录不存在: {self.data_dir}")
            return stocks
        
        for filename in os.listdir(self.data_dir):
            info = self.parse_filename(filename)
            if info:
                stocks.append(info)
        
        logger.info(f"找到 {len(stocks)} 只股票数据文件")
        return stocks
    
    def read_existing_data(self, filepath: str) -> Optional[pd.DataFrame]:
        """读取现有数据"""
        try:
            df = pd.read_csv(filepath)
            if 'date' not in df.columns:
                logger.error(f"文件缺少date列: {filepath}")
                return None
            
            # 转换日期列
            df['date'] = pd.to_datetime(df['date'], format='%Y-%m-%d', errors='coerce')
            
            # 过滤无效日期
            df = df.dropna(subset=['date'])
            
            if df.empty:
                logger.warning(f"文件数据为空: {filepath}")
                return None
            
            return df
        except Exception as e:
            logger.error(f"读取文件失败 {filepath}: {e}")
            return None
    
    def fetch_tushare_data(self, stock_code: str, stock_name: str, 
                          start_date: str, end_date: str) -> pd.DataFrame:
        """
        从tushare API获取股票数据
        使用前复权数据，与历史数据保持一致
        """
        if self.pro is None:
            logger.error("Tushare API 未初始化")
            return pd.DataFrame()
        
        try:
            # 调用tushare API获取日线数据（前复权）
            df = self.pro.daily(
                ts_code=stock_code,
                start_date=start_date,
                end_date=end_date,
                adj='qfq'  # 前复权，与历史数据保持一致
            )
            
            if df is None or len(df) == 0:
                logger.warning(f"{stock_code} 没有获取到数据")
                return pd.DataFrame()
            
            # 添加股票名称
            df['stock_name'] = stock_name
            
            # 重命名列
            df = df.rename(columns={
                'trade_date': 'date',
                'vol': 'volume'
            })
            
            # 转换日期格式
            df['date'] = pd.to_datetime(df['date'])
            
            # 重新排列列顺序
            df = df[['date', 'open', 'high', 'low', 'close', 'volume', 'stock_name']]
            
            # 按日期排序
            df = df.sort_values('date').reset_index(drop=True)
            
            # 计算均线
            df['ma5'] = df['close'].rolling(window=5, min_periods=1).mean().round(2)
            df['ma10'] = df['close'].rolling(window=10, min_periods=1).mean().round(2)
            df['ma20'] = df['close'].rolling(window=20, min_periods=1).mean().round(2)
            
            logger.info(f"获取 {stock_code} 数据成功: {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"获取 {stock_code} 数据失败: {e}")
            return pd.DataFrame()
    
    def update_stock_data(self, stock_info: Dict) -> bool:
        """更新单只股票数据"""
        try:
            stock_code = stock_info['code']
            stock_name = stock_info['name']
            current_end_date = stock_info['end_date']
            current_start_date = stock_info['start_date']
            filepath = stock_info['filepath']

            existing_df = self.read_existing_data(filepath)
            if existing_df is None or existing_df.empty:
                logger.error(f"无法读取现有数据或数据为空: {filepath}")
                return False

            existing_earliest = existing_df['date'].min()
            existing_latest = existing_df['date'].max()

            if self.custom_start_date:
                custom_start_dt = pd.Timestamp(datetime.strptime(self.custom_start_date, '%Y%m%d'))
                today_dt = pd.Timestamp(datetime.strptime(self.today, '%Y%m%d'))

                need_backward_fetch = custom_start_dt < existing_earliest
                need_forward_fetch = today_dt > existing_latest

                if not need_backward_fetch and not need_forward_fetch:
                    logger.debug(f"{stock_code} 数据已覆盖 {self.custom_start_date} ~ {self.today}，无需更新")
                    return True

                frames_to_concat = []

                if need_backward_fetch:
                    backward_start = self.custom_start_date
                    backward_end = (existing_earliest - timedelta(days=1)).strftime('%Y%m%d')
                    logger.info(f"{stock_code} 向前扩展: {backward_start} ~ {backward_end}")
                    backward_df = self.fetch_tushare_data(stock_code, stock_name, backward_start, backward_end)
                    if not backward_df.empty:
                        frames_to_concat.append(backward_df)

                frames_to_concat.append(existing_df)

                if need_forward_fetch:
                    forward_start = (existing_latest + timedelta(days=1)).strftime('%Y%m%d')
                    forward_end = self.today
                    logger.info(f"{stock_code} 向后更新: {forward_start} ~ {forward_end}")
                    forward_df = self.fetch_tushare_data(stock_code, stock_name, forward_start, forward_end)
                    if not forward_df.empty:
                        frames_to_concat.append(forward_df)

                combined_df = pd.concat(frames_to_concat, ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['date'], keep='first')
                combined_df = combined_df.sort_values('date')

                combined_df['ma5'] = combined_df['close'].rolling(window=5, min_periods=1).mean().round(2)
                combined_df['ma10'] = combined_df['close'].rolling(window=10, min_periods=1).mean().round(2)
                combined_df['ma20'] = combined_df['close'].rolling(window=20, min_periods=1).mean().round(2)

                combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')

                new_filename = f"{stock_code}_{stock_name}_tushare_{self.custom_start_date}_{self.today}.csv"
                new_filepath = os.path.join(self.data_dir, new_filename)

                combined_df.to_csv(new_filepath, index=False)

                if os.path.exists(filepath) and os.path.abspath(filepath) != os.path.abspath(new_filepath):
                    os.remove(filepath)
                    logger.info(f"删除旧文件: {filepath}")

                logger.info(f"成功更新 {stock_code} {stock_name}，新文件: {new_filename}")
                return True

            else:
                if current_end_date >= self.today:
                    logger.debug(f"{stock_code} {stock_name} 数据已是最新 ({current_end_date} >= {self.today})")
                    return True

                new_start_date = (existing_latest + timedelta(days=1)).strftime('%Y%m%d')
                new_end_date = self.today

                if new_start_date > new_end_date:
                    logger.debug(f"{stock_code} 无需更新 ({new_start_date} > {new_end_date})")
                    return True

                logger.info(f"获取 {stock_code} 从 {new_start_date} 到 {new_end_date} 的数据")
                new_df = self.fetch_tushare_data(stock_code, stock_name, new_start_date, new_end_date)

                if new_df.empty:
                    logger.warning(f"{stock_code} 没有新数据")
                    return True

                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                combined_df = combined_df.drop_duplicates(subset=['date'], keep='first')
                combined_df = combined_df.sort_values('date')

                combined_df['ma5'] = combined_df['close'].rolling(window=5, min_periods=1).mean().round(2)
                combined_df['ma10'] = combined_df['close'].rolling(window=10, min_periods=1).mean().round(2)
                combined_df['ma20'] = combined_df['close'].rolling(window=20, min_periods=1).mean().round(2)

                combined_df['date'] = combined_df['date'].dt.strftime('%Y-%m-%d')

                new_filename = f"{stock_code}_{stock_name}_tushare_{current_start_date}_{self.today}.csv"
                new_filepath = os.path.join(self.data_dir, new_filename)

                combined_df.to_csv(new_filepath, index=False)

                if os.path.exists(filepath) and os.path.abspath(filepath) != os.path.abspath(new_filepath):
                    os.remove(filepath)
                    logger.info(f"删除旧文件: {filepath}")

                logger.info(f"成功更新 {stock_code} {stock_name}，新文件: {new_filename}")
                return True

        except Exception as e:
            logger.error(f"更新 {stock_info.get('code', 'unknown')} 失败: {e}")
            self.failed_stocks.append(stock_info)
            return False
    
    def _print_progress_bar(self, current: int, total: int, stock_code: str, 
                            stock_name: str, bar_length: int = 40) -> None:
        """打印进度条"""
        percent = current / total
        filled = int(percent * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        progress_str = f"\r[{bar}] {percent*100:5.1f}% ({current}/{total}) | {stock_code} {stock_name}"
        print(progress_str, end='', flush=True)
    
    def update_all_stocks(self, delay: float = 0.5, show_progress: bool = True) -> Dict:
        """批量更新所有股票数据"""
        logger.info("=" * 50)
        logger.info("开始批量更新股票数据")
        logger.info(f"目标日期: {self.today}")
        logger.info("=" * 50)
        
        stocks = self.get_all_stock_files()
        if not stocks:
            logger.warning("没有找到股票数据文件")
            return {'success': 0, 'failed': 0, 'total': 0, 'stopped': False}
        
        success_count = 0
        failed_count = 0
        total_count = len(stocks)
        stopped = False
        
        for i in range(total_count):
            if self._should_stop():
                logger.info("用户请求停止更新")
                stopped = True
                break
            
            current_stocks = self.get_all_stock_files()
            
            if i >= len(current_stocks):
                logger.warning(f"处理到第 {i+1} 只股票，但当前只有 {len(current_stocks)} 只")
                break
            
            stock = current_stocks[i]
            
            result = self.update_stock_data(stock)
            
            if result:
                success_count += 1
            else:
                failed_count += 1
            
            if self._progress_callback:
                self._progress_callback(i + 1, total_count, stock['code'], stock['name'], result)
            
            logger.info(f"[{i+1}/{total_count}] 处理 {stock['code']} {stock['name']}")
            
            if delay > 0 and i < total_count - 1:
                time.sleep(delay)
        
        logger.info("=" * 50)
        logger.info("更新完成")
        logger.info(f"成功: {success_count}, 失败: {failed_count}, 总计: {total_count}")
        logger.info("=" * 50)
        
        if self.failed_stocks:
            logger.warning(f"以下股票更新失败:")
            for stock in self.failed_stocks:
                logger.warning(f"  - {stock.get('code', 'unknown')} {stock.get('name', '')}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'total': total_count,
            'failed_stocks': self.failed_stocks,
            'stopped': stopped
        }


def main():
    """主函数"""
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data_update.log', encoding='utf-8')
        ]
    )
    
    # 创建更新器并执行更新
    updater = StockDataUpdater()
    result = updater.update_all_stocks(delay=0.1)
    
    print(f"\n更新结果:")
    print(f"  成功: {result['success']}")
    print(f"  失败: {result['failed']}")
    print(f"  总计: {result['total']}")
    
    if result['failed_stocks']:
        print(f"\n失败的股票:")
        for stock in result['failed_stocks']:
            print(f"  - {stock.get('code', 'unknown')}")


if __name__ == '__main__':
    main()
