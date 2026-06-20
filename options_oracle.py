from flask import Flask, render_template_string, jsonify
import os
from options_oracle import OptionsOracle, UNDERLYINGS

app = Flask(__name__)

oracle = OptionsOracle()

# ============ STUNNING HTML DASHBOARD ============

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Aurelian Options Oracle | Claude AI-Powered Options Intelligence</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { 
            font-family: 'Segoe UI', system-ui, sans-serif; 
            background: #050508; 
            color: #e0e0e0;
        }
        
        /* HERO SECTION */
        .hero {
            background: linear-gradient(135deg, #0a0a1a 0%, #1a0a2e 50%, #0a1a2e 100%);
            padding: 60px 20px;
            text-align: center;
            border-bottom: 3px solid #00d4ff;
            position: relative;
            overflow: hidden;
        }
        .hero::before {
            content: '';
            position: absolute;
            top: -50%; left: -50%;
            width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(0,212,255,0.1) 0%, transparent 70%);
            animation: rotate 20s linear infinite;
        }
        @keyframes rotate {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        .hero h1 {
            font-size: 3.5em;
            background: linear-gradient(90deg, #00d4ff, #7b2dff, #ff2d7b);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            position: relative;
        }
        .hero .subtitle {
            color: #888;
            font-size: 1.2em;
            margin-top: 10px;
        }
        .hero .badge {
            display: inline-block;
            background: rgba(0,212,255,0.2);
            border: 1px solid #00d4ff;
            color: #00d4ff;
            padding: 8px 20px;
            border-radius: 20px;
            margin-top: 20px;
            font-size: 0.9em;
        }
        
        /* METRICS BAR */
        .metrics {
            display: flex;
            justify-content: center;
            gap: 30px;
            padding: 30px;
            background: #0a0a1a;
            border-bottom: 1px solid #1a1a3e;
        }
        .metric-box {
            text-align: center;
            padding: 20px 40px;
            background: #111;
            border-radius: 15px;
            border: 1px solid #222;
            min-width: 150px;
        }
        .metric-value {
            font-size: 2em;
            font-weight: bold;
            color: #00d4ff;
        }
        .metric-label {
            color: #888;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        /* MAIN GRID */
        .main-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            padding: 30px;
            max-width: 1400px;
            margin: 0 auto;
        }
        
        /* PANELS */
        .panel {
            background: #0f0f1a;
            border: 1px solid #1a1a3e;
            border-radius: 20px;
            padding: 25px;
        }
        .panel h2 {
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 1.3em;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        /* OPTIONS CHAIN TABLE */
        .chain-table {
            width: 100%;
            border-collapse: collapse;
        }
        .chain-table th {
            background: #1a1a3e;
            padding: 12px;
            text-align: center;
            color: #888;
            font-size: 0.85em;
        }
        .chain-table td {
            padding: 10px;
            text-align: center;
            border-bottom: 1px solid #1a1a3e;
        }
        .chain-table tr:hover {
            background: #1a1a2e;
        }
        .call-side { color: #00ff88; }
        .put-side { color: #ff4444; }
        .strike-col { 
            background: #1a1a3e; 
            font-weight: bold;
            color: #ffd700;
        }
        
        /* GREEKS DISPLAY */
        .greeks-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
        }
        .greek-box {
            background: #111;
            padding: 20px;
            border-radius: 12px;
            text-align: center;
            border: 1px solid #222;
        }
        .greek-value {
            font-size: 1.8em;
            font-weight: bold;
        }
        .greek-label {
            color: #888;
            font-size: 0.85em;
            margin-top: 5px;
        }
        
        /* STRATEGY CARDS */
        .strategy-card {
            background: #111;
            border: 1px solid #222;
            border-radius: 15px;
            padding: 20px;
            margin: 15px 0;
            transition: transform 0.2s;
            cursor: pointer;
        }
        .strategy-card:hover {
            transform: translateX(10px);
            border-color: #00d4ff;
        }
        .strategy-name {
            color: #ffd700;
            font-size: 1.2em;
            font-weight: bold;
        }
        .strategy-desc {
            color: #888;
            font-size: 0.9em;
            margin: 5px 0;
        }
        .strategy-metrics {
            display: flex;
            gap: 20px;
            margin-top: 10px;
        }
        .strategy-metric {
            background: #1a1a2e;
            padding: 8px 15px;
            border-radius: 8px;
            font-size: 0.85em;
        }
        
        /* P&L CHART */
        .pnl-chart {
            height: 200px;
            background: #111;
            border-radius: 12px;
            padding: 15px;
            position: relative;
        }
        .pnl-bar {
            position: absolute;
            bottom: 0;
            width: 60px;
            background: linear-gradient(to top, #00ff88, #00d4ff);
            border-radius: 5px 5px 0 0;
            transition: height 0.5s;
        }
        .pnl-bar.negative {
            background: linear-gradient(to top, #ff4444, #ff8844);
        }
        
        /* AI SUGGESTION BOX */
        .ai-box {
            background: linear-gradient(135deg, #1a0a2e, #0a1a2e);
            border: 2px solid #7b2dff;
            border-radius: 20px;
            padding: 30px;
            margin: 30px;
            position: relative;
        }
        .ai-box::before {
            content: '🤖';
            position: absolute;
            top: -20px;
            left: 30px;
            background: #7b2dff;
            padding: 10px 20px;
            border-radius: 20px;
            font-size: 1.2em;
        }
        .ai-content {
            margin-top: 20px;
            line-height: 1.8;
            white-space: pre-wrap;
        }
        
        /* UNDERLYING SELECTOR */
        .selector {
            display: flex;
            justify-content: center;
            gap: 15px;
            padding: 20px;
            background: #0a0a1a;
        }
        .selector-btn {
            background: #1a1a3e;
            border: 2px solid transparent;
            color: #fff;
            padding: 12px 30px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 1em;
            transition: all 0.2s;
        }
        .selector-btn:hover, .selector-btn.active {
            border-color: #00d4ff;
            background: rgba(0,212,255,0.1);
        }
        
        /* FOOTER */
        .footer {
            text-align: center;
            padding: 40px;
            color: #888;
            border-top: 1px solid #1a1a3e;
        }
    </style>
</head>
<body>
    <!-- HERO -->
    <div class="hero">
        <h1>🔮 AURELIAN OPTIONS ORACLE</h1>
        <p class="subtitle">Claude AI-Powered Options Intelligence & Strategy Builder</p>
        <div class="badge">⚡ Real-Time Greeks | 🤖 Claude AI Strategies | 📊 P&L Simulator</div>
    </div>
    
    <!-- UNDERLYING SELECTOR -->
    <div class="selector">
        <button class="selector-btn active" onclick="loadUnderlying('NIFTY')">NIFTY</button>
        <button class="selector-btn" onclick="loadUnderlying('BANKNIFTY')">BANKNIFTY</button>
        <button class="selector-btn" onclick="loadUnderlying('FINNIFTY')">FINNIFTY</button>
    </div>
    
    <!-- METRICS -->
    <div class="metrics">
        <div class="metric-box">
            <div class="metric-value" id="spotPrice">--</div>
            <div class="metric-label">Spot Price</div>
        </div>
        <div class="metric-box">
            <div class="metric-value" id="ivRank">--</div>
            <div class="metric-label">IV Rank</div>
        </div>
        <div class="metric-box">
            <div class="metric-value" id="ivPercentile">--</div>
            <div class="metric-label">IV Percentile</div>
        </div>
        <div class="metric-box">
            <div class="metric-value" id="trend">--</div>
            <div class="metric-label">Market Trend</div>
        </div>
    </div>
    
    <!-- MAIN GRID -->
    <div class="main-grid">
        <!-- OPTIONS CHAIN -->
        <div class="panel">
            <h2>📊 Options Chain</h2>
            <table class="chain-table" id="optionsChain">
                <tr>
                    <th>CALL OI</th>
                    <th>CALL IV</th>
                    <th>CALL LTP</th>
                    <th class="strike-col">STRIKE</th>
                    <th>PUT LTP</th>
                    <th>PUT IV</th>
                    <th>PUT OI</th>
                </tr>
            </table>
        </div>
        
        <!-- GREEKS -->
        <div class="panel">
            <h2>📈 ATM Greeks</h2>
            <div class="greeks-grid" id="greeksGrid">
                <div class="greek-box">
                    <div class="greek-value" style="color: #00ff88;" id="delta">--</div>
                    <div class="greek-label">Delta</div>
                </div>
                <div class="greek-box">
                    <div class="greek-value" style="color: #ffd700;" id="gamma">--</div>
                    <div class="greek-label">Gamma</div>
                </div>
                <div class="greek-box">
                    <div class="greek-value" style="color: #ff8844;" id="theta">--</div>
                    <div class="greek-label">Theta</div>
                </div>
                <div class="greek-box">
                    <div class="greek-value" style="color: #8844ff;" id="vega">--</div>
                    <div class="greek-label">Vega</div>
                </div>
            </div>
        </div>
        
        <!-- STRATEGIES -->
        <div class="panel">
            <h2>🎯 Claude AI Strategy Builder</h2>
            <div id="strategiesList">
                <p style="color: #888;">Loading strategies...</p>
            </div>
        </div>
        
        <!-- P&L SIMULATOR -->
        <div class="panel">
            <h2>💰 P&L Simulator</h2>
            <div class="pnl-chart" id="pnlChart">
                <p style="color: #888; text-align: center; padding-top: 80px;">Select a strategy to view P&L</p>
            </div>
        </div>
    </div>
    
    <!-- AI SUGGESTION -->
    <div class="ai-box">
        <h2 style="color: #7b2dff;">🤖 Claude AI Strategy Recommendation</h2>
        <div class="ai-content" id="aiSuggestion">
            Loading AI analysis...
        </div>
    </div>
    
    <!-- FOOTER -->
    <div class="footer">
        <p>Built with Python | Flask | Claude AI (Anthropic) | Black-Scholes | Real-time NSE Data</p>
        <p style="margin-top: 10px; color: #555;">Aurelian Academy | Grade 12 Capstone Project</p>
    </div>
    
    <script>
        let currentData = null;
        
        function loadUnderlying(underlying) {
            document.querySelectorAll('.selector-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            
            fetch('/api/analyze/' + underlying)
                .then(res => res.json())
                .then(data => {
                    currentData = data;
                    updateDashboard(data);
                });
        }
        
        function updateDashboard(data) {
            document.getElementById('spotPrice').textContent = '₹' + data.spot.toFixed(2);
            document.getElementById('ivRank').textContent = data.iv_rank + '%';
            document.getElementById('ivPercentile').textContent = data.iv_percentile + '%';
            document.getElementById('trend').textContent = data.trend;
            document.getElementById('trend').style.color = data.trend === 'BULLISH' ? '#00ff88' : 
                                                           data.trend === 'BEARISH' ? '#ff4444' : '#ffd700';
            
            const chainTable = document.getElementById('optionsChain');
            chainTable.innerHTML = `
                <tr>
                    <th>CALL OI</th>
                    <th>CALL IV</th>
                    <th>CALL LTP</th>
                    <th class="strike-col">STRIKE</th>
                    <th>PUT LTP</th>
                    <th>PUT IV</th>
                    <th>PUT OI</th>
                </tr>
            `;
            
            if (data.contracts) {
                const strikes = [...new Set(data.contracts.map(c => c.strike))].sort((a,b) => a-b);
                strikes.forEach(strike => {
                    const call = data.contracts.find(c => c.strike === strike && c.option_type === 'CE');
                    const put = data.contracts.find(c => c.strike === strike && c.option_type === 'PE');
                    
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td class="call-side">${call ? call.oi : '--'}</td>
                        <td class="call-side">${call ? call.greeks.iv + '%' : '--'}</td>
                        <td class="call-side">₹${call ? call.premium : '--'}</td>
                        <td class="strike-col">${strike}</td>
                        <td class="put-side">₹${put ? put.premium : '--'}</td>
                        <td class="put-side">${put ? put.greeks.iv + '%' : '--'}</td>
                        <td class="put-side">${put ? put.oi : '--'}</td>
                    `;
                    chainTable.appendChild(row);
                });
            }
            
            if (data.contracts && data.contracts.length > 0) {
                const atm = data.contracts.reduce((prev, curr) => 
                    Math.abs(curr.strike - data.spot) < Math.abs(prev.strike - data.spot) ? curr : prev
                );
                document.getElementById('delta').textContent = atm.greeks.delta;
                document.getElementById('gamma').textContent = atm.greeks.gamma;
                document.getElementById('theta').textContent = atm.greeks.theta;
                document.getElementById('vega').textContent = atm.greeks.vega;
            }
            
            const strategiesList = document.getElementById('strategiesList');
            strategiesList.innerHTML = '';
            if (data.strategies) {
                data.strategies.forEach((strat, idx) => {
                    const card = document.createElement('div');
                    card.className = 'strategy-card';
                    card.onclick = () => showPnL(idx);
                    card.innerHTML = `
                        <div class="strategy-name">${strat.name}</div>
                        <div class="strategy-desc">${strat.description}</div>
                        <div class="strategy-metrics">
                            <span class="strategy-metric" style="color: #00ff88;">Net: ₹${strat.net_premium}</span>
                            <span class="strategy-metric" style="color: #ffd700;">Δ: ${strat.net_delta}</span>
                            <span class="strategy-metric" style="color: #ff8844;">θ: ${strat.net_theta}</span>
                        </div>
                    `;
                    strategiesList.appendChild(card);
                });
            }
            
            document.getElementById('aiSuggestion').textContent = data.ai_suggestion || 'AI analysis loading...';
        }
        
        function showPnL(strategyIdx) {
            if (!currentData || !currentData.strategies) return;
            const strat = currentData.strategies[strategyIdx];
            const chart = document.getElementById('pnlChart');
            
            let html = '<div style="display: flex; justify-content: space-around; align-items: flex-end; height: 100%; padding: 0 20px;">';
            const maxPnL = Math.max(...strat.pnl_simulation.map(p => Math.abs(p.pnl)));
            
            strat.pnl_simulation.forEach(p => {
                const height = Math.abs(p.pnl) / maxPnL * 150;
                const isProfit = p.pnl >= 0;
                html += `
                    <div style="text-align: center;">
                        <div style="font-size: 0.75em; color: #888; margin-bottom: 5px;">₹${p.pnl}</div>
                        <div class="pnl-bar ${isProfit ? '' : 'negative'}" style="height: ${height}px; left: auto; position: relative;"></div>
                        <div style="font-size: 0.75em; color: #888; margin-top: 5px;">${p.spot}</div>
                    </div>
                `;
            });
            html += '</div>';
            chart.innerHTML = html;
        }
        
        window.onload = () => {
            fetch('/api/analyze/NIFTY')
                .then(res => res.json())
                .then(data => {
                    currentData = data;
                    updateDashboard(data);
                });
        };
    </script>
</body>
</html>
"""

# ============ API ROUTES ============

@app.route('/')
def dashboard():
    return render_template_string(DASHBOARD_HTML)

@app.route('/api/analyze/<underlying>')
def analyze(underlying):
    result = oracle.analyze(underlying.upper())
    return jsonify(result)

# ============ RUN ============

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
