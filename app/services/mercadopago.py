import hashlib
import hmac
import logging
import os

import httpx

from app.config import API_URL, MERCADOPAGO_ACCESS_TOKEN

logger = logging.getLogger(__name__)

MP_API = "https://api.mercadopago.com"


async def crear_preferencia_pago(
    patente: str,
    monto: float,
    email: str = "cliente@email.com",
) -> dict:
    if not MERCADOPAGO_ACCESS_TOKEN:
        logger.warning("MERCADOPAGO_ACCESS_TOKEN no configurado, usando modo mock")
        return {
            "init_point": f"https://mpago.la/mock_punatech_2026?patente={patente}&monto={monto}",
            "id": f"mock_{os.urandom(4).hex()}",
            "sandbox_init_point": f"https://mpago.la/mock_punatech_2026?patente={patente}",
        }

    headers = {
        "Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    preference_data = {
        "items": [{
            "title": f"Estacionamiento {patente}",
            "quantity": 1,
            "currency_id": "ARS",
            "unit_price": float(monto),
        }],
        "payer": {"email": email},
        "back_urls": {
            "success": f"{API_URL}/v1/pagos/exito",
            "failure": f"{API_URL}/v1/pagos/error",
            "pending": f"{API_URL}/v1/pagos/pendiente",
        },
        "external_reference": patente,
        "notification_url": f"{API_URL}/v1/pagos/webhook",
    }

    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.post(
            f"{MP_API}/checkout/preferences",
            headers=headers,
            json=preference_data,
        )
        if respuesta.status_code not in [200, 201]:
            logger.error(f"Error creando preferencia MP: {respuesta.text}")
            return {
                "init_point": f"https://mpago.la/mock_punatech_2026?patente={patente}",
                "id": f"mock_{os.urandom(4).hex()}",
            }
        data = respuesta.json()
        logger.info(f"Preferencia MP creada: {data['id']} para patente {patente}")
        return data


def verificar_webhook_signature(x_signature: str, x_request_id: str, data_id: str) -> bool:
    from app.config import MERCADOPAGO_WEBHOOK_SECRET

    if not MERCADOPAGO_WEBHOOK_SECRET:
        return True

    ts, v1 = x_signature.split(",")
    ts = ts.split("=")[1]
    v1 = v1.split("=")[1]

    manifest = f"id:{data_id};request-id:{x_request_id};ts:{ts};"
    hmac_obj = hmac.new(
        MERCADOPAGO_WEBHOOK_SECRET.encode(),
        manifest.encode(),
        hashlib.sha256,
    )
    expected = hmac_obj.hexdigest()
    return hmac.compare_digest(v1, expected)


async def obtener_pago(payment_id: int) -> dict | None:
    if not MERCADOPAGO_ACCESS_TOKEN:
        return {"status": "approved", "id": payment_id}

    headers = {"Authorization": f"Bearer {MERCADOPAGO_ACCESS_TOKEN}"}
    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.get(f"{MP_API}/v1/payments/{payment_id}", headers=headers)
        if respuesta.status_code == 200:
            return respuesta.json()
        logger.error(f"Error obteniendo pago MP: {respuesta.text}")
        return None
