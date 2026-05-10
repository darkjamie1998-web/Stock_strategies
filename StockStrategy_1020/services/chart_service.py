"""
图表服务模块
负责生成各种可视化图表
"""
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from typing import List, Dict, Any, Optional
import logging

from config import UI_CONFIG
from models import TradingSignal, SignalResult

logger = logging.getLogger(__name__)


class ChartService:
    """图表服务类"""
    
    def __init__(self):
        self.theme = UI_CONFIG.THEME
        self.chart_height = UI_CONFIG.CHART_HEIGHT
    
    def create_price_chart(self, df: pd.DataFrame, signals: List[TradingSignal],
                          stock_name: str = "",
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None) -> go.Figure:
        """创建价格走势图"""
        if start_date is not None:
            start_dt = pd.Timestamp(start_date)
            df = df[df['date'] >= start_dt].copy()
            signals = [s for s in signals if s.timestamp >= start_dt]
        if end_date is not None:
            end_dt = pd.Timestamp(end_date)
            df = df[df['date'] <= end_dt].copy()
            signals = [s for s in signals if s.timestamp <= end_dt]

        if df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="所选日期范围内无数据",
                xref="paper", yref="paper", x=0.5, y=0.5,
                showarrow=False, font=dict(size=16, color="#a0aec0")
            )
            fig.update_layout(
                plot_bgcolor=self.theme['card_background'],
                paper_bgcolor=self.theme['background_color'],
                font_color=self.theme['text_color'],
                height=self.chart_height
            )
            return fig

        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.8, 0.2],
            subplot_titles=(f'{stock_name} 价格走势', '成交量')
        )
        
        df = df.reset_index(drop=True)
        x_indices = list(range(len(df)))
        
        date_to_idx = {row['date']: idx for idx, row in df.iterrows()}
        
        # 添加K线图
        fig.add_trace(
            go.Candlestick(
                x=x_indices,
                open=df['open'],
                high=df['high'],
                low=df['low'],
                close=df['close'],
                name='K线',
                increasing_line_color='#f56565',
                decreasing_line_color='#48bb78'
            ),
            row=1, col=1
        )
        
        # 添加均线
        fig.add_trace(
            go.Scatter(
                x=x_indices,
                y=df['ma10'],
                mode='lines',
                name='MA10',
                line=dict(color='#4a90e2', width=1.5)
            ),
            row=1, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=x_indices,
                y=df['ma20'],
                mode='lines',
                name='MA20',
                line=dict(color='#f6ad55', width=1.5)
            ),
            row=1, col=1
        )
        
        # 添加信号标记（使用索引位置）
        for signal in signals:
            signal_idx = date_to_idx.get(signal.timestamp)
            if signal_idx is not None:
                self._add_signal_marker(fig, signal, signal_idx, row=1, col=1)
        
        # 添加成交量
        colors = ['#f56565' if close >= open else '#48bb78' 
                  for close, open in zip(df['close'], df['open'])]
        
        fig.add_trace(
            go.Bar(
                x=x_indices,
                y=df['volume'],
                name='成交量',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # 添加成交量均线
        fig.add_trace(
            go.Scatter(
                x=x_indices,
                y=df['volume_ma10'],
                mode='lines',
                name='成交量MA10',
                line=dict(color='#9f7aea', width=1)
            ),
            row=2, col=1
        )
        
        # 更新布局
        fig.update_layout(
            height=self.chart_height,
            showlegend=True,
            xaxis_rangeslider_visible=False,
            plot_bgcolor=self.theme['card_background'],
            paper_bgcolor=self.theme['background_color'],
            font_color=self.theme['text_color'],
            legend=dict(
                bgcolor=self.theme['card_background'],
                bordercolor=self.theme['border_color'],
                borderwidth=1
            )
        )
        
        # 更新Y轴
        fig.update_yaxes(
            gridcolor=self.theme['border_color'],
            gridwidth=0.5,
            showgrid=True
        )
        
        # 更新X轴 - 使用日期作为刻度标签
        # 选择间隔显示的日期，避免标签重叠
        n_ticks = min(10, len(df))
        tick_indices = [int(i * (len(df) - 1) / (n_ticks - 1)) for i in range(n_ticks)] if n_ticks > 1 else [0]
        tick_texts = [df.iloc[i]['date'].strftime('%m-%d') for i in tick_indices]
        
        fig.update_xaxes(
            gridcolor=self.theme['border_color'],
            gridwidth=0.5,
            showgrid=True,
            rangeslider_visible=False,
            tickmode='array',
            tickvals=tick_indices,
            ticktext=tick_texts,
            tickangle=-45
        )
        
        return fig
    
    def _add_signal_marker(self, fig: go.Figure, signal: TradingSignal, x_idx: int, row: int, col: int):
        """添加信号标记"""
        from models import TradingSignalType
        
        symbol_map = {
            '买入': 'triangle-up',
            '加码': 'diamond',
            '离场': 'triangle-down',
            '止盈': 'star'
        }
        
        symbol = symbol_map.get(signal.action, 'circle')
        
        # 从信号类型获取对应的条件描述
        conditions = signal.signal_type.conditions
        if conditions and signal.condition_id > 0 and signal.condition_id <= len(conditions):
            condition_text = conditions[signal.condition_id - 1]
        elif conditions:
            condition_text = conditions[0]
        else:
            condition_text = '未知条件'
        
        fig.add_trace(
            go.Scatter(
                x=[x_idx],
                y=[signal.price],
                mode='markers',
                marker=dict(
                    symbol=symbol,
                    size=15,
                    color=signal.color,
                    line=dict(width=2, color='white')
                ),
                name=f"{signal.signal_name}",
                showlegend=False,
                hovertemplate=f"<b>{signal.signal_name}</b><br>" +
                             f"日期: {signal.timestamp}<br>" +
                             f"价格: {signal.price:.2f}<br>" +
                             f"<b>满足条件:</b><br>{condition_text}<br>" +
                             f"<extra></extra>"
            ),
            row=row, col=col
        )
    
    def create_signal_summary(self, result: SignalResult) -> Dict[str, Any]:
        """创建信号汇总数据"""
        stats = result.statistics
        
        return {
            'total_signals': stats.get('total_signals', 0),
            'buy_count': stats.get('buy_signals', 0),
            'add_count': stats.get('add_signals', 0),
            'exit_count': stats.get('exit_signals', 0),
            'profit_count': stats.get('profit_signals', 0),
            'estimated_return': stats.get('estimated_return', 'N/A')
        }
    
    def create_signal_table(self, signals: List[TradingSignal]) -> List[Dict]:
        """创建信号表格数据"""
        table_data = []
        
        for signal in signals:
            table_data.append({
                '日期': signal.timestamp.strftime('%Y-%m-%d'),
                '信号': signal.signal_name,
                '操作': signal.action,
                '价格': f"{signal.price:.2f}",
                '条件': '; '.join(signal.conditions[:2]) + ('...' if len(signal.conditions) > 2 else '')
            })
        
        return table_data
