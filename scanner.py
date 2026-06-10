import requests
import pandas as pd
import numpy as np
import os
from supabase import create_client
from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

BASE_URL = "https://api.gateio.ws/api/v4"

# ---------------- SUPABASE SAFETY ----------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = None
if SUPABASE_URL and SUPABASE_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
else:
    print("⚠️ Supabase env missing")

# ---------------- COINS ----------------
def get_usdt_pairs():
    url = f"{BASE_URL}/spot/tickers"
    data = requests.get(url).json()

    pairs = []

    for coin in data:
        try:
            pair = coin.get("currency_pair")
            volume = float(coin.get("quote_volume", 0))

            if pair and pair.endswith("_USDT"):
                pairs.append({"pair": pair, "volume": volume})

        except:
            continue

    pairs.sort(key=lambda x: x["volume"], reverse=True)
    return pairs[:100]


# ---------------- CANDLES ----------------
def get_candles(pair):
    url = f"{BASE_URL}/spot/candlesticks"

    params = {
        "currency_pair": pair,
        "interval": "1h",
        "limit": 200
    }

    try:
        data = requests.get(url, params=params, timeout=10).json()
        return data if isinstance(data, list) else []
    except:
        return []


# ---------------- SAFE CLOSE EXTRACTION ----------------
def get_closes(candles):
    try:
        return [float(c[2]) for c in candles if len(c) > 2]
    except:
        return []


# ---------------- RSI ----------------
def calculate_rsi(candles):
    closes = get_closes(candles)
    closes.reverse()

    df = pd.DataFrame(closes, columns=["close"])
    rsi = RSIIndicator(df["close"], window=14).rsi()

    return round(float(rsi.iloc[-1]), 2)


# ---------------- EMA ----------------
def calculate_emas(candles):
    closes = get_closes(candles)
    closes.reverse()

    df = pd.DataFrame(closes, columns=["close"])

    return {
        "ema20": float(EMAIndicator(df["close"], 20).ema_indicator().iloc[-1]),
        "ema50": float(EMAIndicator(df["close"], 50).ema_indicator().iloc[-1]),
        "ema200": float(EMAIndicator(df["close"], 200).ema_indicator().iloc[-1]),
    }


# ---------------- MACD ----------------
def calculate_macd(candles):
    closes = get_closes(candles)
    closes.reverse()

    df = pd.DataFrame(closes, columns=["close"])

    macd = MACD(df["close"])

    return {
        "macd": float(macd.macd().iloc[-1]),
        "signal": float(macd.macd_signal().iloc[-1]),
        "bullish": macd.macd().iloc[-1] > macd.macd_signal().iloc[-1]
    }


# ---------------- VOLUME ----------------
def calculate_volume_spike(candles):
    volumes = [float(c[1]) for c in candles if len(c) > 1]

    if len(volumes) < 10:
        return {"spike": False, "ratio": 0}

    volumes.reverse()

    current = volumes[-1]
    avg = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else 0

    ratio = current / avg if avg else 0

    return {
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
    if score >= 60:
        return "BUY"
    if score >= 40:
        return "WATCHLIST"
    if score >= 20:
        return "SELL"
    return "STRONG SELL"


# ---------------- LEVELS ----------------
def get_trade_levels(candles):
    closes = get_closes(candles)
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

        print(pair, "|", signal, "|", score)

        # SAFE INSERT
        if supabase:
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
                "reasons": f"RSI:{rsi} EMA MACD:{macd['bullish']} VOL:{volume['spike']}"
            }).execute()

    except Exception as e:
        print(pair, "| ERROR:", str(e))
