import io
import logging

from app.config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)


def generar_comprobante_pdf(
    patente: str,
    monto: float,
    metodo_pago: str,
    tiempo_minutos: float,
    estacionamiento_id: int,
) -> bytes:
    from reportlab.pdfgen import canvas  # noqa

    if not SUPABASE_URL or not SUPABASE_KEY:
        return _generar_comprobante_local(
            patente, monto, metodo_pago, tiempo_minutos, estacionamiento_id
        )

    try:
        return _generar_comprobante_local(
            patente, monto, metodo_pago, tiempo_minutos, estacionamiento_id
        )
    except Exception as e:
        logger.error(f"Error generando comprobante: {e}")
        return b""


def _generar_comprobante_local(
    patente: str,
    monto: float,
    metodo_pago: str,
    tiempo_minutos: float,
    estacionamiento_id: int,
) -> bytes:
    try:
        import importlib.util
        if importlib.util.find_spec("reportlab") is None:
            raise ImportError
        from reportlab.lib.pagesizes import A6  # noqa
        from reportlab.lib.units import mm  # noqa
        from reportlab.pdfgen import canvas  # noqa
    except ImportError:
        logger.warning("reportlab no instalado, no se puede generar PDF")
        return b""

    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(80 * mm, 120 * mm))

    y = 110 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawCentredString(40 * mm, y, "SEM Express")
    y -= 8 * mm
    c.setFont("Helvetica", 8)
    c.drawCentredString(40 * mm, y, "Municipalidad de Salta")
    y -= 5 * mm
    c.line(5 * mm, y, 75 * mm, y)
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 9)
    c.drawString(5 * mm, y, f"Comprobante #{estacionamiento_id}")
    y -= 6 * mm
    c.setFont("Helvetica", 8)
    c.drawString(5 * mm, y, f"Patente: {patente}")
    y -= 5 * mm
    c.drawString(5 * mm, y, f"Tiempo: {tiempo_minutos:.0f} min")
    y -= 5 * mm
    c.drawString(5 * mm, y, f"Pago: {metodo_pago}")
    y -= 5 * mm
    c.line(5 * mm, y, 75 * mm, y)
    y -= 8 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(40 * mm, y, f"${monto:.2f}")
    y -= 10 * mm
    c.setFont("Helvetica", 7)
    c.drawCentredString(40 * mm, y, "Gracias por usar SEM Express")

    c.showPage()
    c.save()
    return buf.getvalue()


async def guardar_comprobante(estacionamiento_id: int, pdf_bytes: bytes) -> str | None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    import httpx

    filename = f"comprobante_{estacionamiento_id}.pdf"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }
    async with httpx.AsyncClient() as cliente:
        respuesta = await cliente.post(
            f"{SUPABASE_URL}/storage/v1/object/comprobantes/{filename}",
            headers=headers,
            content=pdf_bytes,
        )
        if respuesta.status_code in [200, 201]:
            url = f"{SUPABASE_URL}/storage/v1/object/public/comprobantes/{filename}"
            logger.info(f"Comprobante guardado: {url}")
            return url
        logger.error(f"Error guardando comprobante: {respuesta.text}")
        return None
