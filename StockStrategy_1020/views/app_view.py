"""
Dash应用视图
重构后的主应用界面
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
import dash
import logging
from datetime import date
from typing import List, Dict, Any, Optional

from config import UI_CONFIG, TRADING_CONFIG
from services import DataService, StrategyService, ChartService

logger = logging.getLogger(__name__)


class StockStrategyApp:
    """股票策略应用类"""
    
    def __init__(self):
        # 获取项目根目录，确保assets路径正确
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_path = os.path.join(root_dir, 'assets')
        
        self.app = dash.Dash(__name__, 
                            external_stylesheets=['/assets/styles.css'],
                            assets_folder=assets_path,
                            assets_url_path='assets',
                            suppress_callback_exceptions=True)
        self.data_service = DataService()
        self.strategy_service = StrategyService()
        self.chart_service = ChartService()
        self.theme = UI_CONFIG.THEME
        
        self._scanner = None
        self._scan_results = None
        self._scan_running = False
        self._scan_stopped = False
        self._scan_progress_text = ""
        self._scan_progress_current = 0
        self._scan_progress_total = 0
        self._last_scan_results = []
        
        self._setup_layout()
        self._setup_callbacks()
    
    def _setup_layout(self):
        """设置页面布局"""
        self.app.layout = html.Div([
            # 标题
            self._create_header(),
            
            # 主内容区
            html.Div([
                # 左侧控制面板
                self._create_control_panel(),
                
                # 右侧结果展示
                self._create_result_panel()
            ], style={'display': 'flex', 'flexDirection': 'row', 'alignItems': 'flex-start', 'padding': '0 20px 20px 20px'}),
            
            # 隐藏的存储组件
            html.Div(id='update-params-store', style={'display': 'none'}),
            
            dcc.Store(id='scan-state-store', data={'running': False}),
            dcc.Interval(id='scan-poll-interval', interval=500, disabled=True),
            dcc.Download(id='download-scan-csv'),
            
            # 页脚
            html.Footer(
                html.Div([
                    html.P("📈 1020双均线交易策略测试", style={'textAlign': 'center', 'color': '#4a90e2', 'marginBottom': '10px', 'fontSize': '18px'}),
                    html.P("基于历史数据的策略回测与信号分析", style={'textAlign': 'center', 'color': '#a0aec0', 'fontSize': '14px'}),
                    html.P("© 2024 Stock Strategies - All Rights Reserved", style={'textAlign': 'center', 'color': '#718096', 'fontSize': '12px', 'marginTop': '10px'})
                ], style={'padding': '30px', 'backgroundColor': '#16213e', 'marginTop': '30px', 'borderRadius': '10px'})
            )
        ], style={
            'backgroundColor': self.theme['background_color'],
            'minHeight': '100vh',
            'padding': '20px 0'
        })
    
    def _create_header(self) -> html.Div:
        """创建标题区域"""
        return html.Div([
            html.H1("📈 1020双均线交易策略测试",
                   style={'textAlign': 'center', 'color': self.theme['accent_color'],
                          'marginBottom': '10px', 'fontSize': '32px'}),
            html.P("基于历史数据的策略回测与信号分析",
                   style={'textAlign': 'center', 'color': '#a0aec0',
                          'marginBottom': '30px', 'fontSize': '16px'})
        ], style={'padding': '20px 0'})
    
    def _create_control_panel(self) -> html.Div:
        """创建控制面板"""
        return html.Div([
            self._create_stock_selector(),
            self._create_strategy_params(),
            self._create_strategy_guide(),
            self._create_signal_scanner()
        ], style={'width': '35%', 'padding': '20px', 'flex': '0 0 auto'})
    
    def _create_stock_selector(self) -> html.Div:
        """创建股票选择器"""
        initial_stocks = self.data_service.get_stock_list(limit=UI_CONFIG.DROPDOWN_BATCH_SIZE)
        accent_color = self.theme['accent_color']
        
        return html.Div([
            html.H3("🎯 股票选择", className='module-title', 
                   style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                          'marginBottom': '15px', 'paddingBottom': '10px', 
                          'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
            html.Div([
                html.Div([
                    html.Label("选择股票", className='control-label', style={'color': '#a0aec0', 'fontSize': '14px', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.Dropdown(
                        id='stock-selector',
                        options=initial_stocks,
                        value=None,
                        searchable=True,
                        clearable=False,
                        placeholder="搜索或选择股票...",
                        style={
                            'width': '100%',
                            'color': '#000000',
                            'backgroundColor': '#ffffff'
                        }
                    )
                ], className='control-group'),
                html.Div([
                    html.Label("图表起始日期", className='control-label', style={'color': '#a0aec0', 'fontSize': '14px', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.DatePickerSingle(
                        id='chart-start-date',
                        date=None,
                        placeholder='选择起始日期',
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], className='control-group'),
                html.Div([
                    html.Label("图表结束日期", className='control-label', style={'color': '#a0aec0', 'fontSize': '14px', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.DatePickerSingle(
                        id='chart-end-date',
                        date=None,
                        placeholder='选择结束日期',
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], className='control-group'),
                html.Button('🔍 生成信号', id='generate-signals', n_clicks=0,
                           className='btn-primary',
                           style={'marginTop': '20px', 'width': '100%'})
            ], style={'padding': '15px'})
        ], className='module-card', style=self._get_card_style())
    
    def _create_strategy_params(self) -> html.Div:
        """创建策略参数面板"""
        params = [
            ('ma-short', '短期均线（攻击线）', TRADING_CONFIG.MA_SHORT, 5, 20),
            ('ma-long', '长期均线（生命线）', TRADING_CONFIG.MA_LONG, 10, 60),
            ('volume-threshold', '放量阈值（%）', int(TRADING_CONFIG.VOLUME_THRESHOLD * 100), 5, 100),
            ('stop-loss-threshold', '止损阈值（%）', int(TRADING_CONFIG.STOP_LOSS_THRESHOLD * 100), 1, 20),
            ('take-profit-threshold', '止盈阈值（%）', int(TRADING_CONFIG.TAKE_PROFIT_THRESHOLD * 100), 1, 50),
            ('pullback-threshold', '回踩/站上阈值（%）', int(TRADING_CONFIG.PULLBACK_THRESHOLD * 100), 1, 10),
            ('signal-window', '信号屏蔽窗口（天）', TRADING_CONFIG.SIGNAL_WINDOW, 1, 30),
        ]
        
        inputs = []
        for id_, label, value, min_, max_ in params:
            inputs.append(html.Div([
                html.Label(label, className='control-label', style={'color': '#a0aec0', 'fontSize': '14px', 'marginBottom': '8px', 'display': 'block'}),
                dcc.Input(
                    id=id_,
                    type='number',
                    value=value,
                    min=min_,
                    max=max_,
                    step=1,
                    style=self._get_input_style()
                )
            ], className='control-group'))
        
        inputs.append(html.P(
            "修改参数后点击'生成信号'按钮更新图表",
            style={'color': '#a0aec0', 'fontSize': '12px', 
                   'marginTop': '15px', 'fontStyle': 'italic'}
        ))
        
        accent_color = self.theme['accent_color']
        return html.Div([
            html.H3("⚙️ 策略参数", className='module-title', 
                   style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                          'marginBottom': '15px', 'paddingBottom': '10px', 
                          'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
            html.Div(inputs, style={'padding': '15px'})
        ], className='module-card', style=self._get_card_style())
    
    def _create_strategy_guide(self) -> html.Div:
        """创建策略说明"""
        accent_color = self.theme['accent_color']
        return html.Div([
            html.H3("📖 策略说明", className='module-title', 
                   style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                          'marginBottom': '15px', 'paddingBottom': '10px', 
                          'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
            html.Div([
                html.P("🔴 双龙出水（买入）", style={'color': '#f56565', 'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                html.P("满足以下任一条件触发：", style={'color': '#a0aec0', 'fontSize': '12px', 'marginBottom': '5px'}),
                html.P("条件1：首次放量站上双均线（收盘价>开盘价，收盘价>均线，偏差≤阈值）", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '3px', 'marginLeft': '15px'}),
                html.P("条件2：跳空且放量站上双均线", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '3px', 'marginLeft': '15px'}),
                html.P("条件3：空头转多头排列且放量", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '10px', 'marginLeft': '15px'}),

                html.P("🟡 潜龙入渊（加码）", style={'color': '#f6ad55', 'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                html.P("首次回踩10日均线（均线多头排列时，收盘价<开盘价，收盘价>均线，偏差≤阈值）", style={'color': '#a0aec0', 'fontSize': '12px', 'marginBottom': '10px'}),

                html.P("🟡 见龙在田（加码）", style={'color': '#f6ad55', 'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                html.P("首次回踩20日均线（均线多头排列时，收盘价<开盘价，收盘价>均线，偏差≤阈值）", style={'color': '#a0aec0', 'fontSize': '12px', 'marginBottom': '10px'}),

                html.P("🟢 龙战于野（离场）", style={'color': '#48bb78', 'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                html.P("满足以下任一条件触发：", style={'color': '#a0aec0', 'fontSize': '12px', 'marginBottom': '5px'}),
                html.P("条件1：连续2个交易日收盘价低于20日均线", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '3px', 'marginLeft': '15px'}),
                html.P("条件2：单日跌幅超过止损阈值并有效破位（收盘价低于20日均线止损阈值以上）", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '10px', 'marginLeft': '15px'}),

                html.P("🟣 收获果实（止盈）", style={'color': '#9f7aea', 'fontSize': '14px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                html.P("当日收盘价较买入或加码信号涨幅超过止盈阈值", style={'color': '#a0aec0', 'fontSize': '12px', 'marginBottom': '10px'}),

                html.P("⚠️ 约束条件：", style={'color': '#63b3ed', 'fontSize': '13px', 'marginBottom': '5px', 'fontWeight': 'bold'}),
                html.P("1. 买入信号后无离场信号不产生新买入信号", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '3px', 'marginLeft': '15px'}),
                html.P("2. 离场信号后无买入信号不产生新离场信号", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '3px', 'marginLeft': '15px'}),
                html.P("3. 连续5日空头排列后不观测加码和买入信号", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '3px', 'marginLeft': '15px'}),
                html.P("4. 信号屏蔽窗口内不考虑离场信号", style={'color': '#a0aec0', 'fontSize': '11px', 'marginBottom': '0px', 'marginLeft': '15px'}),
            ], style={'padding': '15px'})
        ], className='module-card', style=self._get_card_style())
    
    def _create_signal_scanner(self) -> html.Div:
        """创建信号扫描面板"""
        accent_color = self.theme['accent_color']
        return html.Div([
            html.H3("🔎 信号扫描", className='module-title', 
                   style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                          'marginBottom': '15px', 'paddingBottom': '10px', 
                          'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
            html.Div([
                html.P("查询指定时间段内触发信号的所有股票",
                       style={'color': '#a0aec0', 'fontSize': '12px', 'marginBottom': '15px'}),
                html.Div([
                    html.Label("扫描起始日期", className='control-label', style={'color': '#a0aec0', 'fontSize': '14px', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.DatePickerSingle(
                        id='scan-start-date',
                        date=date.today(),
                        placeholder='选择起始日期',
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], className='control-group'),
                html.Div([
                    html.Label("扫描结束日期", className='control-label', style={'color': '#a0aec0', 'fontSize': '14px', 'marginBottom': '8px', 'display': 'block'}),
                    dcc.DatePickerSingle(
                        id='scan-end-date',
                        date=date.today(),
                        placeholder='选择结束日期',
                        display_format='YYYY-MM-DD',
                        style={'width': '100%'}
                    )
                ], className='control-group'),
                html.Button('🔍 开始扫描', id='start-scan', n_clicks=0,
                           className='btn-primary',
                           style={'marginTop': '20px', 'width': '100%'}),
                html.Button('⏹ 终止扫描', id='stop-scan', n_clicks=0,
                           className='btn-danger',
                           style={'marginTop': '10px', 'width': '100%', 'display': 'none'}),
                html.Div(id='scan-progress', style={'marginTop': '10px', 'textAlign': 'center', 'color': '#a0aec0', 'fontSize': '13px'})
            ], style={'padding': '15px'})
        ], className='module-card', style=self._get_card_style())
    
    def _create_result_panel(self) -> html.Div:
        """创建结果展示面板"""
        accent_color = self.theme['accent_color']
        return html.Div([
            html.Div([
                html.H3("📊 价格走势图", className='module-title', 
                       style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                              'marginBottom': '15px', 'paddingBottom': '10px', 
                              'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
                dcc.Graph(id='price-chart', style={'height': '500px', 'backgroundColor': '#1a1a2e'})
            ], className='module-card', style=self._get_card_style()),

            html.Div([
                html.H3("📈 交易信号", className='module-title', 
                       style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                              'marginBottom': '15px', 'paddingBottom': '10px', 
                              'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
                html.Div(id='signal-list', className='result-box',
                        style={'maxHeight': '600px', 'overflowY': 'auto', 'paddingRight': '10px', 'padding': '15px'})
            ], className='module-card', style=self._get_card_style()),

            html.Div([
                html.H3("📊 统计信息", className='module-title', 
                       style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                              'marginBottom': '15px', 'paddingBottom': '10px', 
                              'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
                html.Div(id='statistics-info', className='result-box', style={'padding': '15px'})
            ], className='module-card', style=self._get_card_style()),

            html.Div([
                html.H3("🔎 扫描结果", className='module-title', 
                       style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                              'marginBottom': '15px', 'paddingBottom': '10px', 
                              'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
                html.Div(id='scan-results', className='result-box',
                         style={'maxHeight': '600px', 'overflowY': 'auto', 'padding': '15px'})
            ], className='module-card', style=self._get_card_style())
        ], style={'width': '60%', 'padding': '20px', 'flex': '1 1 auto'})
    
    def _get_card_style(self) -> Dict:
        """获取卡片样式"""
        return {
            'backgroundColor': self.theme['card_background'],
            'borderRadius': '8px',
            'marginBottom': '20px',
            'border': f"1px solid {self.theme['border_color']}"
        }
    
    def _get_input_style(self) -> Dict:
        """获取输入框样式"""
        return {
            'width': '100%',
            'height': '50px',
            'padding': '10px',
            'backgroundColor': '#1a1a2e',
            'color': '#e0e0e0',
            'border': f"1px solid {self.theme['border_color']}",
            'borderRadius': '4px'
        }
    
    def _setup_callbacks(self):
        """设置回调函数"""

        @self.app.callback(
            Output('stock-selector', 'options'),
            Input('stock-selector', 'search_value')
        )
        def update_stock_options(search_value):
            """根据搜索值动态更新股票选项"""
            if not search_value or len(search_value) < 1:
                return self.data_service.get_stock_list(limit=UI_CONFIG.DROPDOWN_BATCH_SIZE)
            return self.data_service.search_stocks(search_value)

        @self.app.callback(
            Output('chart-start-date', 'date'),
            Output('chart-end-date', 'date'),
            Input('stock-selector', 'value')
        )
        def update_chart_date_range(stock_code):
            """选择股票后自动填充图表日期范围"""
            if not stock_code:
                raise PreventUpdate
            stock_data = self.data_service.get_stock_data(stock_code)
            if stock_data is None:
                raise PreventUpdate
            start = stock_data.start_date.strftime('%Y-%m-%d')
            end = stock_data.end_date.strftime('%Y-%m-%d')
            return start, end

        @self.app.callback(
            Output('price-chart', 'figure'),
            Output('signal-list', 'children'),
            Output('statistics-info', 'children'),
            Input('generate-signals', 'n_clicks'),
            State('stock-selector', 'value'),
            State('ma-short', 'value'),
            State('ma-long', 'value'),
            State('volume-threshold', 'value'),
            State('stop-loss-threshold', 'value'),
            State('take-profit-threshold', 'value'),
            State('pullback-threshold', 'value'),
            State('signal-window', 'value'),
            State('chart-start-date', 'date'),
            State('chart-end-date', 'date')
        )
        def update_analysis(n_clicks, stock_code, ma_short, ma_long,
                           volume_threshold, stop_loss, take_profit,
                           pullback, signal_window, chart_start_date, chart_end_date):
            """更新分析结果"""
            if n_clicks == 0 or not stock_code:
                import plotly.graph_objects as go
                fig = go.Figure()
                fig.add_annotation(
                    text="📊 请选择股票并点击'生成信号'按钮",
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                    showarrow=False,
                    font=dict(size=20, color="#4a90e2")
                )
                fig.update_layout(
                    plot_bgcolor='#1a1a2e',
                    paper_bgcolor='#1a1a2e',
                    xaxis=dict(showgrid=False, showticklabels=False, visible=False),
                    yaxis=dict(showgrid=False, showticklabels=False, visible=False),
                    margin=dict(l=0, r=0, t=0, b=0),
                    height=500
                )
                default_msg = html.Div([
                    html.P("🔍 请选择股票并点击'生成信号'按钮",
                           style={'textAlign': 'center', 'color': '#a0aec0'})
                ])
                return fig, default_msg, default_msg
            
            try:
                self.strategy_service.update_config(
                    ma_short=ma_short,
                    ma_long=ma_long,
                    volume_threshold=volume_threshold / 100,
                    stop_loss_threshold=stop_loss / 100,
                    take_profit_threshold=take_profit / 100,
                    pullback_threshold=pullback / 100,
                    signal_window=signal_window
                )
                
                stock_data = self.data_service.get_stock_data(stock_code)
                if stock_data is None:
                    return {}, html.Div("无法加载股票数据"), html.Div()
                
                result = self.strategy_service.analyze(stock_data)
                
                fig = self.chart_service.create_price_chart(
                    stock_data.df, 
                    result.signals,
                    stock_data.stock_info.display_name,
                    start_date=chart_start_date,
                    end_date=chart_end_date
                )
                
                table_div = self._create_signal_table(result.signals)
                
                stats = self.chart_service.create_signal_summary(result)
                stats_div = self._create_stats_div(stats)
                
                return fig, table_div, stats_div
                
            except Exception as e:
                logger.error(f"分析失败: {e}")
                return {}, html.Div(f"分析失败: {str(e)}"), html.Div()

        @self.app.callback(
            Output('scan-state-store', 'data'),
            Output('scan-poll-interval', 'disabled'),
            Output('start-scan', 'style'),
            Output('stop-scan', 'style'),
            Output('scan-results', 'children'),
            Output('scan-progress', 'children'),
            Input('start-scan', 'n_clicks'),
            State('scan-start-date', 'date'),
            State('scan-end-date', 'date'),
            prevent_initial_call=True
        )
        def start_signal_scan(n_clicks, start_date, end_date):
            if not start_date or not end_date:
                raise PreventUpdate

            import threading
            from services.signal_scanner import SignalScanner

            self._scanner = SignalScanner()
            self._scan_results = None
            self._scan_running = True
            self._scan_stopped = False
            self._scan_progress_text = "正在扫描..."
            self._scan_progress_current = 0
            self._scan_progress_total = 0

            def on_progress(current, total, code, name):
                self._scan_progress_current = current
                self._scan_progress_total = total

            def scan_thread():
                try:
                    self._scan_results = self._scanner.scan_all_stocks(
                        start_date, end_date, progress_callback=on_progress
                    )
                except Exception as e:
                    logger.error(f"扫描出错: {e}")
                    self._scan_results = []
                finally:
                    self._scan_running = False

            thread = threading.Thread(target=scan_thread, daemon=True)
            thread.start()

            start_style = {'marginTop': '20px', 'width': '100%', 'display': 'none'}
            stop_style = {'marginTop': '10px', 'width': '100%', 'display': 'block'}

            loading_div = html.Div([
                html.Div(style={
                    'width': '40px', 'height': '40px',
                    'border': '4px solid #2d3748',
                    'borderTop': '4px solid #4a90e2',
                    'borderRadius': '50%',
                    'animation': 'spin 1s linear infinite',
                    'margin': '20px auto'
                }),
                html.P("正在扫描中，请稍候...", style={'textAlign': 'center', 'color': '#a0aec0', 'fontSize': '14px'})
            ])

            return {'running': True}, False, start_style, stop_style, loading_div, "正在扫描..."

        @self.app.callback(
            Output('scan-results', 'children', allow_duplicate=True),
            Output('scan-progress', 'children', allow_duplicate=True),
            Output('scan-poll-interval', 'disabled', allow_duplicate=True),
            Output('start-scan', 'style', allow_duplicate=True),
            Output('stop-scan', 'style', allow_duplicate=True),
            Input('scan-poll-interval', 'n_intervals'),
            State('scan-state-store', 'data'),
            prevent_initial_call=True
        )
        def poll_scan_results(n_intervals, store_data):
            if not store_data or not store_data.get('running'):
                raise PreventUpdate

            if self._scan_running:
                dots = '.' * ((n_intervals % 3) + 1)
                current = self._scan_progress_current
                total = self._scan_progress_total
                pct = round(current / total * 100, 1) if total > 0 else 0

                loading_div = html.Div([
                    html.Div(style={
                        'width': '40px', 'height': '40px',
                        'border': '4px solid #2d3748',
                        'borderTop': '4px solid #4a90e2',
                        'borderRadius': '50%',
                        'animation': 'spin 1s linear infinite',
                        'margin': '20px auto'
                    }),
                    html.P(f"正在扫描中，请稍候{dots}", style={'textAlign': 'center', 'color': '#a0aec0', 'fontSize': '14px'}),
                    html.Div(style={
                        'width': '80%', 'height': '8px',
                        'backgroundColor': '#2d3748',
                        'borderRadius': '4px',
                        'margin': '15px auto',
                        'overflow': 'hidden'
                    }, children=[
                        html.Div(style={
                            'width': f'{pct}%',
                            'height': '100%',
                            'backgroundColor': '#4a90e2',
                            'borderRadius': '4px',
                            'transition': 'width 0.3s ease'
                        })
                    ]),
                    html.P(f"{current} / {total} ({pct}%)",
                           style={'textAlign': 'center', 'color': '#718096', 'fontSize': '12px'})
                ])
                return loading_div, f"正在扫描... {current}/{total}", dash.no_update, dash.no_update, dash.no_update

            results = self._scan_results or []
            was_stopped = self._scan_stopped
            self._scanner = None
            self._scan_results = None
            self._scan_stopped = False
            self._last_scan_results = results

            start_style = {'marginTop': '20px', 'width': '100%', 'display': 'block'}
            stop_style = {'marginTop': '10px', 'width': '100%', 'display': 'none'}

            if not results:
                if was_stopped:
                    msg = html.Div([
                        html.P("⏹ 扫描已终止，未发现任何信号",
                               style={'textAlign': 'center', 'color': '#f6ad55', 'padding': '20px', 'fontSize': '14px'})
                    ])
                    return msg, "扫描已终止（无信号）", True, start_style, stop_style
                else:
                    msg = html.Div([
                        html.P("未发现任何信号",
                               style={'textAlign': 'center', 'color': '#a0aec0', 'padding': '20px', 'fontSize': '14px'})
                    ])
                    return msg, "扫描完成（无信号）", True, start_style, stop_style

            total_stocks = len(results)
            total_signals = sum(r.total_signals for r in results)
            buy_total = sum(r.buy_count for r in results)
            add_total = sum(r.add_count for r in results)
            exit_total = sum(r.exit_count for r in results)
            profit_total = sum(r.profit_count for r in results)

            status_color = '#f6ad55' if was_stopped else '#48bb78'
            status_text = '⏹ 扫描已终止（部分结果）' if was_stopped else '✅ 扫描完成'

            summary = html.Div([
                html.Div([
                    html.Span(status_text, style={'color': status_color, 'fontWeight': 'bold', 'fontSize': '14px', 'marginRight': '15px'}),
                    html.Span(f"共 {total_stocks} 只股票触发信号", style={'color': '#4a90e2', 'fontWeight': 'bold', 'fontSize': '14px'}),
                    html.Span(f" | 总信号数: {total_signals}", style={'color': '#a0aec0', 'fontSize': '13px', 'marginLeft': '15px'}),
                    html.Span(f" | 买入: {buy_total}", style={'color': '#f56565', 'fontSize': '13px', 'marginLeft': '10px'}),
                    html.Span(f" | 加码: {add_total}", style={'color': '#f6ad55', 'fontSize': '13px', 'marginLeft': '10px'}),
                    html.Span(f" | 离场: {exit_total}", style={'color': '#48bb78', 'fontSize': '13px', 'marginLeft': '10px'}),
                    html.Span(f" | 止盈: {profit_total}", style={'color': '#9f7aea', 'fontSize': '13px', 'marginLeft': '10px'}),
                ], style={'marginBottom': '15px', 'paddingBottom': '10px', 'borderBottom': '1px solid #2d3748'})
            ])

            table_header = html.Div([
                html.Div("股票代码", style={'flex': '1', 'fontWeight': 'bold', 'color': '#4a90e2', 'fontSize': '13px'}),
                html.Div("股票名称", style={'flex': '1.5', 'fontWeight': 'bold', 'color': '#4a90e2', 'fontSize': '13px'}),
                html.Div("买入", style={'flex': '0.6', 'fontWeight': 'bold', 'color': '#f56565', 'fontSize': '13px', 'textAlign': 'center'}),
                html.Div("加码", style={'flex': '0.6', 'fontWeight': 'bold', 'color': '#f6ad55', 'fontSize': '13px', 'textAlign': 'center'}),
                html.Div("离场", style={'flex': '0.6', 'fontWeight': 'bold', 'color': '#48bb78', 'fontSize': '13px', 'textAlign': 'center'}),
                html.Div("止盈", style={'flex': '0.6', 'fontWeight': 'bold', 'color': '#9f7aea', 'fontSize': '13px', 'textAlign': 'center'}),
                html.Div("总计", style={'flex': '0.6', 'fontWeight': 'bold', 'color': '#e0e0e0', 'fontSize': '13px', 'textAlign': 'center'}),
            ], style={'display': 'flex', 'padding': '8px 0', 'borderBottom': '1px solid #2d3748', 'marginBottom': '5px'})

            rows = []
            for r in results:
                bg = '#1e2d4a' if results.index(r) % 2 == 0 else 'transparent'
                rows.append(html.Div([
                    html.Div(r.stock_code, style={'flex': '1', 'fontSize': '12px', 'color': '#e0e0e0'}),
                    html.Div(r.stock_name, style={'flex': '1.5', 'fontSize': '12px', 'color': '#a0aec0'}),
                    html.Div(str(r.buy_count), style={'flex': '0.6', 'fontSize': '12px', 'color': '#f56565', 'textAlign': 'center'}),
                    html.Div(str(r.add_count), style={'flex': '0.6', 'fontSize': '12px', 'color': '#f6ad55', 'textAlign': 'center'}),
                    html.Div(str(r.exit_count), style={'flex': '0.6', 'fontSize': '12px', 'color': '#48bb78', 'textAlign': 'center'}),
                    html.Div(str(r.profit_count), style={'flex': '0.6', 'fontSize': '12px', 'color': '#9f7aea', 'textAlign': 'center'}),
                    html.Div(str(r.total_signals), style={'flex': '0.6', 'fontSize': '12px', 'color': '#e0e0e0', 'textAlign': 'center', 'fontWeight': 'bold'}),
                ], style={'display': 'flex', 'padding': '6px 0', 'backgroundColor': bg, 'borderRadius': '4px'}))

            progress_text = "扫描已终止（部分结果）" if was_stopped else "扫描完成"

            export_btn = html.Button('📥 导出CSV', id='export-scan-csv', n_clicks=0,
                                     style={
                                         'marginTop': '10px', 'padding': '8px 20px',
                                         'backgroundColor': '#48bb78', 'color': '#fff',
                                         'border': 'none', 'borderRadius': '4px',
                                         'cursor': 'pointer', 'fontSize': '13px',
                                         'fontWeight': 'bold'
                                     })

            return html.Div([summary, export_btn, table_header] + rows), progress_text, True, start_style, stop_style

        @self.app.callback(
            Output('scan-state-store', 'data', allow_duplicate=True),
            Input('stop-scan', 'n_clicks'),
            prevent_initial_call=True
        )
        def stop_signal_scan(n_clicks):
            if self._scanner:
                self._scanner.request_stop()
                self._scan_stopped = True
                self._scan_running = False
            return {'running': False}

        @self.app.callback(
            Output('download-scan-csv', 'data'),
            Input('export-scan-csv', 'n_clicks'),
            prevent_initial_call=True
        )
        def export_scan_csv(n_clicks):
            if not self._last_scan_results:
                raise PreventUpdate

            import pandas as pd
            from io import StringIO

            rows = []
            for r in self._last_scan_results:
                rows.append({
                    '股票代码': r.stock_code,
                    '股票名称': r.stock_name,
                    '买入信号': r.buy_count,
                    '加码信号': r.add_count,
                    '离场信号': r.exit_count,
                    '止盈信号': r.profit_count,
                    '总信号数': r.total_signals
                })

            df = pd.DataFrame(rows)
            return dcc.send_data_frame(df.to_csv, "scan_results.csv", index=False, encoding='utf-8-sig')

    def _create_stats_div(self, stats: Dict) -> html.Div:
        """创建统计信息组件"""
        return html.Div([
            html.Div([
                html.P("总信号数", style={'fontSize': '14px', 'color': '#a0aec0', 'marginBottom': '5px'}),
                html.P(f"{stats['total_signals']}", style={'fontSize': '24px', 'fontWeight': 'bold', 'color': '#4a90e2', 'marginBottom': '10px'}),
            ], style={'textAlign': 'center', 'marginBottom': '15px'}),
            html.Div([
                html.Div([
                    html.P("买入信号", style={'fontSize': '12px', 'color': '#a0aec0', 'marginBottom': '5px'}),
                    html.P(f"{stats['buy_count']}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#f56565'}),
                ], style={'textAlign': 'center', 'flex': '1'}),
                html.Div([
                    html.P("加码信号", style={'fontSize': '12px', 'color': '#a0aec0', 'marginBottom': '5px'}),
                    html.P(f"{stats['add_count']}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#f6ad55'}),
                ], style={'textAlign': 'center', 'flex': '1'}),
                html.Div([
                    html.P("止盈信号", style={'fontSize': '12px', 'color': '#a0aec0', 'marginBottom': '5px'}),
                    html.P(f"{stats['profit_count']}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#9f7aea'}),
                ], style={'textAlign': 'center', 'flex': '1'}),
                html.Div([
                    html.P("离场信号", style={'fontSize': '12px', 'color': '#a0aec0', 'marginBottom': '5px'}),
                    html.P(f"{stats['exit_count']}", style={'fontSize': '20px', 'fontWeight': 'bold', 'color': '#48bb78'}),
                ], style={'textAlign': 'center', 'flex': '1'}),
            ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginBottom': '15px'}),
        ])
    
    def _create_signal_table(self, signals: List) -> html.Div:
        """创建信号列表"""
        from models import TradingSignalType

        if not signals:
            return html.Div([html.P("未生成交易信号", style={'textAlign': 'center', 'color': '#a0aec0'})])

        signal_list_items = []
        for signal in signals:
            # 根据信号类型设置样式类
            if signal.signal_type == TradingSignalType.DOUBLE_DRAGON_EMERGENCE:
                signal_class = 'signal-buy'
            elif signal.signal_type in [TradingSignalType.HIDDEN_DRAGON_DESCENT, TradingSignalType.DRAGON_IN_FIELD]:
                signal_class = 'signal-add'
            elif signal.signal_type == TradingSignalType.TAKE_PROFIT:
                signal_class = 'signal-take-profit'
            else:
                signal_class = 'signal-sell'

            # 根据信号类型设置名称颜色
            name_color_map = {
                TradingSignalType.DOUBLE_DRAGON_EMERGENCE: '#f56565',
                TradingSignalType.HIDDEN_DRAGON_DESCENT: '#f6ad55',
                TradingSignalType.DRAGON_IN_FIELD: '#f6ad55',
                TradingSignalType.TAKE_PROFIT: '#9f7aea',
                TradingSignalType.DRAGON_BATTLE: '#48bb78'
            }
            name_color = name_color_map.get(signal.signal_type, '#e0e0e0')

            # 根据信号类型获取对应的策略说明文字
            condition_descriptions = {
                TradingSignalType.DOUBLE_DRAGON_EMERGENCE: [
                    "首次放量站上双均线（收盘价>开盘价，收盘价>均线，偏差≤阈值）",
                    "跳空且放量站上双均线",
                    "空头转多头排列且放量"
                ],
                TradingSignalType.HIDDEN_DRAGON_DESCENT: [
                    "首次回踩10日均线（均线多头排列时，收盘价<开盘价，收盘价>均线，偏差≤阈值）"
                ],
                TradingSignalType.DRAGON_IN_FIELD: [
                    "首次回踩20日均线（均线多头排列时，收盘价<开盘价，收盘价>均线，偏差≤阈值）"
                ],
                TradingSignalType.DRAGON_BATTLE: [
                    "连续2个交易日收盘价低于20日均线",
                    "单日跌幅超过止损阈值并有效破位（收盘价低于20日均线止损阈值以上）"
                ],
                TradingSignalType.TAKE_PROFIT: [
                    "当日收盘价较买入或加码信号涨幅超过止盈阈值"
                ]
            }
            
            # 获取对应信号类型的描述列表，根据condition_id选择对应的描述
            descriptions = condition_descriptions.get(signal.signal_type, [])
            if descriptions and signal.condition_id > 0 and signal.condition_id <= len(descriptions):
                condition_text = descriptions[signal.condition_id - 1]
            elif descriptions:
                condition_text = descriptions[0]
            else:
                condition_text = ''

            # 根据信号类型设置操作描述
            action_descriptions = {
                TradingSignalType.DOUBLE_DRAGON_EMERGENCE: "初始建仓，建立基础仓位",
                TradingSignalType.HIDDEN_DRAGON_DESCENT: "增加持仓，提升风险暴露",
                TradingSignalType.DRAGON_IN_FIELD: "增加持仓，提升风险暴露",
                TradingSignalType.DRAGON_BATTLE: "建议离场，控制风险暴露",
                TradingSignalType.TAKE_PROFIT: "建议止盈，锁定利润"
            }
            action_desc = action_descriptions.get(signal.signal_type, signal.action)

            signal_list_items.append(
                html.Div([
                    # 第一行：信号名称和日期
                    html.Div([
                        html.Span(f"{signal.signal_name}", 
                                 style={'fontWeight': 'bold', 'fontSize': '16px', 'color': name_color}),
                        html.Span(f"{signal.timestamp.strftime('%Y-%m-%d')}", 
                                 style={'color': '#a0aec0', 'fontSize': '14px'}),
                    ], style={'display': 'flex', 'justifyContent': 'space-between', 'marginBottom': '10px'}),
                    # 第二行：条件描述（与操作之间无空行）
                    html.P(condition_text,
                          style={'color': '#a0aec0', 'fontSize': '13px', 'marginBottom': '5px', 'lineHeight': '1.5'}),
                    # 第三行：操作描述
                    html.P([
                        html.Span("操作：", style={'color': '#a0aec0', 'fontSize': '13px'}),
                        html.Span(action_desc, style={'color': '#4a90e2', 'fontSize': '13px'})
                    ], style={'marginBottom': '0px'})
                ], className=f'signal-item {signal_class}')
            )

        return html.Div(signal_list_items)
    
    def run(self, debug: bool = True, host: str = '127.0.0.1', port: int = 8050):
        """运行应用"""
        self.app.run(debug=debug, host=host, port=port)


def create_app() -> StockStrategyApp:
    """创建应用实例"""
    return StockStrategyApp()
