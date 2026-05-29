import json
import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verificar_api_key
from app.config import SUPABASE_KEY, SUPABASE_URL
from app.models.schemas import validar_patente_argentina
from app.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/infracciones", tags=["Infracciones"])

MONTOS_MULTA = {"exceso_tiempo": 5000, "mal_estacionado": 8000, "sin_registro": 10000}


@router.post("/emitir")
async def emitir_infraccion(
    peticion: dict,
    _: str = Depends(verificar_api_key),
):
    import httpx

    patente = peticion.get("patente", "").upper().strip()
    try:
        patente = validar_patente_argentina(patente)
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de patente invalido")

    tipo = peticion.get("tipo_infraccion", "sin_registro")
    if tipo not in MONTOS_MULTA:
        raise HTTPException(status_code=422, detail=f"Tipo invalido. Usar: {list(MONTOS_MULTA.keys())}")

    carga = {
        "patente": patente,
        "tipo_infraccion": tipo,
        "legajo_inspector": peticion.get("legajo_inspector", "INSP-01"),
        "zona_id": peticion.get("zona_id"),
        "lat": peticion.get("lat"),
        "lon": peticion.get("lon"),
        "foto_evidencia": peticion.get("foto_evidencia"),
        "monto_multa": MONTOS_MULTA[tipo],
        "observaciones": peticion.get("observaciones"),
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }

    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.post(
            f"{SUPABASE_URL}/rest/v1/infracciones",
            headers=headers,
            json=carga,
        )
        if respuesta.status_code not in [201, 204]:
            raise HTTPException(status_code=500, detail=f"Error al guardar infraccion: {respuesta.text}")

        data = respuesta.json()[0] if respuesta.status_code == 201 else carga

    await manager.broadcast(json.dumps({"event": "update_dashboard"}))
    logger.info(f"Infraccion emitida: {patente} - {tipo} - ${MONTOS_MULTA[tipo]}")
    return {"mensaje": "Infraccion registrada", "infraccion": data}


@router.get("/consultar")
async def consultar_infracciones(
    patente: str,
    _: str = Depends(verificar_api_key),
):
    import httpx

    patente = patente.upper().strip()

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    async with httpx.AsyncClient() as cliente:
        url = f"{SUPABASE_URL}/rest/v1/infracciones?patente=eq.{patente}&select=*&order=creado_en.desc"
        respuesta = await cliente.get(url, headers=headers)
        if respuesta.status_code != 200:
            raise HTTPException(status_code=500, detail="Error al consultar infracciones")
        return {"patente": patente, "infracciones": respuesta.json(), "total": len(respuesta.json())}


@router.get("/multas/{patente}")
async def multas_ciudadano(patente: str):
    import httpx

    patente = patente.upper().strip()

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    async with httpx.AsyncClient() as cliente:
        url = f"{SUPABASE_URL}/rest/v1/infracciones?patente=eq.{patente}&estado=neq.anulada&select=*"
        respuesta = await cliente.get(url, headers=headers)
        if respuesta.status_code != 200:
            return {"patente": patente, "multas": [], "total_pendiente": 0}
        multas = respuesta.json()
        pendiente = sum(m["monto_multa"] for m in multas if m["estado"] == "pendiente")
        return {"patente": patente, "multas": multas, "total_pendiente": pendiente}


@router.post("/{infraccion_id}/apelar")
async def apelar_infraccion(
    infraccion_id: int,
    peticion: dict,
):
    import httpx

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    carga = {
        "apelacion_texto": peticion.get("motivo", ""),
        "apelacion_estado": "pendiente_revision",
    }
    async with httpx.AsyncClient() as cliente:
        url = f"{SUPABASE_URL}/rest/v1/infracciones?id=eq.{infraccion_id}"
        resp = await cliente.patch(url, headers=headers, json=carga)
        if resp.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Error al registrar apelacion")
        return {"mensaje": "Apelacion registrada. Sera revisada por un supervisor."}


@router.patch("/{infraccion_id}/resolver-apelacion")
async def resolver_apelacion(
    infraccion_id: int,
    peticion: dict,
    _: str = Depends(verificar_api_key),
):
    import httpx

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    carga = {
        "apelacion_estado": peticion.get("decision", "rechazada"),
        "apelacion_respuesta": peticion.get("respuesta", ""),
        "apelacion_revisado_por": peticion.get("revisado_por", "supervisor"),
    }
    if carga["apelacion_estado"] == "aceptada":
        carga["estado"] = "anulada"

    async with httpx.AsyncClient() as cliente:
        url = f"{SUPABASE_URL}/rest/v1/infracciones?id=eq.{infraccion_id}"
        resp = await cliente.patch(url, headers=headers, json=carga)
        if resp.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Error al resolver apelacion")
        return {"mensaje": f"Apelacion {carga['apelacion_estado']}"}


@router.post("/{infraccion_id}/pagar")
async def pagar_infraccion(infraccion_id: int):
    import httpx

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    async with httpx.AsyncClient() as cliente:
        url = f"{SUPABASE_URL}/rest/v1/infracciones?id=eq.{infraccion_id}&select=*"
        resp = await cliente.get(url, headers=headers)
        if resp.status_code != 200 or not resp.json():
            raise HTTPException(status_code=404, detail="Infraccion no encontrada")

        infraccion = resp.json()[0]
        if infraccion["estado"] == "pagada":
            raise HTTPException(status_code=400, detail="Esta infraccion ya fue pagada")

    from app.services.mercadopago import crear_preferencia_pago
    preferencia = await crear_preferencia_pago(
        infraccion["patente"],
        float(infraccion["monto_multa"]),
        "ciudadano@email.com",
    )

    return {
        "mensaje": "Link de pago generado",
        "init_point": preferencia["init_point"],
        "monto": infraccion["monto_multa"],
        "infraccion_id": infraccion_id,
    }
