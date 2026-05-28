import os
import logging
import httpx
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
logger = logging.getLogger(__name__)

async def send_telegram_message(chat_id: int, text: str):
    """Envía un mensaje de texto a Telegram vía API."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Error enviando respuesta a Telegram: {e}")

async def send_chat_action(chat_id: int):
    """Envía la acción de 'typing' a Telegram para indicar que el bot está respondiendo."""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendChatAction"
    payload = {
        "chat_id": chat_id,
        "action": "typing"
    }
    async with httpx.AsyncClient() as client:
        try:
            await client.post(url, json=payload)
        except Exception as e:
            logger.error(f"Error enviando chat action a Telegram: {e}")

async def download_telegram_image(file_id: str) -> bytes | None:
    """Descarga una imagen de Telegram dado su file_id."""
    file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
    async with httpx.AsyncClient() as client:
        try:
            file_response = await client.get(file_url)
            file_data = file_response.json()
            if file_data.get("ok"):
                file_path = file_data["result"]["file_path"]
                download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                img_response = await client.get(download_url)
                return img_response.content
        except Exception as e:
            logger.error(f"Error descargando imagen de Telegram: {e}")
    return None
