"""
股票数据更新脚本
自动更新所有A股上市公司数据到最新日期

使用方法:
    python update_data.py

可选参数:
    --delay: 更新间隔延迟(秒)，默认0.1秒
    --console: 使用控制台模式（无GUI）
"""
import sys
import os
import threading


def get_token_file_path():
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, 'tushare_token.txt')
    base_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_dir, 'tushare_token.txt')


def load_tushare_token():
    token_file = get_token_file_path()
    if os.path.exists(token_file):
        try:
            with open(token_file, 'r', encoding='utf-8') as f:
                token = f.read().strip()
            if token:
                return token
        except Exception:
            pass
    token = os.environ.get('TUSHARE_TOKEN')
    if token:
        return token
    return None


def show_token_missing_popup():
    try:
        from ctypes import windll
        windll.user32.MessageBoxW(
            0,
            f"未配置tushare token！\n\n请在以下位置创建文件并输入您的token：\n{get_token_file_path()}\n\n或者设置环境变量：\nTUSHARE_TOKEN=您的token",
            "tushare token 未配置",
            0x30
        )
    except Exception:
        print("错误：未配置tushare token！")
        print(f"请在以下位置创建文件并输入您的token：{get_token_file_path()}")
        print("或者设置环境变量：TUSHARE_TOKEN=您的token")


def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def setup_logging():
    import logging
    from datetime import datetime

    base_dir = get_base_dir()
    log_dir = os.path.join(base_dir, 'logs')
    os.makedirs(log_dir, exist_ok=True)

    log_filename = os.path.join(log_dir, f"data_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_filename, encoding='utf-8', mode='w')
        ]
    )

    return log_filename


def run_with_gui(delay: float):
    import tkinter as tk
    from tkinter import ttk
    import logging
    import queue
    
    from services.data_updater import StockDataUpdater
    
    logger = logging.getLogger(__name__)
    
    updater = StockDataUpdater()
    stocks = updater.get_all_stock_files()
    total_count = len(stocks)
    
    stop_flag = [False]
    success_count = [0]
    failed_count = [0]
    
    root = tk.Tk()
    root.title("数据更新进度")
    root.geometry("500x320")
    root.resizable(False, False)
    
    main_frame = ttk.Frame(root, padding="20")
    main_frame.pack(fill=tk.BOTH, expand=True)
    
    title_label = ttk.Label(
        main_frame, 
        text="股票数据更新", 
        font=('Microsoft YaHei', 14, 'bold')
    )
    title_label.pack(pady=(0, 10))
    
    progress_var = tk.DoubleVar(value=0)
    progress_bar = ttk.Progressbar(
        main_frame, 
        variable=progress_var,
        maximum=100,
        length=460,
        mode='determinate'
    )
    progress_bar.pack(pady=5)
    
    percent_label = ttk.Label(
        main_frame,
        text="0.0%",
        font=('Microsoft YaHei', 11)
    )
    percent_label.pack()
    
    current_stock_label = ttk.Label(
        main_frame,
        text="准备开始...",
        font=('Microsoft YaHei', 10)
    )
    current_stock_label.pack(pady=5)
    
    stats_frame = ttk.Frame(main_frame)
    stats_frame.pack(pady=10)
    
    success_label = ttk.Label(
        stats_frame,
        text="成功: 0",
        font=('Microsoft YaHei', 10),
        foreground='green'
    )
    success_label.pack(side=tk.LEFT, padx=20)
    
    failed_label = ttk.Label(
        stats_frame,
        text="失败: 0",
        font=('Microsoft YaHei', 10),
        foreground='red'
    )
    failed_label.pack(side=tk.LEFT, padx=20)
    
    count_label = ttk.Label(
        stats_frame,
        text=f"进度: 0/{total_count}",
        font=('Microsoft YaHei', 10)
    )
    count_label.pack(side=tk.LEFT, padx=20)
    
    def on_stop():
        stop_flag[0] = True
        current_stock_label.config(text="正在停止...")
        stop_button.config(state=tk.DISABLED)
    
    stop_button = ttk.Button(
        main_frame,
        text="终止更新",
        command=on_stop,
        width=15
    )
    stop_button.pack(pady=15)
    
    status_label = ttk.Label(
        main_frame,
        text="",
        font=('Microsoft YaHei', 9),
        foreground='gray',
        wraplength=460,
        justify='center'
    )
    status_label.pack()
    
    msg_queue = queue.Queue()
    
    def on_progress(current: int, total: int, code: str, name: str, success: bool):
        msg_queue.put(('progress', current, total, code, name, success))
    
    def should_stop() -> bool:
        return stop_flag[0]
    
    updater.set_progress_callback(on_progress)
    updater.set_should_stop_callback(should_stop)
    
    def run_update():
        try:
            logger.info("开始更新数据...")
            result = updater.update_all_stocks(delay=delay)
            msg_queue.put(('complete', result))
        except Exception as e:
            logger.error(f"更新过程出错: {e}")
            msg_queue.put(('error', str(e)))
    
    def process_queue():
        try:
            while True:
                msg = msg_queue.get_nowait()
                if msg[0] == 'progress':
                    _, current, total, code, name, success = msg
                    if success:
                        success_count[0] += 1
                    else:
                        failed_count[0] += 1
                    percent = (current / total * 100) if total > 0 else 0
                    progress_var.set(percent)
                    percent_label.config(text=f"{percent:.1f}%")
                    current_stock_label.config(text=f"正在更新: {code} {name}")
                    count_label.config(text=f"进度: {current}/{total}")
                    success_label.config(text=f"成功: {success_count[0]}")
                    failed_label.config(text=f"失败: {failed_count[0]}")
                elif msg[0] == 'complete':
                    result = msg[1]
                    current_stock_label.config(text="更新完成！")
                    stop_button.config(text="关闭", command=root.destroy, state=tk.NORMAL)
                    status_label.config(
                        text=f"总计: {result.get('total', 0)} 只，"
                             f"成功: {result.get('success', 0)} 只，"
                             f"失败: {result.get('failed', 0)} 只"
                    )
                    return
                elif msg[0] == 'error':
                    current_stock_label.config(text=f"错误: {msg[1]}")
                    stop_button.config(text="关闭", command=root.destroy, state=tk.NORMAL)
                    return
        except queue.Empty:
            pass
        root.after(100, process_queue)
    
    update_thread = threading.Thread(target=run_update, daemon=True)
    update_thread.start()
    
    root.after(100, process_queue)
    root.mainloop()


def run_with_console(delay: float):
    import logging
    from datetime import datetime
    
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("   A股上市公司数据自动更新工具")
    print("=" * 60)
    print(f"当前日期: {datetime.now().strftime('%Y-%m-%d')}")
    print("=" * 60)
    print()
    
    from services.data_updater import StockDataUpdater
    updater = StockDataUpdater()
    
    def print_progress(current: int, total: int, code: str, name: str):
        percent = current / total * 100 if total > 0 else 0
        bar_length = 40
        filled = int(percent / 100 * bar_length)
        bar = '█' * filled + '░' * (bar_length - filled)
        print(f"\r[{bar}] {percent:5.1f}% ({current}/{total}) | {code} {name}", end='', flush=True)
    
    updater.set_progress_callback(print_progress)
    
    logger.info("开始更新数据...")
    result = updater.update_all_stocks(delay=delay)
    
    print()
    print()
    print("=" * 60)
    print("   更新完成")
    print("=" * 60)
    print(f"成功: {result['success']} 只")
    print(f"失败: {result['failed']} 只")
    print(f"总计: {result['total']} 只")
    
    if result.get('stopped'):
        print("注意: 更新被用户终止")
    
    if result['failed_stocks']:
        print()
        print("更新失败的股票:")
        for stock in result['failed_stocks']:
            print(f"  - {stock.get('code', 'unknown')} {stock.get('name', '')}")
    
    print("=" * 60)
    
    return 0 if result['failed'] == 0 else 1


def main():
    import argparse
    import logging
    from datetime import datetime

    token = load_tushare_token()
    if not token:
        show_token_missing_popup()
        return 1

    parser = argparse.ArgumentParser(description='更新A股上市公司股票数据')
    parser.add_argument('--delay', type=float, default=0.1,
                       help='更新间隔延迟(秒)，默认0.1秒')
    parser.add_argument('--console', action='store_true',
                       help='使用控制台模式（无GUI）')

    args = parser.parse_args()

    log_file = setup_logging()
    logger = logging.getLogger(__name__)
    logger.info(f"日志文件: {log_file}")

    if args.console:
        return run_with_console(args.delay)
    else:
        run_with_gui(args.delay)
        return 0


if __name__ == '__main__':
    sys.exit(main())
