import logging
from datetime import datetime, time

import httpx

from app.config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)


async def obtener_tarifas_activas(ahora: datetime | None = None) -> list[dict]:
    if ahora is None:
        from app.config import TZ_ARG
        ahora = datetime.now(TZ_ARG)

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    fecha_hoy = ahora.date().isoformat()
    url = (
        f"{SUPABASE_URL}/rest/v1/tarifas_especiales"
        f"?activa=eq.true"
        f"&fecha_inicio=lte.{fecha_hoy}"
        f"&fecha_fin=gte.{fecha_hoy}"
        f"&select=*"
    )
    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.get(url, headers=headers)
        if respuesta.status_code == 200:
            tarifas = respuesta.json()
            hora_actual = ahora.time()
            return [
                t for t in tarifas
                if not t.get("hora_inicio") or not t.get("hora_fin")
                or time.fromisoformat(t["hora_inicio"]) <= hora_actual <= time.fromisoformat(t["hora_fin"])
            ]
        return []


def aplicar_tarifa_especial(
    tipo_vehiculo: str,
    costo_base: float,
    tarifas_activas: list[dict],
) -> tuple[float, str | None]:
    if not tarifas_activas:
        return costo_base, None

    tarifa = tarifas_activas[0]
    multiplicador = float(tarifa.get("multiplicador", 1.0) or 1.0)

    if tipo_vehiculo == "auto" and tarifa.get("tarifa_auto_override"):
        nuevo_costo = tarifa["tarifa_auto_override"]
    elif tipo_vehiculo == "moto" and tarifa.get("tarifa_moto_override"):
        nuevo_costo = tarifa["tarifa_moto_override"]
    elif multiplicador != 1.0:
        nuevo_costo = costo_base * multiplicador
    else:
        return costo_base, None

    nombre = tarifa.get("nombre_evento", "Evento especial")
    logger.info(f"Tarifa especial aplicada: {nombre} x{multiplicador}, costo=${nuevo_costo}")
    return nuevo_costo, nombre
