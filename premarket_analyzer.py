import os
import yfinance as yf
import pandas as pd
import requests
from datetime import datetime
import time
import numpy as np

# ================= CONFIGURACIÓN INICIAL =================
# Colores ANSI para consola (para que la prioridad se vea bonita)
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

WATCHLIST = ["VOO", "XLE", "QQQ", "NVDA", "AMD", "META", "AAPL", "GOOGL", "MSFT", "AMZN"]

# Configuración de Gemini (Reemplaza con tu API Key)
# Si no quieres noticias aún, déjala vacía y el código no fallará.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") # <-- Pon aquí tu Key o déjala así si usas Secrets de GitHub
# ========================================================


# ----------------- FUNCIONES TÉCNICAS (YA LAS TENÍAS) -----------------
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
    except Exception:
        return 0.0

def get_premarket_data(symbol):
    """Obtiene datos de Yahoo Finance (precio, soporte, resistencia, etc.)"""
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
        print(f"Error en datos de {symbol}: {e}")
        return None


# ----------------- NUEVA FUNCIÓN DE NOTICIAS Y ANÁLISIS CON IA -----------------
def get_news_and_sentiment(symbol):
    """
    Usa Gemini para buscar noticias reales en internet y analizar el sentimiento.
    (Totalmente Gratis con la API Key de Gemini)
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TU_API_KEY_AQUI":
        return "  ⚠️  API Key de Gemini no configurada. No se pudo obtener el análisis de noticias."

    try:
        # Importamos la librería de Google (Asegúrate de tenerla instalada)
        import google.generativeai as genai
        
        # Configuramos Gemini
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Habilitamos la búsqueda en internet (Google Search grounding)
        # Necesitas tener habilitado "Google Search" en AI Studio, pero la versión base suele funcionar.
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Prompt profesional para que la IA actúe como analista de mercado
        prompt = f"""
        Actúa como un analista financiero experto especializado en trading.

        Busca en internet las 3 noticias MÁS IMPORTANTES Y RECIENTES (últimas 24-48 horas) sobre la acción {symbol}.
        
        Luego, realiza un análisis cualitativo breve.
        
        Responde EXACTAMENTE con el siguiente formato de texto plano (sin usar markdown excesivo, solo texto legible):
        
        📰 **Noticias Recientes sobre {symbol}:**
        1. [Título de la noticia] (Fuente: [Nombre de la fuente])
        2. [Título de la noticia] (Fuente: [Nombre de la fuente])
        3. [Título de la noticia] (Fuente: [Nombre de la fuente])
        
        💡 **Análisis y Sentimiento:**
        [Aquí escribe un párrafo corto describiendo si las noticias son positivas para el precio, negativas, o neutrales. Explica el por qué brevemente].
        
        Reglas IMPORTANTES:
        - Si no encuentras noticias específicas, di "No se encontraron noticias relevantes en las últimas 48 horas."
        - Sé conciso. Máximo 80 palabras en total.
        """
        
        # Llamada a la API de Gemini
        response = model.generate_content(prompt)
        
        # Pequeña pausa para no saturar la cuota gratuita (60 requests/minuto)
        time.sleep(1.5)
        
        # Devolvemos el texto limpio
        return response.text.strip()
        
    except ImportError:
        return "  ❌ Librería 'google-generativeai' no instalada. Ejecuta: pip install google-generativeai"
    except Exception as e:
        return f"  ❌ Error al conectar con Gemini: {str(e)}"

def get_market_summary():
    """
    Genera un resumen cualitativo del mercado general usando IA.
    """
    if not GEMINI_API_KEY or GEMINI_API_KEY == "TU_API_KEY_AQUI":
        return "## Resumen de Mercado\nNo disponible (API Key faltante)"
        
    try:
        import google.generativeai as genai
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        prompt = f"""
        Eres un analista de mercado macro.
        Basándote en el contexto actual del mercado bursátil del día {datetime.now().strftime('%Y-%m-%d')}:
        
        1. Proporciona un breve resumen del sentimiento general del mercado (alcista, bajista, lateral).
        2. Menciona los sectores que están liderando las ganancias o pérdidas (Tecnología, Energía, Finanzas, etc.).
        3. Da una recomendación general de actitud para el día (agresiva, cautelosa, oportunista).
        
        Formato:
        **🌍 Panorama General del Mercado:**
        [Texto aquí]
        **📊 Áreas de Interés:**
        [Texto aquí]
        **🎯 Estrategia Sugerida:**
        [Texto aquí]
        """
        response = model.generate_content(prompt)
        time.sleep(1.5)
        return response.text.strip()
    except Exception as e:
        return f"Error generando resumen: {e}"


# ----------------- FUNCIÓN DE PRIORIDAD (YA LA TENÍAS MEJORADA) -----------------
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


# ----------------- FUNCIÓN PRINCIPAL -----------------
def main():
    print(f"\n{'='*80}")
    print(f"🚀 PRE-MARKET INTELLIGENCE - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")

    # 1. DATOS TÉCNICOS (Precios, ATR, Soportes)
    print("📡 Conectando con Yahoo Finance...")
    results = []
    for symbol in WATCHLIST:
        print(f"   Procesando {symbol}...", end=" ")
        data = get_premarket_data(symbol)
        if data:
            results.append(data)
            print(f"✓ (${data['price']})")
        else:
            print(f"❌ Sin datos")
            results.append({"symbol": symbol, "atr": 0, "change_pct": 0}) # Placeholder para no romper el sort

    if not results:
        print("❌ No se pudo obtener datos de Yahoo Finance.")
        return

    df = pd.DataFrame(results)
    # Limpiar datos nulos o vacíos para el cálculo de prioridad
    df = df.dropna(subset=['atr', 'change_pct'])
    if df.empty:
        print("❌ Datos insuficientes para calcular prioridades.")
        return

    # Calcular umbrales de prioridad
    atr_values = df["atr"].values
    atr_threshold_high = np.percentile(atr_values, 70) if len(atr_values) > 0 else 0
    atr_threshold_low = np.percentile(atr_values, 30) if len(atr_values) > 0 else 0
    
    df["priority"] = df.apply(lambda row: classify_priority(row, atr_threshold_high, atr_threshold_low), axis=1)
    
    # Ordenar: HIGH -> MEDIUM -> LOW
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    df["_order"] = df["priority"].map(priority_order)
    df = df.sort_values("_order").drop("_order", axis=1)
    
    # Mostrar Tabla de Prioridades (igual que antes)
    print(f"\n{'='*80}")
    print("📊 PRIORIDADES DE TRADING (Técnico)")
    print(f"{'='*80}\n")
    
    for _, row in df.iterrows():
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

    # 2. ANÁLISIS DE NOTICIAS (IA)
    print(f"\n{'='*80}")
    print("📰 ANÁLISIS FUNDAMENTAL (Noticias y Sentimiento vía IA)")
    print(f"{'='*80}\n")
    
    # Solo analizamos los de ALTA y MEDIA prioridad para ahorrar tokens de la API Gratis
    top_assets = df[df['priority'].isin(['HIGH', 'MEDIUM'])]['symbol'].tolist()
    
    if GEMINI_API_KEY and GEMINI_API_KEY != "TU_API_KEY_AQUI":
        print(f"🧠 Analizando noticias para: {', '.join(top_assets)}...\n")
        for asset in top_assets:
            print(f"🔍 Investigando {asset}...")
            news_analysis = get_news_and_sentiment(asset)
            print(news_analysis)
            print("-" * 40)
    else:
        print("⚠️  Configuración de noticias omitida.")
        print("   Para activar el análisis con IA, obtén una API Key gratuita en:")
        print("   👉 https://aistudio.google.com/")
        print("   Luego pégala en la variable 'GEMINI_API_KEY' dentro del código o en los Secrets de GitHub.\n")

    # 3. RESUMEN DE MERCADO (Contexto General)
    print(f"\n{'='*80}")
    print("🌎 CONTEXTO MACRO Y ESTRATEGIA")
    print(f"{'='*80}\n")
    
    if GEMINI_API_KEY and GEMINI_API_KEY != "TU_API_KEY_AQUI":
        macro_summary = get_market_summary()
        print(macro_summary)
    else:
        print("⚠️  Resumen de mercado no disponible (API Key faltante).")
        print("   Actívala para tomar mejores decisiones.\n")

    # 4. GUARDAR REPORTE FINAL (CSV)
    csv_filename = f"reports/premarket_{datetime.now().strftime('%Y%m%d')}.csv"
    os.makedirs("reports", exist_ok=True)
    df.to_csv(csv_filename, index=False, encoding='utf-8')
    
    print(f"\n{'='*80}")
    print(f"📁 Reporte técnico guardado en: {csv_filename}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
