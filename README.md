# SEM Express - Sistema de Estacionamiento Medido

Sistema integral para la gestion y cobro de estacionamiento medido municipal de la Ciudad de Salta.

[![Tests](https://github.com/Fernandofarfan/MuniConecta/actions/workflows/deploy.yml/badge.svg)](https://github.com/Fernandofarfan/MuniConecta/actions/workflows/deploy.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115%2B-009688)](https://fastapi.tiangolo.com/)

---

## Arquitectura

```
MuniConecta/
├── app/
│   ├── main.py                  # Entry point FastAPI con lifespan (scheduler + anomaly monitor)
│   ├── config.py                # Variables de entorno y constantes de negocio
│   ├── auth.py                  # API Key + JWT (inspectores) + rate limiting
│   ├── database.py              # Capa de abstraccion Supabase (6 clases)
│   ├── logging_config.py        # Structured JSON logging
│   ├── websocket_manager.py     # WebSocket broadcast con manejo de desconexion
│   ├── models/schemas.py        # Pydantic models con validacion de patente argentina
│   ├── routers/ (18 modulos)
│   │   ├── estacionamiento.py   # /iniciar, /cobrar, /deuda
│   │   ├── zonas.py             # CRUD zonas + ocupacion en tiempo real
│   │   ├── auth.py              # JWT login inspectores
│   │   ├── pagos.py             # MercadoPago + webhook + comprobantes
│   │   ├── infracciones.py      # Emision y consulta de multas
│   │   ├── tarifas.py           # Tarifas especiales/dinamicas
│   │   ├── analiticas.py        # Estadisticas historicas
│   │   ├── anomalias.py         # Deteccion de anomalias + prediccion demanda
│   │   ├── ciudadanos.py        # Registro ciudadanos Telegram
│   │   ├── dnrpa.py             # Lookup DNRPA
│   │   ├── qr_portal.py         # Portal de pago ciudadano (/p/{id})
│   │   ├── inspector_pwa.py     # PWA offline para inspectores
│   │   ├── ocr.py               # Reconocimiento de patentes
│   │   ├── admin.py             # Cierre diario + reportes
│   │   ├── admin_crud.py        # CRUD inspectores + digest email
│   │   ├── auditoria.py         # Registro de auditoria
│   │   ├── vehiculos_abonos.py  # Historial vehiculos + abonos + portal ciudadano
│   │   └── health.py            # Health check
│   ├── services/ (21 modulos)
│   │   ├── pricing.py           # Calculo de tarifas unificado
│   │   ├── schedule.py          # Ordenanza 12.170
│   │   ├── cierre_diario.py     # Cierre masivo de sesiones
│   │   ├── mercadopago.py       # SDK MercadoPago + verificacion firma
│   │   ├── comprobante.py       # PDF fiscal con ReportLab
│   │   ├── ocr_engine.py        # Google Cloud Vision (mock fallback)
│   │   ├── notificador.py       # Notificaciones Telegram
│   │   ├── scheduler.py         # Cierre diario automatico 23:55
│   │   ├── dnrpa_lookup.py      # Consulta DNRPA (mock)
│   │   ├── anomaly_detector.py  # Deteccion de anomalias operativas
│   │   ├── tarifas_especiales.py # Tarifas por eventos
│   │   ├── qr_generator.py      # QR para pago ciudadano
│   │   ├── reporte_ejecutivo.py # PDF ejecutivo mensual
│   │   ├── alert_manager.py     # Alertas multicanal
│   │   ├── predictive_analytics.py # Prediccion de demanda
│   │   ├── abonos.py            # Gestion de abonos mensuales/semanales
│   │   ├── auditoria.py         # Servicio de auditoria
│   │   ├── capacity.py          # Control de capacidad por zona
│   │   ├── email_digest.py      # Reportes periodicos por email
│   │   ├── geofence.py          # Deteccion automatica de zona por GPS
│   │   └── vehiculo_historial.py # Historial completo de vehiculos
│   └── static/inspector/        # PWA (manifest.json, sw.js)
├── supabase/migrations/         # 7 migraciones SQL versionadas
├── tests/                       # Tests en 10 archivos
├── dashboard.py                 # Streamlit dashboard con UX premium
├── bot_telegram.py              # Bot Telegram con 7 comandos
├── run_local.py                 # Orquestador local (API + Dashboard + Bot)
├── seed_demo_data.py            # Sembrador de datos de demostracion
├── Dockerfile                   # Python 3.11-slim, Cloud Run
├── main.tf                      # Terraform IaC GCP
├── pyproject.toml               # Ruff + Pytest config
└── requirements.txt             # Dependencias versionadas
```

---

## Tecnologias

| Capa | Stack |
|------|-------|
| **API** | FastAPI, Uvicorn, Pydantic v2, slowapi |
| **Auth** | API Key + JWT (python-jose, passlib/bcrypt) |
| **DB** | Supabase PostgreSQL via httpx REST API |
| **Dashboard** | Streamlit, Pandas, Plotly, NumPy |
| **IA** | Google Gemini 2.0 Flash (reportes ejecutivos) |
| **Pagos** | MercadoPago SDK + Webhook IPN |
| **OCR** | Google Cloud Vision (mock fallback) |
| **PDF** | ReportLab (comprobantes + reportes) |
| **QR** | qrcode + Pillow |
| **Mensajeria** | python-telegram-bot async |
| **Scheduler** | APScheduler (cierre diario automatico) |
| **Infra** | Docker, Terraform, GCP Cloud Run |
| **CI/CD** | GitHub Actions (ruff + pytest + deploy) |

---

## Caracteristicas

### Nucleo
- **Registro de estacionamiento** con validacion de patente argentina (3 formatos), GPS y zona
- **Calculo de cobro estricto** segun Ordenanza 12.170 (tolerancia 5 min, fracciones 15 min, 20% desc. digital)
- **Validacion de horarios cobrables** (lun-vie 7-21, sab 7-14, nocturno 22-5)

### Panel de Control
- Metricas en tiempo real (vehiculos, recaudacion, adopcion digital)
- Mapa de ocupacion con coordenadas reales
- Grafico de tendencias 30 dias
- Ocupacion por zona tarifaria
- Reporte ejecutivo con IA (Gemini)
- Alertas de anomalias operativas en vivo

### Pagos y Fiscalizacion
- **MercadoPago**: preferencias de pago + webhook IPN + verificacion de firma
- **Comprobantes PDF**: tickets fiscales con ReportLab
- **Infracciones**: emision de multas con foto evidencia, consulta ciudadana
- **Tarifas dinamicas**: precios especiales por eventos con multiplicador

### Ciudadanos
- **Telegram Bot**: `/deuda`, `/registrar`, `/mis_patentes`, `/desregistrar`, `/multas`, `/dnrpa`
- **Portal QR**: web mobile responsiva para pago sin app (`/p/{session_id}`)
- **Notificaciones proactivas**: aviso al iniciar estacionamiento

### Inspectores
- **Auth JWT**: login con legajo/password, roles (inspector/supervisor/admin)
- **OCR**: reconocimiento de patentes via Cloud Vision
- **PWA offline**: app progresiva con service worker para uso sin conexion
- **DNRPA**: consulta de registro nacional de automotor

### Operaciones
- **Cierre diario automatico**: scheduler a las 23:55 ARG
- **Deteccion de anomalias**: saturacion de zonas, sesiones prolongadas, cada 5 min
- **Prediccion de demanda**: por zona/hora basado en 30 dias historicos
- **Alertas multicanal**: Telegram + email + SMS con escalacion por severidad
- **Analiticas historicas**: endpoint con agrupacion por dia/hora/semana
- **Reporte ejecutivo PDF**: multi-pagina con resumen, graficos y conclusiones IA

### DevOps
- **API versioning**: `/v1/` prefix en todas las rutas
- **Migraciones SQL**: 7 archivos versionados para Supabase
- **Structured JSON logging**: timestamp, severity, trace_id, exception
- **Rate limiting**: slowapi en todos los endpoints
- **79 tests**: unitarios + integracion con pytest
- **CI/CD**: ruff linting + pytest + deploy a Cloud Run

---

## Instalacion

### 1. Variables de entorno

```env
SUPABASE_URL=https://tu-proyecto.supabase.co
SUPABASE_KEY=sb_publishable_tu_key
GEMINI_API_KEY=tu_api_key_gemini
TELEGRAM_BOT_TOKEN=tu_bot_token
API_KEY=tu_api_key_secreta
JWT_SECRET=tu_jwt_secret
API_URL=http://127.0.0.1:8000

# Opcionales
MERCADOPAGO_ACCESS_TOKEN=tu_mp_token
MERCADOPAGO_WEBHOOK_SECRET=tu_mp_webhook_secret
GOOGLE_APPLICATION_CREDENTIALS=ruta_a_credenciales.json
```

### 2. Dependencias

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # testing + linting
```

### 3. Base de datos

Ejecuta las migraciones en orden desde `supabase/migrations/` en el SQL Editor de Supabase.

### 3. Ejecutar los Servicios (Entorno Local)

Para simplificar el desarrollo y las pruebas, hemos creado un orquestador que levanta toda la arquitectura en paralelo.

Simplemente ejecuta en tu terminal:
```bash
python run_local.py
```
Esto iniciará automáticamente:
1. La API y WebSockets (Puerto 8000).
2. El Dashboard de Streamlit (Puerto 8501).
3. El proceso en background del Bot de Telegram.

---

## API Reference (v1)

```
GET  /v1/                                    # Root con lista de endpoints
GET  /health                                 # Health check

# Estacionamiento
POST /v1/estacionamiento/iniciar             # GPS + zona opcionales
POST /v1/estacionamiento/cobrar              # Calculo + finalizacion
POST /v1/estacionamiento/deuda               # Consulta sin finalizar

# Zonas
GET  /v1/zonas                               # Listar zonas
POST /v1/zonas                               # Crear zona
GET  /v1/zonas/ocupacion                     # Capacidad en tiempo real

# Auth
POST /v1/auth/login                          # JWT inspectores

# Pagos
POST /v1/pagos/crear                         # Preferencia MercadoPago
POST /v1/pagos/webhook                       # IPN MercadoPago
GET  /v1/pagos/comprobante/{id}              # Descargar PDF

# Infracciones
POST /v1/infracciones/emitir                 # Emitir multa
GET  /v1/infracciones/consultar?patente=X    # Consultar multas
GET  /v1/infracciones/multas/{patente}       # Multas ciudadano (public)

# Tarifas
GET  /v1/tarifas/activas                     # Tarifas especiales vigentes
POST /v1/tarifas/especiales                  # Crear tarifa especial

# Analiticas
GET  /v1/analiticas/estadisticas             # ?desde=&hasta=&agrupacion=dia|hora|semana

# Anomalias
GET  /v1/anomalias                           # Deteccion en tiempo real
GET  /v1/anomalias/prediccion-demanda        # Prediccion por zona/hora

# DNRPA
GET  /v1/dnrpa/{patente}                     # Consulta registro automotor

# Ciudadanos
POST /v1/ciudadanos/registrar                # Vincular Telegram
GET  /v1/ciudadanos/buscar?patente=X         # Buscar ciudadano

# OCR
POST /v1/escanear_patente                    # Reconocimiento de imagen

# Admin
POST /v1/cierre_diario_forzado               # Cierre manual (respaldo)

# Publico
GET  /p/{session_id}                         # Portal de pago QR ciudadano
GET  /inspector/                             # PWA inspector
```

---

## WebSocket

```
ws://host/ws/dashboard
```

Eventos broadcast:
- `{"event": "update_dashboard"}` - Datos actualizados
- `{"event": "anomalias", "data": [...]}` - Anomalias detectadas
- `{"event": "cierre_diario", "resultado": {...}}` - Cierre completado

---

## Base de Datos (8 tablas)

| Tabla | Descripcion |
|-------|-------------|
| `estacionamientos` | Sesiones de estacionamiento con GPS, zona, DNRPA |
| `zonas` | Zonas tarifarias con capacidad |
| `inspectores` | Usuarios con roles y JWT |
| `ciudadanos` | Vinculacion Telegram-patentes |
| `infracciones` | Multas con foto evidencia |
| `tarifas_especiales` | Precios por eventos |
| `anomalias` | Registro de anomalias detectadas |
| `cierre_diario_log` | Historial de cierres automaticos |
| `comprobantes` | Tickets fiscales generados |
