import logging
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.config import SUPABASE_KEY, SUPABASE_URL

logger = logging.getLogger(__name__)


async def enviar_digest_email(email: str, nombre: str, frecuencia: str) -> bool:
    import os
    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_pass = os.getenv("SMTP_PASSWORD", "")

    if not smtp_host:
        logger.info(f"Digest {frecuencia} simulado para {email}: SMTP no configurado")
        return True

    try:
        msg = MIMEMultipart()
        msg["From"] = smtp_user
        msg["To"] = email
        msg["Subject"] = f"SEM Express - Reporte {frecuencia.capitalize()}"

        body = f"""
        <h2>SEM Express - Municipalidad de Salta</h2>
        <p>Hola {nombre},</p>
        <p>Adjunto el reporte {frecuencia} de estacionamiento medido.</p>
        <p>Consulta el dashboard en tiempo real para mas informacion.</p>
        <hr>
        <p><small>Este es un correo automatico de SEM Express.</small></p>
        """
        msg.attach(MIMEText(body, "html"))

        # Generate PDF and attach
        from app.services.reporte_ejecutivo import generar_reporte_ejecutivo_pdf
        pdf_bytes = generar_reporte_ejecutivo_pdf({
            "desde": "Periodo actual",
            "hasta": "",
            "total_estacionamientos": 0,
            "recaudacion_total": 0,
            "porcentaje_digital": 0,
            "duracion_promedio_minutos": 0,
            "conclusion_ia": "Reporte generado automaticamente por SEM Express.",
        })

        if pdf_bytes:
            part = MIMEBase("application", "pdf")
            part.set_payload(pdf_bytes)
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename=reporte_{frecuencia}.pdf")
            msg.attach(part)

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_pass)
            server.send_message(msg)

        logger.info(f"Digest {frecuencia} enviado a {email}")
        return True
    except Exception as e:
        logger.error(f"Error enviando digest a {email}: {e}")
        return False


async def enviar_digests_automaticos(frecuencia: str):
    import httpx

    headers = {"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"}
    url = f"{SUPABASE_URL}/rest/v1/suscriptores_digest?frecuencia=eq.{frecuencia}&activo=eq.true&select=*"

    async with httpx.AsyncClient() as cliente:
        resp = await cliente.get(url, headers=headers)
        if resp.status_code != 200:
            return
        suscriptores = resp.json()

    for s in suscriptores:
        await enviar_digest_email(s["email"], s.get("nombre", ""), frecuencia)
