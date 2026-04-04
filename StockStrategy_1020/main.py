"""
1020双均线交易策略应用 - 重构版

主入口文件

使用方法:
    python main.py

特性:
    - 分离关注点：配置、模型、服务、视图
    - 单例模式管理数据和配置
    - 优化的策略逻辑
    - 更好的错误处理和日志
"""
import logging

from utils import setup_logging
from views import create_app


def main():
    """主函数"""
    # 设置日志
    logger = setup_logging(level=logging.INFO)
    logger.info("=" * 50)
    logger.info("启动 1020双均线交易策略应用")
    logger.info("=" * 50)
    
    try:
        # 创建应用
        app = create_app()
        
        # 运行应用
        logger.info("应用启动成功，访问 http://127.0.0.1:8050")
        app.run(debug=True, port=8050)
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}", exc_info=True)
        raise


if __name__ == '__main__':
    main()
