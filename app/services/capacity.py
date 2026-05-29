import logging

logger = logging.getLogger(__name__)


async def verificar_capacidad(zona_id: int) -> tuple[bool, int, int]:
    from app.database import ZonaDB, EstacionamientoDB

    zonas = await ZonaDB.obtener_ocupacion()
    zona = next((z for z in zonas if z["id"] == zona_id), None)
    if not zona:
        return True, 0, 0

    capacidad = zona.get("capacidad_maxima", 0)
    ocupados = zona.get("ocupados", 0)
    disponible = ocupados < capacidad

    if not disponible:
        logger.warning(f"Zona {zona['nombre']} llena: {ocupados}/{capacidad}")

    return disponible, ocupados, capacidad


async def agregar_lista_espera(zona_id: int, patente: str, chat_id: int | None = None):
    import httpx
    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }
    carga = {"zona_id": zona_id, "patente": patente, "chat_id": chat_id}
    async with httpx.AsyncClient() as cliente:
        await cliente.post(f"{SUPABASE_URL}/rest/v1/lista_espera", headers=headers, json=carga)


async def notificar_lista_espera(zona_id: int):
    import httpx
    from app.config import SUPABASE_KEY, SUPABASE_URL
    from app.services.notificador import enviar_mensaje as enviar_telegram

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    async with httpx.AsyncClient() as cliente:
        url = f"{SUPABASE_URL}/rest/v1/lista_espera?zona_id=eq.{zona_id}&notificado=eq.false&select=*&limit=5"
        resp = await cliente.get(url, headers=headers)
        if resp.status_code != 200:
            return
        items = resp.json()
        for item in items:
            if item.get("chat_id"):
                await enviar_telegram(item["chat_id"], f"Se libero un lugar en la zona. Tu turno llego!")
            patch_url = f"{SUPABASE_URL}/rest/v1/lista_espera?id=eq.{item['id']}"
            await cliente.patch(patch_url, headers={**headers, "Content-Type": "application/json"}, json={"notificado": True})
