import os

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["PWA"])

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static", "inspector")


@router.get("/inspector/")
async def inspector_pwa():
    return HTMLResponse("""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="manifest" href="/manifest.json">
    <title>SEM Express - Inspector</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Inter', sans-serif; background: #0f172a; color: #e2e8f0; padding: 20px; }
        .header { text-align: center; margin-bottom: 30px; }
        .header h1 { color: #00b1ea; font-size: 1.5rem; }
        .card { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; padding: 20px; margin-bottom: 20px; }
        .card h2 { color: #00b1ea; margin-bottom: 15px; font-size: 1.1rem; }
        input, select, button { width: 100%; padding: 12px; margin: 8px 0; border-radius: 10px; border: 1px solid rgba(255,255,255,0.1); background: rgba(255,255,255,0.05); color: white; font-size: 1rem; }
        button { background: linear-gradient(135deg, #00b1ea, #0091c7); border: none; font-weight: 600; cursor: pointer; }
        button:hover { opacity: 0.9; }
        .status { padding: 15px; border-radius: 10px; margin-top: 10px; text-align: center; font-weight: 600; }
        .status.success { background: rgba(133,187,101,0.2); color: #85bb65; }
        .status.error { background: rgba(239,68,68,0.2); color: #ef4444; }
        .offline-badge { background: rgba(239,204,68,0.2); color: #e5c74a; padding: 5px 15px; border-radius: 20px; font-size: 0.8rem; display: inline-block; margin-bottom: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <h1>🚗 SEM Express</h1>
        <p>App Permisionario</p>
        <div id="offlineBadge" class="offline-badge" style="display:none">Sin conexion</div>
    </div>

    <div class="card">
        <h2>📸 Escanear Patente</h2>
        <input id="captureBtn" type="file" accept="image/*" capture="environment">
        <div id="ocrResult" class="status" style="display:none"></div>
    </div>

    <div class="card">
        <h2>🚘 Iniciar Estacionamiento</h2>
        <input id="patenteInicio" placeholder="Patente (Ej: AB123CD)">
        <select id="tipoVehiculo"><option value="auto">Auto</option><option value="moto">Moto</option></select>
        <input id="legajoInspector" placeholder="Tu Legajo" value="INSP-01">
        <button onclick="iniciarEstacionamiento()">✅ Iniciar</button>
        <div id="inicioResult" class="status" style="display:none"></div>
    </div>

    <div class="card">
        <h2>💸 Cobrar Estacionamiento</h2>
        <input id="patenteCobro" placeholder="Patente a retirar">
        <select id="metodoPago"><option value="digital">Mercado Pago</option><option value="efectivo">Efectivo</option></select>
        <button onclick="calcularCobro()">💳 Calcular y Cobrar</button>
        <div id="cobroResult" class="status" style="display:none"></div>
    </div>

    <script>
        if ('serviceWorker' in navigator) { navigator.serviceWorker.register('/sw.js'); }

        let isOnline = navigator.onLine;
        window.addEventListener('online', () => { isOnline = true; document.getElementById('offlineBadge').style.display = 'none'; });
        window.addEventListener('offline', () => { isOnline = false; document.getElementById('offlineBadge').style.display = 'inline-block'; });

        async function iniciarEstacionamiento() {
            const resultDiv = document.getElementById('inicioResult');
            const patente = document.getElementById('patenteInicio').value.toUpperCase();
            const tipo = document.getElementById('tipoVehiculo').value;
            const legajo = document.getElementById('legajoInspector').value;

            if (!patente) { resultDiv.style.display = 'block'; resultDiv.className = 'status error'; resultDiv.textContent = 'Ingresa una patente'; return; }

            try {
                const res = await fetch('/v1/estacionamiento/iniciar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-API-Key': ''},
                    body: JSON.stringify({patente, tipo_vehiculo: tipo, legajo_permisionario: legajo})
                });
                const data = await res.json();
                resultDiv.style.display = 'block';
                if (res.ok) {
                    resultDiv.className = 'status success';
                    resultDiv.textContent = '¡Registrado! ' + patente;
                } else {
                    resultDiv.className = 'status error';
                    resultDiv.textContent = data.detail || 'Error';
                }
            } catch (e) {
                resultDiv.style.display = 'block';
                resultDiv.className = 'status error';
                resultDiv.textContent = isOnline ? 'Error de servidor' : 'Sin conexion - se sincronizara al reconectar';
            }
        }

        async function calcularCobro() {
            const resultDiv = document.getElementById('cobroResult');
            const patente = document.getElementById('patenteCobro').value.toUpperCase();
            const metodo = document.getElementById('metodoPago').value;

            if (!patente) { resultDiv.style.display = 'block'; resultDiv.className = 'status error'; resultDiv.textContent = 'Ingresa una patente'; return; }

            try {
                const res = await fetch('/v1/estacionamiento/cobrar', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-API-Key': ''},
                    body: JSON.stringify({patente, metodo_pago: metodo})
                });
                const data = await res.json();
                resultDiv.style.display = 'block';
                if (res.ok) {
                    resultDiv.className = 'status success';
                    resultDiv.innerHTML = 'Total: $' + data.monto_final + (data.link_pago_mp ? '<br><a href="' + data.link_pago_mp + '" style="color:#00b1ea">Pagar con MercadoPago</a>' : '');
                } else {
                    resultDiv.className = 'status error';
                    resultDiv.textContent = data.detail || 'Error';
                }
            } catch (e) {
                resultDiv.style.display = 'block';
                resultDiv.className = 'status error';
                resultDiv.textContent = isOnline ? 'Error de servidor' : 'Sin conexion';
            }
        }
    </script>
</body>
</html>
""")
