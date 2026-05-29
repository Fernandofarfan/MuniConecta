import logging

from fastapi import APIRouter, HTTPException

from app.services.dnrpa_lookup import consultar_dnrpa

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/dnrpa", tags=["DNRPA"])


@router.get("/{patente}")
async def lookup_dnrpa(patente: str):
    try:
        resultado = await consultar_dnrpa(patente)
        return resultado
    except Exception as e:
        logger.error(f"Error DNRPA: {e}")
        raise HTTPException(status_code=404, detail="No se encontraron datos para esa patente")
