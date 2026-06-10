import requests

url = "https://api.gateio.ws/api/v4/spot/tickers"

response = requests.get(url)

data = response.json()

print("Total Coins:", len(data))

for coin in data[:10]:
    print(
        coin["currency_pair"],
        coin["last"]
    )
