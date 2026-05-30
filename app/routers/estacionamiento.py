import json
import logging
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.auth import verificar_api_key
from app.config import TZ_ARG
from app.database import CiudadanoDB, EstacionamientoDB, InspectorFinanzasDB, VehiculoSaldoDB
from app.models.schemas import (
    PeticionCalcularCobro,
    PeticionConsultaDeuda,
    PeticionIniciarEstacionamiento,
)
from app.services.abonos import verificar_abono_activo
from app.services.auditoria import registrar_auditoria
from app.services.capacity import notificar_lista_espera, verificar_capacidad
from app.services.geofence import detectar_zona_por_gps
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

    zona_id = peticion.zona_id
    zona_detectada = None
    if not zona_id and peticion.lat and peticion.lon:
        geo = await detectar_zona_por_gps(peticion.lat, peticion.lon)
        if geo:
            zona_id = geo["zona_id"]
            zona_detectada = geo["zona_nombre"]

    if zona_id:
        disponible, ocupados, capacidad = await verificar_capacidad(zona_id)
        if not disponible:
            raise HTTPException(
                status_code=409,
                detail=f"Zona llena ({ocupados}/{capacidad}). Intente en otra zona.",
            )

    abono = await verificar_abono_activo(peticion.patente, zona_id)

    minutos_saldo_consumidos = 0
    if not abono:
        minutos_saldo = await VehiculoSaldoDB.obtener_saldo(peticion.patente)
        if minutos_saldo > 0:
            minutos_saldo_consumidos = await VehiculoSaldoDB.consumir_saldo(peticion.patente, 60)

    carga_datos = {
        "patente": peticion.patente,
        "tipo_vehiculo": peticion.tipo_vehiculo,
        "legajo_permisionario": peticion.legajo_permisionario,
        "hora_inicio": ahora.isoformat(),
        "estado": "activo",
        "lat": peticion.lat,
        "lon": peticion.lon,
        "zona_id": zona_id,
    }

    await EstacionamientoDB.crear(carga_datos)
    await manager.broadcast(json.dumps({"event": "update_dashboard"}))

    background_tasks.add_task(_notificar_ciudadanos, peticion.patente)
    background_tasks.add_task(registrar_auditoria, peticion.legajo_permisionario, "iniciar_estacionamiento", "estacionamiento", 0, {"patente": peticion.patente})

    logger.info(f"Estacionamiento iniciado: patente={peticion.patente}, tipo={peticion.tipo_vehiculo}, zona={zona_id}")
    return {
        "mensaje": "Estacionamiento iniciado correctamente",
        "datos": carga_datos,
        "zona_detectada": zona_detectada,
        "zona_id": zona_id,
        "abono_activo": abono is not None,
        "minutos_saldo_consumidos": minutos_saldo_consumidos,
    }


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

    # Rendicion de efectivo: el municipio cobra 20% de cada ticket en efectivo
    if peticion.metodo_pago == "efectivo" and costo_total > 0:
        legajo = registro.get("legajo_permisionario", "INSP-01")
        comision_municipal = round(costo_total * 0.20, 2)
        import asyncio
        asyncio.create_task(InspectorFinanzasDB.sumar_saldo_adeudado(legajo, comision_municipal))

    # Saldo de tiempo a favor: calcular minutos no consumidos
    import asyncio
    minutos_sobrantes = 0
    try:
        from datetime import datetime as dt
        hora_inicio_dt = dt.fromisoformat(hora_inicio_str.replace("Z", "+00:00"))
        delta_real = hora_fin - hora_inicio_dt
        minutos_reales = delta_real.total_seconds() / 60.0

        # Calcular minutos pagados (lo que el costo cubre)
        from app.config import get_tarifa
        tarifa_base = get_tarifa(tipo_vehiculo)
        minutos_pagados = 60.0
        if costo_total > tarifa_base:
            costo_excedente = costo_total - tarifa_base
            fracciones_pagadas = costo_excedente / (tarifa_base / 4)
            minutos_pagados = 60.0 + fracciones_pagadas * 15.0
        elif costo_total == 0:
            minutos_pagados = 0

        minutos_sobrantes = max(0, int(minutos_pagados - minutos_reales))
        if minutos_sobrantes > 0 and peticion.metodo_pago == "efectivo":
            asyncio.create_task(VehiculoSaldoDB.acreditar_saldo(peticion.patente, minutos_sobrantes))
    except Exception:
        minutos_sobrantes = 0

    await manager.broadcast(json.dumps({"event": "update_dashboard"}))
    asyncio.create_task(registrar_auditoria(registro.get("legajo_permisionario", "INSP-01"), "cobrar_estacionamiento", "estacionamiento", registro.get("id", 0), {"patente": peticion.patente, "monto": costo_total}))
    if registro.get("zona_id"):
        asyncio.create_task(notificar_lista_espera(registro["zona_id"]))

    logger.info(f"Cobro calculado: patente={peticion.patente}, monto=${costo_total}")
    return {
        "mensaje": "Estacionamiento finalizado y cobro calculado",
        "patente": peticion.patente,
        "tiempo_transcurrido_minutos": minutos_transcurridos,
        "monto_final": costo_total,
        "metodo_pago": peticion.metodo_pago,
        "link_pago_mp": link_pago_mp,
        "minutos_sobrantes_acreditados": minutos_sobrantes,
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


@router.post("/ciudadano/iniciar", tags=["Estacionamiento"])
async def ciudadano_inicia_estacionamiento(peticion: dict):
    patente = peticion.get("patente", "").upper().strip()
    if not patente:
        raise HTTPException(status_code=422, detail="Patente requerida")

    try:
        from app.models.schemas import validar_patente_argentina
        patente = validar_patente_argentina(patente)
    except ValueError:
        raise HTTPException(status_code=422, detail="Formato de patente invalido")

    zona_id = peticion.get("zona_id")
    ahora = datetime.now(TZ_ARG)

    registro_existente = await EstacionamientoDB.buscar_activo_por_patente(patente)
    if registro_existente:
        raise HTTPException(status_code=400, detail="El vehiculo ya tiene un estacionamiento activo en curso")

    if zona_id:
        disponible, ocupados, capacidad = await verificar_capacidad(zona_id)
        if not disponible:
            raise HTTPException(status_code=409, detail=f"Zona llena ({ocupados}/{capacidad})")

    abono = await verificar_abono_activo(patente, zona_id)

    minutos_saldo_consumidos = 0
    if not abono:
        minutos_saldo = await VehiculoSaldoDB.obtener_saldo(patente)
        if minutos_saldo > 0:
            minutos_saldo_consumidos = await VehiculoSaldoDB.consumir_saldo(patente, 60)

    carga_datos = {
        "patente": patente,
        "tipo_vehiculo": "auto",
        "legajo_permisionario": "CIUDADANO",
        "hora_inicio": ahora.isoformat(),
        "estado": "activo",
        "zona_id": zona_id,
    }

    await EstacionamientoDB.crear(carga_datos)
    await manager.broadcast(json.dumps({"event": "update_dashboard"}))

    logger.info(f"Ciudadano inicio estacionamiento: patente={patente}, zona={zona_id}")
    return {
        "mensaje": "Estacionamiento iniciado por el ciudadano. Un permisionario verificara visualmente.",
        "datos": carga_datos,
        "zona_id": zona_id,
        "abono_activo": abono is not None,
        "minutos_saldo_consumidos": minutos_saldo_consumidos,
    }
