import io
import logging

logger = logging.getLogger(__name__)


def generar_qr_pago(patente: str, session_id: int, base_url: str) -> bytes:
    try:
        import qrcode
        from qrcode.image.styledpil import StyledPilImage
        from qrcode.image.styles.moduledrawers.pil import RoundedModuleDrawer

        data = f"{base_url}/v1/p/{session_id}"
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_H)
        qr.add_data(data)
        qr.make(fit=True)

        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            fill_color="#00b1ea",
            back_color="white",
        )

        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return buf.getvalue()
    except ImportError:
        logger.warning("qrcode no instalado")
        return _qr_placeholder(patente, session_id)


def _qr_placeholder(patente: str, session_id: int) -> bytes:
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        return b""
    img = Image.new("RGB", (300, 300), "white")
    draw = ImageDraw.Draw(img)
    draw.rectangle([20, 20, 280, 280], outline="#00b1ea", width=3)
    draw.text((150, 130), patente, fill="#00b1ea", anchor="mm")
    draw.text((150, 160), f"ID: {session_id}", fill="gray", anchor="mm")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()
