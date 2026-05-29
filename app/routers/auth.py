import logging

from fastapi import APIRouter, HTTPException

from app.auth import crear_jwt, verificar_password
from app.database import InspectorDB
from app.models.schemas import PeticionLogin, RespuestaLogin

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=RespuestaLogin)
async def login(peticion: PeticionLogin):
    inspector = await InspectorDB.buscar_por_legajo(peticion.legajo)
    if not inspector:
        raise HTTPException(status_code=401, detail="Legajo o password invalidos")

    if not verificar_password(peticion.password, inspector["password_hash"]):
        raise HTTPException(status_code=401, detail="Legajo o password invalidos")

    token = crear_jwt({
        "sub": inspector["legajo"],
        "rol": inspector.get("rol", "inspector"),
        "zona_id": inspector.get("zona_asignada_id"),
        "inspector_id": inspector["id"],
    })

    logger.info(f"Inspector {inspector['legajo']} autenticado")
    return RespuestaLogin(
        access_token=token,
        inspector={
            "legajo": inspector["legajo"],
            "nombre": inspector["nombre"],
            "rol": inspector["rol"],
            "zona_id": inspector.get("zona_asignada_id"),
        },
    )
