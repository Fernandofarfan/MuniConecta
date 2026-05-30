import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import crear_hash_password, verificar_api_key, verificar_jwt
from app.database import InspectorDB, InspectorFinanzasDB
from app.services.email_digest import enviar_digests_automaticos

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["Admin CRUD"])


def _verificar_admin(jwt: dict):
    if jwt.get("rol") not in ("supervisor", "admin"):
        raise HTTPException(status_code=403, detail="Requiere rol supervisor o admin")


@router.get("/inspectores")
async def listar_inspectores(_: str = Depends(verificar_api_key), jwt: dict = Depends(verificar_jwt)):
    _verificar_admin(jwt)
    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    async with httpx.AsyncClient() as cliente:
        resp = await cliente.get(f"{SUPABASE_URL}/rest/v1/inspectores?select=*", headers=headers)
        if resp.status_code != 200:
            raise HTTPException(status_code=500, detail="Error al consultar inspectores")
        return {"inspectores": resp.json()}


@router.post("/inspectores")
async def crear_inspector(peticion: dict, _: str = Depends(verificar_api_key), jwt: dict = Depends(verificar_jwt)):
    _verificar_admin(jwt)

    legajo = peticion.get("legajo", "").strip()
    if not legajo:
        raise HTTPException(status_code=422, detail="Legajo requerido")

    existing = await InspectorDB.buscar_por_legajo(legajo)
    if existing:
        raise HTTPException(status_code=409, detail="El legajo ya existe")

    carga = {
        "legajo": legajo,
        "nombre": peticion.get("nombre", legajo),
        "password_hash": crear_hash_password(peticion.get("password", "cambiar123")),
        "zona_asignada_id": peticion.get("zona_asignada_id"),
        "rol": peticion.get("rol", "inspector"),
    }
    inspector = await InspectorDB.crear(carga)
    return {"mensaje": "Inspector creado", "inspector": inspector}


@router.patch("/inspectores/{legajo}")
async def actualizar_inspector(legajo: str, peticion: dict, _: str = Depends(verificar_api_key), jwt: dict = Depends(verificar_jwt)):
    _verificar_admin(jwt)

    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    carga = {}
    if "nombre" in peticion:
        carga["nombre"] = peticion["nombre"]
    if "zona_asignada_id" in peticion:
        carga["zona_asignada_id"] = peticion["zona_asignada_id"]
    if "rol" in peticion:
        carga["rol"] = peticion["rol"]
    if "activo" in peticion:
        carga["activo"] = peticion["activo"]
    if "password" in peticion and peticion["password"]:
        carga["password_hash"] = crear_hash_password(peticion["password"])

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient() as cliente:
        resp = await cliente.patch(
            f"{SUPABASE_URL}/rest/v1/inspectores?legajo=eq.{legajo}",
            headers=headers,
            json=carga,
        )
        if resp.status_code not in [200, 204]:
            raise HTTPException(status_code=500, detail="Error al actualizar inspector")
        return {"mensaje": "Inspector actualizado"}


@router.get("/digest/enviar")
async def disparar_digest(frecuencia: str = "semanal", _: str = Depends(verificar_api_key), jwt: dict = Depends(verificar_jwt)):
    _verificar_admin(jwt)
    await enviar_digests_automaticos(frecuencia)
    return {"mensaje": f"Digest {frecuencia} enviado"}


@router.post("/digest/suscribir")
async def suscribir_digest(peticion: dict, _: str = Depends(verificar_api_key)):
    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient() as cliente:
        resp = await cliente.post(
            f"{SUPABASE_URL}/rest/v1/suscriptores_digest",
            headers=headers,
            json={
                "email": peticion["email"],
                "nombre": peticion.get("nombre", ""),
                "frecuencia": peticion.get("frecuencia", "semanal"),
            },
        )
        if resp.status_code not in [201, 204]:
            detail = resp.text if resp.status_code == 409 else "Error al suscribir"
            status = 409 if resp.status_code == 409 else 500
            raise HTTPException(status_code=status, detail=detail)
        return {"mensaje": "Suscripto al digest"}


@router.post("/rendicion/{legajo}")
async def rendicion_efectivo(legajo: str, peticion: dict, _: str = Depends(verificar_api_key)):
    monto = peticion.get("monto", 0)
    if monto <= 0:
        raise HTTPException(status_code=422, detail="El monto a rendir debe ser mayor a 0")

    try:
        resultado = await InspectorFinanzasDB.rendir(legajo, float(monto))
        return {"mensaje": f"Rendicion registrada. Nuevo saldo: ${resultado['saldo_actual']:.2f}", **resultado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar rendicion: {e}")
