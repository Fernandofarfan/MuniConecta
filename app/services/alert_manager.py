import logging

from app.services.notificador import enviar_mensaje as enviar_telegram

logger = logging.getLogger(__name__)


async def enviar_alerta_ciudadano(
    chat_id: int = 0,
    email: str | None = None,
    telefono: str | None = None,
    titulo: str = "",
    mensaje: str = "",
    severidad: str = "media",
    canal_principal: str = "telegram",
) -> dict:
    resultados = {"telegram": False, "email": False, "sms": False}
    texto = f"{'🔴' if severidad == 'alta' else '🟡' if severidad == 'media' else '🟢'} {titulo}\n\n{mensaje}"

    if chat_id and canal_principal == "telegram":
        resultados["telegram"] = await enviar_telegram(chat_id, texto)

    if email:
        logger.info(f"Email simulado a {email}: {titulo}")
        resultados["email"] = True

    if telefono:
        logger.info(f"SMS simulado a {telefono}: {titulo}")
        resultados["sms"] = True

    return resultados


async def alertar_supervisor(mensaje: str, severidad: str = "media"):
    supervisor_chat_id = None
    try:
        from app.config import MUNICIPAL_CHANNEL_ID
        if MUNICIPAL_CHANNEL_ID:
            supervisor_chat_id = int(MUNICIPAL_CHANNEL_ID)
    except (ImportError, ValueError):
        pass

    if supervisor_chat_id:
        await enviar_telegram(supervisor_chat_id, f"🚨 Alerta SEM Express ({severidad}): {mensaje}")
    else:
        logger.info(f"Alerta supervisor (sin canal configurado): {mensaje}")
