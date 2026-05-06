import os
import sys
import json
import webbrowser
import threading
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from data_sources import TushareClient
from data_sources.industry_fetcher import IndustryFetcher, THS_INDUSTRY_MAP
from data_sources.capital_fetcher import CapitalFetcher
from data_sources.technical_fetcher import TechnicalFetcher

from models import (
    IndustryData, PolicyData, CapitalData, TechnicalData,
    TechnicalSignal, IndustryScoreResult
)
from engine import IndustryScoringEngine

app = Flask(__name__, static_folder='web', static_url_path='')

_tushare_client = None
_engine = IndustryScoringEngine()


def get_tushare_client(token: str) -> TushareClient:
    global _tushare_client
    if _tushare_client is None or _tushare_client.token != token:
        _tushare_client = TushareClient(token)
    return _tushare_client


@app.route('/')
def index():
    return send_from_directory('web', 'index.html')


@app.route('/api/industry_list', methods=['GET'])
def api_industry_list():
    industries = []
    for name, code in THS_INDUSTRY_MAP.items():
        industries.append({"name": name, "ths_code": code})
    return jsonify({"industries": industries, "count": len(industries)})


@app.route('/api/fetch_industry', methods=['POST'])
def api_fetch_industry():
    data = request.get_json()
    token = data.get('token', '')
    industry_name = data.get('industry_name', '')

    if not token:
        return jsonify({"error": "请提供Tushare Token"}), 400
    if not industry_name:
        return jsonify({"error": "请提供行业名称"}), 400

    try:
        client = get_tushare_client(token)
        fetcher = IndustryFetcher(client)
        result = fetcher.get_industry_data(industry_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/fetch_capital', methods=['POST'])
def api_fetch_capital():
    data = request.get_json()
    token = data.get('token', '')
    industry_name = data.get('industry_name', '')

    if not token:
        return jsonify({"error": "请提供Tushare Token"}), 400
    if not industry_name:
        return jsonify({"error": "请提供行业名称"}), 400

    try:
        client = get_tushare_client(token)
        fetcher = CapitalFetcher(client)
        result = fetcher.get_capital_data(industry_name)
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/fetch_technical', methods=['POST'])
def api_fetch_technical():
    data = request.get_json()
    token = data.get('token', '')
    industry_name = data.get('industry_name', '')

    if not token:
        return jsonify({"error": "请提供Tushare Token"}), 400
    if not industry_name:
        return jsonify({"error": "请提供行业名称"}), 400

    try:
        client = get_tushare_client(token)
        from data_sources.industry_fetcher import IndustryFetcher as IF
        ths_code = IF(client).get_ths_code(industry_name)

        tech_fetcher = TechnicalFetcher(client)
        result = tech_fetcher.detect_signals(ths_code)
        result["ths_code"] = ths_code
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/fetch_all', methods=['POST'])
def api_fetch_all():
    data = request.get_json()
    token = data.get('token', '')
    industry_name = data.get('industry_name', '')

    if not token:
        return jsonify({"error": "请提供Tushare Token"}), 400
    if not industry_name:
        return jsonify({"error": "请提供行业名称"}), 400

    try:
        client = get_tushare_client(token)

        ind_fetcher = IndustryFetcher(client)
        industry_data = ind_fetcher.get_industry_data(industry_name)

        cap_fetcher = CapitalFetcher(client)
        capital_data = cap_fetcher.get_capital_data(industry_name)

        ths_code = industry_data.get('ths_code', '')
        tech_fetcher = TechnicalFetcher(client)
        technical_data = tech_fetcher.detect_signals(ths_code)

        return jsonify({
            "industry": industry_data,
            "capital": capital_data,
            "technical": technical_data,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/score', methods=['POST'])
def api_score():
    data = request.get_json()

    try:
        industry_name = data.get('industry_name', '未知行业')

        industry_data = IndustryData(
            name=industry_name,
            industry_type=data.get('industry_type', ''),
            cycle_phase=data.get('cycle_phase', ''),
            is_recommended=data.get('is_recommended', False)
        )

        policy_data = PolicyData(
            has_support_policy=data.get('has_support_policy', False),
            policy_description=data.get('policy_description', ''),
            has_catalyst_event=data.get('has_catalyst_event', False),
            catalyst_description=data.get('catalyst_description', '')
        )

        capital_data = CapitalData(
            etf_net_subscription=float(data.get('etf_net_subscription', 0)),
            fund_position_change=float(data.get('fund_position_change', 0))
        )

        technical_data = TechnicalData()
        for sig in data.get('technical_signals', []):
            if isinstance(sig, str):
                technical_data.add_signal(TechnicalSignal(signal_type=sig, description=sig))
            elif isinstance(sig, dict):
                technical_data.add_signal(TechnicalSignal(
                    signal_type=sig.get('signal_type', ''),
                    description=sig.get('description', ''),
                    stock_code=sig.get('stock_code', '')
                ))

        result = _engine.score_industry(
            industry_name=industry_name,
            industry_data=industry_data,
            policy_data=policy_data,
            capital_data=capital_data,
            technical_data=technical_data
        )

        return jsonify(result.to_dict())

    except Exception as e:
        return jsonify({"error": str(e)}), 500


def start_server(port=8080):
    print("\n" + "=" * 70)
    print("       四维行业打分体系 - Web服务启动")
    print("=" * 70)
    print(f"\n  本地访问：http://localhost:{port}")
    print(f"  API接口：http://localhost:{port}/api/")
    print(f"\n  已启用的API：")
    print(f"    GET  /api/industry_list    - 获取支持的行业列表")
    print(f"    POST /api/fetch_industry   - 获取行业景气度数据")
    print(f"    POST /api/fetch_capital    - 获取资金面数据")
    print(f"    POST /api/fetch_technical  - 获取技术面信号")
    print(f"    POST /api/fetch_all        - 一键获取全部数据")
    print(f"    POST /api/score            - 执行四维评分")
    print()

    def open_browser():
        webbrowser.open(f'http://localhost:{port}')

    threading.Timer(1.0, open_browser).start()
    app.run(host='0.0.0.0', port=port, debug=False)


if __name__ == '__main__':
    start_server()
