import requests
import pandas as pd
import numpy as np
import os

from supabase import create_client
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

BASE_URL = "https://api.gateio.ws/api/v4"

# ---------------- SUPABASE ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------- COINS ----------------
def get_usdt_pairs():
    url = f"{BASE_URL}/spot/tickers"
    response = requests.get(url)
    data = response.json()

    pairs = []

    for coin in data:
        try:
            pair = coin["currency_pair"]
            if pair.endswith("_USDT"):
                pairs.append({
                    "pair": pair,
                    "volume": float(coin["quote_volume"])
                })
        except:
            continue

    pairs = sorted(pairs, key=lambda x: x["volume"], reverse=True)
    return pairs[:100]


# ---------------- CANDLES ----------------
def get_candles(pair):
    url = f"{BASE_URL}/spot/candlesticks"

    params = {
        "currency_pair": pair,
        "interval": "1h",
        "limit": 200
    }

    response = requests.get(url, params=params)
    data = response.json()

    if not isinstance(data, list) or len(data) == 0:
        return []

    return data


# ---------------- RSI ----------------
def calculate_rsi(candles):
    closes = [float(c[2]) for c in candles]
    closes.reverse()

    df = pd.DataFrame(closes, columns=["close"])

    rsi = RSIIndicator(df["close"], window=14).rsi()

    return round(float(rsi.iloc[-1]), 2)


# ---------------- EMA ----------------
def calculate_emas(candles):
    closes = [float(c[2]) for c in candles]
    closes.reverse()

    df = pd.DataFrame(closes, columns=["close"])

    ema20 = EMAIndicator(df["close"], window=20).ema_indicator()
    ema50 = EMAIndicator(df["close"], window=50).ema_indicator()
    ema200 = EMAIndicator(df["close"], window=200).ema_indicator()

    return {
        "ema20": float(ema20.iloc[-1]),
        "ema50": float(ema50.iloc[-1]),
        "ema200": float(ema200.iloc[-1]),
    }


# ---------------- MACD ----------------
def calculate_macd(candles):
    closes = [float(c[2]) for c in candles]
    closes.reverse()

    df = pd.DataFrame(closes, columns=["close"])

    macd = MACD(df["close"])

    macd_line = macd.macd().iloc[-1]
    signal_line = macd.macd_signal().iloc[-1]

    return {
        "macd": float(macd_line),
        "signal": float(signal_line),
        "bullish": macd_line > signal_line
    }


# ---------------- VOLUME ----------------
def calculate_volume_spike(candles):
    volumes = [float(c[1]) for c in candles]
    volumes.reverse()

    if len(volumes) < 10:
        return {"spike": False, "ratio": 0}

    current = volumes[-1]
    avg = sum(volumes[:-1]) / len(volumes[:-1])

    ratio = current / avg if avg != 0 else 0

    return {
        "current": current,
        "average": avg,
        "ratio": round(ratio, 2),
        "spike": ratio >= 1.5
    }


# ---------------- SCORE ----------------
def get_trend_score(rsi, emas, macd, volume):
    score = 0

    if rsi > 55:
        score += 20

    if emas["ema20"] > emas["ema50"]:
        score += 20

    if emas["ema50"] > emas["ema200"]:
        score += 20

    if macd["bullish"]:
        score += 20

    if volume["spike"]:
        score += 20

    return score


# ---------------- SIGNAL ----------------
def get_signal(score):
    if score >= 80:
        return "STRONG BUY"
    elif score >= 60:
        return "BUY"
    elif score >= 40:
        return "WATCHLIST"
    elif score >= 20:
        return "SELL"
    else:
        return "STRONG SELL"


# ---------------- LEVELS ----------------
def get_trade_levels(candles):
    closes = [float(c[2]) for c in candles]
    closes.reverse()

    price = closes[-1]

    return {
        "price": price,
        "entry_low": price * 0.995,
        "entry_high": price * 1.005,
        "tp1": price * 1.03,
        "tp2": price * 1.06,
        "tp3": price * 1.10,
        "sl": price * 0.97
    }


# ---------------- MAIN ----------------
pairs = get_usdt_pairs()

print("TOP COINS:", len(pairs))

for coin in pairs[:10]:
    print(coin["pair"], coin["volume"])


for coin in pairs[:5]:

    pair = coin["pair"]

    try:
        candles = get_candles(pair)

        if len(candles) < 20:
            continue

        rsi = calculate_rsi(candles)
        emas = calculate_emas(candles)
        macd = calculate_macd(candles)
        volume = calculate_volume_spike(candles)

        score = get_trend_score(rsi, emas, macd, volume)
        signal = get_signal(score)

        levels = get_trade_levels(candles)

        supabase.table("signals").insert({
            "coin": pair,
            "signal_type": signal,
            "score": score,
            "price": levels["price"],
            "entry_low": levels["entry_low"],
            "entry_high": levels["entry_high"],
            "tp1": levels["tp1"],
            "tp2": levels["tp2"],
            "tp3": levels["tp3"],
            "sl": levels["sl"],
            "reasons": f"RSI:{rsi} EMA20>{emas['ema20']} EMA50>{emas['ema50']} MACD:{macd['bullish']} VOL:{volume['spike']}"
        }).execute()

        print(pair, "|", signal, "| Score:", score)

    except Exception as e:
        print(pair, "| ERROR:", str(e))
