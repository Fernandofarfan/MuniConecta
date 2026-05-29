import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import TZ_ARG

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone=TZ_ARG)


def iniciar_scheduler():
    from app.services.cierre_diario import procesar_cierre_diario

    async def cierre_diario_job():
        logger.info("Ejecutando cierre diario automatico")
        try:
            resultado = await procesar_cierre_diario()
            logger.info(f"Cierre diario automatico: {resultado}")
            import json

            from app.websocket_manager import manager
            await manager.broadcast(json.dumps({"event": "cierre_diario", "resultado": resultado}))
        except Exception as e:
            logger.error(f"Error en cierre diario automatico: {e}")

    scheduler.add_job(
        cierre_diario_job,
        trigger=CronTrigger(hour=23, minute=55),
        id="cierre_diario",
        name="Cierre diario automatico",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler iniciado: cierre diario programado a las 23:55 ARG")


def detener_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler detenido")
