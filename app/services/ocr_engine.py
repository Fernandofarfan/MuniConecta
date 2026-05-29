import base64
import logging
import re

from app.models.schemas import PATENTE_MOTO_RE, PATENTE_NUEVA_RE, PATENTE_VIEJA_RE

logger = logging.getLogger(__name__)

_PLATE_RE = re.compile(
    f"({PATENTE_VIEJA_RE.pattern}|{PATENTE_NUEVA_RE.pattern}|{PATENTE_MOTO_RE.pattern})"
)


async def detectar_patente(imagen_base64: str) -> dict:
    try:
        from google.cloud import vision
    except (ImportError, ModuleNotFoundError):
        logger.warning("google-cloud-vision no instalado, usando OCR mock")
        return {
            "patente_detectada": "AB123CD",
            "confianza": 0.98,
            "mensaje": "OCR Mock (google-cloud-vision no instalado)",
        }

    try:
        image_bytes = base64.b64decode(imagen_base64)
        if len(image_bytes) > 10 * 1024 * 1024:
            return {
                "patente_detectada": None,
                "confianza": 0.0,
                "mensaje": "Imagen demasiado grande (max 10MB)",
            }

        cliente = vision.ImageAnnotatorClient()
        image = vision.Image(content=image_bytes)
        response = cliente.text_detection(image=image)

        if response.error.message:
            logger.error(f"Error Cloud Vision: {response.error.message}")
            return {
                "patente_detectada": None,
                "confianza": 0.0,
                "mensaje": f"Error de Vision API: {response.error.message}",
            }

        texts = response.text_annotations
        if not texts:
            return {
                "patente_detectada": None,
                "confianza": 0.0,
                "mensaje": "No se detecto texto en la imagen",
            }

        full_text = texts[0].description.replace(" ", "").replace("-", "").upper()
        match = _PLATE_RE.search(full_text)

        if match:
            patente = match.group(0)
            logger.info(f"Patente detectada: {patente}")
            return {
                "patente_detectada": patente,
                "confianza": 0.92,
                "mensaje": f"Patente detectada: {patente}",
            }

        return {
            "patente_detectada": None,
            "confianza": 0.0,
            "mensaje": "No se encontro formato de patente argentina en la imagen",
        }

    except Exception as e:
        logger.error(f"Error en OCR: {e}")
        return {
            "patente_detectada": None,
            "confianza": 0.0,
            "mensaje": "Error al procesar la imagen",
        }
