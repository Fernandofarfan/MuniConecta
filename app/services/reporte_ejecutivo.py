import io
import logging
from datetime import datetime

from app.config import TZ_ARG

logger = logging.getLogger(__name__)


def generar_reporte_ejecutivo_pdf(
    resumen: dict,
    grafico_bytes: bytes | None = None,
) -> bytes:
    try:
        import importlib.util
        if importlib.util.find_spec("reportlab") is None:
            raise ImportError
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm, mm
        from reportlab.pdfgen import canvas
    except ImportError:
        logger.warning("reportlab no instalado")
        return b""

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    ancho, alto = A4

    # Caratula
    c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(ancho / 2, alto - 3 * cm, "SEM Express")
    c.setFont("Helvetica", 14)
    c.drawCentredString(ancho / 2, alto - 4.5 * cm, "Reporte Ejecutivo Mensual")
    c.setFont("Helvetica", 10)
    c.drawCentredString(ancho / 2, alto - 5.5 * cm, "Municipalidad de Salta - Direccion de Transito")
    c.line(2 * cm, alto - 6 * cm, ancho - 2 * cm, alto - 6 * cm)

    # Resumen
    y = alto - 7.5 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Resumen del Periodo")
    y -= 1 * cm

    c.setFont("Helvetica", 10)
    lineas = [
        f"Periodo: {resumen.get('desde', '')} al {resumen.get('hasta', '')}",
        f"Total estacionamientos: {resumen.get('total_estacionamientos', 0)}",
        f"Recaudacion total: ${resumen.get('recaudacion_total', 0):,.2f}",
        f"Pagos digitales: {resumen.get('porcentaje_digital', 0):.1f}%",
        f"Duracion promedio: {resumen.get('duracion_promedio_minutos', 0):.0f} min",
    ]
    for linea in lineas:
        c.drawString(2.5 * cm, y, linea)
        y -= 0.7 * cm

    # Conclusion IA
    y -= 1 * cm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(2 * cm, y, "Conclusiones y Recomendaciones")
    y -= 1 * cm
    c.setFont("Helvetica", 9)
    if resumen.get("conclusion_ia"):
        texto = resumen["conclusion_ia"]
        for i in range(0, len(texto), 120):
            c.drawString(2.5 * cm, y, texto[i:i+120])
            y -= 0.5 * cm

    c.setFont("Helvetica", 8)
    c.drawCentredString(ancho / 2, 1.5 * cm, f"Generado el {datetime.now(TZ_ARG).strftime('%d/%m/%Y %H:%M')}")

    c.showPage()
    c.save()
    return buf.getvalue()
