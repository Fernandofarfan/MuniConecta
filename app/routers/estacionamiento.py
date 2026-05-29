import json
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.auth import verificar_api_key
from app.config import TZ_ARG
from app.database import EstacionamientoDB
from app.models.schemas import (
    PeticionCalcularCobro,
    PeticionConsultaDeuda,
    PeticionIniciarEstacionamiento,
)
from app.services.pricing import calcular_costo
from app.services.schedule import es_horario_cobrable
from app.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Estacionamiento"])


@router.post("/iniciar_estacionamiento")
async def iniciar_estacionamiento(
    peticion: PeticionIniciarEstacionamiento,
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
    }

    await EstacionamientoDB.crear(carga_datos)
    await manager.broadcast(json.dumps({"event": "update_dashboard"}))
    logger.info(f"Estacionamiento iniciado: patente={peticion.patente}, tipo={peticion.tipo_vehiculo}")
    return {"mensaje": "Estacionamiento iniciado correctamente", "datos": carga_datos}


@router.post("/calcular_cobro")
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

    link_pago_mp = "https://mpago.la/mock_punatech_2026" if peticion.metodo_pago == "digital" else None

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


@router.post("/consultar_deuda")
async def consultar_deuda(
    peticion: PeticionConsultaDeuda,
    _: str = Depends(verificar_api_key),
):
    registro = await EstacionamientoDB.buscar_activo_por_patente_o_error(peticion.patente)
    tipo_vehiculo = registro.get("tipo_vehiculo")
    hora_inicio_str = registro.get("hora_inicio")

    costo_total, minutos_transcurridos, _ = calcular_costo(tipo_vehiculo, hora_inicio_str)
    costo_digital, _, _ = calcular_costo(tipo_vehiculo, hora_inicio_str, "digital")

    link_pago_mp = "https://mpago.la/mock_punatech_2026"

    logger.info(f"Consulta deuda: patente={peticion.patente}, monto=${costo_total}")
    return {
        "mensaje": "Consulta de deuda exitosa (no finaliza estacionamiento)",
        "patente": peticion.patente,
        "tiempo_transcurrido_minutos": minutos_transcurridos,
        "monto_total": costo_total,
        "monto_con_descuento_digital": costo_digital,
        "link_pago_mp": link_pago_mp,
    }
