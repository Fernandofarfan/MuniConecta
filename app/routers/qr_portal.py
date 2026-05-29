import logging

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

logger = logging.getLogger(__name__)
router = APIRouter(tags=["QR Portal"])


@router.get("/p/{session_id}", response_class=HTMLResponse)
async def portal_pago_ciudadano(session_id: int):
    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    async with httpx.AsyncClient() as cliente:
        url = f"{SUPABASE_URL}/rest/v1/estacionamientos?id=eq.{session_id}&select=*"
        resp = await cliente.get(url, headers=headers)
        if resp.status_code != 200 or not resp.json():
            return HTMLResponse("<h1>Estacionamiento no encontrado</h1>", status_code=404)

        registro = resp.json()[0]
        patente = registro.get("patente", "Desconocida")
        monto = registro.get("monto_final", 0) or 0
        estado = registro.get("estado", "activo")
        tiempo = "En curso"

        if registro.get("hora_inicio") and registro.get("hora_fin"):
            try:
                from datetime import datetime
                ini = datetime.fromisoformat(registro["hora_inicio"].replace("Z", "+00:00"))
                fin = datetime.fromisoformat(registro["hora_fin"].replace("Z", "+00:00"))
                tiempo = f"{(fin - ini).total_seconds() / 60:.0f} min"
            except (ValueError, KeyError):
                pass

    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>SEM Express - Pago</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ font-family: 'Inter', sans-serif; background: linear-gradient(135deg, #0f172a, #1e293b); color: #e2e8f0; min-height: 100vh; display: flex; align-items: center; justify-content: center; }}
            .card {{ background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 20px; padding: 40px; max-width: 400px; width: 90%; text-align: center; backdrop-filter: blur(10px); }}
            h1 {{ color: #00b1ea; font-size: 1.5rem; margin-bottom: 10px; }}
            .patente {{ font-size: 2rem; font-weight: 800; letter-spacing: 3px; margin: 20px 0; color: white; }}
            .monto {{ font-size: 2.5rem; font-weight: 800; color: #85bb65; margin: 15px 0; }}
            .detalle {{ color: #94a3b8; font-size: 0.9rem; margin: 10px 0; }}
            .btn {{ display: inline-block; background: linear-gradient(135deg, #00b1ea, #0091c7); color: white; text-decoration: none; padding: 15px 40px; border-radius: 12px; font-weight: 600; font-size: 1.1rem; margin-top: 20px; border: none; cursor: pointer; }}
            .btn:hover {{ opacity: 0.9; }}
            .estado {{ font-size: 0.85rem; padding: 5px 15px; border-radius: 20px; display: inline-block; }}
            .estado.activo {{ background: rgba(0,177,234,0.2); color: #00b1ea; }}
            .estado.finalizado {{ background: rgba(133,187,101,0.2); color: #85bb65; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>SEM Express</h1>
            <p>Estacionamiento Medido - Salta</p>
            <div class="patente">{patente}</div>
            <span class="estado {estado}">{estado.upper()}</span>
            <div class="detalle">Tiempo: {tiempo}</div>
            <div class="monto">${monto:,.2f}</div>
            <a href="https://mpago.la/mock_punatech_2026?patente={patente}&monto={monto}" class="btn">💳 Pagar Ahora</a>
            <div class="detalle" style="margin-top:15px;">Municipalidad de Salta</div>
        </div>
    </body>
    </html>
    """)
