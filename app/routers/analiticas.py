import logging
from collections import defaultdict

from fastapi import APIRouter, Depends, Query

from app.auth import verificar_api_key
from app.database import EstacionamientoDB

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/analiticas", tags=["Analiticas"])


@router.get("/estadisticas")
async def estadisticas(
    desde: str = Query(..., description="Fecha inicio YYYY-MM-DD"),
    hasta: str = Query(..., description="Fecha fin YYYY-MM-DD"),
    agrupacion: str = Query("dia", description="dia|hora|semana"),
    _: str = Depends(verificar_api_key),
):
    registros = await EstacionamientoDB.obtener_analiticas(f"{desde}T00:00:00-03:00", f"{hasta}T23:59:59-03:00")

    total_estacionamientos = len(registros)
    recaudacion_total = sum(float(r.get("monto_final", 0) or 0) for r in registros)
    pagos_digitales = sum(1 for r in registros if r.get("metodo_pago") == "digital")
    finalizados = [
        r for r in registros
        if r.get("estado") == "finalizado"
        and r.get("hora_inicio") and r.get("hora_fin")
    ]

    duraciones = []
    for r in finalizados:
        try:
            from datetime import datetime
            ini = datetime.fromisoformat(r["hora_inicio"].replace("Z", "+00:00"))
            fin = datetime.fromisoformat(r["hora_fin"].replace("Z", "+00:00"))
            duraciones.append((fin - ini).total_seconds() / 60)
        except (ValueError, KeyError):
            pass

    duracion_promedio = sum(duraciones) / len(duraciones) if duraciones else 0

    porcentaje_digital = (pagos_digitales / total_estacionamientos * 100) if total_estacionamientos > 0 else 0

    agrupados = defaultdict(lambda: {"total": 0, "cantidad": 0, "digitales": 0})
    for r in registros:
        try:
            from datetime import datetime
            fecha = datetime.fromisoformat(r["hora_inicio"].replace("Z", "+00:00"))
            if agrupacion == "dia":
                clave = fecha.strftime("%Y-%m-%d")
            elif agrupacion == "hora":
                clave = fecha.strftime("%H:00")
            elif agrupacion == "semana":
                clave = fecha.strftime("%Y-W%W")
            else:
                clave = fecha.strftime("%Y-%m-%d")
        except (ValueError, KeyError):
            clave = "desconocido"

        monto = float(r.get("monto_final", 0) or 0)
        agrupados[clave]["total"] += monto
        agrupados[clave]["cantidad"] += 1
        if r.get("metodo_pago") == "digital":
            agrupados[clave]["digitales"] += 1

    serie_temporal = [
        {
            "periodo": clave,
            "recaudacion": round(datos["total"], 2),
            "estacionamientos": datos["cantidad"],
            "digitales": datos["digitales"],
        }
        for clave, datos in sorted(agrupados.items())
    ]

    return {
        "desde": desde,
        "hasta": hasta,
        "agrupacion": agrupacion,
        "total_estacionamientos": total_estacionamientos,
        "recaudacion_total": round(recaudacion_total, 2),
        "porcentaje_digital": round(porcentaje_digital, 1),
        "duracion_promedio_minutos": round(duracion_promedio, 1),
        "serie_temporal": serie_temporal,
    }
