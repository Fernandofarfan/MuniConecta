import logging

from app.database import EstacionamientoDB
from app.services.pricing import calcular_costo

logger = logging.getLogger(__name__)


async def procesar_cierre_diario() -> dict:
    activos = await EstacionamientoDB.obtener_todos_activos()
    total_proyectado = 0.0
    procesados = 0
    errores = 0

    for registro in activos:
        try:
            tipo_vehiculo = registro.get("tipo_vehiculo")
            hora_inicio_str = registro.get("hora_inicio")
            costo_total, _, _ = calcular_costo(tipo_vehiculo, hora_inicio_str)

            await EstacionamientoDB.actualizar_por_id(
                registro["id"],
                {
                    "monto_final": costo_total,
                    "estado": "finalizado",
                },
            )
            total_proyectado += costo_total
            procesados += 1
        except Exception as e:
            logger.error(f"Error al cerrar registro {registro.get('id')}: {e}")
            errores += 1

    logger.info(
        f"Cierre diario completado. {procesados} procesados, "
        f"{errores} errores, total proyectado: ${total_proyectado:.2f}"
    )
    return {
        "procesados": procesados,
        "errores": errores,
        "total_proyectado": round(total_proyectado, 2),
    }
