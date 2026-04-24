import os
import requests
import yfinance as yf
import pandas as pd
from datetime import datetime

WATCHLIST = ["VOO", "XLE", "QQQ", "NVDA", "AMD", "META", "AAPL", "GOOGL", "MSFT", "AMZN"]

def get_data(symbol):
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="5d")
    last_close = hist["Close"].iloc[-1]
    # Calcular ATR
    high_low = hist["High"] - hist["Low"]
    high_close = abs(hist["High"] - hist["Close"].shift())
    low_close = abs(hist["Low"] - hist["Close"].shift())
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = tr.rolling(window=14).mean().iloc[-1]
    
    return {
        "price": round(last_close, 2),
        "atr": round(atr, 2),
        "support": round(last_close * 0.98, 2),
        "resistance": round(last_close * 1.02, 2)
    }

def main():
    results = []
    for symbol in WATCHLIST:
        d = get_data(symbol)
        results.append({
            "Symbol": symbol,
            "Price": f"${d['price']}",
            "ATR": f"${d['atr']}",
            "Support": f"${d['support']}",
            "Resistance": f"${d['resistance']}",
            "Date": datetime.now().strftime("%Y-%m-%d")
        })
    
    df = pd.DataFrame(results)
    print(df.to_string(index=False))
    
    # Guardar CSV
    os.makedirs("reports", exist_ok=True)
    df.to_csv(f"reports/premarket_{datetime.now().strftime('%Y%m%d')}.csv", index=False)
    print(f"\nReport saved to reports/premarket_{datetime.now().strftime('%Y%m%d')}.csv")

if __name__ == "__main__":
    main()
