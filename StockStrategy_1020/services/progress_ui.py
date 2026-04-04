"""
进度条GUI界面
用于显示数据更新进度并提供终止功能
"""
import tkinter as tk
from tkinter import ttk
import threading
import queue
from typing import Callable, Optional
from datetime import datetime


class ProgressWindow:
    """进度条窗口"""
    
    def __init__(self, title: str = "数据更新进度", total: int = 0):
        self.total = total
        self.current = 0
        self.success_count = 0
        self.failed_count = 0
        self._stop_flag = False
        self._closed = False
        self._queue = queue.Queue()
        
        self._create_window(title)
        
    def _create_window(self, title: str):
        self.root = tk.Tk()
        self.root.title(title)
        self.root.geometry("500x280")
        self.root.resizable(False, False)
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        
        self._setup_ui()
        
        self.root.after(100, self._process_queue)
    
    def _setup_ui(self):
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(
            main_frame, 
            text="股票数据更新", 
            font=('Microsoft YaHei', 14, 'bold')
        )
        title_label.pack(pady=(0, 10))
        
        self.progress_var = tk.DoubleVar(value=0)
        self.progress_bar = ttk.Progressbar(
            main_frame, 
            variable=self.progress_var,
            maximum=100,
            length=460,
            mode='determinate'
        )
        self.progress_bar.pack(pady=5)
        
        self.percent_label = ttk.Label(
            main_frame,
            text="0.0%",
            font=('Microsoft YaHei', 11)
        )
        self.percent_label.pack()
        
        self.current_stock_label = ttk.Label(
            main_frame,
            text="准备开始...",
            font=('Microsoft YaHei', 10)
        )
        self.current_stock_label.pack(pady=5)
        
        stats_frame = ttk.Frame(main_frame)
        stats_frame.pack(pady=10)
        
        self.success_label = ttk.Label(
            stats_frame,
            text="成功: 0",
            font=('Microsoft YaHei', 10),
            foreground='green'
        )
        self.success_label.pack(side=tk.LEFT, padx=20)
        
        self.failed_label = ttk.Label(
            stats_frame,
            text="失败: 0",
            font=('Microsoft YaHei', 10),
            foreground='red'
        )
        self.failed_label.pack(side=tk.LEFT, padx=20)
        
        self.count_label = ttk.Label(
            stats_frame,
            text="进度: 0/0",
            font=('Microsoft YaHei', 10)
        )
        self.count_label.pack(side=tk.LEFT, padx=20)
        
        self.stop_button = ttk.Button(
            main_frame,
            text="终止更新",
            command=self._on_stop,
            width=15
        )
        self.stop_button.pack(pady=15)
        
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=('Microsoft YaHei', 9),
            foreground='gray'
        )
        self.status_label.pack()
    
    def _process_queue(self):
        if self._closed:
            return
            
        try:
            while True:
                msg = self._queue.get_nowait()
                self._handle_message(msg)
        except queue.Empty:
            pass
        
        self.root.after(100, self._process_queue)
    
    def _handle_message(self, msg):
        msg_type = msg.get('type')
        
        if msg_type == 'progress':
            self.current = msg.get('current', 0)
            self.total = msg.get('total', 1)
            stock_code = msg.get('code', '')
            stock_name = msg.get('name', '')
            
            percent = (self.current / self.total * 100) if self.total > 0 else 0
            self.progress_var.set(percent)
            self.percent_label.config(text=f"{percent:.1f}%")
            self.current_stock_label.config(text=f"正在更新: {stock_code} {stock_name}")
            self.count_label.config(text=f"进度: {self.current}/{self.total}")
            
        elif msg_type == 'success':
            self.success_count = msg.get('count', 0)
            self.success_label.config(text=f"成功: {self.success_count}")
            
        elif msg_type == 'failed':
            self.failed_count = msg.get('count', 0)
            self.failed_label.config(text=f"失败: {self.failed_count}")
            
        elif msg_type == 'complete':
            self.current_stock_label.config(text="更新完成！")
            self.stop_button.config(text="关闭", command=self._on_close, state=tk.NORMAL)
            result = msg.get('result', {})
            self.status_label.config(
                text=f"总计: {result.get('total', 0)} 只，"
                     f"成功: {result.get('success', 0)} 只，"
                     f"失败: {result.get('failed', 0)} 只"
            )
            
        elif msg_type == 'error':
            self.current_stock_label.config(text=f"错误: {msg.get('message', '')}")
            self.stop_button.config(text="关闭", command=self._on_close, state=tk.NORMAL)
    
    def _on_stop(self):
        self._stop_flag = True
        self.current_stock_label.config(text="正在停止...")
        self.stop_button.config(state=tk.DISABLED)
    
    def _on_close(self):
        self._stop_flag = True
        self._closed = True
        self.root.destroy()
    
    def update_progress(self, current: int, total: int, code: str, name: str):
        self._queue.put({
            'type': 'progress',
            'current': current,
            'total': total,
            'code': code,
            'name': name
        })
    
    def update_success(self, count: int):
        self._queue.put({'type': 'success', 'count': count})
    
    def update_failed(self, count: int):
        self._queue.put({'type': 'failed', 'count': count})
    
    def show_complete(self, result: dict):
        self._queue.put({'type': 'complete', 'result': result})
    
    def show_error(self, message: str):
        self._queue.put({'type': 'error', 'message': message})
    
    def should_stop(self) -> bool:
        return self._stop_flag
    
    def run(self):
        self.root.mainloop()
    
    def start_mainloop(self):
        self.root.mainloop()


class ProgressController:
    """进度控制器，用于在后台线程中更新GUI"""
    
    def __init__(self, total: int = 0):
        self.window = ProgressWindow(total=total)
        self._thread: Optional[threading.Thread] = None
    
    def start(self):
        self._thread = threading.Thread(target=self.window.run, daemon=True)
        self._thread.start()
        import time
        time.sleep(0.2)
    
    def update_progress(self, current: int, total: int, code: str, name: str):
        self.window.update_progress(current, total, code, name)
    
    def update_success(self, count: int):
        self.window.update_success(count)
    
    def update_failed(self, count: int):
        self.window.update_failed(count)
    
    def show_complete(self, result: dict):
        self.window.show_complete(result)
    
    def show_error(self, message: str):
        self.window.show_error(message)
    
    def should_stop(self) -> bool:
        return self.window.should_stop()
    
    def wait(self):
        if self._thread and self._thread.is_alive():
            self._thread.join()
