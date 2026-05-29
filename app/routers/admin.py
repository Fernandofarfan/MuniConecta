import json
import logging

from fastapi import APIRouter, BackgroundTasks

from app.services.cierre_diario import procesar_cierre_diario
from app.websocket_manager import manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Admin"])


@router.post("/cierre_diario_forzado")
async def cierre_diario_forzado(background_tasks: BackgroundTasks):
    logger.info("Cierre diario forzado disparado en segundo plano")

    async def _ejecutar_y_notificar():
        await procesar_cierre_diario()
        await manager.broadcast(json.dumps({"event": "update_dashboard"}))

    background_tasks.add_task(_ejecutar_y_notificar)
    return {
        "mensaje": (
            "Cierre diario iniciado en segundo plano. "
            "Los registros se actualizaran asincronamente para evitar caidas del servidor."
        )
    }
