import json
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth import verificar_api_key
from app.config import TZ_ARG
from app.database import CiudadanoDB, EstacionamientoDB
from app.models.schemas import (
    PeticionCalcularCobro,
    PeticionConsultaDeuda,
    PeticionIniciarEstacionamiento,
)
from app.services.pricing import calcular_costo
from app.services.schedule import es_horario_cobrable
from app.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/estacionamiento", tags=["Estacionamiento"])


async def _notificar_ciudadanos(patente: str, monto: float = 0, link_pago: str = ""):
    try:
        ciudadanos = await CiudadanoDB.buscar_por_patente(patente)
        for c in ciudadanos:
            if c.get("notificaciones_activas"):
                chat_id = c["telegram_chat_id"]
                from app.services.notificador import notificar_inicio_estacionamiento
                await notificar_inicio_estacionamiento(chat_id, patente, "auto")
    except Exception as e:
        logger.warning(f"No se pudo notificar ciudadanos: {e}")


@router.post(
    "/iniciar",
    summary="Iniciar estacionamiento",
    description="Registra el inicio de un estacionamiento con validacion de horario y patente.",
    responses={
        200: {"description": "Estacionamiento iniciado"},
        400: {"description": "Fuera de horario o vehiculo ya activo"},
        422: {"description": "Datos invalidos"},
    },
)
async def iniciar_estacionamiento(
    peticion: PeticionIniciarEstacionamiento,
    background_tasks: BackgroundTasks,
    _: str = Depends(verificar_api_key),
):
    ahora = datetime.now(TZ_ARG)
    if not es_horario_cobrable(ahora):
        raise HTTPException(
            status_code=400,
            detail=(
                "El estacionamiento es libre y gratuito en este horario y dia de la semana "
                "segun la Ordenanza 12.170. No se requiere iniciar registro."
            ),
        )

    registro_existente = await EstacionamientoDB.buscar_activo_por_patente(peticion.patente)
    if registro_existente:
        raise HTTPException(status_code=400, detail="El vehiculo ya tiene un estacionamiento activo en curso")

    carga_datos = {
        "patente": peticion.patente,
        "tipo_vehiculo": peticion.tipo_vehiculo,
        "legajo_permisionario": peticion.legajo_permisionario,
        "hora_inicio": ahora.isoformat(),
        "estado": "activo",
        "lat": peticion.lat,
        "lon": peticion.lon,
        "zona_id": peticion.zona_id,
    }

    await EstacionamientoDB.crear(carga_datos)
    await manager.broadcast(json.dumps({"event": "update_dashboard"}))

    background_tasks.add_task(_notificar_ciudadanos, peticion.patente)

    logger.info(f"Estacionamiento iniciado: patente={peticion.patente}, tipo={peticion.tipo_vehiculo}")
    return {"mensaje": "Estacionamiento iniciado correctamente", "datos": carga_datos}


@router.post(
    "/cobrar",
    summary="Calcular y cobrar estacionamiento",
    description="Finaliza un estacionamiento activo, calcula el costo y aplica descuentos.",
    responses={
        200: {"description": "Cobro calculado"},
        404: {"description": "No hay estacionamiento activo"},
        422: {"description": "Datos invalidos"},
    },
)
async def calcular_cobro(
    peticion: PeticionCalcularCobro,
    _: str = Depends(verificar_api_key),
):
    registro = await EstacionamientoDB.buscar_activo_por_patente_o_error(peticion.patente)
    tipo_vehiculo = registro.get("tipo_vehiculo")
    hora_inicio_str = registro.get("hora_inicio")

    costo_total, minutos_transcurridos, hora_fin = calcular_costo(
        tipo_vehiculo, hora_inicio_str, peticion.metodo_pago
    )

    await EstacionamientoDB.actualizar_activo_por_patente(
        peticion.patente,
        {
            "estado": "finalizado",
            "hora_fin": hora_fin.isoformat(),
            "monto_final": costo_total,
            "metodo_pago": peticion.metodo_pago,
        },
    )

    link_pago_mp = None
    if peticion.metodo_pago == "digital":
        link_pago_mp = f"https://mpago.la/mock_punatech_2026?patente={peticion.patente}"

    await manager.broadcast(json.dumps({"event": "update_dashboard"}))
    logger.info(f"Cobro calculado: patente={peticion.patente}, monto=${costo_total}")
    return {
        "mensaje": "Estacionamiento finalizado y cobro calculado",
        "patente": peticion.patente,
        "tiempo_transcurrido_minutos": minutos_transcurridos,
        "monto_final": costo_total,
        "metodo_pago": peticion.metodo_pago,
        "link_pago_mp": link_pago_mp,
    }


@router.post(
    "/deuda",
    summary="Consultar deuda",
    description="Consulta la deuda acumulada de un estacionamiento activo sin finalizarlo.",
    responses={
        200: {"description": "Deuda consultada"},
        404: {"description": "No hay estacionamiento activo"},
    },
)
async def consultar_deuda(
    peticion: PeticionConsultaDeuda,
    _: str = Depends(verificar_api_key),
):
    registro = await EstacionamientoDB.buscar_activo_por_patente_o_error(peticion.patente)
    tipo_vehiculo = registro.get("tipo_vehiculo")
    hora_inicio_str = registro.get("hora_inicio")

    costo_total, minutos_transcurridos, _ = calcular_costo(tipo_vehiculo, hora_inicio_str)
    costo_digital, _, _ = calcular_costo(tipo_vehiculo, hora_inicio_str, "digital")

    link_pago_mp = f"https://mpago.la/mock_punatech_2026?patente={peticion.patente}"

    logger.info(f"Consulta deuda: patente={peticion.patente}, monto=${costo_total}")
    return {
        "mensaje": "Consulta de deuda exitosa (no finaliza estacionamiento)",
        "patente": peticion.patente,
        "tiempo_transcurrido_minutos": minutos_transcurridos,
        "monto_total": costo_total,
        "monto_con_descuento_digital": costo_digital,
        "link_pago_mp": link_pago_mp,
    }
