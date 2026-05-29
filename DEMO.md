# DEMO.md - Guion de Presentacion (4 minutos)

## Setup (antes de la demo)
```bash
# 1. Sembrar datos de demostracion
python seed_demo_data.py

# 2. Iniciar servicios
python run_local.py
```

## Minuto 1: El Problema y la Vision
**Narracion:** "En Salta, 50.000 vehiculos circulan diariamente. El estacionamiento medido se gestiona con papel y lapicera. Los inspectores no tienen visibilidad en tiempo real, los ciudadanos no saben cuanto deben, y la municipalidad pierde millones en recaudacion no fiscalizada."

**Mostrar:** Dashboard en pantalla (pestana Monitoreo) con datos sembrados.
- Senalar las 4 metricas en vivo
- Senalar el mapa de ocupacion
- "Todo esto se actualiza cada 10 segundos via WebSocket"

## Minuto 2: El Inspector Digital
**Accion:** Sidebar -> Iniciar Estacionamiento
- Ingresar patente "AB123CD", auto, legajo INSP-01
- Click "Iniciar"
- **Mostrar que la metrica de "Estacionados" sube en tiempo real**
- El mapa muestra el nuevo punto

**Accion:** Sidebar -> Consultar DNRPA
- Ingresar "AB123CD"
- Mostrar datos del vehiculo (marca, modelo, alerta de secuestro si hay)

**Accion:** Sidebar -> Cobrar Estacionamiento  
- Ingresar "AB123CD", efectivo
- Click "Cobrar"
- **Mostrar que la recaudacion sube instantaneamente**

## Minuto 3: El Ciudadano Empoderado
**Mostrar:** Telegram Bot en el telefono
- `/deuda AB123CD` -> Muestra deuda actual
- `/registrar AB123CD` -> Registra la patente
- `/historial AB123CD` -> Historial completo

**Mostrar:** Portal QR (abrir en telefono)
- `http://localhost:8000/p/1` (o el ID real)
- Mostrar la pagina mobile con el boton "Pagar Ahora"
- "El ciudadano escanea un QR, ve su deuda en tiempo real, y paga con MercadoPago"

## Minuto 4: Inteligencia Municipal
**Mostrar:** Pestana Administracion
- Emitir una infraccion desde el sidebar
- Mostrar apelaciones pendientes en pestana Infracciones

**Mostrar:** Intendente AI
- Click "Generar Reporte IA"
- Leer el reporte generado por Gemini en voz alta

**Cierre:** "SEM Express: 29 features, 79 tests, arquitectura modular lista para produccion. Transformamos el estacionamiento medido en una herramienta de gestion inteligente para la ciudad."

---

## Funcionalidades a destacar durante preguntas:
- **Geofencing automatico**: el sistema detecta la zona desde el GPS del inspector
- **PWA offline**: los inspectores pueden trabajar sin conexion
- **Tarifas dinamicas**: precios especiales para eventos (partidos, ferias)
- **Cierre diario automatico**: 23:55 todos los dias sin intervencion
- **Auditoria completa**: cada accion queda registrada
- **Deteccion de anomalias**: zonas saturadas, sesiones prolongadas
