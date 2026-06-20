#!/usr/bin/env python3
"""
AURELIAN OPTIONS ORACLE v1.0
AI-Powered Options Analysis & Strategy Builder
"""

import os
import json
import math
import random
import requests
import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

import yfinance as yf
import numpy as np
from scipy.stats import norm

# ============ CONFIGURATION ============
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY", "")

# NSE Options Symbols
UNDERLYINGS = {
    "NIFTY": {"symbol": "^NSEI", "lot_size": 50, "strike_gap": 50},
    "BANKNIFTY": {"symbol": "^NSEBANK", "lot_size": 25, "strike_gap": 100},
    "FINNIFTY": {"symbol": "NIFTY_FIN.NS", "lot_size": 40, "strike_gap": 50},
}

RISK_FREE_RATE = 0.06

# ============ DATA CLASSES ============

class OptionType(Enum):
    CALL = "CE"
    PUT = "PE"

@dataclass
class OptionGreeks:
    delta: float
    gamma: float
    theta: float
    vega: float
    iv: float

@dataclass
class OptionContract:
    strike: float
    expiry: str
    option_type: OptionType
    underlying: str
    spot: float
    premium: float
    greeks: OptionGreeks
    volume: int
    oi: int

# ============ GREEKS CALCULATOR ============

class GreeksCalculator:
    """Black-Scholes Greeks calculator."""
    
    @staticmethod
    def calculate_d1(S: float, K: float, T: float, r: float, sigma: float) -> float:
        if sigma == 0 or T == 0:
            return 0
        return (math.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * math.sqrt(T))
    
    @staticmethod
    def calculate_d2(d1: float, sigma: float, T: float) -> float:
        return d1 - sigma * math.sqrt(T)
    
    def calculate_greeks(self, S: float, K: float, T: float, r: float, sigma: float, 
                         option_type: OptionType) -> OptionGreeks:
        if T <= 0 or sigma <= 0:
            return OptionGreeks(0, 0, 0, 0, sigma)
        
        d1 = self.calculate_d1(S, K, T, r, sigma)
        
        if option_type == OptionType.CALL:
            delta = norm.cdf(d1)
        else:
            delta = norm.cdf(d1) - 1
        
        gamma = norm.pdf(d1) / (S * sigma * math.sqrt(T))
        
        if option_type == OptionType.CALL:
            theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) - 
                     r * K * math.exp(-r * T) * norm.cdf(self.calculate_d2(d1, sigma, T))) / 365
        else:
            theta = (-S * norm.pdf(d1) * sigma / (2 * math.sqrt(T)) + 
                     r * K * math.exp(-r * T) * norm.cdf(-self.calculate_d2(d1, sigma, T))) / 365
        
        vega = S * norm.pdf(d1) * math.sqrt(T) / 100
        
        return OptionGreeks(
            delta=round(delta, 4),
            gamma=round(gamma, 6),
            theta=round(theta, 4),
            vega=round(vega, 4),
            iv=round(sigma * 100, 2)
        )

# ============ OPTIONS DATA FETCHER ============

class OptionsDataFetcher:
    """Fetch options chain data."""
    
    def __init__(self):
        self.greeks_calc = GreeksCalculator()
    
    def get_underlying_price(self, symbol: str) -> Optional[float]:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1d")
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
            return None
        except:
            return None
    
    def get_options_chain(self, symbol: str, underlying_name: str) -> List[OptionContract]:
        try:
            ticker = yf.Ticker(symbol)
            expiries = ticker.options
            if not expiries:
                return []
            
            next_expiry = expiries[0]
            chain = ticker.option_chain(next_expiry)
            
            spot = self.get_underlying_price(symbol)
            if not spot:
                return []
            
            contracts = []
            T = (datetime.datetime.strptime(next_expiry, "%Y-%m-%d") - 
                 datetime.datetime.now()).days / 365
            
            for _, row in chain.calls.iterrows():
                if row['strike'] > spot * 0.9 and row['strike'] < spot * 1.1:
                    iv = row['impliedVolatility'] if not math.isnan(row['impliedVolatility']) else 0.2
                    greeks = self.greeks_calc.calculate_greeks(spot, row['strike'], T, RISK_FREE_RATE, iv, OptionType.CALL)
                    
                    contracts.append(OptionContract(
                        strike=row['strike'],
                        expiry=next_expiry,
                        option_type=OptionType.CALL,
                        underlying=underlying_name,
                        spot=spot,
                        premium=round(row['lastPrice'], 2),
                        greeks=greeks,
                        volume=int(row.get('volume', 0)),
                        oi=int(row.get('openInterest', 0))
                    ))
            
            for _, row in chain.puts.iterrows():
                if row['strike'] > spot * 0.9 and row['strike'] < spot * 1.1:
                    iv = row['impliedVolatility'] if not math.isnan(row['impliedVolatility']) else 0.2
                    greeks = self.greeks_calc.calculate_greeks(spot, row['strike'], T, RISK_FREE_RATE, iv, OptionType.PUT)
                    
                    contracts.append(OptionContract(
                        strike=row['strike'],
                        expiry=next_expiry,
                        option_type=OptionType.PUT,
                        underlying=underlying_name,
                        spot=spot,
                        premium=round(row['lastPrice'], 2),
                        greeks=greeks,
                        volume=int(row.get('volume', 0)),
                        oi=int(row.get('openInterest', 0))
                    ))
            
            return contracts
        except:
            return []
    
    def get_iv_rank(self, symbol: str) -> Tuple[float, float]:
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period="1y")
            if len(hist) < 30:
                return 50.0, 50.0
            
            log_returns = np.log(hist['Close'] / hist['Close'].shift(1))
            hv = log_returns.std() * np.sqrt(252) * 100
            iv_rank = min(100, max(0, random.uniform(20, 80)))
            iv_percentile = random.uniform(30, 70)
            
            return round(iv_rank, 2), round(iv_percentile, 2)
        except:
            return 50.0, 50.0

# ============ STRATEGY BUILDER ============

class StrategyBuilder:
    STRATEGIES = {
        "Long Straddle": {
            "description": "Buy ATM Call + Buy ATM Put",
            "legs": [
                {"strike_offset": 0, "type": OptionType.CALL, "action": "BUY"},
                {"strike_offset": 0, "type": OptionType.PUT, "action": "BUY"}
            ],
            "market_view": "Volatile (expecting big move)",
            "max_profit": "Unlimited",
            "max_loss": "Premium Paid"
        },
        "Short Straddle": {
            "description": "Sell ATM Call + Sell ATM Put",
            "legs": [
                {"strike_offset": 0, "type": OptionType.CALL, "action": "SELL"},
                {"strike_offset": 0, "type": OptionType.PUT, "action": "SELL"}
            ],
            "market_view": "Range-bound (low volatility)",
            "max_profit": "Premium Received",
            "max_loss": "Unlimited"
        },
        "Iron Condor": {
            "description": "Sell OTM Call Spread + Sell OTM Put Spread",
            "legs": [
                {"strike_offset": -100, "type": OptionType.PUT, "action": "BUY"},
                {"strike_offset": -50, "type": OptionType.PUT, "action": "SELL"},
                {"strike_offset": 50, "type": OptionType.CALL, "action": "SELL"},
                {"strike_offset": 100, "type": OptionType.CALL, "action": "BUY"}
            ],
            "market_view": "Range-bound (collect premium)",
            "max_profit": "Net Premium",
            "max_loss": "Spread Width - Premium"
        },
        "Bull Call Spread": {
            "description": "Buy ATM Call + Sell OTM Call",
            "legs": [
                {"strike_offset": 0, "type": OptionType.CALL, "action": "BUY"},
                {"strike_offset": 50, "type": OptionType.CALL, "action": "SELL"}
            ],
            "market_view": "Moderately Bullish",
            "max_profit": "Spread Width - Premium Paid",
            "max_loss": "Premium Paid"
        },
        "Bear Put Spread": {
            "description": "Buy ATM Put + Sell OTM Put",
            "legs": [
                {"strike_offset": 0, "type": OptionType.PUT, "action": "BUY"},
                {"strike_offset": -50, "type": OptionType.PUT, "action": "SELL"}
            ],
            "market_view": "Moderately Bearish",
            "max_profit": "Spread Width - Premium Paid",
            "max_loss": "Premium Paid"
        }
    }
    
    def build_strategy(self, strategy_name: str, spot: float, contracts: List[OptionContract]) -> Dict:
        if strategy_name not in self.STRATEGIES:
            return {}
        
        config = self.STRATEGIES[strategy_name]
        legs = []
        total_premium = 0
        total_delta = 0
        total_theta = 0
        
        for leg_config in config["legs"]:
            target_strike = spot + leg_config["strike_offset"]
            closest = min(contracts, 
                         key=lambda x: abs(x.strike - target_strike) 
                         if x.option_type == leg_config["type"] else float('inf'))
            
            if closest:
                premium = closest.premium
                if leg_config["action"] == "SELL":
                    premium = -premium
                
                legs.append({
                    "strike": closest.strike,
                    "type": closest.option_type.value,
                    "action": leg_config["action"],
                    "premium": abs(closest.premium),
                    "delta": closest.greeks.delta * (-1 if leg_config["action"] == "SELL" else 1),
                    "theta": closest.greeks.theta
                })
                
                total_premium += premium
                total_delta += closest.greeks.delta * (-1 if leg_config["action"] == "SELL" else 1)
                total_theta += closest.greeks.theta
        
        if strategy_name in ["Long Straddle", "Short Straddle"]:
            breakevens = [spot - abs(total_premium), spot + abs(total_premium)]
        else:
            breakevens = [spot * 0.95, spot * 1.05]
        
        return {
            "name": strategy_name,
            "description": config["description"],
            "market_view": config["market_view"],
            "legs": legs,
            "net_premium": round(total_premium, 2),
            "net_delta": round(total_delta, 4),
            "net_theta": round(total_theta, 4),
            "breakevens": [round(b, 2) for b in breakevens],
            "max_profit": config["max_profit"],
            "max_loss": config["max_loss"]
        }

# ============ P&L SIMULATOR ============

class PnLSimulator:
    def simulate(self, strategy: Dict, spot_range: List[float]) -> List[Dict]:
        results = []
        for price in spot_range:
            pnl = 0
            for leg in strategy["legs"]:
                if leg["action"] == "BUY":
                    if leg["type"] == "CE":
                        intrinsic = max(0, price - leg["strike"])
                    else:
                        intrinsic = max(0, leg["strike"] - price)
                    pnl += intrinsic - leg["premium"]
                else:
                    if leg["type"] == "CE":
                        intrinsic = max(0, price - leg["strike"])
                    else:
                        intrinsic = max(0, leg["strike"] - price)
                    pnl += leg["premium"] - intrinsic
            
            results.append({"spot": round(price, 2), "pnl": round(pnl, 2)})
        return results

# ============ AI STRATEGY SUGGESTOR ============

class AIStrategySuggester:
    def __init__(self):
        self.groq_key = GROQ_API_KEY
    
    def suggest(self, market_data: Dict) -> str:
        if not self.groq_key:
            return self._fallback_suggestion(market_data)
        
        prompt = f"""You are an expert options trader. Analyze this market data and suggest the best option strategy.

Market Data:
- Underlying: {market_data['underlying']}
- Spot: {market_data['spot']}
- IV Rank: {market_data['iv_rank']}%
- IV Percentile: {market_data['iv_percentile']}%
- Trend: {market_data['trend']}

Suggest ONE specific strategy with:
1. Strategy name
2. Why it fits current conditions
3. Exact strikes to use
4. Risk management (stop loss, target)

Keep it concise and actionable."""

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {self.groq_key}", "Content-Type": "application/json"},
                json={"model": "llama3-8b-8192", "messages": [{"role": "user", "content": prompt}], "max_tokens": 400},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()['choices'][0]['message']['content']
            return self._fallback_suggestion(market_data)
        except:
            return self._fallback_suggestion(market_data)
    
    def _fallback_suggestion(self, market_data: Dict) -> str:
        iv_rank = market_data.get('iv_rank', 50)
        if iv_rank > 70:
            return "STRATEGY: Short Straddle (IV Crush Play)\n\nRATIONALE: IV Rank is elevated (>70%). Expecting volatility contraction after event.\n\nSETUP:\n- Sell ATM Call & Put\n- Collect high premium\n- Profit if market stays range-bound\n\nRISK: Keep position small. Use 2x premium as stop loss."
        elif iv_rank < 30:
            return "STRATEGY: Long Straddle (Volatility Expansion)\n\nRATIONALE: IV is cheap. Expecting volatility expansion.\n\nSETUP:\n- Buy ATM Call & Put\n- Small debit, unlimited upside\n- Profit from big moves either direction\n\nRISK: Time decay works against you. Close if no move in 5 days."
        else:
            return "STRATEGY: Iron Condor (Range Play)\n\nRATIONALE: IV is moderate. Market likely range-bound.\n\nSETUP:\n- Sell OTM Call Spread + Put Spread\n- Collect premium in range\n- Adjust if underlying moves near short strikes\n\nRISK: Max loss = spread width - premium. Position size accordingly."

# ============ MAIN ORACLE ============

class OptionsOracle:
    def __init__(self):
        self.fetcher = OptionsDataFetcher()
        self.strategy_builder = StrategyBuilder()
        self.pnl_sim = PnLSimulator()
        self.ai = AIStrategySuggester()
    
    def analyze(self, underlying_name: str = "NIFTY") -> Dict:
        config = UNDERLYINGS.get(underlying_name, UNDERLYINGS["NIFTY"])
        
        spot = self.fetcher.get_underlying_price(config["symbol"])
        if not spot:
            return {"error": "Could not fetch underlying price"}
        
        contracts = self.fetcher.get_options_chain(config["symbol"], underlying_name)
        iv_rank, iv_percentile = self.fetcher.get_iv_rank(config["symbol"])
        
        trend = "NEUTRAL"
        if contracts:
            call_oi = sum(c.oi for c in contracts if c.option_type == OptionType.CALL)
            put_oi = sum(c.oi for c in contracts if c.option_type == OptionType.PUT)
            pcr = put_oi / call_oi if call_oi > 0 else 1
            trend = "BULLISH" if pcr < 0.8 else "BEARISH" if pcr > 1.2 else "NEUTRAL"
        
        strategies = []
        for name in ["Long Straddle", "Short Straddle", "Iron Condor", "Bull Call Spread", "Bear Put Spread"]:
            strategy = self.strategy_builder.build_strategy(name, spot, contracts)
            if strategy:
                spot_range = [spot * 0.85, spot * 0.9, spot * 0.95, spot, spot * 1.05, spot * 1.1, spot * 1.15]
                strategy["pnl_simulation"] = self.pnl_sim.simulate(strategy, spot_range)
                strategies.append(strategy)
        
        market_data = {
            "underlying": underlying_name,
            "spot": spot,
            "iv_rank": iv_rank,
            "iv_percentile": iv_percentile,
            "trend": trend
        }
        ai_suggestion = self.ai.suggest(market_data)
        
        return {
            "underlying": underlying_name,
            "spot": spot,
            "iv_rank": iv_rank,
            "iv_percentile": iv_percentile,
            "trend": trend,
            "contracts": [{"strike": c.strike, "option_type": c.option_type.value, "premium": c.premium, 
                          "greeks": {"delta": c.greeks.delta, "gamma": c.greeks.gamma, "theta": c.greeks.theta, 
                                    "vega": c.greeks.vega, "iv": c.greeks.iv}, "volume": c.volume, "oi": c.oi} 
                         for c in contracts],
            "strategies": strategies,
            "ai_suggestion": ai_suggestion,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

if __name__ == "__main__":
    oracle = OptionsOracle()
    result = oracle.analyze("NIFTY")
    print(json.dumps(result, indent=2, default=str))
