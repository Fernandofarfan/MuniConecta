import logging

logger = logging.getLogger(__name__)


async def verificar_abono_activo(patente: str, zona_id: int | None = None) -> dict | None:
    from datetime import date

    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    hoy = date.today().isoformat()
    url = (
        f"{SUPABASE_URL}/rest/v1/abonos"
        f"?patente=eq.{patente}"
        f"&estado=eq.activo"
        f"&fecha_inicio=lte.{hoy}"
        f"&fecha_fin=gte.{hoy}"
        f"&select=*"
    )
    async with httpx.AsyncClient() as cliente:
        resp = await cliente.get(url, headers=headers)
        if resp.status_code != 200:
            return None
        abonos = resp.json()
        if zona_id:
            abonos = [a for a in abonos if a.get("zona_id") == zona_id or a.get("zona_id") is None]
        return abonos[0] if abonos else None


async def crear_abono(patente: str, zona_id: int, tipo: str, chat_id: int | None = None) -> dict:
    from datetime import date, timedelta

    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    hoy = date.today()
    dias = 7 if tipo == "semanal" else 30
    fin = hoy + timedelta(days=dias)
    montos = {"semanal": 4000, "mensual": 15000}

    carga = {
        "patente": patente,
        "zona_id": zona_id,
        "tipo": tipo,
        "fecha_inicio": hoy.isoformat(),
        "fecha_fin": fin.isoformat(),
        "monto": montos.get(tipo, 15000),
        "estado": "activo",
        "chat_id": chat_id,
    }

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    async with httpx.AsyncClient() as cliente:
        resp = await cliente.post(f"{SUPABASE_URL}/rest/v1/abonos", headers=headers, json=carga)
        if resp.status_code not in [201, 204]:
            raise Exception(f"Error creando abono: {resp.text}")
        data = resp.json()[0] if resp.status_code == 201 else carga
        logger.info(f"Abono creado: {patente} {tipo} hasta {fin}")
        return data
