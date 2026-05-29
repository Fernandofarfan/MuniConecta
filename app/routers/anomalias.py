import logging

from app.services.anomaly_detector import detectar_anomalias
from app.services.predictive_analytics import predecir_demanda

logger = logging.getLogger(__name__)

ROUTER_PREFIX = "/anomalias"
TAGS = ["Anomalias"]


def crear_router(prefix: str = ""):
    from fastapi import APIRouter, Depends

    from app.auth import verificar_api_key

    router = APIRouter(prefix=prefix + ROUTER_PREFIX, tags=TAGS)

    @router.get("")
    async def listar_anomalias(_: str = Depends(verificar_api_key)):
        anomalias = await detectar_anomalias()
        return {"anomalias": anomalias, "total": len(anomalias), "timestamp": __import__("datetime").datetime.now().isoformat()}

    @router.get("/prediccion-demanda")
    async def prediccion(_: str = Depends(verificar_api_key)):
        data = await predecir_demanda()
        return {"predicciones": data, "total": len(data)}

    return router
