import logging

from fastapi import APIRouter, Depends

from app.auth import verificar_api_key
from app.database import CiudadanoDB
from app.models.schemas import PeticionRegistrarCiudadano

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ciudadanos", tags=["Ciudadanos"])


@router.post("/registrar")
async def registrar_ciudadano(
    peticion: PeticionRegistrarCiudadano,
    _: str = Depends(verificar_api_key),
):
    carga = {
        "nombre": peticion.nombre,
        "patentes_registradas": peticion.patentes,
        "notificaciones_activas": True,
    }
    await CiudadanoDB.upsert(peticion.telegram_chat_id, carga)
    logger.info(f"Ciudadano registrado: chat_id={peticion.telegram_chat_id}, patentes={peticion.patentes}")
    return {"mensaje": "Ciudadano registrado correctamente", "patentes": peticion.patentes}


@router.get("/buscar")
async def buscar_por_patente(
    patente: str,
    _: str = Depends(verificar_api_key),
):
    ciudadanos = await CiudadanoDB.buscar_por_patente(patente)
    return {"ciudadanos": ciudadanos, "total": len(ciudadanos)}
