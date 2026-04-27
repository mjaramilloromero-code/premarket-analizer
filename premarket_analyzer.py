import os
import yfinance as yf
import pandas as pd
from datetime import datetime

# Colores ANSI para consola
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

# Tu watchlist
WATCHLIST = ["VOO", "XLE", "QQQ", "NVDA", "AMD", "META", "AAPL", "GOOGL", "MSFT", "AMZN"]

def calculate_atr(ticker, period=14):
    try:
        hist = ticker.history(period="20d")
        if len(hist) < period:
            return 0.0
        high_low = hist["High"] - hist["Low"]
        high_close = abs(hist["High"] - hist["Close"].shift())
        low_close = abs(hist["Low"] - hist["Close"].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return round(atr.iloc[-1], 2)
    except Exception as e:
        print(f"Error ATR {ticker}: {e}")
        return 0.0

def get_premarket_data(symbol):
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period="5d")
        if len(hist) == 0:
            return None

        last_close = hist["Close"].iloc[-1]
        support = round(last_close * 0.98, 2)
        resistance = round(last_close * 1.02, 2)
        atr = calculate_atr(ticker)

        if len(hist) > 1:
            prev_close = hist["Close"].iloc[-2]
            change_pct = round(((last_close - prev_close) / prev_close) * 100, 2)
        else:
            change_pct = 0.0

        return {
            "symbol": symbol,
            "price": round(last_close, 2),
            "change_pct": change_pct,
            "atr": atr,
            "support": support,
            "resistance": resistance,
            "volume": hist["Volume"].iloc[-1] if len(hist) > 0 else 0,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    except Exception as e:
        print(f"Error {symbol}: {e}")
        return None

def classify_priority(row, atr_threshold_high, atr_threshold_low):
    """Clasifica prioridad según ATR y movimiento de precio"""
    symbol = row["symbol"]
    atr = row["atr"]
    change = abs(row["change_pct"])
    
    # Reglas de prioridad (ajustables)
    # Alta: mucha volatilidad O movimiento fuerte + volatilidad media
    if atr >= atr_threshold_high or (atr >= atr_threshold_low and change >= 1.5):
        return "HIGH"
    # Media: volatilidad media o movimiento moderado
    elif atr >= atr_threshold_low or change >= 0.8:
        return "MEDIUM"
    # Baja: baja volatilidad y poco movimiento
    else:
        return "LOW"

def main():
    print(f"\n{'='*80}")
    print(f"PRE-MARKET ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    results = []
    for symbol in WATCHLIST:
        print(f"Analizando {symbol}...")
        data = get_premarket_data(symbol)
        if data:
            results.append(data)
            print(f"  ✓ ${data['price']} | Var: {data['change_pct']:+.2f}% | ATR: ${data['atr']}")
        else:
            print(f"  ✗ Sin datos")

    if not results:
        print("❌ No hay datos")
        return

    df = pd.DataFrame(results)
    
    # Calcular umbrales de ATR para prioridades
    atr_values = df["atr"].values
    atr_threshold_high = np.percentile(atr_values, 70) if len(atr_values) > 0 else 0
    atr_threshold_low = np.percentile(atr_values, 30) if len(atr_values) > 0 else 0
    
    # Aplicar clasificación
    df["priority"] = df.apply(lambda row: classify_priority(row, atr_threshold_high, atr_threshold_low), axis=1)
    
    # Ordenar: HIGH -> MEDIUM -> LOW
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df["_order"] = df["priority"].map(priority_order)
    df = df.sort_values("_order").drop("_order", axis=1)
    
    # Mostrar resultados con colores
    print(f"\n{'='*80}")
    print("RESULTADOS FINALES")
    print(f"{'='*80}\n")
    
    for _, row in df.iterrows():
        # Color según prioridad
        if row["priority"] == "HIGH":
            color = GREEN
            label = "ALTA   "
        elif row["priority"] == "MEDIUM":
            color = YELLOW
            label = "MEDIA  "
        else:
            color = RED
            label = "BAJA   "
        
        print(f"{color}[{label}]{RESET} {row['symbol']:6} | "
              f"${row['price']:8,.2f} | "
              f"Var: {row['change_pct']:+6.2f}% | "
              f"ATR: ${row['atr']:6.2f} | "
              f"Sop: ${row['support']:7,.2f} | "
              f"Res: ${row['resistance']:7,.2f}")
    
    # Guardar CSV con colores (sin colores ANSI, solo texto plano)
    csv_filename = f"reports/premarket_{datetime.now().strftime('%Y%m%d')}.csv"
    os.makedirs("reports", exist_ok=True)
    df_csv = df.copy()
    df_csv["priority_label"] = df_csv["priority"]  # HIGH/MEDIUM/LOW
    df_csv.to_csv(csv_filename, index=False, encoding='utf-8')
    
    print(f"\n{'='*80}")
    print(f"✓ Reporte guardado: {csv_filename}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    import numpy as np
    main()
