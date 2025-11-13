import requests
import matplotlib.pyplot as plt
import numpy as np
import io
from datetime import datetime, timedelta
from telegram import Bot

# --- CONFIGURACIÓN DEL BOT ---
TELEGRAM_TOKEN = "8388545388:AAFphIeJ04XDvgWiwbKjaHqRPpyHPzTmtlU"        # reemplaza con tu token
CHAT_ID = "7743163483"                  # reemplaza con el ID de tu grupo o chat

bot = Bot(token=TELEGRAM_TOKEN)

# Función para obtener precios de criptomonedas
def obtener_precios():
    """Obtiene precios actuales de Bitcoin y Ethereum desde CoinGecko"""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum&vs_currencies=usd"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Esto asegura que si hay un error HTTP, se lanzará una excepción
        data = response.json()

        # Verificar que los datos estén en el formato esperado
        if 'bitcoin' in data and 'ethereum' in data:
            btc = data['bitcoin']['usd']
            eth = data['ethereum']['usd']
            return btc, eth
        else:
            print("Error: Datos no encontrados en la respuesta de la API.")
            return None, None

    except requests.exceptions.RequestException as e:
        print(f"Error al realizar la solicitud: {e}")
        return None, None

# Función para generar un gráfico de precios
def generar_grafico():
    """Genera un gráfico de precios de las criptomonedas"""
    btc, eth = obtener_precios()

    # Verificar que obtuvimos los precios correctamente
    if btc is None or eth is None:
        print("Error al obtener los precios de las criptomonedas.")
        return None

    # Simulación de datos para el gráfico (últimos 10 minutos)
    tiempos = [datetime.now() - timedelta(minutes=i) for i in range(10)]
    bitcoin_prices = np.random.uniform(low=btc-500, high=btc+500, size=10)  # Generación de precios simulados
    ethereum_prices = np.random.uniform(low=eth-50, high=eth+50, size=10)  # Generación de precios simulados

    # Crear el gráfico
    fig, ax = plt.subplots()
    ax.plot(tiempos, bitcoin_prices, label="Bitcoin", color='blue')
    ax.plot(tiempos, ethereum_prices, label="Ethereum", color='green')

    ax.set(xlabel='Tiempo', ylabel='Precio en USD',
           title='Estado del mercado de criptomonedas')
    ax.grid()
    ax.legend()

    # Guardar el gráfico en un objeto de bytes para enviarlo por Telegram
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    return buf

# Llamada a la función para generar el gráfico
grafico = generar_grafico()
if grafico:
    # Aquí podrías agregar el código para enviar el gráfico por Telegram si lo necesitas
    pass


