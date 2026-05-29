import logging

from fastapi import APIRouter

from app.models.schemas import PeticionOCR

logger = logging.getLogger(__name__)
router = APIRouter(tags=["OCR"])


@router.post("/escanear_patente")
async def escanear_patente(peticion: PeticionOCR):
    logger.info("OCR mock ejecutado")
    return {
        "patente_detectada": "AB123CD",
        "confianza": 0.98,
        "mensaje": "Lectura procesada por motor OCR (Mock)",
    }
