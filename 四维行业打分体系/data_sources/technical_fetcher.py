import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .tushare_client import TushareClient


class TechnicalFetcher:
    def __init__(self, client: TushareClient):
        self.client = client

    def detect_signals(self, ths_code: str) -> dict:
        if not ths_code:
            return {"signals": [], "reason": "无行业指数代码", "metrics": {}}

        try:
            start_date = (datetime.now() - timedelta(days=180)).strftime('%Y%m%d')
            end_date = datetime.now().strftime('%Y%m%d')
            df = self.client.get_ths_daily(ths_code, start_date, end_date)

            if df.empty:
                return {"signals": [], "reason": "无法获取行业指数数据", "metrics": {}}

            df = df.sort_values('trade_date')
            for col in ['close', 'open', 'high', 'low', 'vol']:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')

            df = df.dropna(subset=['close'])
            if len(df) < 30:
                return {"signals": [], "reason": "数据不足（少于30个交易日）", "metrics": {}}

            df['ma10'] = df['close'].rolling(10).mean()
            df['ma20'] = df['close'].rolling(20).mean()
            df['ma60'] = df['close'].rolling(60).mean()
            df['pct_change'] = df['close'].pct_change() * 100
            df['vol_ma20'] = df['vol'].rolling(20).mean()
            df['deviation_ma20'] = (df['close'] - df['ma20']) / df['ma20'] * 100

            signals = []

            signal_1020 = self._detect_1020(df)
            if signal_1020:
                signals.append(signal_1020)

            signal_dip = self._detect_dip_buy(df)
            if signal_dip:
                signals.append(signal_dip)

            signal_dragon = self._detect_dragon_back(df)
            if signal_dragon:
                signals.append(signal_dragon)

            latest = df.iloc[-1]
            metrics = {
                "close": round(float(latest['close']), 2),
                "ma10": round(float(latest['ma10']), 2) if pd.notna(latest.get('ma10')) else None,
                "ma20": round(float(latest['ma20']), 2) if pd.notna(latest.get('ma20')) else None,
                "ma60": round(float(latest['ma60']), 2) if pd.notna(latest.get('ma60')) else None,
                "pct_change": round(float(latest['pct_change']), 2) if pd.notna(latest.get('pct_change')) else None,
                "deviation_ma20": round(float(latest['deviation_ma20']), 2) if pd.notna(latest.get('deviation_ma20')) else None,
            }

            reason = f"检测到{len(signals)}个技术信号" if signals else "未检测到技术信号"

            return {"signals": signals, "reason": reason, "metrics": metrics}

        except Exception as e:
            return {"signals": [], "reason": f"技术分析出错：{str(e)}", "metrics": {}}

    def _detect_1020(self, df: pd.DataFrame) -> dict:
        if len(df) < 12:
            return None

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        if pd.isna(latest.get('ma10')) or pd.isna(latest.get('ma20')):
            return None

        close_above = latest['close'] > latest['ma10'] and latest['close'] > latest['ma20']
        prev_below = (pd.notna(prev.get('ma10')) and prev['close'] <= prev['ma10']) or \
                     (pd.notna(prev.get('ma20')) and prev['close'] <= prev['ma20'])

        if close_above and prev_below:
            return {
                "signal_type": "1020起爆点",
                "description": f"收盘价{latest['close']:.2f}站上MA10({latest['ma10']:.2f})和MA20({latest['ma20']:.2f})",
                "trigger_date": str(df.iloc[-1].get('trade_date', '')),
            }

        if close_above:
            prev_5 = df.iloc[-6:-1]
            below_count = 0
            for _, row in prev_5.iterrows():
                if pd.notna(row.get('ma10')) and row['close'] <= row['ma10']:
                    below_count += 1
                elif pd.notna(row.get('ma20')) and row['close'] <= row['ma20']:
                    below_count += 1
            if below_count >= 3:
                return {
                    "signal_type": "1020起爆点",
                    "description": f"近5日有{below_count}日在均线下方，今日站上MA10和MA20",
                    "trigger_date": str(df.iloc[-1].get('trade_date', '')),
                }

        return None

    def _detect_dip_buy(self, df: pd.DataFrame) -> dict:
        if len(df) < 25:
            return None

        latest = df.iloc[-1]
        if pd.isna(latest.get('pct_change')) or pd.isna(latest.get('deviation_ma20')):
            return None

        is_big_drop = latest['pct_change'] < -3
        is_deviated = latest['deviation_ma20'] < -5
        vol_ratio = latest['vol'] / latest['vol_ma20'] if pd.notna(latest.get('vol_ma20')) and latest['vol_ma20'] > 0 else 0

        if is_big_drop and is_deviated and vol_ratio > 1.3:
            return {
                "signal_type": "意外大跌抄底",
                "description": f"单日跌幅{latest['pct_change']:.1f}%，偏离MA20 {latest['deviation_ma20']:.1f}%，放量{vol_ratio:.1f}倍",
                "trigger_date": str(latest.get('trade_date', '')),
            }

        if is_big_drop and is_deviated:
            return {
                "signal_type": "意外大跌抄底",
                "description": f"单日跌幅{latest['pct_change']:.1f}%，偏离MA20 {latest['deviation_ma20']:.1f}%",
                "trigger_date": str(latest.get('trade_date', '')),
            }

        return None

    def _detect_dragon_back(self, df: pd.DataFrame) -> dict:
        if len(df) < 40:
            return None

        recent_20 = df.iloc[-20:]
        prior_20 = df.iloc[-40:-20]

        if prior_20.empty or recent_20.empty:
            return None

        prior_start = prior_20['close'].iloc[0]
        prior_high = prior_20['close'].max()
        prior_rally = (prior_high - prior_start) / prior_start * 100

        if prior_rally < 10:
            return None

        recent_low = recent_20['close'].min()
        pullback = (prior_high - recent_low) / prior_high * 100

        if pullback < 5:
            return None

        latest = df.iloc[-1]
        if pd.isna(latest.get('ma20')):
            return None

        near_ma20 = abs(latest['close'] - latest['ma20']) / latest['ma20'] * 100 < 4
        today_up = latest.get('pct_change', 0) > 1.5

        vol_ratio = latest['vol'] / latest['vol_ma20'] if pd.notna(latest.get('vol_ma20')) and latest['vol_ma20'] > 0 else 0

        if near_ma20 and today_up and vol_ratio > 1.2:
            return {
                "signal_type": "龙回头",
                "description": f"前期涨幅{prior_rally:.1f}%后回调{pullback:.1f}%，回踩MA20后放量反弹",
                "trigger_date": str(latest.get('trade_date', '')),
            }

        return None
