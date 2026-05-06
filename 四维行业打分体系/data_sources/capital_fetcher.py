import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from .tushare_client import TushareClient

ETF_INDUSTRY_MAP = {
    "芯片": ["159995.SZ", "512760.SH"],
    "半导体": ["512480.SH", "159813.SZ"],
    "机器人": ["562500.SH", "159770.SZ"],
    "电池": ["159755.SZ", "561910.SH"],
    "创新药": ["159992.SZ", "515120.SH"],
    "光伏": ["515790.SH", "159857.SZ"],
    "人工智能": ["159819.SZ", "515070.SH"],
    "新能源汽车": ["515030.SH", "159806.SZ"],
    "军工": ["512660.SH", "512670.SH"],
}


class CapitalFetcher:
    def __init__(self, client: TushareClient):
        self.client = client

    def get_etf_codes(self, industry_name: str) -> list:
        if industry_name in ETF_INDUSTRY_MAP:
            return ETF_INDUSTRY_MAP[industry_name]
        for kw, codes in ETF_INDUSTRY_MAP.items():
            if kw in industry_name or industry_name in kw:
                return codes
        return []

    def get_etf_flow(self, industry_name: str) -> dict:
        etf_codes = self.get_etf_codes(industry_name)
        if not etf_codes:
            return {"etf_net_subscription": 0, "reason": "未找到对应ETF", "details": []}

        total_amount = 0
        details = []
        today = datetime.now()

        for code in etf_codes:
            try:
                start_date = (today - timedelta(days=60)).strftime('%Y%m%d')
                end_date = today.strftime('%Y%m%d')
                df = self.client.get_fund_daily(code, start_date, end_date)

                if df.empty:
                    details.append({"code": code, "status": "no_data"})
                    continue

                df = df.sort_values('trade_date')
                df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
                df = df.dropna(subset=['amount'])

                if len(df) < 5:
                    details.append({"code": code, "status": "insufficient_data"})
                    continue

                recent_avg = df['amount'].tail(20).mean() if len(df) >= 20 else df['amount'].mean()
                prev_avg = df['amount'].iloc[:-min(20, len(df)-1)].tail(20).mean() if len(df) > 20 else df['amount'].iloc[:-1].mean()

                flow = recent_avg - prev_avg
                total_amount += flow

                details.append({
                    "code": code,
                    "recent_avg_amount": round(float(recent_avg), 2),
                    "prev_avg_amount": round(float(prev_avg), 2),
                    "flow": round(float(flow), 2),
                    "status": "ok"
                })
            except Exception as e:
                details.append({"code": code, "status": "error", "error": str(e)})

        total_amount = round(total_amount / 10000, 2)

        reason_parts = []
        for d in details:
            if d.get("status") == "ok":
                direction = "流入" if d["flow"] > 0 else "流出"
                reason_parts.append(f"{d['code']}: {direction}{abs(d['flow']):.0f}万")

        reason = "；".join(reason_parts) if reason_parts else "无法获取ETF资金流向数据"

        return {
            "etf_net_subscription": total_amount,
            "reason": reason,
            "details": details
        }

    def get_fund_position_change(self, industry_name: str) -> dict:
        return {
            "fund_position_change": 0,
            "reason": "公募基金持仓数据需Tushare高级积分，当前不可用，请手动填写",
            "available": False
        }

    def get_capital_data(self, industry_name: str) -> dict:
        etf_flow = self.get_etf_flow(industry_name)
        fund_pos = self.get_fund_position_change(industry_name)

        return {
            "etf_net_subscription": etf_flow["etf_net_subscription"],
            "etf_flow_reason": etf_flow["reason"],
            "etf_details": etf_flow.get("details", []),
            "fund_position_change": fund_pos["fund_position_change"],
            "fund_position_available": fund_pos["available"],
            "fund_position_reason": fund_pos["reason"],
        }
