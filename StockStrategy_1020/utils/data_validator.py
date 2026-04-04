"""
数据验证工具
用于验证股票数据文件的完整性和格式
"""
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """数据验证器"""
    
    REQUIRED_COLUMNS = ['date', 'open', 'high', 'low', 'close', 'volume']
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
    
    def validate_file(self, filepath: Path) -> Dict[str, any]:
        """
        验证单个数据文件
        
        Args:
            filepath: 文件路径
            
        Returns:
            验证结果字典
        """
        result = {
            'valid': True,
            'errors': [],
            'warnings': [],
            'row_count': 0,
            'date_range': None
        }
        
        try:
            # 读取文件
            df = pd.read_csv(filepath)
            result['row_count'] = len(df)
            
            # 检查必要列
            missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                result['valid'] = False
                result['errors'].append(f"缺少必要列: {missing_cols}")
                return result
            
            # 检查数据类型
            for col in ['open', 'high', 'low', 'close', 'volume']:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    result['valid'] = False
                    result['errors'].append(f"列 {col} 不是数值类型")
            
            # 检查日期格式
            try:
                df['date'] = pd.to_datetime(df['date'])
                result['date_range'] = (df['date'].min(), df['date'].max())
            except Exception as e:
                result['valid'] = False
                result['errors'].append(f"日期格式错误: {e}")
            
            # 检查数据完整性
            if df.isnull().any().any():
                null_counts = df.isnull().sum()
                null_cols = null_counts[null_counts > 0].to_dict()
                result['warnings'].append(f"存在空值: {null_cols}")
            
            # 检查价格合理性
            for col in ['open', 'high', 'low', 'close']:
                if (df[col] <= 0).any():
                    result['warnings'].append(f"列 {col} 存在非正值")
            
            # 检查高低价关系
            if (df['high'] < df['low']).any():
                result['valid'] = False
                result['errors'].append("存在最高价低于最低价的记录")
            
            # 检查成交量
            if (df['volume'] < 0).any():
                result['valid'] = False
                result['errors'].append("存在负成交量")
            
        except Exception as e:
            result['valid'] = False
            result['errors'].append(f"读取文件失败: {e}")
        
        return result
    
    def validate_directory(self) -> Dict[str, any]:
        """
        验证整个数据目录
        
        Returns:
            验证结果字典
        """
        results = {
            'total_files': 0,
            'valid_files': 0,
            'invalid_files': 0,
            'file_results': []
        }
        
        if not self.data_dir.exists():
            logger.error(f"数据目录不存在: {self.data_dir}")
            return results
        
        # 获取所有CSV文件
        csv_files = list(self.data_dir.glob('*.csv'))
        results['total_files'] = len(csv_files)
        
        for filepath in csv_files:
            file_result = self.validate_file(filepath)
            file_result['filename'] = filepath.name
            
            if file_result['valid']:
                results['valid_files'] += 1
            else:
                results['invalid_files'] += 1
            
            results['file_results'].append(file_result)
        
        return results
    
    def print_validation_report(self, results: Dict[str, any]):
        """打印验证报告"""
        print("\n" + "=" * 60)
        print("数据验证报告")
        print("=" * 60)
        print(f"总文件数: {results['total_files']}")
        print(f"有效文件: {results['valid_files']}")
        print(f"无效文件: {results['invalid_files']}")
        
        if results['invalid_files'] > 0:
            print("\n无效文件列表:")
            for file_result in results['file_results']:
                if not file_result['valid']:
                    print(f"\n文件: {file_result['filename']}")
                    for error in file_result['errors']:
                        print(f"  错误: {error}")
        
        if any(file_result['warnings'] for file_result in results['file_results']):
            print("\n警告:")
            for file_result in results['file_results']:
                if file_result['warnings']:
                    print(f"\n文件: {file_result['filename']}")
                    for warning in file_result['warnings']:
                        print(f"  警告: {warning}")
        
        print("=" * 60)


def main():
    """主函数"""
    import sys
    from utils import get_project_root
    
    # 设置日志
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # 获取数据目录
    data_dir = get_project_root() / 'A股上市公司数据'
    
    # 创建验证器
    validator = DataValidator(data_dir)
    
    # 执行验证
    results = validator.validate_directory()
    
    # 打印报告
    validator.print_validation_report(results)
    
    # 返回退出码
    return 0 if results['invalid_files'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
