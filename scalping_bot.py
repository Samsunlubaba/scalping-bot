from binance.client import Client
from binance.enums import *
import pandas as pd
import ta
import time
import requests

# Binance API bilgileri
api_key = "c1AWkzhpkRCPR9DIYocjja7z7VymYjSbtmXfRzMiraJJ7QT5hP0f5kRrhzsPiwNG"
api_secret = "ECBaCFC6RaYSc8kzUvGJ43Oob0tnUC5PCYCVt0xtkzzkBKD15MFqlfvLmrYrxf8p"
client = Client(api_key, api_secret)

# Telegram bilgileri
telegram_token = "7713086178:AAHSYFZ69oOp8QJatCNjQw7ylJfpZQ-27Wg"
chat_id = "7733770130"

# Telegram mesaj fonksiyonu
def send_telegram(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message}
    try:
        response = requests.post(url, data=data)
        print("Telegram mesajı gönderildi:", response.status_code)
    except Exception as e:
        print("Telegram mesajı gönderilemedi:", e)

# Bot ayarları
symbol = "BTCUSDT"
quantity = 0.001
leverage = 5
client.futures_change_leverage(symbol=symbol, leverage=leverage)

# Fiyat ve RSI verisi çek
def get_data():
    klines = client.futures_klines(symbol=symbol, interval='1m', limit=100)
    df = pd.DataFrame(klines, columns=[
        'time', 'open', 'high', 'low', 'close', 'volume',
        'close_time', 'quote_asset_volume', 'number_of_trades',
        'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
    ])
    df['close'] = pd.to_numeric(df['close'])
    return df

# RSI stratejisi
def strategy(df):
    rsi = ta.momentum.RSIIndicator(df['close']).rsi()
    last_rsi = rsi.iloc[-1]
    return last_rsi, last_rsi < 30

# Alım emri ve TP/SL ayarları
def open_trade(entry_price):
    try:
        client.futures_create_order(
            symbol=symbol,
            side=SIDE_BUY,
            type='STOP_MARKET',
            quantity=quantity
        )
        send_telegram(f"✅ ALIM YAPILDI\nFiyat: {entry_price} USDT")

       tp = round(entry_price * 1.01, 2)
       sl = round(entry_price * 0.985, 2)


        client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_LIMIT,
            quantity=quantity,
            price=str(tp),
            timeInForce=TIME_IN_FORCE_GTC
        )
        client.futures_create_order(
            symbol=symbol,
            side=SIDE_SELL,
            type=ORDER_TYPE_STOP_MARKET,
            stopPrice=str(sl),
            quantity=quantity,
            timeInForce=TIME_IN_FORCE_GTC
        )

        send_telegram(f"🎯 TP: {tp} USDT\n🛑 SL: {sl} USDT")

    except Exception as e:
        send_telegram(f"❌ İşlem açma hatası: {e}")
        print("İşlem hatası:", e)

# Ana döngü
while True:
    try:
        df = get_data()
        rsi_val, is_signal = strategy(df)
        entry_price = float(client.futures_mark_price(symbol=symbol)['markPrice'])

        send_telegram(f"📊 RSI: {round(rsi_val, 2)} | Fiyat: {entry_price} USDT")

        if is_signal:
            open_trade(entry_price)
        else:
            print("⏳ RSI > 30, bekleniyor...")

        time.sleep(60)

    except Exception as e:
        send_telegram(f"⚠️ Genel hata: {e}")
        print("Genel hata:", e)
        time.sleep(60)
