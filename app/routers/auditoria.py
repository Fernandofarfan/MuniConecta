import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verificar_api_key, verificar_jwt
from app.services.auditoria import obtener_auditoria

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auditoria", tags=["Auditoria"])


@router.get("")
async def listar_auditoria(
    desde: str = "",
    hasta: str = "",
    legajo: str = "",
    limit: int = 100,
    _: str = Depends(verificar_api_key),
    jwt: dict = Depends(verificar_jwt),
):
    if jwt.get("rol") not in ("supervisor", "admin"):
        raise HTTPException(status_code=403, detail="Requiere rol supervisor o admin")
    registros = await obtener_auditoria(desde, hasta, legajo, limit)
    return {"registros": registros, "total": len(registros)}
