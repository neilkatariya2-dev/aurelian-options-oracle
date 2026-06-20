"""
Options Oracle — Flask API Server
Serves options data, Greeks, chain, and strategy simulation endpoints.
"""
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS
import json
from datetime import datetime

# Import from the local module (NOT from itself!)
from options_oracle import OptionsOracle, UNDERLYINGS, OptionLeg

app = Flask(__name__)
CORS(app)

# ─── Helper: serialize dataclasses ─────────────────────────
def serialize_option(contract):
    return {
        "strike": contract.strike,
        "expiry": contract.expiry,
        "option_type": contract.option_type,
        "bid": contract.bid,
        "ask": contract.ask,
        "last": contract.last,
        "volume": contract.volume,
        "open_interest": contract.open_interest,
        "iv": contract.iv,
        "delta": contract.delta,
        "gamma": contract.gamma,
        "theta": contract.theta,
        "vega": contract.vega,
        "itm": contract.itm
    }

# ─── API Routes ─────────────────────────────────────────────

@app.route("/")
def index():
    """Serve the main dashboard."""
    return render_template_string(INDEX_HTML)

@app.route("/api/tickers")
def get_tickers():
    """Get available tickers."""
    return jsonify({"tickers": UNDERLYINGS})

@app.route("/api/metrics/<ticker>")
def get_metrics(ticker):
    """Get live metrics for a ticker."""
    oracle = OptionsOracle(ticker)
    return jsonify(oracle.get_metrics())

@app.route("/api/chain/<ticker>")
def get_chain(ticker):
    """Get options chain for a ticker."""
    oracle = OptionsOracle(ticker)
    chain = oracle.get_options_chain()
    return jsonify({
        "ticker": ticker,
        "spot": oracle.spot,
        "calls": [serialize_option(c) for c in chain["calls"]],
        "puts": [serialize_option(p) for p in chain["puts"]]
    })

@app.route("/api/greeks/<ticker>")
def get_greeks(ticker):
    """Get Greeks summary for a ticker."""
    oracle = OptionsOracle(ticker)
    return jsonify(oracle.get_greeks_summary())

@app.route("/api/simulate", methods=["POST"])
def simulate():
    """Simulate strategy P&L."""
    data = request.json
    ticker = data.get("ticker", "AAPL")
    legs_data = data.get("legs", [])
    price_range = data.get("price_range", [150, 220])

    oracle = OptionsOracle(ticker)
    legs = [OptionLeg(
        strike=l["strike"],
        expiry=l.get("expiry", "2024-12-20"),
        option_type=l["option_type"],
        quantity=l["quantity"],
        premium=l["premium"]
    ) for l in legs_data]

    results = oracle.simulate_strategy(legs, tuple(price_range))
    return jsonify({"results": results})

@app.route("/api/ai-suggest/<ticker>")
def ai_suggest(ticker):
    """Get AI strategy suggestion."""
    oracle = OptionsOracle(ticker)
    return jsonify(oracle.get_ai_suggestion())

# ─── Health Check ─────────────────────────────────────────
@app.route("/health")
def health():
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

# ─── Embedded Dashboard HTML ──────────────────────────────
INDEX_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Options Oracle | Advanced Options Analytics</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {
            --bg-primary: #0a0e1a;
            --bg-secondary: #111827;
            --bg-card: #1a1f2e;
            --bg-elevated: #232837;
            --border: #2a3142;
            --text-primary: #f0f2f5;
            --text-secondary: #94a3b8;
            --text-muted: #64748b;
            --accent: #6366f1;
            --accent-glow: rgba(99, 102, 241, 0.3);
            --green: #22c55e;
            --green-glow: rgba(34, 197, 94, 0.2);
            --red: #ef4444;
            --red-glow: rgba(239, 68, 68, 0.2);
            --orange: #f59e0b;
            --cyan: #06b6d4;
            --purple: #a855f7;
            --pink: #ec4899;
        }

        * { margin: 0; padding: 0; box-sizing: border-box; }

        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            overflow-x: hidden;
        }

        /* ─── Animated Background ─── */
        .bg-mesh {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            background: 
                radial-gradient(ellipse at 20% 20%, rgba(99, 102, 241, 0.08) 0%, transparent 50%),
                radial-gradient(ellipse at 80% 80%, rgba(236, 72, 153, 0.06) 0%, transparent 50%),
                radial-gradient(ellipse at 50% 50%, rgba(6, 182, 212, 0.04) 0%, transparent 60%);
            animation: bgPulse 12s ease-in-out infinite alternate;
        }

        @keyframes bgPulse {
            0% { opacity: 0.8; transform: scale(1); }
            100% { opacity: 1; transform: scale(1.05); }
        }

        .grid-overlay {
            position: fixed;
            top: 0; left: 0; width: 100%; height: 100%;
            z-index: 0;
            background-image: 
                linear-gradient(rgba(99, 102, 241, 0.03) 1px, transparent 1px),
                linear-gradient(90deg, rgba(99, 102, 241, 0.03) 1px, transparent 1px);
            background-size: 60px 60px;
            pointer-events: none;
        }

        /* ─── Layout ─── */
        .container {
            position: relative;
            z-index: 1;
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 24px;
        }

        /* ─── Navbar ─── */
        .navbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 20px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 32px;
        }

        .logo {
            display: flex;
            align-items: center;
            gap: 12px;
            font-weight: 800;
            font-size: 1.4rem;
            letter-spacing: -0.5px;
        }

        .logo-icon {
            width: 36px; height: 36px;
            background: linear-gradient(135deg, var(--accent), var(--purple));
            border-radius: 10px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.1rem;
        }

        .ticker-select {
            background: var(--bg-card);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 10px 16px;
            border-radius: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.95rem;
            cursor: pointer;
            outline: none;
            transition: all 0.2s;
        }
        .ticker-select:hover, .ticker-select:focus {
            border-color: var(--accent);
            box-shadow: 0 0 0 3px var(--accent-glow);
        }

        /* ─── Hero ─── */
        .hero {
            text-align: center;
            padding: 48px 0 56px;
        }

        .hero-title {
            font-size: 3.2rem;
            font-weight: 800;
            letter-spacing: -2px;
            line-height: 1.1;
            margin-bottom: 16px;
            background: linear-gradient(90deg, #fff 0%, #a5b4fc 30%, #c084fc 60%, #67e8f9 100%);
            background-size: 200% auto;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            animation: gradientShift 6s ease-in-out infinite alternate;
        }

        @keyframes gradientShift {
            0% { background-position: 0% 50%; }
            100% { background-position: 100% 50%; }
        }

        .hero-subtitle {
            color: var(--text-secondary);
            font-size: 1.1rem;
            max-width: 500px;
            margin: 0 auto;
            line-height: 1.6;
        }

        /* ─── Section Headers ─── */
        .section-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
        }
        .section-header::before {
            content: '';
            width: 4px; height: 20px;
            background: linear-gradient(180deg, var(--accent), var(--purple));
            border-radius: 2px;
        }

        /* ─── Metrics Grid ─── */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 40px;
        }

        .metric-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 24px;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .metric-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--purple));
            opacity: 0;
            transition: opacity 0.3s;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: var(--accent);
            box-shadow: 0 20px 40px rgba(0,0,0,0.3), 0 0 20px var(--accent-glow);
        }
        .metric-card:hover::before { opacity: 1; }

        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            color: var(--text-muted);
            margin-bottom: 8px;
        }
        .metric-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.8rem;
            font-weight: 600;
            color: var(--text-primary);
        }
        .metric-change {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            margin-top: 6px;
            font-weight: 500;
        }
        .metric-change.up { color: var(--green); }
        .metric-change.down { color: var(--red); }

        .metric-card.spot .metric-value { color: var(--cyan); }
        .metric-card.iv .metric-value { color: var(--orange); }
        .metric-card.iv-rank .metric-value { color: var(--purple); }
        .metric-card.trend .metric-value { font-size: 1.3rem; }
        .trend-bullish { color: var(--green); }
        .trend-bearish { color: var(--red); }
        .trend-neutral { color: var(--orange); }
        .trend-strong-bullish { color: var(--green); text-shadow: 0 0 10px var(--green-glow); }
        .trend-strong-bearish { color: var(--red); text-shadow: 0 0 10px var(--red-glow); }

        /* ─── Greeks Dashboard ─── */
        .greeks-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 16px;
            margin-bottom: 40px;
        }

        .greek-box {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 28px 24px;
            text-align: center;
            transition: all 0.3s ease;
            position: relative;
        }
        .greek-box:hover {
            transform: scale(1.03);
            border-color: var(--accent);
        }
        .greek-symbol {
            font-size: 2.5rem;
            font-weight: 800;
            font-family: 'Inter', sans-serif;
            margin-bottom: 8px;
            background: linear-gradient(135deg, var(--accent), var(--cyan));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .greek-label {
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 12px;
        }
        .greek-value {
            font-family: 'JetBrains Mono', monospace;
            font-size: 1.4rem;
            font-weight: 600;
        }
        .greek-sub {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 6px;
        }

        /* ─── Options Chain ─── */
        .chain-container {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            overflow: hidden;
            margin-bottom: 40px;
        }
        .chain-header {
            display: grid;
            grid-template-columns: 1fr 1fr 80px;
            padding: 16px 24px;
            background: var(--bg-elevated);
            border-bottom: 1px solid var(--border);
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            color: var(--text-muted);
        }
        .chain-row {
            display: grid;
            grid-template-columns: 1fr 1fr 80px;
            padding: 12px 24px;
            border-bottom: 1px solid rgba(42, 49, 66, 0.5);
            transition: background 0.2s;
            align-items: center;
        }
        .chain-row:hover { background: var(--bg-elevated); }
        .chain-row:last-child { border-bottom: none; }

        .call-side, .put-side {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 8px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }
        .call-side { color: var(--green); }
        .put-side { color: var(--red); }
        .strike-col {
            text-align: center;
            font-weight: 700;
            color: var(--text-primary);
            font-size: 0.95rem;
        }
        .itm { font-weight: 700; }
        .itm.call { background: rgba(34, 197, 94, 0.08); border-radius: 6px; padding: 4px; }
        .itm.put { background: rgba(239, 68, 68, 0.08); border-radius: 6px; padding: 4px; }

        .chain-col-header {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-bottom: 4px;
        }

        /* ─── Strategy Cards ─── */
        .strategies-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .strategy-card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 28px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }
        .strategy-card::after {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; bottom: 0;
            background: linear-gradient(135deg, transparent 40%, rgba(99, 102, 241, 0.05) 100%);
            opacity: 0;
            transition: opacity 0.3s;
        }
        .strategy-card:hover {
            transform: translateY(-6px) scale(1.01);
            border-color: var(--accent);
            box-shadow: 0 25px 50px rgba(0,0,0,0.4), 0 0 30px var(--accent-glow);
        }
        .strategy-card:hover::after { opacity: 1; }
        .strategy-card:active { transform: translateY(-2px) scale(0.99); }

        .strategy-icon {
            width: 48px; height: 48px;
            border-radius: 14px;
            display: flex; align-items: center; justify-content: center;
            font-size: 1.5rem;
            margin-bottom: 16px;
        }
        .strategy-card.bull .strategy-icon { background: linear-gradient(135deg, rgba(34,197,94,0.2), rgba(34,197,94,0.05)); }
        .strategy-card.bear .strategy-icon { background: linear-gradient(135deg, rgba(239,68,68,0.2), rgba(239,68,68,0.05)); }
        .strategy-card.neutral .strategy-icon { background: linear-gradient(135deg, rgba(245,158,11,0.2), rgba(245,158,11,0.05)); }
        .strategy-card.vol .strategy-icon { background: linear-gradient(135deg, rgba(168,85,247,0.2), rgba(168,85,247,0.05)); }

        .strategy-name {
            font-size: 1.15rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .strategy-desc {
            color: var(--text-secondary);
            font-size: 0.9rem;
            line-height: 1.5;
            margin-bottom: 16px;
        }
        .strategy-tags {
            display: flex;
            gap: 8px;
            flex-wrap: wrap;
        }
        .tag {
            font-size: 0.7rem;
            padding: 4px 10px;
            border-radius: 20px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        .tag.debit { background: rgba(34,197,94,0.15); color: var(--green); }
        .tag.credit { background: rgba(239,68,68,0.15); color: var(--red); }
        .tag.def-risk { background: rgba(6,182,212,0.15); color: var(--cyan); }
        .tag.unlim { background: rgba(245,158,11,0.15); color: var(--orange); }

        /* ─── P&L Simulator ─── */
        .simulator-container {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 32px;
            margin-bottom: 40px;
        }
        .simulator-controls {
            display: flex;
            gap: 16px;
            margin-bottom: 24px;
            flex-wrap: wrap;
        }
        .sim-input {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            color: var(--text-primary);
            padding: 10px 14px;
            border-radius: 10px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.9rem;
            outline: none;
            width: 140px;
        }
        .sim-input:focus { border-color: var(--accent); }
        .sim-btn {
            background: linear-gradient(135deg, var(--accent), var(--purple));
            border: none;
            color: white;
            padding: 10px 24px;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .sim-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px var(--accent-glow);
        }

        .chart-container {
            position: relative;
            height: 320px;
        }

        /* ─── AI Suggestion Box ─── */
        .ai-box {
            background: linear-gradient(135deg, var(--bg-card), var(--bg-secondary));
            border: 1px solid var(--border);
            border-radius: 20px;
            padding: 32px;
            margin-bottom: 40px;
            position: relative;
            overflow: hidden;
        }
        .ai-box::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, var(--accent), var(--purple), var(--pink), var(--cyan), var(--accent));
            background-size: 200% auto;
            animation: gradientShift 3s linear infinite;
        }
        .ai-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 20px;
        }
        .ai-badge {
            background: linear-gradient(135deg, var(--accent), var(--purple));
            color: white;
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            display: flex; align-items: center; gap: 6px;
        }
        .ai-badge .pulse {
            width: 8px; height: 8px;
            background: #fff;
            border-radius: 50%;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
        }
        .ai-confidence {
            margin-left: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--text-muted);
        }
        .ai-confidence span { color: var(--accent); font-weight: 700; }

        .ai-strategy-name {
            font-size: 1.5rem;
            font-weight: 700;
            margin-bottom: 8px;
        }
        .ai-description {
            color: var(--text-secondary);
            line-height: 1.6;
            margin-bottom: 20px;
            max-width: 700px;
        }
        .ai-legs {
            display: flex;
            gap: 12px;
            flex-wrap: wrap;
        }
        .ai-leg {
            background: var(--bg-elevated);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 14px 18px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }
        .ai-leg .action { font-weight: 700; }
        .ai-leg .action.buy { color: var(--green); }
        .ai-leg .action.sell { color: var(--red); }

        /* ─── Footer ─── */
        .footer {
            text-align: center;
            padding: 40px 0;
            color: var(--text-muted);
            font-size: 0.85rem;
            border-top: 1px solid var(--border);
        }

        /* ─── Loading ─── */
        .loading {
            display: inline-block;
            width: 20px; height: 20px;
            border: 2px solid var(--border);
            border-top-color: var(--accent);
            border-radius: 50%;
            animation: spin 0.8s linear infinite;
        }
        @keyframes spin { to { transform: rotate(360deg); } }

        .skeleton {
            background: linear-gradient(90deg, var(--bg-elevated) 25%, var(--bg-card) 50%, var(--bg-elevated) 75%);
            background-size: 200% 100%;
            animation: skeleton 1.5s infinite;
            border-radius: 8px;
        }
        @keyframes skeleton { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }

        /* ─── Responsive ─── */
        @media (max-width: 768px) {
            .hero-title { font-size: 2rem; }
            .greeks-grid { grid-template-columns: repeat(2, 1fr); }
            .chain-header, .chain-row { grid-template-columns: 1fr; gap: 8px; }
            .call-side, .put-side { grid-template-columns: repeat(3, 1fr); }
        }
    </style>
</head>
<body>
    <div class="bg-mesh"></div>
    <div class="grid-overlay"></div>

    <div class="container">
        <!-- Navbar -->
        <nav class="navbar">
            <div class="logo">
                <div class="logo-icon">🔮</div>
                <span>Options Oracle</span>
            </div>
            <select class="ticker-select" id="tickerSelect">
                <option value="AAPL">AAPL</option>
                <option value="TSLA">TSLA</option>
                <option value="NVDA">NVDA</option>
                <option value="SPY">SPY</option>
                <option value="QQQ">QQQ</option>
                <option value="AMZN">AMZN</option>
                <option value="MSFT">MSFT</option>
                <option value="GOOGL">GOOGL</option>
                <option value="META">META</option>
                <option value="AMD">AMD</option>
            </select>
        </nav>

        <!-- Hero -->
        <section class="hero">
            <h1 class="hero-title">Options Oracle</h1>
            <p class="hero-subtitle">Advanced options analytics, Greeks visualization, and AI-powered strategy recommendations in real-time.</p>
        </section>

        <!-- Live Metrics -->
        <div class="section-header">Live Metrics</div>
        <div class="metrics-grid" id="metricsGrid">
            <div class="metric-card spot">
                <div class="metric-label">Spot Price</div>
                <div class="metric-value skeleton" style="height:36px;width:120px;"></div>
            </div>
            <div class="metric-card iv">
                <div class="metric-label">Implied Volatility</div>
                <div class="metric-value skeleton" style="height:36px;width:100px;"></div>
            </div>
            <div class="metric-card iv-rank">
                <div class="metric-label">IV Rank</div>
                <div class="metric-value skeleton" style="height:36px;width:80px;"></div>
            </div>
            <div class="metric-card">
                <div class="metric-label">IV Percentile</div>
                <div class="metric-value skeleton" style="height:36px;width:80px;"></div>
            </div>
            <div class="metric-card trend">
                <div class="metric-label">Trend</div>
                <div class="metric-value skeleton" style="height:36px;width:140px;"></div>
            </div>
        </div>

        <!-- Greeks Dashboard -->
        <div class="section-header">Greeks Dashboard</div>
        <div class="greeks-grid" id="greeksGrid">
            <div class="greek-box">
                <div class="greek-symbol">Δ</div>
                <div class="greek-label">Delta</div>
                <div class="greek-value skeleton" style="height:28px;width:80px;margin:0 auto;"></div>
                <div class="greek-sub skeleton" style="height:16px;width:60px;margin:6px auto 0;"></div>
            </div>
            <div class="greek-box">
                <div class="greek-symbol">Γ</div>
                <div class="greek-label">Gamma</div>
                <div class="greek-value skeleton" style="height:28px;width:80px;margin:0 auto;"></div>
                <div class="greek-sub skeleton" style="height:16px;width:60px;margin:6px auto 0;"></div>
            </div>
            <div class="greek-box">
                <div class="greek-symbol">Θ</div>
                <div class="greek-label">Theta</div>
                <div class="greek-value skeleton" style="height:28px;width:80px;margin:0 auto;"></div>
                <div class="greek-sub skeleton" style="height:16px;width:60px;margin:6px auto 0;"></div>
            </div>
            <div class="greek-box">
                <div class="greek-symbol">V</div>
                <div class="greek-label">Vega</div>
                <div class="greek-value skeleton" style="height:28px;width:80px;margin:0 auto;"></div>
                <div class="greek-sub skeleton" style="height:16px;width:60px;margin:6px auto 0;"></div>
            </div>
        </div>

        <!-- Options Chain -->
        <div class="section-header">Options Chain</div>
        <div class="chain-container" id="chainContainer">
            <div class="chain-header">
                <div style="color:var(--green);">Calls</div>
                <div style="color:var(--red);">Puts</div>
                <div>Strike</div>
            </div>
            <div id="chainBody">
                <div class="chain-row" style="justify-content:center;padding:40px;">
                    <div class="loading"></div>
                </div>
            </div>
        </div>

        <!-- Strategy Cards -->
        <div class="section-header">Strategy Builder</div>
        <div class="strategies-grid" id="strategiesGrid">
            <div class="strategy-card bull" onclick="selectStrategy('bull_call_spread')">
                <div class="strategy-icon">📈</div>
                <div class="strategy-name">Bull Call Spread</div>
                <div class="strategy-desc">Limited risk, limited reward bullish strategy. Buy ATM call, sell OTM call.</div>
                <div class="strategy-tags">
                    <span class="tag debit">Debit</span>
                    <span class="tag def-risk">Defined Risk</span>
                </div>
            </div>
            <div class="strategy-card bear" onclick="selectStrategy('bear_put_spread')">
                <div class="strategy-icon">📉</div>
                <div class="strategy-name">Bear Put Spread</div>
                <div class="strategy-desc">Limited risk bearish strategy. Buy ATM put, sell OTM put.</div>
                <div class="strategy-tags">
                    <span class="tag debit">Debit</span>
                    <span class="tag def-risk">Defined Risk</span>
                </div>
            </div>
            <div class="strategy-card neutral" onclick="selectStrategy('iron_condor')">
                <div class="strategy-icon">⚖️</div>
                <div class="strategy-name">Iron Condor</div>
                <div class="strategy-desc">Profit from low volatility. Sell OTM call & put spreads.</div>
                <div class="strategy-tags">
                    <span class="tag credit">Credit</span>
                    <span class="tag def-risk">Defined Risk</span>
                </div>
            </div>
            <div class="strategy-card vol" onclick="selectStrategy('straddle')">
                <div class="strategy-icon">🌊</div>
                <div class="strategy-name">Long Straddle</div>
                <div class="strategy-desc">Profit from large moves either direction. Buy ATM call & put.</div>
                <div class="strategy-tags">
                    <span class="tag debit">Debit</span>
                    <span class="tag unlim">Unlimited</span>
                </div>
            </div>
        </div>

        <!-- P&L Simulator -->
        <div class="section-header">P&L Simulator</div>
        <div class="simulator-container">
            <div class="simulator-controls">
                <input type="number" class="sim-input" id="simStrike" placeholder="Strike" value="185">
                <input type="number" class="sim-input" id="simPremium" placeholder="Premium" value="5.20" step="0.01">
                <input type="number" class="sim-input" id="simQty" placeholder="Qty" value="1">
                <select class="sim-input" id="simType" style="width:100px;">
                    <option value="call">Call</option>
                    <option value="put">Put</option>
                </select>
                <button class="sim-btn" onclick="runSimulation()">Run Simulation</button>
            </div>
            <div class="chart-container">
                <canvas id="pnlChart"></canvas>
            </div>
        </div>

        <!-- AI Suggestion -->
        <div class="section-header">AI Recommendation</div>
        <div class="ai-box" id="aiBox">
            <div class="ai-header">
                <div class="ai-badge"><span class="pulse"></span> Groq AI</div>
                <div class="ai-confidence">Confidence: <span id="aiConfidence">--</span>%</div>
            </div>
            <div class="ai-strategy-name" id="aiStrategyName">Analyzing market data...</div>
            <div class="ai-description" id="aiDescription">Please wait while our AI analyzes current market conditions and volatility surface.</div>
            <div class="ai-legs" id="aiLegs"></div>
        </div>

        <!-- Footer -->
        <div class="footer">
            Options Oracle — Advanced Options Analytics Platform. Data is simulated for demonstration.
        </div>
    </div>

    <script>
    // ─── State ───
    let currentTicker = 'AAPL';
    let pnlChart = null;
    let currentSpot = 185;

    // ─── Init ───
    document.addEventListener('DOMContentLoaded', () => {
        loadAllData();
        document.getElementById('tickerSelect').addEventListener('change', (e) => {
            currentTicker = e.target.value;
            loadAllData();
        });
    });

    async function loadAllData() {
        await Promise.all([
            loadMetrics(),
            loadGreeks(),
            loadChain(),
            loadAI()
        ]);
        runSimulation();
    }

    // ─── Metrics ───
    async function loadMetrics() {
        try {
            const res = await fetch(`/api/metrics/${currentTicker}`);
            const data = await res.json();
            currentSpot = data.spot;
            const grid = document.getElementById('metricsGrid');

            const trendClass = data.trend.toLowerCase().replace(' ', '-');
            const changeClass = data.change_pct >= 0 ? 'up' : 'down';
            const changeIcon = data.change_pct >= 0 ? '▲' : '▼';

            grid.innerHTML = `
                <div class="metric-card spot">
                    <div class="metric-label">Spot Price</div>
                    <div class="metric-value">$${data.spot.toFixed(2)}</div>
                    <div class="metric-change ${changeClass}">${changeIcon} ${Math.abs(data.change_pct)}% Today</div>
                </div>
                <div class="metric-card iv">
                    <div class="metric-label">Implied Volatility</div>
                    <div class="metric-value">${data.iv}%</div>
                    <div class="metric-change">IV Surface</div>
                </div>
                <div class="metric-card iv-rank">
                    <div class="metric-label">IV Rank</div>
                    <div class="metric-value">${data.iv_rank}</div>
                    <div class="metric-change">${data.iv_rank > 50 ? 'High' : 'Low'} relative to 52W</div>
                </div>
                <div class="metric-card">
                    <div class="metric-label">IV Percentile</div>
                    <div class="metric-value">${data.iv_percentile}%</div>
                    <div class="metric-change">252-day lookback</div>
                </div>
                <div class="metric-card trend">
                    <div class="metric-label">Trend</div>
                    <div class="metric-value trend-${trendClass}">${data.trend}</div>
                    <div class="metric-change">Market regime</div>
                </div>
            `;
        } catch (e) { console.error('Metrics error:', e); }
    }

    // ─── Greeks ───
    async function loadGreeks() {
        try {
            const res = await fetch(`/api/greeks/${currentTicker}`);
            const data = await res.json();
            const grid = document.getElementById('greeksGrid');

            grid.innerHTML = `
                <div class="greek-box">
                    <div class="greek-symbol">Δ</div>
                    <div class="greek-label">Delta</div>
                    <div class="greek-value" style="color:${data.delta.call > 0 ? 'var(--green)' : 'var(--red)'}">${data.delta.call > 0 ? '+' : ''}${data.delta.call}</div>
                    <div class="greek-sub">Call ATM</div>
                </div>
                <div class="greek-box">
                    <div class="greek-symbol">Γ</div>
                    <div class="greek-label">Gamma</div>
                    <div class="greek-value" style="color:var(--orange)">${data.gamma.call}</div>
                    <div class="greek-sub">Max at ATM</div>
                </div>
                <div class="greek-box">
                    <div class="greek-symbol">Θ</div>
                    <div class="greek-label">Theta</div>
                    <div class="greek-value" style="color:var(--red)">${data.theta.call}</div>
                    <div class="greek-sub">Daily decay</div>
                </div>
                <div class="greek-box">
                    <div class="greek-symbol">V</div>
                    <div class="greek-label">Vega</div>
                    <div class="greek-value" style="color:var(--purple)">${data.vega.call}</div>
                    <div class="greek-sub">Per 1% IV</div>
                </div>
            `;
        } catch (e) { console.error('Greeks error:', e); }
    }

    // ─── Options Chain ───
    async function loadChain() {
        try {
            const res = await fetch(`/api/chain/${currentTicker}`);
            const data = await res.json();
            const body = document.getElementById('chainBody');

            let html = '';
            const calls = data.calls;
            const puts = data.puts;

            for (let i = 0; i < calls.length; i++) {
                const c = calls[i];
                const p = puts[i];
                const isATM = Math.abs(c.strike - data.spot) < 3;

                html += `
                    <div class="chain-row" style="${isATM ? 'background:rgba(99,102,241,0.05);' : ''}">
                        <div class="call-side">
                            <div class="${c.itm ? 'itm call' : ''}">${c.bid.toFixed(2)}</div>
                            <div class="${c.itm ? 'itm call' : ''}">${c.ask.toFixed(2)}</div>
                            <div class="${c.itm ? 'itm call' : ''}">${c.last.toFixed(2)}</div>
                            <div class="${c.itm ? 'itm call' : ''}">${c.volume.toLocaleString()}</div>
                            <div class="${c.itm ? 'itm call' : ''}">${c.iv.toFixed(1)}%</div>
                        </div>
                        <div class="put-side">
                            <div class="${p.itm ? 'itm put' : ''}">${p.bid.toFixed(2)}</div>
                            <div class="${p.itm ? 'itm put' : ''}">${p.ask.toFixed(2)}</div>
                            <div class="${p.itm ? 'itm put' : ''}">${p.last.toFixed(2)}</div>
                            <div class="${p.itm ? 'itm put' : ''}">${p.volume.toLocaleString()}</div>
                            <div class="${p.itm ? 'itm put' : ''}">${p.iv.toFixed(1)}%</div>
                        </div>
                        <div class="strike-col" style="${isATM ? 'color:var(--accent);font-weight:800;' : ''}">${c.strike.toFixed(1)}</div>
                    </div>
                `;
            }
            body.innerHTML = html;
        } catch (e) { console.error('Chain error:', e); }
    }

    // ─── AI Suggestion ───
    async function loadAI() {
        try {
            const res = await fetch(`/api/ai-suggest/${currentTicker}`);
            const data = await res.json();

            document.getElementById('aiConfidence').textContent = data.confidence;
            document.getElementById('aiStrategyName').textContent = data.strategy;
            document.getElementById('aiDescription').innerHTML = 
                `${data.description}<br><br>` +
                `<span style="color:var(--text-muted);">Trend: <span style="color:var(--accent);">${data.trend}</span> · ` +
                `IV Assessment: <span style="color:var(--orange);">${data.iv_assessment}</span> · ` +
                `Spot: <span style="color:var(--cyan);">$${data.spot}</span></span>`;

            const legsContainer = document.getElementById('aiLegs');
            legsContainer.innerHTML = data.legs.map(leg => `
                <div class="ai-leg">
                    <span class="action ${leg.action}">${leg.action.toUpperCase()}</span> 
                    ${leg.qty}x ${leg.strike} ${leg.type.toUpperCase()}
                </div>
            `).join('');
        } catch (e) { console.error('AI error:', e); }
    }

    // ─── P&L Simulation ───
    async function runSimulation() {
        const strike = parseFloat(document.getElementById('simStrike').value);
        const premium = parseFloat(document.getElementById('simPremium').value);
        const qty = parseInt(document.getElementById('simQty').value);
        const type = document.getElementById('simType').value;

        const minPrice = strike * 0.7;
        const maxPrice = strike * 1.3;

        const legs = [{
            strike: strike,
            option_type: type,
            quantity: qty,
            premium: premium,
            expiry: "2024-12-20"
        }];

        try {
            const res = await fetch('/api/simulate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    ticker: currentTicker,
                    legs: legs,
                    price_range: [minPrice, maxPrice]
                })
            });
            const data = await res.json();
            renderPnlChart(data.results, strike);
        } catch (e) { console.error('Sim error:', e); }
    }

    function renderPnlChart(results, strike) {
        const ctx = document.getElementById('pnlChart').getContext('2d');

        if (pnlChart) pnlChart.destroy();

        const prices = results.map(r => r.price);
        const pnls = results.map(r => r.pnl);
        const maxPnL = Math.max(...pnls);
        const minPnL = Math.min(...pnls);

        // Create gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 300);
        gradient.addColorStop(0, 'rgba(99, 102, 241, 0.3)');
        gradient.addColorStop(1, 'rgba(99, 102, 241, 0.0)');

        pnlChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: prices.map(p => '$' + p.toFixed(0)),
                datasets: [{
                    label: 'P&L ($)',
                    data: pnls,
                    borderColor: '#6366f1',
                    backgroundColor: gradient,
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointRadius: 0,
                    pointHoverRadius: 6,
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: '#6366f1',
                    pointHoverBorderWidth: 2
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: 'index' },
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: '#1a1f2e',
                        titleColor: '#94a3b8',
                        bodyColor: '#f0f2f5',
                        borderColor: '#2a3142',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {
                            label: (ctx) => `P&L: $${ctx.parsed.y.toFixed(2)}`
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(42, 49, 66, 0.3)' },
                        ticks: { color: '#64748b', maxTicksLimit: 8 }
                    },
                    y: {
                        grid: { color: 'rgba(42, 49, 66, 0.3)' },
                        ticks: { 
                            color: '#64748b',
                            callback: (v) => '$' + v.toFixed(0)
                        },
                        position: 'right'
                    }
                },
                animation: {
                    duration: 1000,
                    easing: 'easeOutQuart'
                }
            }
        });
    }

    // ─── Strategy Selection ───
    function selectStrategy(name) {
        const cards = document.querySelectorAll('.strategy-card');
        cards.forEach(c => {
            c.style.borderColor = '';
            c.style.boxShadow = '';
        });
        event.currentTarget.style.borderColor = 'var(--accent)';
        event.currentTarget.style.boxShadow = '0 0 30px var(--accent-glow)';

        // Auto-fill simulator based on strategy
        const configs = {
            'bull_call_spread': { strike: Math.round(currentSpot/5)*5, type: 'call', premium: 3.50 },
            'bear_put_spread': { strike: Math.round(currentSpot/5)*5, type: 'put', premium: 3.20 },
            'iron_condor': { strike: Math.round(currentSpot/5)*5, type: 'call', premium: 2.80 },
            'straddle': { strike: Math.round(currentSpot/5)*5, type: 'call', premium: 6.40 }
        };
        const cfg = configs[name];
        if (cfg) {
            document.getElementById('simStrike').value = cfg.strike;
            document.getElementById('simPremium').value = cfg.premium;
            document.getElementById('simType').value = cfg.type;
            runSimulation();
        }
    }
    </script>
</body>
</html>
"""

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
