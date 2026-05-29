import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from app.auth import limiter
from app.logging_config import setup_logging

logger = logging.getLogger(__name__)
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.services.scheduler import iniciar_scheduler, detener_scheduler

    iniciar_scheduler()
    asyncio.create_task(_anomaly_monitor_loop())
    logger.info("SEM Express iniciado - scheduler y monitor de anomalias activos")
    yield
    detener_scheduler()
    logger.info("SEM Express detenido")


async def _anomaly_monitor_loop():
    from app.services.anomaly_detector import detectar_anomalias
    import json

    while True:
        await asyncio.sleep(300)
        try:
            anomalias = await detectar_anomalias()
            if anomalias:
                from app.websocket_manager import manager
                await manager.broadcast(json.dumps({"event": "anomalias", "data": anomalias}))
                for a in anomalias:
                    if a["severidad"] == "alta":
                        from app.services.alert_manager import alertar_supervisor
                        await alertar_supervisor(a["descripcion"], a["severidad"])
        except Exception as e:
            logger.error(f"Error en monitor de anomalias: {e}")


app = FastAPI(
    title="SEM Express",
    description="Sistema de Estacionamiento Medido - Municipalidad de Salta",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Estacionamiento", "description": "Gestion de estacionamientos medidos"},
        {"name": "Zonas", "description": "Zonas tarifarias de estacionamiento"},
        {"name": "Auth", "description": "Autenticacion de inspectores"},
        {"name": "Pagos", "description": "Integracion MercadoPago y comprobantes"},
        {"name": "Analiticas", "description": "Estadisticas y metricas historicas"},
        {"name": "Ciudadanos", "description": "Registro y busqueda de ciudadanos"},
        {"name": "Infracciones", "description": "Emision y consulta de multas"},
        {"name": "Tarifas", "description": "Tarifas especiales y dinamicas"},
        {"name": "Anomalias", "description": "Deteccion de anomalias operativas"},
        {"name": "Admin", "description": "Administracion del sistema"},
        {"name": "OCR", "description": "Reconocimiento de patentes"},
        {"name": "QR Portal", "description": "Portal de pago ciudadano"},
        {"name": "PWA", "description": "App progresiva para inspectores"},
        {"name": "Health", "description": "Health check"},
    ],
)

ALLOWED_ORIGINS = [
    "http://localhost:8501",
    "http://127.0.0.1:8501",
    "https://municonecta-service-728832414144.us-central1.run.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "OPTIONS"],
    allow_headers=["X-API-Key", "Content-Type", "Authorization"],
)

app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)

# Routers
from app.routers import (
    admin, admin_crud, analiticas, auditoria, auth, ciudadanos, dnrpa,
    estacionamiento, health, infracciones, inspector_pwa, ocr, pagos,
    qr_portal, tarifas, vehiculos_abonos, zonas,
)
from app.routers.anomalias import crear_router as crear_router_anomalias

app.include_router(estacionamiento.router, prefix="/v1")
app.include_router(zonas.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(pagos.router, prefix="/v1")
app.include_router(analiticas.router, prefix="/v1")
app.include_router(ciudadanos.router, prefix="/v1")
app.include_router(dnrpa.router, prefix="/v1")
app.include_router(infracciones.router, prefix="/v1")
app.include_router(tarifas.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")
app.include_router(admin_crud.router, prefix="/v1")
app.include_router(auditoria.router, prefix="/v1")
app.include_router(vehiculos_abonos.router, prefix="/v1")
app.include_router(vehiculos_abonos.router_abonos, prefix="/v1")
app.include_router(vehiculos_abonos.router_ciudadano_portal, prefix="/v1")
app.include_router(ocr.router, prefix="/v1")
app.include_router(health.router)
app.include_router(qr_portal.router)
app.include_router(inspector_pwa.router)
app.include_router(crear_router_anomalias(prefix="/v1"))

# PWA static
from fastapi.staticfiles import StaticFiles
import os

_static_dir = os.path.join(os.path.dirname(__file__), "static", "inspector")
if os.path.isdir(_static_dir):
    app.mount("/inspector", StaticFiles(directory=_static_dir, html=True), name="inspector_static")


@app.get("/v1/")
async def api_root():
    return {
        "api": "SEM Express",
        "version": "1.0.0",
        "auto_daily_close": "23:55 ARG",
        "anomaly_monitor": "every 5 min",
        "endpoints": [
            "POST /v1/estacionamiento/iniciar",
            "POST /v1/estacionamiento/cobrar",
            "POST /v1/estacionamiento/deuda",
            "GET  /v1/zonas",
            "GET  /v1/zonas/ocupacion",
            "POST /v1/auth/login",
            "POST /v1/pagos/crear",
            "POST /v1/pagos/webhook",
            "GET  /v1/analiticas/estadisticas",
            "POST /v1/infracciones/emitir",
            "GET  /v1/infracciones/consultar",
            "GET  /v1/tarifas/activas",
            "GET  /v1/anomalias",
            "GET  /v1/anomalias/prediccion-demanda",
            "POST /v1/cierre_diario_forzado",
            "GET  /p/{session_id}",
            "GET  /inspector/",
        ],
    }


@app.websocket("/ws/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    from app.websocket_manager import manager
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
