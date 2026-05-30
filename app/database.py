import httpx
from fastapi import HTTPException

from app.config import SUPABASE_KEY, SUPABASE_URL, USE_MOCK_DB

BASE_URL = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""


def get_headers() -> dict:
    if not SUPABASE_KEY:
        raise HTTPException(status_code=500, detail="Supabase Key no configurada en el servidor.")
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
    }


# ── Mock fallback imports ──
if USE_MOCK_DB:
    from app.mock_database import mock_db as _mdb


class EstacionamientoDB:
    TABLE = "estacionamientos"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def buscar_activo_por_patente(patente: str) -> dict | None:
        if USE_MOCK_DB:
            return _mdb.buscar_activo_por_patente(patente)
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
        if USE_MOCK_DB:
            _mdb.crear_estacionamiento(carga)
            return
        headers = get_headers()
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.post(EstacionamientoDB.URL, headers=headers, json=carga)
            if respuesta.status_code not in [201, 204]:
                raise HTTPException(status_code=500, detail=f"Error al guardar el registro en Supabase: {respuesta.text}")

    @staticmethod
    async def actualizar_activo_por_patente(patente: str, carga: dict) -> None:
        if USE_MOCK_DB:
            _mdb.actualizar_activo(patente, carga)
            return
        headers = get_headers()
        headers["Prefer"] = "return=representation"
        url = f"{EstacionamientoDB.URL}?patente=eq.{patente}&estado=eq.activo"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.patch(url, headers=headers, json=carga)
            if respuesta.status_code not in [200, 204]:
                raise HTTPException(status_code=500, detail=f"Error al actualizar: {respuesta.text}")

    @staticmethod
    async def actualizar_por_id(registro_id: int, carga: dict) -> None:
        if USE_MOCK_DB:
            for e in _mdb._find("estacionamientos", "id", registro_id):
                e.update(carga)
            return
        headers = get_headers()
        headers["Prefer"] = "return=minimal"
        url = f"{EstacionamientoDB.URL}?id=eq.{registro_id}"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.patch(url, headers=headers, json=carga)
            if respuesta.status_code not in [200, 204]:
                raise HTTPException(status_code=500, detail=f"Error al actualizar: {respuesta.text}")

    @staticmethod
    async def obtener_todos_activos() -> list[dict]:
        if USE_MOCK_DB:
            return _mdb.obtener_activos()
        headers = get_headers()
        url = f"{EstacionamientoDB.URL}?estado=eq.activo&select=*&limit=1000"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error al consultar Supabase: {respuesta.text}")
            return respuesta.json()

    @staticmethod
    async def obtener_analiticas(desde: str, hasta: str) -> list[dict]:
        if USE_MOCK_DB:
            return _mdb.obtener_analiticas(desde, hasta)
        headers = get_headers()
        url = f"{EstacionamientoDB.URL}?hora_inicio=gte.{desde}&hora_inicio=lte.{hasta}&select=*&order=hora_inicio.asc&limit=10000"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error: {respuesta.text}")
            return respuesta.json()


class ZonaDB:
    TABLE = "zonas"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def obtener_todas() -> list[dict]:
        if USE_MOCK_DB:
            return _mdb.get_zonas()
        headers = get_headers()
        url = f"{ZonaDB.URL}?activa=eq.true&select=*"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code != 200:
                raise HTTPException(status_code=500, detail=f"Error: {respuesta.text}")
            return respuesta.json()

    @staticmethod
    async def crear(carga: dict) -> dict:
        if USE_MOCK_DB:
            carga["id"] = len(_mdb.get_zonas()) + 1
            return carga
        headers = get_headers()
        headers["Prefer"] = "return=representation"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.post(ZonaDB.URL, headers=headers, json=carga)
            if respuesta.status_code not in [201, 204]:
                raise HTTPException(status_code=500, detail=f"Error: {respuesta.text}")
            return respuesta.json()[0] if respuesta.status_code == 201 else carga

    @staticmethod
    async def obtener_ocupacion() -> list[dict]:
        if USE_MOCK_DB:
            return _mdb.get_zonas_ocupacion()
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
        if USE_MOCK_DB:
            return _mdb.buscar_inspector(legajo)
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
        if USE_MOCK_DB:
            return _mdb.crear_inspector(carga)
        headers = get_headers()
        headers["Prefer"] = "return=representation"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.post(InspectorDB.URL, headers=headers, json=carga)
            if respuesta.status_code not in [201, 204]:
                raise HTTPException(status_code=500, detail=f"Error: {respuesta.text}")
            return respuesta.json()[0] if respuesta.status_code == 201 else carga


class CiudadanoDB:
    TABLE = "ciudadanos"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def buscar_por_chat_id(chat_id: int) -> dict | None:
        if USE_MOCK_DB:
            return _mdb.get_ciudadano_by_chat(chat_id)
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
        if USE_MOCK_DB:
            return _mdb.get_ciudadano_by_patente(patente)
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
        if USE_MOCK_DB:
            existing = _mdb.get_ciudadano_by_chat(chat_id)
            if existing:
                existing.update(carga)
            else:
                carga["telegram_chat_id"] = chat_id
                _in_memory_db = __import__("app.mock_database")._in_memory_db
                _in_memory_db["ciudadanos"].append(carga)
            return
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
                raise HTTPException(status_code=500, detail=f"Error: {respuesta.text}")


class VehiculoSaldoDB:
    TABLE = "vehiculos_saldos"
    URL = f"{BASE_URL}/{TABLE}"

    @staticmethod
    async def obtener_saldo(patente: str) -> int:
        if USE_MOCK_DB:
            return _mdb.get_vehiculo_saldo(patente)
        headers = get_headers()
        url = f"{VehiculoSaldoDB.URL}?patente=eq.{patente}&select=minutos_disponibles"
        async with httpx.AsyncClient() as cliente:
            respuesta = await cliente.get(url, headers=headers)
            if respuesta.status_code == 200:
                data = respuesta.json()
                return data[0]["minutos_disponibles"] if data else 0
            return 0

    @staticmethod
    async def consumir_saldo(patente: str, minutos_a_consumir: int) -> int:
        if USE_MOCK_DB:
            saldo = _mdb.get_vehiculo_saldo(patente)
            consumidos = min(saldo, minutos_a_consumir)
            _mdb.set_vehiculo_saldo(patente, saldo - consumidos)
            return consumidos
        headers = get_headers()
        saldo_actual = await VehiculoSaldoDB.obtener_saldo(patente)
        consumidos = min(saldo_actual, minutos_a_consumir)
        nuevo_saldo = saldo_actual - consumidos
        headers["Prefer"] = "return=minimal"
        async with httpx.AsyncClient() as cliente:
            url = f"{VehiculoSaldoDB.URL}?patente=eq.{patente}"
            existing = await cliente.get(url, headers={k: v for k, v in headers.items() if k != "Prefer"})
            if existing.status_code == 200 and existing.json():
                await cliente.patch(url, headers=headers, json={"minutos_disponibles": nuevo_saldo})
            else:
                await cliente.post(VehiculoSaldoDB.URL, headers=headers, json={"patente": patente, "minutos_disponibles": nuevo_saldo})
        return consumidos

    @staticmethod
    async def acreditar_saldo(patente: str, minutos: int) -> None:
        if USE_MOCK_DB:
            saldo = _mdb.get_vehiculo_saldo(patente)
            _mdb.set_vehiculo_saldo(patente, saldo + minutos)
            return
        headers = get_headers()
        saldo_actual = await VehiculoSaldoDB.obtener_saldo(patente)
        nuevo_saldo = saldo_actual + minutos
        headers["Prefer"] = "return=minimal"
        async with httpx.AsyncClient() as cliente:
            url = f"{VehiculoSaldoDB.URL}?patente=eq.{patente}"
            existing = await cliente.get(url, headers={k: v for k, v in headers.items() if k != "Prefer"})
            if existing.status_code == 200 and existing.json():
                await cliente.patch(url, headers=headers, json={"minutos_disponibles": nuevo_saldo})
            else:
                await cliente.post(VehiculoSaldoDB.URL, headers=headers, json={"patente": patente, "minutos_disponibles": nuevo_saldo})


class InspectorFinanzasDB:
    @staticmethod
    async def sumar_saldo_adeudado(legajo: str, monto: float) -> None:
        if USE_MOCK_DB:
            _mdb.sumar_saldo_adeudado(legajo, monto)
            return
        headers = get_headers()
        headers["Prefer"] = "return=minimal"
        inspector = await InspectorDB.buscar_por_legajo(legajo)
        if not inspector:
            return
        saldo_actual = float(inspector.get("saldo_adeudado", 0) or 0)
        nuevo_saldo = round(saldo_actual + monto, 2)
        url = f"{InspectorDB.URL}?legajo=eq.{legajo}"
        async with httpx.AsyncClient() as cliente:
            await cliente.patch(url, headers=headers, json={"saldo_adeudado": nuevo_saldo})

    @staticmethod
    async def rendir(legajo: str, monto: float) -> dict:
        if USE_MOCK_DB:
            inspector = _mdb.buscar_inspector(legajo)
            if not inspector:
                raise HTTPException(status_code=404, detail="Inspector no encontrado")
            saldo = inspector.get("saldo_adeudado", 0)
            if monto > saldo:
                raise HTTPException(status_code=400, detail=f"Monto (${monto}) supera saldo (${saldo})")
            inspector["saldo_adeudado"] = round(saldo - monto, 2)
            return {"legajo": legajo, "saldo_anterior": saldo, "rendido": monto, "saldo_actual": inspector["saldo_adeudado"]}
        headers = get_headers()
        inspector = await InspectorDB.buscar_por_legajo(legajo)
        if not inspector:
            raise HTTPException(status_code=404, detail="Inspector no encontrado")
        saldo_actual = float(inspector.get("saldo_adeudado", 0) or 0)
        if monto > saldo_actual:
            raise HTTPException(status_code=400, detail=f"Monto (${monto}) supera saldo (${saldo_actual})")
        nuevo_saldo = round(saldo_actual - monto, 2)
        headers["Prefer"] = "return=representation"
        url = f"{InspectorDB.URL}?legajo=eq.{legajo}"
        async with httpx.AsyncClient() as cliente:
            await cliente.patch(url, headers=headers, json={"saldo_adeudado": nuevo_saldo})
        return {"legajo": legajo, "saldo_anterior": saldo_actual, "rendido": monto, "saldo_actual": nuevo_saldo}
