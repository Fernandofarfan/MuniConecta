import logging

import httpx

from app.config import TELEGRAM_BOT_TOKEN

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"


async def enviar_mensaje(chat_id: int, texto: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado, notificacion no enviada")
        return False

    async with httpx.AsyncClient() as cliente:
        try:
            respuesta = await cliente.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": chat_id, "text": texto},
                timeout=10.0,
            )
            if respuesta.status_code == 200:
                logger.info(f"Notificacion enviada a chat_id={chat_id}")
                return True
            logger.error(f"Error Telegram: {respuesta.text}")
            return False
        except Exception as e:
            logger.error(f"Error enviando notificacion Telegram: {e}")
            return False


async def notificar_inicio_estacionamiento(
    chat_id: int, patente: str, tipo: str
) -> bool:
    texto = (
        f"Tu vehiculo {patente} ({tipo}) ha sido registrado.\n"
        f"Podes consultar tu deuda con /deuda {patente}"
    )
    return await enviar_mensaje(chat_id, texto)


async def notificar_deuda_acumulada(
    chat_id: int, patente: str, monto: float, link_pago: str
) -> bool:
    texto = (
        f"Recordatorio: tu vehiculo {patente} tiene una deuda de ${monto:.2f}\n"
        f"Podes pagar con 20% de descuento: {link_pago}"
    )
    return await enviar_mensaje(chat_id, texto)
