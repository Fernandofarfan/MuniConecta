import os
import json
import logging
import asyncio
import httpx
from dotenv import load_dotenv

# Cargar variables de entorno del archivo .env
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

import google.generativeai as genai

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

try:
    with open("plan_vial.json", "r", encoding="utf-8") as f:
        PLAN_VIAL_DATA = json.load(f)
except Exception as e:
    logger.error(f"Error cargando plan_vial.json: {e}")
    PLAN_VIAL_DATA = []

system_instruction = f"""Sos el asistente virtual oficial de la Municipalidad de Salta. El usuario reporta un incidente urbano. 
Acá tenés el Plan de Obras actual: {json.dumps(PLAN_VIAL_DATA, ensure_ascii=False)}. 
Analizá el reclamo, extraé la calle o barrio, y verificá si está en el plan. 
Si ESTÁ, respondé de manera institucional indicando que la obra ya se encuentra programada o en ejecución para llevar tranquilidad al vecino. 
Si NO ESTÁ, confirmá formalmente la recepción del reclamo y su derivación al área de Obras Públicas correspondiente. 
IMPORTANTE: Si la imagen recibida NO muestra un problema urbano real (ej. selfies, personas, mascotas, saludos, pulgares arriba), respondé amablemente indicando que el canal es de uso exclusivo para reportes de infraestructura pública dañada.
SI DETECTÁS lenguaje violento, amenazas, o situaciones de emergencia (ej. accidentes graves, delitos), no proceses el reclamo y respondé: 'Por motivos de seguridad, los reportes de emergencias deben realizarse a través de los canales oficiales al 911'.
Respondé SIEMPRE en un tono formal, neutro, profesional y claro, adecuado para una entidad gubernamental. Mostrá empatía y vocación de servicio, pero evitá estrictamente el lunfardo, la jerga informal o el exceso de coloquialismos."""

try:
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash',
        system_instruction=system_instruction
    )
except Exception as e:
    logger.error(f"Error inicializando el modelo Gemini: {e}")
    model = None

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
                
                # Obtener la ruta del archivo de la foto
                file_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getFile?file_id={file_id}"
                async with httpx.AsyncClient() as client:
                    file_response = await client.get(file_url)
                    file_data = file_response.json()
                    
                if file_data.get("ok"):
                    file_path = file_data["result"]["file_path"]
                    download_url = f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_path}"
                    
                    # Descargar los bytes de la imagen
                    async with httpx.AsyncClient() as client:
                        img_response = await client.get(download_url)
                        img_bytes = img_response.content
                        
                        content_parts.append({
                            "mime_type": "image/jpeg",
                            "data": img_bytes
                        })
            
            # Invocar a Gemini con el texto y la imagen
            try:
                if model:
                    response = await model.generate_content_async(content_parts)
                    gemini_text = response.text
                else:
                    gemini_text = "Uh, disculpá che. Tengo un problema de configuración interno."
            except Exception as e:
                logger.error(f"Error llamando a Gemini: {e}")
                gemini_text = "Uh, disculpá che. Se nos cayó el sistema un ratito. ¿Podés intentar de nuevo en un toque?"
                
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
