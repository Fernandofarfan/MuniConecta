import os
import logging
from fastapi import FastAPI, Request
import httpx
from dotenv import load_dotenv

from services.telegram_client import send_telegram_message, send_chat_action, download_telegram_image
from services.gemini_service import generate_content_async

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno (útil para desarrollo local)
load_dotenv()

MUNICIPAL_CHANNEL_ID = os.getenv("MUNICIPAL_CHANNEL_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

app = FastAPI(title="MuniConecta API")

@app.post("/webhook")
async def telegram_webhook(request: Request):
    """Endpoint para recibir updates (mensajes y fotos) de Telegram."""
    try:
        update = await request.json()
        logger.info(f"Update recibido: {update}")
        
        if "message" in update:
            message = update["message"]
            chat_id = message["chat"]["id"]
            
            # Enviar acción de "escribiendo..." al usuario
            await send_chat_action(chat_id)
            
            # Obtener texto del mensaje o caption de la foto
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
                # Telegram envía varias resoluciones, tomamos la de mayor calidad (la última)
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
                
            # Enviar la respuesta generada al usuario por Telegram
            await send_telegram_message(chat_id, gemini_text)
            
            # Enviar una copia del reporte al canal privado de la municipalidad (Human-in-the-Loop)
            if MUNICIPAL_CHANNEL_ID:
                await send_telegram_message(MUNICIPAL_CHANNEL_ID, f"Nuevo Reporte: {user_text}")
                
            # Guardar reporte en Supabase
            if SUPABASE_URL and SUPABASE_KEY:
                try:
                    async with httpx.AsyncClient() as sb_client:
                        headers = {
                            "apikey": SUPABASE_KEY,
                            "Authorization": f"Bearer {SUPABASE_KEY}",
                            "Content-Type": "application/json",
                            "Prefer": "return=minimal"
                        }
                        payload = {"ubicacion": "Reporte de Telegram", "detalle": user_text if user_text else "Reporte con imagen"}
                        sb_url = f"{SUPABASE_URL}/rest/v1/reclamos"
                        sb_res = await sb_client.post(sb_url, headers=headers, json=payload)
                        logger.info(f"Supabase status: {sb_res.status_code}")
                except Exception as sb_e:
                    logger.error(f"Error escribiendo en Supabase: {sb_e}")
            
    except Exception as e:
        logger.error(f"Error general en webhook: {e}")
        # Retornamos 200 siempre en el finally / except para evitar reintentos infinitos de Telegram
        
    return {"status": "ok"}
