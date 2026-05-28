import os
import logging
import asyncio
import httpx
from dotenv import load_dotenv

from services.telegram_client import send_telegram_message, send_chat_action, download_telegram_image
from services.gemini_service import generate_content_async

# Cargar variables de entorno del archivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def process_update(update: dict):
    """Procesa un update (mensaje) recibido de Telegram usando Gemini."""
    try:
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            
            # Enviar acción de "escribiendo..." al usuario
            await send_chat_action(chat_id)
            
            user_text = message.get("text", "")
            caption = message.get("caption", "")
            
            prompt_text = ""
            if user_text:
                prompt_text += user_text + "\n"
            if caption:
                prompt_text += caption + "\n"
                
            content_parts = []
            if prompt_text:
                content_parts.append(prompt_text)
            else:
                content_parts.append("Reclamo ciudadano (imagen adjunta)")

            # Procesar foto si fue enviada
            photos = message.get("photo", [])
            if photos:
                photo = photos[-1]
                file_id = photo["file_id"]
                img_bytes = await download_telegram_image(file_id)
                if img_bytes:
                    content_parts.append({
                        "mime_type": "image/jpeg",
                        "data": img_bytes
                    })
            
            # Invocar a Gemini con el texto y la imagen
            gemini_text = await generate_content_async(content_parts)
                
            # Enviar respuesta de vuelta a Telegram
            await send_telegram_message(chat_id, gemini_text)
            logger.info(f"Mensaje respondido a chat_id {chat_id}")
            
    except Exception as e:
        logger.error(f"Error procesando update: {e}")

async def main():
    if not TELEGRAM_BOT_TOKEN:
        logger.error("Falta TELEGRAM_BOT_TOKEN en el entorno (.env).")
        return
        
    async with httpx.AsyncClient() as client:
        # Borrar webhook si existiera para que getUpdates funcione sin problemas
        logger.info("Borrando webhook de Telegram...")
        await client.get(f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteWebhook")
        
        logger.info("Bot MuniConecta iniciado en modo Local (Polling)...")
        offset = 0
        while True:
            try:
                url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates?offset={offset}&timeout=30"
                response = await client.get(url, timeout=35.0)
                data = response.json()
                
                if data.get("ok"):
                    updates = data.get("result", [])
                    for update in updates:
                        await process_update(update)
                        offset = update["update_id"] + 1
            except asyncio.CancelledError:
                logger.info("Desconectando...")
                break
            except Exception as e:
                logger.error(f"Error en loop de polling: {e}")
                await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot detenido por teclado.")
