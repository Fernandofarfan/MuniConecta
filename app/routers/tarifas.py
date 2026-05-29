import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verificar_api_key
from app.config import TZ_ARG
from app.services.tarifas_especiales import obtener_tarifas_activas

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tarifas", tags=["Tarifas"])


@router.get("/activas")
async def tarifas_activas(_: str = Depends(verificar_api_key)):
    ahora = datetime.now(TZ_ARG)
    tarifas = await obtener_tarifas_activas(ahora)
    return {"tarifas": tarifas, "total": len(tarifas), "consulta": ahora.isoformat()}


@router.post("/especiales")
async def crear_tarifa_especial(peticion: dict, _: str = Depends(verificar_api_key)):
    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.post(
            f"{SUPABASE_URL}/rest/v1/tarifas_especiales",
            headers=headers,
            json=peticion,
        )
        if respuesta.status_code not in [201, 204]:
            raise HTTPException(status_code=500, detail=respuesta.text)
        data = respuesta.json()[0] if respuesta.status_code == 201 else peticion
        return {"mensaje": "Tarifa especial creada", "tarifa": data}
