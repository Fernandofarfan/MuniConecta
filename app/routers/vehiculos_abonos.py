import logging

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verificar_api_key
from app.services.abonos import crear_abono, verificar_abono_activo
from app.services.geofence import detectar_zona_por_gps
from app.services.vehiculo_historial import obtener_historial_vehiculo
from app.services.capacity import verificar_capacidad, agregar_lista_espera

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/vehiculos", tags=["Vehiculos"])


@router.get("/{patente}/historial")
async def historial_vehiculo(patente: str, _: str = Depends(verificar_api_key)):
    data = await obtener_historial_vehiculo(patente.upper().strip())
    return data


@router.get("/{patente}/abono")
async def verificar_abono(patente: str, zona_id: int | None = None, _: str = Depends(verificar_api_key)):
    abono = await verificar_abono_activo(patente.upper().strip(), zona_id)
    if abono:
        return {"tiene_abono": True, "abono": abono}
    return {"tiene_abono": False, "abono": None}


class AbonoRouter:
    prefix = "/abonos"

    @staticmethod
    def crear() -> APIRouter:
        r = APIRouter(prefix="/abonos", tags=["Abonos"])

        @r.post("/crear")
        async def crear(peticion: dict, _: str = Depends(verificar_api_key)):
            patente = peticion.get("patente", "").upper().strip()
            zona_id = peticion.get("zona_id", 1)
            tipo = peticion.get("tipo", "mensual")
            chat_id = peticion.get("chat_id")

            if tipo not in ("semanal", "mensual"):
                raise HTTPException(status_code=422, detail="Tipo debe ser semanal o mensual")

            abono = await crear_abono(patente, zona_id, tipo, chat_id)
            return {"mensaje": f"Abono {tipo} creado para {patente}", "abono": abono}

        return r


router_abonos = AbonoRouter.crear()


class CiudadanoPortal:
    prefix = "/ciudadano"

    @staticmethod
    def crear() -> APIRouter:
        r = APIRouter(prefix="/ciudadano", tags=["Ciudadano Portal"])

        @r.get("/resumen/{chat_id}")
        async def resumen_ciudadano(chat_id: int, _: str = Depends(verificar_api_key)):
            from app.database import CiudadanoDB

            ciudadano = await CiudadanoDB.buscar_por_chat_id(chat_id)
            if not ciudadano:
                raise HTTPException(status_code=404, detail="Ciudadano no encontrado")

            patentes = ciudadano.get("patentes_registradas", [])
            resultado = {"ciudadano": ciudadano["nombre"], "patentes": []}

            for p in patentes:
                hist = await obtener_historial_vehiculo(p)
                resultado["patentes"].append({
                    "patente": p,
                    "total_gastado": hist["totales"]["total_gastado"],
                    "total_multas": hist["totales"]["total_multas"],
                    "pendiente_multas": hist["totales"]["total_pendiente_multas"],
                    "estacionamientos": len(hist["estacionamientos"]),
                })

            return resultado

        return r


router_ciudadano_portal = CiudadanoPortal.crear()
