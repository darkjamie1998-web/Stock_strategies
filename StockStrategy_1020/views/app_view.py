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
import logging
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
                            assets_url_path='assets')
        self.data_service = DataService()
        self.strategy_service = StrategyService()
        self.chart_service = ChartService()
        self.theme = UI_CONFIG.THEME
        
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
            # 股票选择
            self._create_stock_selector(),
            
            # 策略参数
            self._create_strategy_params(),
            
            # 策略说明
            self._create_strategy_guide()
        ], style={'width': '35%', 'padding': '20px', 'flex': '0 0 auto'})
    
    def _create_stock_selector(self) -> html.Div:
        """创建股票选择器"""
        # 初始加载部分股票
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
    
    def _create_result_panel(self) -> html.Div:
        """创建结果展示面板"""
        accent_color = self.theme['accent_color']
        return html.Div([
            # 价格走势图
            html.Div([
                html.H3("📊 价格走势图", className='module-title', 
                       style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                              'marginBottom': '15px', 'paddingBottom': '10px', 
                              'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
                dcc.Graph(id='price-chart', style={'height': '500px', 'backgroundColor': '#1a1a2e'})
            ], className='module-card', style=self._get_card_style()),

            # 交易信号列表
            html.Div([
                html.H3("📈 交易信号", className='module-title', 
                       style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                              'marginBottom': '15px', 'paddingBottom': '10px', 
                              'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
                html.Div(id='signal-list', className='result-box',
                        style={'maxHeight': '600px', 'overflowY': 'auto', 'paddingRight': '10px', 'padding': '15px'})
            ], className='module-card', style=self._get_card_style()),

            # 统计信息
            html.Div([
                html.H3("📊 统计信息", className='module-title', 
                       style={'color': accent_color, 'fontSize': '18px', 'fontWeight': 'bold', 
                              'marginBottom': '15px', 'paddingBottom': '10px', 
                              'paddingLeft': '5%', 'borderBottom': f'2px solid {accent_color}'}),
                html.Div(id='statistics-info', className='result-box', style={'padding': '15px'})
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
                # 返回初始批次
                return self.data_service.get_stock_list(limit=UI_CONFIG.DROPDOWN_BATCH_SIZE)
            # 搜索匹配的股票
            return self.data_service.search_stocks(search_value)

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
            State('signal-window', 'value')
        )
        def update_analysis(n_clicks, stock_code, ma_short, ma_long,
                           volume_threshold, stop_loss, take_profit,
                           pullback, signal_window):
            """更新分析结果"""
            if n_clicks == 0 or not stock_code:
                # 创建默认图表 - 显示"请选择股票"
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
                # 更新策略配置
                self.strategy_service.update_config(
                    ma_short=ma_short,
                    ma_long=ma_long,
                    volume_threshold=volume_threshold / 100,
                    stop_loss_threshold=stop_loss / 100,
                    take_profit_threshold=take_profit / 100,
                    pullback_threshold=pullback / 100,
                    signal_window=signal_window
                )
                
                # 加载股票数据（使用缓存，避免重复加载）
                stock_data = self.data_service.get_stock_data(stock_code)
                if stock_data is None:
                    return {}, html.Div("无法加载股票数据"), html.Div()
                
                # 执行策略分析
                result = self.strategy_service.analyze(stock_data)
                
                # 生成图表
                fig = self.chart_service.create_price_chart(
                    stock_data.df, 
                    result.signals,
                    stock_data.stock_info.display_name
                )
                
                # 生成信号列表
                table_div = self._create_signal_table(result.signals)
                
                # 生成统计信息
                stats = self.chart_service.create_signal_summary(result)
                stats_div = self._create_stats_div(stats)
                
                return fig, table_div, stats_div
                
            except Exception as e:
                logger.error(f"分析失败: {e}")
                return {}, html.Div(f"分析失败: {str(e)}"), html.Div()
    
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
