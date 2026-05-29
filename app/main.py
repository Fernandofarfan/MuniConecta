from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from slowapi.middleware import SlowAPIMiddleware

from app.auth import limiter
from app.logging_config import setup_logging
from app.routers import admin, analiticas, auth, ciudadanos, estacionamiento, health, ocr, pagos, zonas
from app.websocket_manager import manager

setup_logging()

app = FastAPI(
    title="SEM Express",
    description="Sistema de Estacionamiento Medido - Municipalidad de Salta",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Estacionamiento", "description": "Gestion de estacionamientos medidos"},
        {"name": "Zonas", "description": "Zonas tarifarias de estacionamiento"},
        {"name": "Auth", "description": "Autenticacion de inspectores"},
        {"name": "Pagos", "description": "Integracion MercadoPago y comprobantes"},
        {"name": "Analiticas", "description": "Estadisticas y metricas historicas"},
        {"name": "Ciudadanos", "description": "Registro y busqueda de ciudadanos"},
        {"name": "Admin", "description": "Administracion del sistema"},
        {"name": "OCR", "description": "Reconocimiento de patentes"},
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

app.include_router(estacionamiento.router, prefix="/v1")
app.include_router(zonas.router, prefix="/v1")
app.include_router(auth.router, prefix="/v1")
app.include_router(pagos.router, prefix="/v1")
app.include_router(analiticas.router, prefix="/v1")
app.include_router(ciudadanos.router, prefix="/v1")
app.include_router(admin.router, prefix="/v1")
app.include_router(ocr.router, prefix="/v1")
app.include_router(health.router)


@app.get("/v1/")
async def api_root():
    return {
        "api": "SEM Express",
        "version": "1.0.0",
        "endpoints": [
            "POST /v1/iniciar_estacionamiento",
            "POST /v1/calcular_cobro",
            "POST /v1/consultar_deuda",
            "POST /v1/escanear_patente",
            "GET  /v1/zonas",
            "GET  /v1/zonas/ocupacion",
            "POST /v1/auth/login",
            "POST /v1/pagos/crear",
            "GET  /v1/analiticas/estadisticas",
            "POST /v1/ciudadanos/registrar",
            "POST /v1/cierre_diario_forzado",
        ],
    }
