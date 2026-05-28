# SEM Express - Sistema de Estacionamiento Medido

SEM Express es un sistema integral para la gestión y cobro de estacionamiento medido municipal. Consta de una API robusta y un panel de control en tiempo real para visualizar las métricas clave.

## 🛠️ Tecnologías Utilizadas
- **Backend:** FastAPI, Python, Supabase (REST API vía httpx)
- **Frontend / Panel de Control:** Streamlit, Pandas, Plotly
- **Base de Datos:** Supabase (PostgreSQL)

## 🚀 Características Principales
- **Inicio de Estacionamiento:** Registro en tiempo real de vehículos (autos y motos).
- **Cálculo de Cobro Estricto:**
  - Tolerancia de 5 minutos sin cargo.
  - Primera hora completa, luego fraccionado cada 15 minutos exactos.
  - Descuento del 20% aplicable para pagos digitales (Mercado Pago).
- **Panel de Control en Vivo:**
  - Métricas de vehículos estacionados, recaudación del día y adopción de pagos digitales.
  - Gráficos interactivos de métodos de pago.
  - Tabla de registros activos en tiempo real.
- 🌟 **Innovaciones (Fase 2):**
  - Escaneo de Patentes vía OCR.
  - Cierre Automático de Sesiones (Cronjob).
  - Bot de Telegram para consultas de conductores.

## 💻 Instalación y Uso Local

### 1. Configurar Variables de Entorno
Crea un archivo `.env` en la raíz del proyecto con tus credenciales de Supabase:
```env
SUPABASE_URL=tu_url_de_supabase
SUPABASE_KEY=tu_anon_key_de_supabase
GEMINI_API_KEY=tu_api_key_de_gemini
```

### 2. Instalar Dependencias
Asegúrate de tener un entorno virtual activo e instala las dependencias necesarias.
Ejemplo de dependencias clave requeridas:
```bash
pip install fastapi uvicorn httpx pydantic streamlit pandas plotly requests
```

### 3. Ejecutar los Servicios

**Iniciar la API (FastAPI):**
```bash
fastapi dev main.py
# o alternativamente:
uvicorn main:app --reload
```

**Iniciar el Panel de Control (Streamlit):**
```bash
streamlit run dashboard.py
```

## 🏗️ Estructura de la Base de Datos (Supabase)
Para que el sistema funcione correctamente, se requiere una tabla llamada `estacionamientos` con la siguiente estructura:
- `id` (uuid o int8, primary key, auto-generado)
- `patente` (text)
- `tipo_vehiculo` (text: 'auto' o 'moto')
- `legajo_permisionario` (text)
- `hora_inicio` (timestamptz)
- `hora_fin` (timestamptz, nullable)
- `estado` (text: 'activo' o 'finalizado')
- `monto_final` (numeric, nullable)
- `metodo_pago` (text, nullable: 'digital' o 'efectivo')

## 🛡️ Arquitectura e Infraestructura (DevOps)
El despliegue de SEM Express está diseñado bajo estándares empresariales:
- **Infraestructura como Código (IaC):** Todo el entorno de Google Cloud (Cloud Run, IAM) se gestiona mediante **Terraform** (`main.tf`), garantizando reproducibilidad y control de versiones.
- **Alta Disponibilidad:** El servicio Cloud Run está configurado con Auto-Scaling (min 1, max 10) para evitar "Cold Starts" y soportar picos de concurrencia durante los cambios de turno (hasta 80 request simultáneos por instancia).
- **Procesamiento Asíncrono:** Uso de `BackgroundTasks` de FastAPI para el cierre masivo de jornadas, previniendo cuellos de botella y *timeouts* en el servidor.
- **TDD & QA Automático:** Suite de pruebas unitarias con `pytest` integradas en el pipeline de GitHub Actions (`deploy.yml`) para garantizar cero regresiones en cada despliegue.
- **Patrones de Diseño:** Uso de Dependency Injection en FastAPI para manejar las credenciales, facilitando el testing y la modularidad.
- **Arquitectura Event-Driven (Preparada):** Implementación de WebSockets (`/ws/dashboard`) para permitir notificaciones Push en tiempo real a clientes conectados, reduciendo el polling a la base de datos.
