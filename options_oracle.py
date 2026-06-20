"""
Options Oracle — Core engine for options pricing, Greeks, and IV calculations.
"""
import math
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import random

# ─── Constants ──────────────────────────────────────────────
UNDERLYINGS = ["AAPL", "TSLA", "NVDA", "SPY", "QQQ", "AMZN", "MSFT", "GOOGL", "META", "AMD"]

@dataclass
class OptionLeg:
    """Single option leg for strategy construction."""
    strike: float
    expiry: str
    option_type: str  # 'call' or 'put'
    quantity: int
    premium: float

@dataclass
class Greeks:
    """Option Greeks."""
    delta: float
    gamma: float
    theta: float
    vega: float
    rho: float

@dataclass
class OptionContract:
    """Single option contract data."""
    strike: float
    expiry: str
    option_type: str
    bid: float
    ask: float
    last: float
    volume: int
    open_interest: int
    iv: float
    delta: float
    gamma: float
    theta: float
    vega: float
    itm: bool

class OptionsOracle:
    """Main engine for options analysis."""

    def __init__(self, ticker: str = "AAPL"):
        self.ticker = ticker.upper()
        self.spot = self._get_spot_price()
        self.historical_iv = self._get_historical_iv()
        self.iv_rank = self._calc_iv_rank()
        self.iv_percentile = self._calc_iv_percentile()
        self.trend = self._detect_trend()

    def _get_spot_price(self) -> float:
        """Simulated spot price (replace with real API)."""
        base_prices = {
            "AAPL": 185.0, "TSLA": 245.0, "NVDA": 890.0, "SPY": 520.0,
            "QQQ": 440.0, "AMZN": 180.0, "MSFT": 420.0, "GOOGL": 175.0,
            "META": 500.0, "AMD": 165.0
        }
        base = base_prices.get(self.ticker, 100.0)
        # Add small random movement
        return round(base + random.uniform(-2.0, 2.0), 2)

    def _get_historical_iv(self) -> List[float]:
        """Simulated 252-day historical IV data."""
        base_iv = 0.30
        if self.ticker in ["TSLA", "NVDA", "AMD"]:
            base_iv = 0.55
        elif self.ticker in ["AAPL", "AMZN", "META"]:
            base_iv = 0.35
        elif self.ticker in ["SPY", "QQQ"]:
            base_iv = 0.18

        # Generate 252 days of IV with mean reversion
        iv_data = []
        current = base_iv
        for _ in range(252):
            change = random.uniform(-0.02, 0.02)
            current = max(0.10, min(0.80, current + change))
            iv_data.append(current)
        return iv_data

    def _calc_iv_rank(self) -> float:
        """Calculate IV Rank (0-100)."""
        if not self.historical_iv:
            return 50.0
        current_iv = self.historical_iv[-1]
        min_iv = min(self.historical_iv)
        max_iv = max(self.historical_iv)
        if max_iv == min_iv:
            return 50.0
        rank = (current_iv - min_iv) / (max_iv - min_iv) * 100
        return round(rank, 1)

    def _calc_iv_percentile(self) -> float:
        """Calculate IV Percentile (0-100)."""
        if not self.historical_iv:
            return 50.0
        current_iv = self.historical_iv[-1]
        count_below = sum(1 for iv in self.historical_iv if iv < current_iv)
        percentile = (count_below / len(self.historical_iv)) * 100
        return round(percentile, 1)

    def _detect_trend(self) -> str:
        """Detect market trend based on simulated price action."""
        trends = ["Bullish", "Bearish", "Neutral", "Strong Bullish", "Strong Bearish"]
        weights = [0.25, 0.20, 0.30, 0.15, 0.10]
        return random.choices(trends, weights=weights)[0]

    def get_metrics(self) -> Dict:
        """Get all live metrics for the ticker."""
        current_iv = self.historical_iv[-1] if self.historical_iv else 0.30
        return {
            "ticker": self.ticker,
            "spot": self.spot,
            "iv": round(current_iv * 100, 1),
            "iv_rank": self.iv_rank,
            "iv_percentile": self.iv_percentile,
            "trend": self.trend,
            "change_pct": round(random.uniform(-2.5, 2.5), 2),
            "volume": random.randint(5000000, 50000000),
        }

    def _black_scholes_greeks(self, S: float, K: float, T: float, r: float, sigma: float, option_type: str) -> Tuple[float, Greeks]:
        """Calculate option price and Greeks using Black-Scholes."""
        from math import log, sqrt, exp, pi

        d1 = (log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt(T))
        d2 = d1 - sigma * sqrt(T)

        # Cumulative normal distribution approximation
        def ndf(x):
            return (1.0 / sqrt(2 * pi)) * exp(-0.5 * x * x)

        def cdf(x):
            # Abramowitz & Stegun approximation
            a1 =  0.254829592
            a2 = -0.284496736
            a3 =  1.421413741
            a4 = -1.453152027
            a5 =  1.061405429
            p  =  0.3275911
            sign = 1 if x >= 0 else -1
            x = abs(x) / sqrt(2.0)
            t = 1.0 / (1.0 + p * x)
            y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * exp(-x * x)
            return 0.5 * (1.0 + sign * y)

        if option_type == "call":
            price = S * cdf(d1) - K * exp(-r * T) * cdf(d2)
            delta = cdf(d1)
        else:
            price = K * exp(-r * T) * cdf(-d2) - S * cdf(-d1)
            delta = cdf(d1) - 1

        gamma = ndf(d1) / (S * sigma * sqrt(T))
        theta = -(S * ndf(d1) * sigma) / (2 * sqrt(T)) - r * K * exp(-r * T) * cdf(d2 if option_type == "call" else -d2)
        theta = theta / 365  # Daily theta
        vega = S * ndf(d1) * sqrt(T) / 100  # Per 1% IV change
        rho = K * T * exp(-r * T) * cdf(d2 if option_type == "call" else -d2) / 100

        return round(price, 2), Greeks(
            delta=round(delta, 4),
            gamma=round(gamma, 4),
            theta=round(theta, 4),
            vega=round(vega, 4),
            rho=round(rho, 4)
        )

    def get_options_chain(self, expiry: Optional[str] = None) -> Dict[str, List[OptionContract]]:
        """Generate options chain for the ticker."""
        if expiry is None:
            expiry = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")

        # Generate strikes around spot price
        atm = round(self.spot / 5) * 5
        strikes = [atm + i * 5 for i in range(-10, 11)]

        T = 30 / 365  # ~30 days to expiry
        r = 0.045  # Risk-free rate
        sigma = self.historical_iv[-1] if self.historical_iv else 0.30

        calls = []
        puts = []

        for strike in strikes:
            call_price, call_greeks = self._black_scholes_greeks(self.spot, strike, T, r, sigma, "call")
            put_price, put_greeks = self._black_scholes_greeks(self.spot, strike, T, r, sigma, "put")

            # Add realistic market noise
            call_bid = max(0.01, round(call_price - random.uniform(0.01, 0.10), 2))
            call_ask = round(call_price + random.uniform(0.01, 0.10), 2)
            put_bid = max(0.01, round(put_price - random.uniform(0.01, 0.10), 2))
            put_ask = round(put_price + random.uniform(0.01, 0.10), 2)

            calls.append(OptionContract(
                strike=strike,
                expiry=expiry,
                option_type="call",
                bid=call_bid,
                ask=call_ask,
                last=round(call_price, 2),
                volume=random.randint(10, 5000),
                open_interest=random.randint(100, 50000),
                iv=round(sigma * 100 + random.uniform(-2, 2), 1),
                delta=call_greeks.delta,
                gamma=call_greeks.gamma,
                theta=call_greeks.theta,
                vega=call_greeks.vega,
                itm=strike < self.spot
            ))

            puts.append(OptionContract(
                strike=strike,
                expiry=expiry,
                option_type="put",
                bid=put_bid,
                ask=put_ask,
                last=round(put_price, 2),
                volume=random.randint(10, 5000),
                open_interest=random.randint(100, 50000),
                iv=round(sigma * 100 + random.uniform(-2, 2), 1),
                delta=put_greeks.delta,
                gamma=put_greeks.gamma,
                theta=put_greeks.theta,
                vega=put_greeks.vega,
                itm=strike > self.spot
            ))

        return {"calls": calls, "puts": puts}

    def get_greeks_summary(self) -> Dict:
        """Get portfolio-level Greeks summary."""
        chain = self.get_options_chain()
        atm_call = next((c for c in chain["calls"] if abs(c.strike - self.spot) < 3), None)
        atm_put = next((p for p in chain["puts"] if abs(p.strike - self.spot) < 3), None)

        if atm_call and atm_put:
            return {
                "delta": {"call": atm_call.delta, "put": atm_put.delta, "net": round(atm_call.delta + atm_put.delta, 4)},
                "gamma": {"call": atm_call.gamma, "put": atm_put.gamma, "net": round(atm_call.gamma + atm_put.gamma, 4)},
                "theta": {"call": atm_call.theta, "put": atm_put.theta, "net": round(atm_call.theta + atm_put.theta, 4)},
                "vega": {"call": atm_call.vega, "put": atm_put.vega, "net": round(atm_call.vega + atm_put.vega, 4)},
            }
        return {}

    def simulate_strategy(self, legs: List[OptionLeg], price_range: Tuple[float, float], steps: int = 50) -> List[Dict]:
        """Simulate P&L for a multi-leg options strategy."""
        min_price, max_price = price_range
        prices = [min_price + i * (max_price - min_price) / steps for i in range(steps + 1)]

        results = []
        for price in prices:
            total_pnl = 0
            for leg in legs:
                # Simplified P&L: intrinsic value - premium paid
                if leg.option_type == "call":
                    intrinsic = max(0, price - leg.strike)
                else:
                    intrinsic = max(0, leg.strike - price)

                leg_pnl = (intrinsic - leg.premium) * leg.quantity * 100  # *100 for contract multiplier
                total_pnl += leg_pnl

            results.append({"price": round(price, 2), "pnl": round(total_pnl, 2)})

        return results

    def get_ai_suggestion(self) -> Dict:
        """Generate AI-powered strategy suggestion based on current market conditions."""
        suggestions = {
            "Bullish": {
                "strategy": "Bull Call Spread",
                "description": "Buy ATM call, sell OTM call to reduce cost basis.",
                "confidence": 78,
                "legs": [
                    {"strike": round(self.spot / 5) * 5, "type": "call", "action": "buy", "qty": 1},
                    {"strike": round((self.spot + 10) / 5) * 5, "type": "call", "action": "sell", "qty": 1}
                ]
            },
            "Bearish": {
                "strategy": "Bear Put Spread",
                "description": "Buy ATM put, sell OTM put to reduce cost basis.",
                "confidence": 72,
                "legs": [
                    {"strike": round(self.spot / 5) * 5, "type": "put", "action": "buy", "qty": 1},
                    {"strike": round((self.spot - 10) / 5) * 5, "type": "put", "action": "sell", "qty": 1}
                ]
            },
            "Neutral": {
                "strategy": "Iron Condor",
                "description": "Sell OTM call spread and OTM put spread to collect premium.",
                "confidence": 65,
                "legs": [
                    {"strike": round((self.spot + 10) / 5) * 5, "type": "call", "action": "sell", "qty": 1},
                    {"strike": round((self.spot + 15) / 5) * 5, "type": "call", "action": "buy", "qty": 1},
                    {"strike": round((self.spot - 10) / 5) * 5, "type": "put", "action": "sell", "qty": 1},
                    {"strike": round((self.spot - 15) / 5) * 5, "type": "put", "action": "buy", "qty": 1}
                ]
            },
            "Strong Bullish": {
                "strategy": "Long Call",
                "description": "Buy ATM call for unlimited upside with defined risk.",
                "confidence": 85,
                "legs": [
                    {"strike": round(self.spot / 5) * 5, "type": "call", "action": "buy", "qty": 1}
                ]
            },
            "Strong Bearish": {
                "strategy": "Long Put",
                "description": "Buy ATM put for downside protection or speculation.",
                "confidence": 82,
                "legs": [
                    {"strike": round(self.spot / 5) * 5, "type": "put", "action": "buy", "qty": 1}
                ]
            }
        }

        suggestion = suggestions.get(self.trend, suggestions["Neutral"])
        suggestion["trend"] = self.trend
        suggestion["iv_assessment"] = "High" if self.iv_rank > 70 else "Low" if self.iv_rank < 30 else "Moderate"
        suggestion["spot"] = self.spot

        return suggestion
