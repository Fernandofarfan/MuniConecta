import requests
import time
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

def responder_telegram():
    last_update_id = 0
    while True:
        try:
            updates = requests.get(f"https://api.telegram.org/bot{TOKEN}/getUpdates?offset={last_update_id + 1}").json()
            for update in updates.get("result", []):
                last_update_id = update["update_id"]
                msg = update.get("message", {}).get("text", "")
                chat_id = update["message"]["chat"]["id"]
                if "Deuda" in msg:
                    patente = msg.split()[-1]
                    res = requests.post(f"{API_URL}/calcular_cobro", json={"patente": patente, "metodo_pago": "digital"}).json()
                    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": chat_id, "text": f"🚗 Patente: {patente}\n💰 Total: ${res.get('monto_final')}\n💳 Link: {res.get('link_pago_mp')}"})
        except Exception as e: print(f"Error bot: {e}")
        time.sleep(2)

if __name__ == "__main__": responder_telegram()
