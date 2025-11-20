import time
import requests
import smtplib
import schedule
import numpy as np
import matplotlib.pyplot as plt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
from openai import OpenAI

# =============================
# CONFIGURACIÓN
# =============================
EMAIL_USER = "maquinillo1988@gmail.com"
EMAIL_PASS = "mknp wofw retz njwv"
EMAIL_DESTINOS = ["rucho_88@hotmail.es", "bujias_88@hotmail.com", "sauldiazquintela@hotmail.com"]

OPENAI_API_KEY = "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"
client = OpenAI(api_key=OPENAI_API_KEY)

CRIPTOS = [
    "bitcoin", "ethereum", "solana", "ripple", "dogecoin",
    "stellar", "cardano", "binancecoin", "memecoin"
]

historial = {c: [] for c in CRIPTOS}
prices_15m = {c: [] for c in CRIPTOS}

portfolio = {"usd": 1000.0, "positions": {}, "trades": []}
fee_rate = 0.001
slippage = 0.0005

# =============================
# FUNCIONES DE PRECIOS
# =============================
def obtener_precios():
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": ",".join(CRIPTOS), "vs_currencies": "usd"}
    try:
        r = requests.get(url, params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print("ERROR al obtener precios:", e)
        return {}

# =============================
# INDICADORES
# =============================
def ema(values, period):
    return np.convolve(values, np.ones(period)/period, mode='valid')

def rsi(values, period=14):
    deltas = np.diff(values)
    up = deltas[deltas > 0].sum() / period
    down = -deltas[deltas < 0].sum() / period
    rs = up / down if down != 0 else 0
    return 100 - (100 / (1 + rs))

def macd(values):
    ema12 = ema(values, 12)
    ema26 = ema(values, 26)
    if len(ema26) < 1: return None, None, None
    macd_line = ema12[-1] - ema26[-1]
    signal = ema(macd_line * np.ones(9), 9)[-1]
    hist = macd_line - signal
    return macd_line, signal, hist

def bollinger(values, period=20):
    if len(values) < period: return None, None, None
    sma = np.mean(values[-period:])
    std = np.std(values[-period:])
    return sma + 2*std, sma - 2*std, sma

# =============================
# PAPER TRADING
# =============================
def ejecutar_trade(cripto, side, amount_usd, price):
    real_price = price * (1 + slippage if side == "buy" else 1 - slippage)
    fee = amount_usd * fee_rate
    final_amount = amount_usd - fee
    if side == "buy":
        qty = final_amount / real_price
        portfolio["usd"] -= amount_usd
        portfolio["positions"][cripto] = portfolio["positions"].get(cripto,0) + qty
    else:
        qty = final_amount / real_price
        portfolio["positions"][cripto] -= qty
        portfolio["usd"] += amount_usd
    portfolio["trades"].append({
        "time": datetime.now(),
        "side": side,
        "crypto": cripto,
        "amount": amount_usd,
        "price": real_price,
        "fee": fee
    })

def ladder_buy(cripto, price):
    steps = [0.25, 0.25, 0.25, 0.25]
    dips = [0.01, 0.02, 0.03, 0.04]
    for i in range(4):
        target = price * (1 - dips[i])
        if price <= target:
            ejecutar_trade(cripto, "buy", portfolio["usd"] * steps[i], price)

# =============================
# PREDICCIONES 24/48H
# =============================
def prediccion_horas(prices):
    if len(prices) < 5: return None, None
    x = np.arange(len(prices))
    coef = np.polyfit(x, prices, 1)
    pred_24h = np.polyval(coef, len(prices) + 96)
    pred_48h = np.polyval(coef, len(prices) + 192)
    return pred_24h, pred_48h

def generar_senal_trading(price_actual, pred_24h, pred_48h, umbral=0.005):
    if pred_24h is None or pred_48h is None: return "hold"
    cambio_24h = (pred_24h - price_actual)/price_actual
    cambio_48h = (pred_48h - price_actual)/price_actual
    if cambio_24h > umbral and cambio_48h > umbral: return "buy"
    elif cambio_24h < -umbral and cambio_48h < -umbral: return "sell"
    return "hold"

# =============================
# IA
# =============================
def generar_analisis_ia(texto_mercado):
    prompt = f"""
Analiza el mercado cripto con datos reales:

{texto_mercado}

Devuelve:
• Resumen breve  
• Tendencias fuertes  
• Riesgos  
• Señales alcistas/bajistas  
• Predicción 24h (orientativa)  
• Momento probable de mejor entrada  
"""
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system","content":"Eres un analista experto en criptomonedas."},
                {"role": "user","content": prompt}
            ]
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"ERROR OpenAI: {e}"

# =============================
# GRAFICO CON TRADES
# =============================
def generar_grafico():
    plt.figure(figsize=(12,6))
    for c in CRIPTOS:
        if len(historial[c])>1:
            times = [datetime.strptime(p[0], "%H:%M") if isinstance(p[0], str) else p[0] for p in historial[c]]
            vals = [p[1] for p in historial[c]]
            plt.plot(times, vals, label=c)
    plt.legend()
    plt.grid()
    plt.xlabel("Hora")
    plt.ylabel("Precio USD")
    plt.title("Historial Criptos con Predicciones y Trades")
    plt.savefig("grafico.png")
    plt.close()

# =============================
# EMAIL
# =============================
def enviar_correo(asunto, mensaje, imagen):
    msg = MIMEMultipart("related")
    msg["From"] = EMAIL_USER
    msg["To"] = EMAIL_USER
    msg["Bcc"] = ", ".join(EMAIL_DESTINOS)
    msg["Subject"] = asunto
    html = f"""
    <html><body>
    <h2>Informe Cripto + IA</h2>
    <pre>{mensaje}</pre>
    <img src="cid:grafico">
    </body></html>
    """
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html,"html"))
    msg.attach(alt)
    with open(imagen,"rb") as f:
        img = MIMEImage(f.read())
        img.add_header("Content-ID","<grafico>")
        msg.attach(img)
    try:
        s = smtplib.SMTP("smtp.gmail.com",587)
        s.starttls()
        s.login(EMAIL_USER,EMAIL_PASS)
        s.send_message(msg)
        s.quit()
    except Exception as e:
        print("ERROR enviando correo:",e)

# =============================
# TAREA PRINCIPAL
# =============================
def tarea():
    precios = obtener_precios()
    if not precios: return
    hora = datetime.now().strftime("%H:%M")
    texto_total = f"⏱ Informe {hora}\n\n"
    for c in CRIPTOS:
        price = precios[c]["usd"]
        historial[c].append((hora, price))
        prices_15m[c].append(price)
        if len(prices_15m[c])>200: prices_15m[c]=prices_15m[c][-200:]
        arr = np.array(prices_15m[c])
        r = rsi(arr) if len(arr)>15 else None
        macd_line, signal, histo = macd(arr)
        upper, lower, mid = bollinger(arr)
        pred24, pred48 = prediccion_horas(arr)
        senal = generar_senal_trading(price,pred24,pred48)
        texto_total += f"{c.upper()} → ${price}\n  RSI:{r}\n  MACD:{histo}\n  BB mid:{mid}\n  Pred 24h:{pred24}\n  Pred 48h:{pred48}\n  Señal:{senal}\n\n"
        if senal=="buy" and portfolio["usd"]>10: ejecutar_trade(c,"buy",portfolio["usd"]*0.1,price)
        elif senal=="sell" and portfolio["positions"].get(c,0)>0: ejecutar_trade(c,"sell",portfolio["positions"][c]*price*0.1,price)
    analisis = generar_analisis_ia(texto_total)
    mensaje_final = analisis + "\n\n" + texto_total
    generar_grafico()
    enviar_correo("📈 Informe Cripto + IA + Trading", mensaje_final,"grafico.png")
    print("✓ Informe enviado:",hora)

# =============================
# EJECUCIÓN
# =============================
tarea()
schedule.every(15).minutes.do(tarea)
print("Bot cripto ejecutándose... (Ctrl+C para detener)")
while True:
    schedule.run_pending()
    time.sleep(1)
