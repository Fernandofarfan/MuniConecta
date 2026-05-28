import os
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
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

async def generate_content_async(content_parts: list) -> str:
    """Genera contenido de manera asíncrona usando Gemini."""
    try:
        if model:
            response = await model.generate_content_async(content_parts)
            return response.text
        else:
            return "Uh, disculpá che. Tengo un problema de configuración interno."
    except Exception as e:
        logger.error(f"Error llamando a Gemini: {e}")
        return "Uh, disculpá che. Se nos cayó el sistema un ratito. ¿Podés intentar de nuevo en un toque?"
