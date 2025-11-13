import os
import requests
import openai
from telegram import Bot
from datetime import datetime, timezone

# ===== CONFIGURACIÓN =====
openai.api_key = os.getenv("OPENAI_API_KEY")
TELEGRAM_TOKEN = os.getenv("8388545388:AAFphIeJ04XDvgWiwbKjaHqRPpyHPzTmtlU")
CHAT_ID = os.getenv("7743163483")

bot = Bot(token=TELEGRAM_TOKEN)

def obtener_precio(symbol="BTCUSDT"):
    """Obtiene el precio actual de Binance"""
    url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol}"
    resp = requests.get(url)
    data = resp.json()
    return float(data["price"])

def analizar_tendencia(precios):
    """Usa ChatGPT para analizar la tendencia del mercado"""
    prompt = f"""
    Tengo los siguientes precios recientes de Bitcoin (en USD): {precios}.
    Analiza brevemente si el precio parece estar subiendo, bajando o estable,
    y da una predicción a corto plazo (por ejemplo, para la próxima hora),
    explicando tu razonamiento.
    """
    response = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6
    )
    return response.choices[0].message["content"]

def enviar_mensaje(texto):
    """Envía un mensaje al chat de Telegram"""
    bot.send_message(chat_id=CHAT_ID, text=texto)

def main():
    try:
        precios = [obtener_precio() for _ in range(3)]  # tres lecturas rápidas
        analisis = analizar_tendencia(precios)
        mensaje = f"📊 Análisis de BTC/USD ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}):\n\n{analisis}"
        enviar_mensaje(mensaje)
        print("✅ Mensaje enviado a Telegram.")
    except Exception as e:
        print("❌ Error:", e)
        enviar_mensaje(f"⚠️ Error en el bot: {e}")

if __name__ == "__main__":
    main()
