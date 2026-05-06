import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .tushare_client import TushareClient

THS_INDUSTRY_MAP = {
    "芯片": "885756.TI",
    "半导体": "885908.TI",
    "机器人": "885517.TI",
    "人形机器人": "886069.TI",
    "电池": "885710.TI",
    "固态电池": "886032.TI",
    "创新药": "886015.TI",
    "光伏": "885531.TI",
    "人工智能": "885728.TI",
    "AI智能体": "886099.TI",
    "新能源汽车": "885431.TI",
    "军工": "885700.TI",
    "消费电子": "885800.TI",
}

CYCLICAL_INDUSTRIES = {"芯片", "半导体", "电池", "固态电池", "光伏", "新能源汽车", "军工", "钢铁", "有色金属", "化工", "煤炭", "石油石化"}
NON_CYCLICAL_INDUSTRIES = {"创新药", "医药", "消费电子", "食品饮料", "白酒", "家电", "人工智能", "AI智能体", "机器人", "人形机器人"}


class IndustryFetcher:
    def __init__(self, client: TushareClient):
        self.client = client

    def get_industry_type(self, industry_name: str) -> str:
        for kw, itype in [("周期性", CYCLICAL_INDUSTRIES), ("非周期性", NON_CYCLICAL_INDUSTRIES)]:
            pass
        if industry_name in CYCLICAL_INDUSTRIES:
            return "周期性"
        if industry_name in NON_CYCLICAL_INDUSTRIES:
            return "非周期性"
        for kw in CYCLICAL_INDUSTRIES:
            if kw in industry_name:
                return "周期性"
        for kw in NON_CYCLICAL_INDUSTRIES:
            if kw in industry_name:
                return "非周期性"
        return "非周期性"

    def get_ths_code(self, industry_name: str) -> str:
        if industry_name in THS_INDUSTRY_MAP:
            return THS_INDUSTRY_MAP[industry_name]
        for kw, code in THS_INDUSTRY_MAP.items():
            if kw in industry_name or industry_name in kw:
                return code
        return ""

    def get_cycle_phase(self, industry_name: str) -> dict:
        ths_code = self.get_ths_code(industry_name)
        if not ths_code:
            return {"cycle_phase": "成长期", "reason": "未找到对应行业指数，默认判定为成长期", "metrics": {}}

        try:
            df = self.client.get_ths_daily(ths_code)
            if df.empty:
                return {"cycle_phase": "成长期", "reason": "无法获取行业指数数据", "metrics": {}}

            df = df.sort_values('trade_date')
            df['close'] = pd.to_numeric(df['close'], errors='coerce')
            df = df.dropna(subset=['close'])

            if len(df) < 20:
                return {"cycle_phase": "成长期", "reason": "数据不足（少于20个交易日）", "metrics": {}}

            df['ma20'] = df['close'].rolling(20).mean()
            df['ma60'] = df['close'].rolling(60).mean()
            latest = df.iloc[-1]
            close = latest['close']
            ma20 = latest.get('ma20', close)
            ma60 = latest.get('ma60', close)

            pct_1m = (df['close'].iloc[-1] / df['close'].iloc[-min(20, len(df))] - 1) * 100 if len(df) >= 20 else 0
            pct_3m = (df['close'].iloc[-1] / df['close'].iloc[-min(60, len(df))] - 1) * 100 if len(df) >= 60 else 0

            ma20_slope = 0
            if len(df) >= 25:
                ma20_series = df['ma20'].dropna()
                if len(ma20_series) >= 5:
                    ma20_slope = (ma20_series.iloc[-1] - ma20_series.iloc[-5]) / ma20_series.iloc[-5] * 100

            metrics = {
                "close": round(float(close), 2),
                "ma20": round(float(ma20), 2) if pd.notna(ma20) else None,
                "ma60": round(float(ma60), 2) if pd.notna(ma60) else None,
                "pct_1m": round(pct_1m, 2),
                "pct_3m": round(pct_3m, 2),
                "ma20_slope_5d": round(ma20_slope, 2),
            }

            if pct_3m < -15 and close > ma20 and ma20_slope > 0:
                phase = "底部反转"
                reason = f"近3月跌幅{pct_3m:.1f}%，价格站上MA20且均线拐头向上，判定为底部反转"
            elif pct_3m < -10 and close <= ma20:
                phase = "底部"
                reason = f"近3月跌幅{pct_3m:.1f}%，价格仍在MA20下方，判定为底部区域"
            elif pct_3m > 20 and ma20_slope > 3:
                phase = "成长期"
                reason = f"近3月涨幅{pct_3m:.1f}%，MA20趋势向上，判定为成长期"
            elif pct_3m > 5 and abs(ma20_slope) < 2:
                phase = "成熟期"
                reason = f"近3月涨幅{pct_3m:.1f}%，趋势平缓，判定为成熟期"
            elif pct_3m < -10 and ma20_slope < -2:
                phase = "衰退期"
                reason = f"近3月跌幅{pct_3m:.1f}%，MA20趋势向下，判定为衰退期"
            elif ma20_slope > 1:
                phase = "成长期"
                reason = f"MA20趋势向上（斜率{ma20_slope:.1f}%），判定为成长期"
            elif ma20_slope < -1:
                phase = "衰退期"
                reason = f"MA20趋势向下（斜率{ma20_slope:.1f}%），判定为衰退期"
            else:
                phase = "成熟期"
                reason = "趋势不明朗，判定为成熟期"

            return {"cycle_phase": phase, "reason": reason, "metrics": metrics}

        except Exception as e:
            return {"cycle_phase": "成长期", "reason": f"分析出错：{str(e)}", "metrics": {}}

    def get_industry_data(self, industry_name: str) -> dict:
        industry_type = self.get_industry_type(industry_name)
        phase_result = self.get_cycle_phase(industry_name)
        ths_code = self.get_ths_code(industry_name)

        return {
            "name": industry_name,
            "industry_type": industry_type,
            "cycle_phase": phase_result["cycle_phase"],
            "phase_reason": phase_result["reason"],
            "metrics": phase_result.get("metrics", {}),
            "ths_code": ths_code,
        }
