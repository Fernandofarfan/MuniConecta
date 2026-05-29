import logging

logger = logging.getLogger(__name__)


async def registrar_auditoria(legajo: str, accion: str, entidad: str = "", entidad_id: int = 0, detalles: dict | None = None):
    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    carga = {
        "legajo_inspector": legajo,
        "accion": accion,
        "entidad": entidad,
        "entidad_id": entidad_id,
        "detalles": detalles or {},
    }
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    try:
        async with httpx.AsyncClient() as cliente:
            resp = await cliente.post(f"{SUPABASE_URL}/rest/v1/auditoria", headers=headers, json=carga)
            if resp.status_code not in [201, 204]:
                logger.warning(f"Error registrando auditoria: {resp.text}")
    except Exception as e:
        logger.warning(f"Error registrando auditoria: {e}")


async def obtener_auditoria(desde: str = "", hasta: str = "", legajo: str = "", limit: int = 100) -> list[dict]:
    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    params = [f"limit={limit}", "order=creado_en.desc"]
    if desde:
        params.append(f"creado_en=gte.{desde}")
    if hasta:
        params.append(f"creado_en=lte.{hasta}")
    if legajo:
        params.append(f"legajo_inspector=eq.{legajo}")

    url = f"{SUPABASE_URL}/rest/v1/auditoria?{'&'.join(params)}&select=*"
    async with httpx.AsyncClient() as cliente:
        resp = await cliente.get(url, headers=headers)
        if resp.status_code != 200:
            return []
        return resp.json()
