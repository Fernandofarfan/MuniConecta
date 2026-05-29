from unittest.mock import patch


class TestMercadoPago:
    async def test_crear_preferencia_sin_token(self):
        with patch("app.services.mercadopago.MERCADOPAGO_ACCESS_TOKEN", None):
            from app.services.mercadopago import crear_preferencia_pago
            result = await crear_preferencia_pago("AB123CD", 700.0)
            assert "init_point" in result
            assert "mock" in result["init_point"]

    async def test_webhook_signature_sin_secret(self):
        from app.services.mercadopago import verificar_webhook_signature
        result = verificar_webhook_signature("ts=1,v1=abc", "rid", "did")
        assert result is True
