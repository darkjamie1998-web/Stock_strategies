"""
三维共振打分系统 - Web可视化界面
使用Flask + ECharts
"""

from flask import Flask, render_template, jsonify, request
import json
import pandas as pd
from datetime import datetime
from scoring_system import ThreeDimensionalScoringSystem
from market_data import ZhongZhengData

app = Flask(__name__)

# 千问API密钥
API_KEY = "sk-4613f6b3b3664049b0b7d808bd3c9b9a"

# 全局变量存储最新结果
latest_result = None


@app.route('/')
def index():
    """主页面"""
    return render_template('index.html')


@app.route('/api/analyze', methods=['POST'])
def analyze():
    """执行三维共振分析"""
    global latest_result
    
    try:
        # 创建打分系统实例
        scoring_system = ThreeDimensionalScoringSystem(API_KEY)
        
        # 运行完整分析
        result = scoring_system.run_full_analysis()
        latest_result = result
        
        return jsonify({
            "success": True,
            "data": result
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/latest', methods=['GET'])
def get_latest():
    """获取最新分析结果"""
    if latest_result:
        return jsonify({
            "success": True,
            "data": latest_result
        })
    else:
        return jsonify({
            "success": False,
            "error": "暂无分析结果，请先执行分析"
        }), 404


@app.route('/api/mock', methods=['GET'])
def mock_data():
    """获取模拟数据（用于测试）"""
    mock_result = {
        "analysis_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "dimensions": [
            {
                "dimension": "政策面",
                "score": 1,
                "max_score": 1,
                "analysis": "当前货币政策宽松，央行降准释放流动性，财政刺激政策持续发力",
                "raw_content": "政策分析内容...",
                "timestamp": datetime.now().isoformat()
            },
            {
                "dimension": "资金面",
                "score": 1,
                "max_score": 1,
                "analysis": "成交量明显放大且持续性良好",
                "details": {
                    "recent_5d_volume_mean": 4500.5,
                    "previous_5d_volume_mean": 3800.2,
                    "volume_change_ratio": 18.5,
                    "up_days_in_5": 4,
                    "reasons": ["近5日成交量较前5日放大18.5%", "近5个交易日有4天成交量上升，持续性良好"]
                },
                "index_name": "中证全指",
                "latest_close": 4850.32,
                "timestamp": datetime.now().isoformat()
            },
            {
                "dimension": "技术面",
                "score": 1,
                "max_score": 1,
                "analysis": "指数站稳10日与20日均线，形成有效突破",
                "details": {
                    "latest_close": 4850.32,
                    "ma10": 4820.15,
                    "ma20": 4785.68,
                    "deviation_ma10": 0.63,
                    "deviation_ma20": 1.35,
                    "above_ma10": True,
                    "above_ma20": True,
                    "consecutive_days_above": 3,
                    "reasons": ["收盘价4850.32点站稳MA10(4820.15)和MA20(4785.68)", "已连续3天站稳双均线，确认为有效突破"]
                },
                "index_name": "中证全指",
                "latest_close": 4850.32,
                "timestamp": datetime.now().isoformat()
            }
        ],
        "summary": {
            "total_score": 3,
            "max_score": 3,
            "market_status": "单边上行行情",
            "position_suggestion": "70-100%",
            "description": "三维共振成立，政策利好释放、资金大规模流入、技术形态突破并站稳均线"
        }
    }
    
    return jsonify({
        "success": True,
        "data": mock_result
    })


@app.route('/api/kline', methods=['GET'])
def get_kline_data():
    """获取中证全指K线数据（最近3个月）"""
    try:
        analyzer = ZhongZhengData()
        df = analyzer.get_index_data(days=90)
        
        if df.empty:
            return jsonify({
                "success": False,
                "error": "未能获取K线数据"
            }), 500
        
        # 计算MA10和MA20
        df = analyzer.calculate_ma(df)
        
        # 转换为ECharts需要的格式
        # K线数据: [open, close, low, high]
        kline_data = []
        ma10_data = []
        ma20_data = []
        volume_data = []
        dates = []
        
        for idx, row in df.iterrows():
            dates.append(row['date'].strftime('%Y-%m-%d'))
            # K线: [open, close, low, high]
            kline_data.append([
                float(row['open']),
                float(row['close']),
                float(row['low']),
                float(row['high'])
            ])
            # MA10和MA20
            ma10_val = float(row['MA10']) if pd.notna(row['MA10']) else None
            ma20_val = float(row['MA20']) if pd.notna(row['MA20']) else None
            ma10_data.append(ma10_val)
            ma20_data.append(ma20_val)
            # 成交量（转换为亿）
            volume_data.append(float(row['volume'] / 1e8))
        
        return jsonify({
            "success": True,
            "data": {
                "dates": dates,
                "kline": kline_data,
                "ma10": ma10_data,
                "ma20": ma20_data,
                "volume": volume_data,
                "index_name": "中证全指",
                "index_code": "000985.SH"
            }
        })
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    print("启动三维共振打分系统...")
    print("访问地址: http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=5000)
