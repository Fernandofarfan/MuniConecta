import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
API_KEY = os.getenv("API_KEY", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Bienvenido a SEM Express!\n\n"
        "Enviame una patente para consultar tu deuda de estacionamiento.\n"
        "Ejemplo: AB123CD\n\n"
        "Comandos:\n"
        "/start - Este mensaje\n"
        "/deuda AB123CD - Consultar deuda de una patente"
    )


async def consultar_deuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Uso: /deuda AB123CD")
        return

    patente = context.args[0]
    await _procesar_consulta(update, patente)


async def manejar_mensaje(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text.strip().upper()
    if len(texto) >= 6:
        import re
        if re.match(r"^[A-Z]{2,3}\d{3}[A-Z]{0,2}$", texto) or re.match(r"^\d{3}[A-Z]{3}$", texto):
            await _procesar_consulta(update, texto)
            return
    await update.message.reply_text(
        "Envia una patente valida (ej: AB123CD) o usa /deuda AB123CD"
    )


async def _procesar_consulta(update: Update, patente: str):
    import httpx

    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["X-API-Key"] = API_KEY

    async with httpx.AsyncClient() as cliente:
        try:
            respuesta = await cliente.post(
                f"{API_URL}/consultar_deuda",
                json={"patente": patente},
                headers=headers,
                timeout=10.0,
            )
            if respuesta.status_code == 200:
                data = respuesta.json()
                texto = (
                    f"Patente: {patente}\n"
                    f"Tiempo transcurrido: {data.get('tiempo_transcurrido_minutos')} min\n"
                    f"Monto total: ${data.get('monto_total')}\n"
                    f"Monto con MercadoPago (20% off): ${data.get('monto_con_descuento_digital')}\n"
                    f"Link de pago: {data.get('link_pago_mp')}"
                )
            elif respuesta.status_code == 404:
                texto = f"No se encontro un estacionamiento activo para {patente}"
            elif respuesta.status_code == 422:
                texto = f"Patente con formato invalido: {patente}"
            else:
                texto = f"Error del servidor ({respuesta.status_code})"
        except Exception as e:
            logger.error(f"Error consultando API: {e}")
            texto = "Error de conexion con el servidor. Intenta de nuevo mas tarde."

    await update.message.reply_text(texto)


def main():
    if not TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN no configurado")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("deuda", consultar_deuda))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, manejar_mensaje))

    logger.info("Bot de Telegram iniciado...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
