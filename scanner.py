import requests
import pandas as pd
import numpy as np
from ta.momentum import RSIIndicator

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

    return round(
        rsi.iloc[-1],
        2
    )


pairs = get_usdt_pairs()

print("TOP COINS FOUND:", len(pairs))

for coin in pairs[:10]:
    print(
        coin["pair"],
        coin["volume"]
    )

candles = get_candles("BTC_USDT")

print("Candles Found:", len(candles))

rsi = calculate_rsi(candles)

print("BTC RSI:", rsi)
