import logging

logger = logging.getLogger(__name__)


async def obtener_historial_vehiculo(patente: str, desde: str = "", hasta: str = "") -> dict:
    import httpx

    from app.config import SUPABASE_KEY, SUPABASE_URL

    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}

    params_est = [f"patente=eq.{patente}", "select=*", "order=hora_inicio.desc", "limit=500"]
    if desde:
        params_est.append(f"hora_inicio=gte.{desde}")
    if hasta:
        params_est.append(f"hora_inicio=lte.{hasta}")

    params_inf = [f"patente=eq.{patente}", "select=*", "order=creado_en.desc"]
    if desde:
        params_inf.append(f"creado_en=gte.{desde}")

    async with httpx.AsyncClient() as cliente:
        est_url = f"{SUPABASE_URL}/rest/v1/estacionamientos?{'&'.join(params_est)}"
        inf_url = f"{SUPABASE_URL}/rest/v1/infracciones?{'&'.join(params_inf)}"
        abo_url = f"{SUPABASE_URL}/rest/v1/abonos?patente=eq.{patente}&select=*"

        est_resp = await cliente.get(est_url, headers=headers)
        inf_resp = await cliente.get(inf_url, headers=headers)
        abo_resp = await cliente.get(abo_url, headers=headers)

    estacionamientos = est_resp.json() if est_resp.status_code == 200 else []
    infracciones = inf_resp.json() if inf_resp.status_code == 200 else []
    abonos = abo_resp.json() if abo_resp.status_code == 200 else []

    total_gastado = sum(float(e.get("monto_final", 0) or 0) for e in estacionamientos if e.get("estado") == "finalizado")
    total_pendiente_multas = sum(m["monto_multa"] for m in infracciones if m.get("estado") == "pendiente")

    zonas = {}
    for e in estacionamientos:
        z = e.get("zona_id", "desconocido")
        zonas[z] = zonas.get(z, 0) + 1
    zona_favorita = max(zonas, key=zonas.get) if zonas else None

    duraciones = []
    for e in estacionamientos:
        if e.get("hora_inicio") and e.get("hora_fin") and e.get("estado") == "finalizado":
            try:
                from datetime import datetime
                ini = datetime.fromisoformat(e["hora_inicio"].replace("Z", "+00:00"))
                fin = datetime.fromisoformat(e["hora_fin"].replace("Z", "+00:00"))
                duraciones.append((fin - ini).total_seconds() / 60)
            except (ValueError, KeyError):
                pass
    duracion_promedio = sum(duraciones) / len(duraciones) if duraciones else 0

    pagos = [e.get("metodo_pago") for e in estacionamientos if e.get("metodo_pago")]
    metodo_favorito = max(set(pagos), key=pagos.count) if pagos else None

    abono_activo = next((a for a in abonos if a.get("estado") == "activo"), None)

    return {
        "patente": patente,
        "estacionamientos": estacionamientos,
        "infracciones": infracciones,
        "abono_activo": abono_activo,
        "totales": {
            "total_estacionamientos": len(estacionamientos),
            "total_gastado": round(total_gastado, 2),
            "total_multas": len(infracciones),
            "total_pendiente_multas": total_pendiente_multas,
        },
        "estadisticas": {
            "zona_favorita": zona_favorita,
            "metodo_pago_favorito": metodo_favorito,
            "duracion_promedio_min": round(duracion_promedio, 1),
        },
    }
