import os
from datetime import timedelta, timezone
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
API_KEY = os.getenv("API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")

GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
MERCADOPAGO_ACCESS_TOKEN = os.getenv("MERCADOPAGO_ACCESS_TOKEN")
MERCADOPAGO_PUBLIC_KEY = os.getenv("MERCADOPAGO_PUBLIC_KEY")

JWT_SECRET = os.getenv("JWT_SECRET", "semexpress-secret-cambiar-en-produccion")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 12

TZ_ARG = timezone(timedelta(hours=-3))

TARIFA_AUTO = 700
TARIFA_MOTO = 300
TOLERANCIA_MINUTOS = 5
DESCUENTO_DIGITAL = 0.80
FRACCION_MINUTOS = 15

MP_WEBHOOK_SECRET = os.getenv("MERCADOPAGO_WEBHOOK_SECRET", "")
MERCADOPAGO_WEBHOOK_SECRET = MP_WEBHOOK_SECRET


def get_tarifa(tipo_vehiculo: str) -> int:
    if tipo_vehiculo == "auto":
        return TARIFA_AUTO
    if tipo_vehiculo == "moto":
        return TARIFA_MOTO
    raise ValueError(f"Tipo de vehiculo no valido: {tipo_vehiculo}")
