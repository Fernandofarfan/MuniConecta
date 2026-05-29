import httpx
from fastapi import HTTPException

from app.config import SUPABASE_KEY, SUPABASE_URL

BASE_URL = f"{SUPABASE_URL}/rest/v1"


def get_headers() -> dict:
    if not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase Key no configurada en el servidor.")
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


class EstacionamientoDB:
    TABLE = "estacionamientos"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def buscar_activo_por_patente(patente: str) -> dict | None:
        headers = get_headers()
        url = f"{EstacionamientoDB.URL}?patente=eq.{patente}&estado=eq.activo&select=*"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code == 200:
                data = respuesta.json()
                return data[0] if data else None
            return None

    @staticmethod
    async def buscar_activo_por_patente_o_error(patente: str) -> dict:
        registro = await EstacionamientoDB.buscar_activo_por_patente(patente)
        if not registro:
            raise HTTPException(status_code=404, detail="No se encontro un estacionamiento activo para esta patente")
        return registro

    @staticmethod
    async def crear(carga: dict) -> None:
        headers = get_headers()
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.post(EstacionamientoDB.URL, headers=headers, json=carga)
            if respuesta.status_code not in [201, 204]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al guardar el registro en Supabase: {respuesta.text}",
                )

    @staticmethod
    async def actualizar_activo_por_patente(patente: str, carga: dict) -> None:
        headers = get_headers()
        headers["Prefer"] = "return=representation"
        url = f"{EstacionamientoDB.URL}?patente=eq.{patente}&estado=eq.activo"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.patch(url, headers=headers, json=carga)
            if respuesta.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al actualizar el registro en Supabase: {respuesta.text}",
                )

    @staticmethod
    async def actualizar_por_id(registro_id: int, carga: dict) -> None:
        headers = get_headers()
        headers["Prefer"] = "return=minimal"
        url = f"{EstacionamientoDB.URL}?id=eq.{registro_id}"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.patch(url, headers=headers, json=carga)
            if respuesta.status_code not in [200, 204]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al actualizar registro {registro_id}: {respuesta.text}",
                )

    @staticmethod
    async def obtener_todos_activos() -> list[dict]:
        headers = get_headers()
        url = f"{EstacionamientoDB.URL}?estado=eq.activo&select=*&limit=1000"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error al consultar Supabase: {respuesta.text}")
            return respuesta.json()

    @staticmethod
    async def obtener_analiticas(desde: str, hasta: str) -> list[dict]:
        headers = get_headers()
        url = (
            f"{EstacionamientoDB.URL}"
            f"?hora_inicio=gte.{desde}"
            f"&hora_inicio=lte.{hasta}"
            f"&select=*&order=hora_inicio.asc&limit=10000"
        )
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error al consultar analiticas: {respuesta.text}")
            return respuesta.json()


class ZonaDB:
    TABLE = "zonas"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def obtener_todas() -> list[dict]:
        headers = get_headers()
        url = f"{ZonaDB.URL}?activa=eq.true&select=*"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error al consultar zonas: {respuesta.text}")
            return respuesta.json()

    @staticmethod
    async def crear(carga: dict) -> dict:
        headers = get_headers()
        headers["Prefer"] = "return=representation"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.post(ZonaDB.URL, headers=headers, json=carga)
            if respuesta.status_code not in [201, 204]:
                raise HTTPException(status_code=500, detail=f"Error al crear zona: {respuesta.text}")
            return respuesta.json()[0] if respuesta.status_code == 201 else carga

    @staticmethod
    async def obtener_ocupacion() -> list[dict]:
        headers = get_headers()
        async with httpx.AsyncClient() as cliente:
            zonas = await ZonaDB.obtener_todas()
            resultado = []
            for zona in zonas:
                url = f"{EstacionamientoDB.URL}?zona_id=eq.{zona['id']}&estado=eq.activo&select=id"
                resp = await cliente.get(url, headers=headers)
                ocupados = len(resp.json()) if resp.status_code == 200 else 0
                resultado.append({**zona, "ocupados": ocupados})
            return resultado


class InspectorDB:
    TABLE = "inspectores"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def buscar_por_legajo(legajo: str) -> dict | None:
        headers = get_headers()
        url = f"{InspectorDB.URL}?legajo=eq.{legajo}&activo=eq.true&select=*"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code == 200:
                data = respuesta.json()
                return data[0] if data else None
            return None

    @staticmethod
    async def crear(carga: dict) -> dict:
        headers = get_headers()
        headers["Prefer"] = "return=representation"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.post(InspectorDB.URL, headers=headers, json=carga)
            if respuesta.status_code not in [201, 204]:
                raise HTTPException(status_code=500, detail=f"Error al crear inspector: {respuesta.text}")
            return respuesta.json()[0] if respuesta.status_code == 201 else carga


class CiudadanoDB:
    TABLE = "ciudadanos"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def buscar_por_chat_id(chat_id: int) -> dict | None:
        headers = get_headers()
        url = f"{CiudadanoDB.URL}?telegram_chat_id=eq.{chat_id}&select=*"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code == 200:
                data = respuesta.json()
                return data[0] if data else None
            return None

    @staticmethod
    async def buscar_por_patente(patente: str) -> list[dict]:
        headers = get_headers()
        url = f"{CiudadanoDB.URL}?select=*"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                return []
            ciudadanos = respuesta.json()
            return [c for c in ciudadanos if patente in c.get("patentes_registradas", [])]

    @staticmethod
    async def upsert(chat_id: int, carga: dict) -> None:
        headers = get_headers()
        headers["Prefer"] = "return=minimal"
        url = f"{CiudadanoDB.URL}?telegram_chat_id=eq.{chat_id}"
        async with httpx.AsyncClient() as cliente:
            existing = await CiudadanoDB.buscar_por_chat_id(chat_id)
            if existing:
                respuesta = await cliente.patch(url, headers=headers, json=carga)
            else:
                carga["telegram_chat_id"] = chat_id
                respuesta = await cliente.post(CiudadanoDB.URL, headers=headers, json=carga)
            if respuesta.status_code not in [200, 201, 204]:
                raise HTTPException(status_code=500, detail=f"Error al guardar ciudadano: {respuesta.text}")
