const demoSignals = [
{
    coin: "BTC/USDT",
    type: "STRONG BUY",
    score: 92,
    entry: "105000 - 106000",
    tp1: "108000",
    tp2: "112000",
    tp3: "118000",
    sl: "102000",
    reasons: [
        "RSI Recovery",
        "MACD Bullish Cross",
        "EMA Alignment",
        "Volume Spike",
        "BTC Trend Bullish"
    ]
},
{
    coin: "ETH/USDT",
    type: "BUY",
    score: 81,
    entry: "5200 - 5250",
    tp1: "5400",
    tp2: "5600",
    tp3: "5900",
    sl: "5000",
    reasons: [
        "Bullish Structure",
        "Volume Increase",
        "MACD Positive"
    ]
}
];

function getBadgeClass(type) {
    if(type === "STRONG BUY") return "strong-buy";
    if(type === "BUY") return "buy";
    if(type === "SELL") return "sell";
    return "strong-sell";
}

function renderSignals() {

    const container = document.getElementById("signals");

    container.innerHTML = "";

    let buyCount = 0;
    let strongBuyCount = 0;

    demoSignals.forEach(signal => {

        if(signal.type === "BUY") buyCount++;
        if(signal.type === "STRONG BUY") strongBuyCount++;

        const reasonsHTML = signal.reasons
        .map(r => `<p>✅ ${r}</p>`)
        .join("");

        container.innerHTML += `
        <div class="signal-card">

            <div class="badge ${getBadgeClass(signal.type)}">
                ${signal.type}
            </div>

            <h3>${signal.coin}</h3>

            <p><b>Score:</b> ${signal.score}/100</p>

            <p><b>Entry:</b> ${signal.entry}</p>

            <p><b>TP1:</b> ${signal.tp1}</p>
            <p><b>TP2:</b> ${signal.tp2}</p>
            <p><b>TP3:</b> ${signal.tp3}</p>

            <p><b>SL:</b> ${signal.sl}</p>

            <div class="reason-box">
                ${reasonsHTML}
            </div>

        </div>
        `;
    });

    document.getElementById("signalCount").innerText =
        demoSignals.length;

    document.getElementById("buyCount").innerText =
        buyCount;

    document.getElementById("strongBuyCount").innerText =
        strongBuyCount;
}

renderSignals();
