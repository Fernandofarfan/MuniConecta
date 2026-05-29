from unittest.mock import AsyncMock, patch

from app.services.notificador import enviar_mensaje, notificar_inicio_estacionamiento


class TestNotificador:
    async def test_enviar_mensaje_sin_token(self):
        with patch("app.services.notificador.TELEGRAM_BOT_TOKEN", None):
            result = await enviar_mensaje(123, "test")
            assert result is False

    async def test_enviar_mensaje_exitoso(self):
        with patch("app.services.notificador.TELEGRAM_BOT_TOKEN", "fake"), \
             patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = AsyncMock()
            mock_resp.status_code = 200
            mock_post.return_value = mock_resp
            result = await enviar_mensaje(123, "test")
            assert result is True

    async def test_enviar_mensaje_error(self):
        with patch("app.services.notificador.TELEGRAM_BOT_TOKEN", "fake"), \
             patch("httpx.AsyncClient.post") as mock_post:
            mock_resp = AsyncMock()
            mock_resp.status_code = 400
            mock_post.return_value = mock_resp
            result = await enviar_mensaje(123, "test")
            assert result is False

    async def test_notificar_inicio(self):
        with patch("app.services.notificador.enviar_mensaje", new_callable=AsyncMock) as mock_env:
            mock_env.return_value = True
            result = await notificar_inicio_estacionamiento(123, "AB123CD", "auto")
            assert result is True
            mock_env.assert_called_once()
