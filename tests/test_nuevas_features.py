from unittest.mock import AsyncMock, patch

from fastapi import HTTPException


class TestAuth:
    def test_login_legajo_invalido(self, cliente):
        with patch("app.routers.auth.InspectorDB.buscar_por_legajo", new_callable=AsyncMock) as mock_buscar:
            mock_buscar.return_value = None
            respuesta = cliente.post(
                "/v1/auth/login",
                json={"legajo": "INSP-999", "password": "test123"},
            )
            assert respuesta.status_code == 401

    def test_login_password_invalido(self, cliente):
        with patch("app.routers.auth.InspectorDB.buscar_por_legajo", new_callable=AsyncMock) as mock_buscar, \
             patch("app.routers.auth.verificar_password") as mock_verify:
            mock_buscar.return_value = {
                "id": 1, "legajo": "INSP-01", "nombre": "Juan",
                "password_hash": "$2b$12$hash", "rol": "inspector",
            }
            mock_verify.return_value = False
            respuesta = cliente.post(
                "/v1/auth/login",
                json={"legajo": "INSP-01", "password": "wrong"},
            )
            assert respuesta.status_code == 401

    def test_login_exitoso(self, cliente):
        with patch("app.routers.auth.InspectorDB.buscar_por_legajo", new_callable=AsyncMock) as mock_buscar, \
             patch("app.routers.auth.verificar_password") as mock_verify:
            mock_buscar.return_value = {
                "id": 1, "legajo": "INSP-01", "nombre": "Juan",
                "password_hash": "$2b$12$hash", "rol": "inspector",
            }
            mock_verify.return_value = True
            respuesta = cliente.post(
                "/v1/auth/login",
                json={"legajo": "INSP-01", "password": "test123"},
            )
            assert respuesta.status_code == 200
            data = respuesta.json()
            assert "access_token" in data
            assert data["token_type"] == "bearer"
            assert data["inspector"]["legajo"] == "INSP-01"


class TestZonas:
    def test_listar_zonas(self, cliente, headers):
        with patch("app.routers.zonas.ZonaDB.obtener_todas", new_callable=AsyncMock) as mock_zonas:
            mock_zonas.return_value = [
                {"id": 1, "nombre": "Microcentro", "tarifa_auto": 700, "capacidad_maxima": 100},
            ]
            respuesta = cliente.get("/v1/zonas", headers=headers)
            assert respuesta.status_code == 200
            assert len(respuesta.json()["zonas"]) == 1

    def test_ocupacion(self, cliente, headers):
        with patch("app.routers.zonas.ZonaDB.obtener_ocupacion", new_callable=AsyncMock) as mock_ocup:
            mock_ocup.return_value = [
                {"id": 1, "nombre": "Microcentro", "capacidad_maxima": 100, "ocupados": 25},
            ]
            respuesta = cliente.get("/v1/zonas/ocupacion", headers=headers)
            assert respuesta.status_code == 200
            assert respuesta.json()["zonas"][0]["ocupados"] == 25

    def test_crear_zona(self, cliente, headers):
        with patch("app.routers.zonas.ZonaDB.crear", new_callable=AsyncMock) as mock_crear:
            mock_crear.return_value = {"id": 1, "nombre": "Test", "tarifa_auto": 500}
            respuesta = cliente.post(
                "/v1/zonas",
                json={"nombre": "Test", "tarifa_auto": 500, "tarifa_moto": 200, "capacidad_maxima": 50},
                headers=headers,
            )
            assert respuesta.status_code == 200


class TestPagos:
    def test_crear_pago_sin_activo(self, cliente, headers):
        with patch("app.routers.pagos.EstacionamientoDB.buscar_activo_por_patente_o_error") as mock_buscar:
            mock_buscar.side_effect = HTTPException(status_code=404, detail="No se encontro")
            respuesta = cliente.post(
                "/v1/pagos/crear",
                json={"patente": "AB123CD", "email": "test@test.com"},
                headers=headers,
            )
            assert respuesta.status_code == 404

    def test_webhook_sin_signature(self, cliente):
        respuesta = cliente.post("/v1/pagos/webhook", json={"data": {"id": "123"}})
        assert respuesta.status_code == 200
        assert respuesta.json()["status"] in ["ok", "ignored"]


class TestAnaliticas:
    def test_estadisticas_con_datos(self, cliente, headers):
        mock = patch(
            "app.routers.analiticas.EstacionamientoDB.obtener_analiticas",
            new_callable=AsyncMock,
        )
        with mock as mock_analiticas:
            mock_analiticas.return_value = []
            respuesta = cliente.get(
                "/v1/analiticas/estadisticas?desde=2026-01-01&hasta=2026-01-31&agrupacion=dia",
                headers=headers,
            )
            assert respuesta.status_code == 200
            data = respuesta.json()
            assert data["total_estacionamientos"] == 0
            assert data["recaudacion_total"] == 0.0
            assert data["porcentaje_digital"] == 0.0


class TestCiudadanos:
    def test_registrar_ciudadano(self, cliente, headers):
        with patch("app.routers.ciudadanos.CiudadanoDB.upsert", new_callable=AsyncMock) as mock_upsert:
            mock_upsert.return_value = None
            respuesta = cliente.post(
                "/v1/ciudadanos/registrar",
                json={
                    "telegram_chat_id": 123456,
                    "nombre": "Juan",
                    "patentes": ["AB123CD", "AAA000"],
                },
                headers=headers,
            )
            assert respuesta.status_code == 200
            assert "Ciudadano registrado" in respuesta.json()["mensaje"]


class TestAPIv1:
    def test_health(self, cliente):
        respuesta = cliente.get("/health")
        assert respuesta.status_code == 200

    def test_api_root(self, cliente):
        respuesta = cliente.get("/v1/")
        assert respuesta.status_code == 200
        assert respuesta.json()["api"] == "SEM Express"
        assert respuesta.json()["version"] == "1.0.0"
