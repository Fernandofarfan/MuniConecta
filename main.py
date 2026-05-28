import os
import json
import logging
from fastapi import FastAPI, Request
import httpx
import google.generativeai as genai
from dotenv import load_dotenv

# Configuración básica de logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno (útil para desarrollo local)
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
MUNICIPAL_CHANNEL_ID = os.getenv("MUNICIPAL_CHANNEL_ID", "")
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

# Configurar Gemini
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI(title="MuniConecta API")

# Cargar plan vial desde el JSON estático en memoria
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
                        
                        # Añadir la imagen al payload para Gemini (Multimodal)
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
                            "Content-Type": "application/json"
                        }
                        payload = {"ubicacion": "Reporte de Telegram", "detalle": user_text}
                        sb_url = f"{SUPABASE_URL}/rest/v1/reclamos"
                        sb_res = await sb_client.post(sb_url, headers=headers, json=payload)
                        logger.info(f"Supabase status: {sb_res.status_code}")
                except Exception as sb_e:
                    logger.error(f"Error escribiendo en Supabase: {sb_e}")
            
    except Exception as e:
        logger.error(f"Error general en webhook: {e}")
        # Retornamos 200 siempre en el finally / except para evitar reintentos infinitos de Telegram
        
    return {"status": "ok"}
