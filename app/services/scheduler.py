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

    async def digest_semanal_job():
        logger.info("Ejecutando digest semanal")
        try:
            from app.services.email_digest import enviar_digests_automaticos
            await enviar_digests_automaticos("semanal")
        except Exception as e:
            logger.error(f"Error en digest semanal: {e}")

    async def digest_mensual_job():
        logger.info("Ejecutando digest mensual")
        try:
            from app.services.email_digest import enviar_digests_automaticos
            await enviar_digests_automaticos("mensual")
        except Exception as e:
            logger.error(f"Error en digest mensual: {e}")

    scheduler.add_job(
        cierre_diario_job,
        trigger=CronTrigger(hour=23, minute=55),
        id="cierre_diario",
        replace_existing=True,
    )

    scheduler.add_job(
        digest_semanal_job,
        trigger=CronTrigger(day_of_week="mon", hour=8, minute=0),
        id="digest_semanal",
        replace_existing=True,
    )

    scheduler.add_job(
        digest_mensual_job,
        trigger=CronTrigger(day=1, hour=8, minute=0),
        id="digest_mensual",
        replace_existing=True,
    )

    scheduler.start()
    logger.info("Scheduler iniciado: cierre diario 23:55, digest semanal lun 8:00, digest mensual dia 1 8:00")


def detener_scheduler():
    scheduler.shutdown(wait=False)
    logger.info("Scheduler detenido")
