import os
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime

# Colores ANSI para consola
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

WATCHLIST = ["VOO", "XLE", "QQQ", "NVDA", "AMD", "META", "AAPL", "GOOGL", "MSFT", "AMZN"]

# Configuración de Gemini (opcional - para noticias)
# Obtén tu API Key gratis en: https://aistudio.google.com/
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")  # Déjalo así, usa Secrets de GitHub

def calculate_atr(ticker, period=14):
    """Calcula el Average True Range correctamente"""
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
        print(f"Error ATR: {e}")
        return 0.0

def get_market_data(symbol):
    """Obtiene datos de mercado CORRECTOS desde Yahoo Finance"""
    try:
        ticker = yf.Ticker(symbol)
        
        # Obtener datos - IMPORTANTE: usamos '1d' para datos diarios limpios
        hist = ticker.history(period="5d")
        
        if hist.empty or len(hist) == 0:
            print(f"  ✗ Sin datos para {symbol}")
            return None
        
        # El precio está en dólares, sin multiplicadores raros
        last_close = float(hist["Close"].iloc[-1])
        
        # Calcular soporte y resistencia (2% arriba y abajo)
        support = round(last_close * 0.98, 2)
        resistance = round(last_close * 1.02, 2)
        
        # Calcular ATR
        atr = calculate_atr(ticker)
        
        # Calcular cambio porcentual
        if len(hist) > 1:
            prev_close = float(hist["Close"].iloc[-2])
            change_pct = round(((last_close - prev_close) / prev_close) * 100, 2)
        else:
            change_pct = 0.0
        
        # Volumen (asegurar que es entero)
        volume = int(hist["Volume"].iloc[-1]) if len(hist) > 0 else 0
        
        return {
            "symbol": symbol,
            "price": last_close,
            "change_pct": change_pct,
            "atr": atr,
            "support": support,
            "resistance": resistance,
            "volume": volume,
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    except Exception as e:
        print(f"  ✗ Error en {symbol}: {e}")
        return None

def classify_priority(row, atr_threshold_high, atr_threshold_low):
    """Clasifica prioridad según ATR y movimiento de precio"""
    atr = row["atr"]
    change = abs(row["change_pct"])
    
    if atr >= atr_threshold_high or (atr >= atr_threshold_low and change >= 1.5):
        return "HIGH"
    elif atr >= atr_threshold_low or change >= 0.8:
        return "MEDIUM"
    else:
        return "LOW"

def get_news_analysis(symbol):
    """Obtiene noticias y análisis cualitativo usando Gemini AI"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "":
        return "   ⚠️ API Key no configurada. Para activar noticias, configura GEMINI_API_KEY en GitHub Secrets."
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Busca en tu conocimiento las NOTICIAS MÁS RELEVANTES de las últimas 48 horas sobre la empresa {symbol}.
        
        Responde EXACTAMENTE en este formato (texto plano, sin markdown):
        
        NOTICIAS:
        • [Noticia 1 - máximo 15 palabras]
        • [Noticia 2 - máximo 15 palabras]  
        • [Noticia 3 - máximo 15 palabras]
        
        ANALISIS: [Una sola oración diciendo si es positivo, negativo o neutral para el precio]
        
        Si no hay noticias relevantes, escribe: "NOTICIAS: Sin noticias relevantes en últimas 48 horas"
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except ImportError:
        return "   ❌ Librería google-generativeai no instalada"
    except Exception as e:
        return f"   ❌ Error Gemini: {str(e)[:100]}"

def get_market_context():
    """Obtiene contexto general del mercado"""
    if not GEMINI_API_KEY or GEMINI_API_KEY == "":
        return "Contexto de mercado no disponible (API Key faltante)"
    
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        today = datetime.now().strftime("%Y-%m-%d")
        prompt = f"""
        Fecha: {today}
        
        Da un resumen MUY CORTO (máximo 4 líneas) del sentimiento actual del mercado bursátil:
        - ¿Alcista, bajista o lateral?
        - ¿Qué sectores están liderando?
        - Recomendación general para hoy (agresiva/cautelosa)
        
        Responde solo con texto plano, sin formato.
        """
        
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        return f"Error: {str(e)[:80]}"

def main():
    print(f"\n{'='*80}")
    print(f"📈 PRE-MARKET ANALYSIS - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    # ===== 1. OBTENER DATOS TÉCNICOS =====
    print("📡 Obteniendo datos de mercado...")
    results = []
    
    for symbol in WATCHLIST:
        print(f"   {symbol}...", end=" ")
        data = get_market_data(symbol)
        if data:
            results.append(data)
            print(f"✓ ${data['price']:.2f} (Var: {data['change_pct']:+.2f}%)")
        else:
            print("❌")
    
    if not results:
        print("\n❌ No se pudieron obtener datos. Verifica tu conexión a internet.")
        return
    
    df = pd.DataFrame(results)
    
    # Calcular umbrales de prioridad
    atr_values = df["atr"].values
    atr_threshold_high = np.percentile(atr_values, 70) if len(atr_values) > 0 else 0
    atr_threshold_low = np.percentile(atr_values, 30) if len(atr_values) > 0 else 0
    
    df["priority"] = df.apply(lambda row: classify_priority(row, atr_threshold_high, atr_threshold_low), axis=1)
    
    # Ordenar por prioridad
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df["_order"] = df["priority"].map(priority_order)
    df = df.sort_values("_order").drop("_order", axis=1)
    
    # ===== 2. MOSTRAR TABLA DE PRIORIDADES =====
    print(f"\n{'='*80}")
    print("🎯 PRIORIDADES DE TRADING")
    print(f"{'='*80}\n")
    
    for _, row in df.iterrows():
        if row["priority"] == "HIGH":
            color = GREEN
            label = "🔴 ALTA   "
        elif row["priority"] == "MEDIUM":
            color = YELLOW
            label = "🟡 MEDIA  "
        else:
            color = RED
            label = "🟢 BAJA   "
        
        print(f"{color}{label}{RESET} {row['symbol']:6} | "
              f"${row['price']:7.2f} | "
              f"Var: {row['change_pct']:+6.2f}% | "
              f"ATR: ${row['atr']:5.2f} | "
              f"Soporte: ${row['support']:7.2f} | "
              f"Resistencia: ${row['resistance']:7.2f}")
    
    # ===== 3. ANÁLISIS DE NOTICIAS =====
    print(f"\n{'='*80}")
    print("📰 NOTICIAS RELEVANTES Y ANÁLISIS")
    print(f"{'='*80}\n")
    
    if GEMINI_API_KEY and GEMINI_API_KEY != "":
        # Analizar solo HIGH y MEDIUM prioridad
        assets_to_analyze = df[df["priority"].isin(["HIGH", "MEDIUM"])]["symbol"].tolist()
        
        for symbol in assets_to_analyze:
            print(f"\n🔍 {symbol}:")
            news = get_news_analysis(symbol)
            print(news)
    else:
        print("⚠️  ANÁLISIS DE NOTICIAS NO DISPONIBLE")
        print("   Para activarlo:")
        print("   1. Ve a https://aistudio.google.com/")
        print("   2. Crea una API Key gratis")
        print("   3. En GitHub: Settings → Secrets → Actions → New secret")
        print("   4. Name: GEMINI_API_KEY | Value: tu clave")
        print("")
        print("   Mientras tanto, puedes ver noticias manualmente en:")
        print("   • Finviz: https://finviz.com/")
        print("   • TradingView: https://www.tradingview.com/\n")
    
    # ===== 4. CONTEXTO DE MERCADO =====
    print(f"\n{'='*80}")
    print("🌍 CONTEXTO GENERAL DEL MERCADO")
    print(f"{'='*80}\n")
    
    if GEMINI_API_KEY and GEMINI_API_KEY != "":
        context = get_market_context()
        print(context)
    else:
        print("Contexto de mercado no disponible (configura GEMINI_API_KEY)")
        print("\nSugerencia: Los futuros del S&P 500 y Nasdaq son los principales indicadores pre-market.")
    
    # ===== 5. GUARDAR CSV =====
    csv_filename = f"reports/premarket_{datetime.now().strftime('%Y%m%d')}.csv"
    os.makedirs("reports", exist_ok=True)
    
    # Guardar con formato correcto (sin multiplicadores raros)
    df_csv = df.copy()
    df_csv.to_csv(csv_filename, index=False, encoding='utf-8')
    
    print(f"\n{'='*80}")
    print(f"📁 Reporte guardado: {csv_filename}")
    print(f"{'='*80}\n")
    
    # Mostrar resumen ejecutivo
    print("📊 RESUMEN EJECUTIVO:")
    high_count = len(df[df["priority"] == "HIGH"])
    medium_count = len(df[df["priority"] == "MEDIUM"])
    low_count = len(df[df["priority"] == "LOW"])
    print(f"   🔴 Alta prioridad: {high_count} instrumentos")
    print(f"   🟡 Media prioridad: {medium_count} instrumentos")
    print(f"   🟢 Baja prioridad: {low_count} instrumentos")

if __name__ == "__main__":
    main()
