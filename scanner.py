import requests
import pandas as pd
import numpy as np

from ta.momentum import RSIIndicator
from ta.trend import EMAIndicator, MACD

BASE_URL = "https://api.gateio.ws/api/v4"


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
            pass

    pairs = sorted(
        pairs,
        key=lambda x: x["volume"],
        reverse=True
    )

    return pairs[:100]


def get_candles(pair):

    url = f"{BASE_URL}/spot/candlesticks"

    params = {
        "currency_pair": pair,
        "interval": "1h",
        "limit": 200
    }

    response = requests.get(
        url,
        params=params
    )

    return response.json()


def calculate_rsi(candles):

    closes = []

    for candle in candles:
        closes.append(float(candle[2]))

    closes.reverse()

    df = pd.DataFrame(
        closes,
        columns=["close"]
    )

    rsi = RSIIndicator(
        close=df["close"],
        window=14
    ).rsi()

    return round(float(rsi.iloc[-1]), 2)


def calculate_emas(candles):

    closes = []

    for candle in candles:
        closes.append(float(candle[2]))

    closes.reverse()

    df = pd.DataFrame(
        closes,
        columns=["close"]
    )

    ema20 = EMAIndicator(
        close=df["close"],
        window=20
    ).ema_indicator()

    ema50 = EMAIndicator(
        close=df["close"],
        window=50
    ).ema_indicator()

    ema200 = EMAIndicator(
        close=df["close"],
        window=200
    ).ema_indicator()

    return {
        "ema20": round(float(ema20.iloc[-1]), 4),
        "ema50": round(float(ema50.iloc[-1]), 4),
        "ema200": round(float(ema200.iloc[-1]), 4)
    }


def calculate_macd(candles):

    closes = []

    for candle in candles:
        closes.append(float(candle[2]))

    closes.reverse()

    df = pd.DataFrame(
        closes,
        columns=["close"]
    )

    macd = MACD(close=df["close"])

    macd_line = macd.macd().iloc[-1]
    signal_line = macd.macd_signal().iloc[-1]

    return {
        "macd": round(float(macd_line), 4),
        "signal": round(float(signal_line), 4),
        "bullish": macd_line > signal_line
    }


def calculate_volume_spike(candles):

    volumes = []

    for candle in candles:
        volumes.append(float(candle[1]))

    volumes.reverse()

    current_volume = volumes[-1]

    average_volume = sum(volumes[:-1]) / len(volumes[:-1])

    ratio = current_volume / average_volume

    return {
        "current": round(current_volume, 2),
        "average": round(average_volume, 2),
        "ratio": round(ratio, 2),
        "spike": ratio >= 1.5
    }


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


# MAIN

pairs = get_usdt_pairs()

print("TOP COINS FOUND:", len(pairs))

for coin in pairs[:10]:
    print(coin["pair"], coin["volume"])

candles = get_candles("BTC_USDT")

print("Candles Found:", len(candles))

rsi = calculate_rsi(candles)

emas = calculate_emas(candles)

macd = calculate_macd(candles)

volume = calculate_volume_spike(candles)

score = get_trend_score(
    rsi,
    emas,
    macd,
    volume
)

print("RSI:", rsi)

print("EMA20:", emas["ema20"])
print("EMA50:", emas["ema50"])
print("EMA200:", emas["ema200"])

print("MACD:", macd["macd"])
print("Signal:", macd["signal"])
print("Bullish:", macd["bullish"])

print("Volume Ratio:", volume["ratio"])
print("Volume Spike:", volume["spike"])

print("AI SCORE:", score)
