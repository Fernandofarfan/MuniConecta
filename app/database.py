import httpx
from fastapi import HTTPException

from app.config import SUPABASE_KEY, SUPABASE_URL

BASE_URL = f"{SUPABASE_URL}/rest/v1/estacionamientos"


def get_headers() -> dict:
    if not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase Key no configurada en el servidor.")
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


class EstacionamientoDB:
    @staticmethod
    async def buscar_activo_por_patente(patente: str) -> dict | None:
        headers = get_headers()
        url = f"{BASE_URL}?patente=eq.{patente}&estado=eq.activo&select=*"
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
            respuesta = await cliente.post(BASE_URL, headers=headers, json=carga)
            if respuesta.status_code not in [201, 204]:
                raise HTTPException(
                    status_code=500,
                    detail=f"Error al guardar el registro en Supabase: {respuesta.text}",
                )

    @staticmethod
    async def actualizar_activo_por_patente(patente: str, carga: dict) -> None:
        headers = get_headers()
        headers["Prefer"] = "return=representation"
        url = f"{BASE_URL}?patente=eq.{patente}&estado=eq.activo"
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
        url = f"{BASE_URL}?id=eq.{registro_id}"
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
        url = f"{BASE_URL}?estado=eq.activo&select=*&limit=1000"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error al consultar Supabase: {respuesta.text}")
            return respuesta.json()
