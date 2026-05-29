import logging

from fastapi import APIRouter, Depends

from app.auth import verificar_api_key
from app.database import ZonaDB
from app.models.schemas import PeticionCrearZona

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/zonas", tags=["Zonas"])


@router.get("")
async def listar_zonas(_: str = Depends(verificar_api_key)):
    zonas = await ZonaDB.obtener_todas()
    return {"zonas": zonas}


@router.post("")
async def crear_zona(
    peticion: PeticionCrearZona,
    _: str = Depends(verificar_api_key),
):
    carga = {
        "nombre": peticion.nombre,
        "tarifa_auto": peticion.tarifa_auto,
        "tarifa_moto": peticion.tarifa_moto,
        "capacidad_maxima": peticion.capacidad_maxima,
        "activa": peticion.activa,
    }
    zona = await ZonaDB.crear(carga)
    logger.info(f"Zona creada: {zona['nombre']}")
    return {"mensaje": "Zona creada correctamente", "zona": zona}


@router.get("/ocupacion")
async def ocupacion_zonas(_: str = Depends(verificar_api_key)):
    ocupacion = await ZonaDB.obtener_ocupacion()
    return {"zonas": ocupacion}
