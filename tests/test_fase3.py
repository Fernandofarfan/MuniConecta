from unittest.mock import AsyncMock, MagicMock, patch

from app.services.anomaly_detector import detectar_anomalias
from app.services.dnrpa_lookup import consultar_dnrpa
from app.services.predictive_analytics import predecir_demanda
from app.services.tarifas_especiales import aplicar_tarifa_especial


class TestDNRPA:
    async def test_consulta_mock(self):
        result = await consultar_dnrpa("AB123CD")
        assert "marca" in result
        assert "modelo" in result
        assert result["patente"] == "AB123CD"


class TestTarifasEspeciales:
    def test_sin_tarifas(self):
        costo, nombre = aplicar_tarifa_especial("auto", 700.0, [])
        assert costo == 700.0
        assert nombre is None

    def test_con_multiplicador(self):
        tarifas = [{"nombre_evento": "Feria", "multiplicador": 1.5}]
        costo, nombre = aplicar_tarifa_especial("auto", 700.0, tarifas)
        assert costo == 1050.0
        assert nombre == "Feria"

    def test_con_override_auto(self):
        tarifas = [{"nombre_evento": "Partido", "tarifa_auto_override": 1000, "multiplicador": 1.0}]
        costo, nombre = aplicar_tarifa_especial("auto", 700.0, tarifas)
        assert costo == 1000.0


class TestAnomalyDetector:
    async def test_detectar_saturacion(self):
        with patch(
            "app.services.anomaly_detector.ZonaDB.obtener_ocupacion",
            new_callable=AsyncMock,
        ) as mock_zonas, patch(
            "app.services.anomaly_detector.EstacionamientoDB.obtener_todos_activos",
            new_callable=AsyncMock,
        ) as mock_activos:
            mock_zonas.return_value = [
                {"id": 1, "nombre": "Microcentro", "capacidad_maxima": 100, "ocupados": 96},
            ]
            mock_activos.return_value = []
            anomalias = await detectar_anomalias()
            assert any(a["tipo"] == "saturacion_zona" for a in anomalias)


class TestPredictiveAnalytics:
    async def test_sin_datos(self):
        with patch(
            "app.services.predictive_analytics.EstacionamientoDB.obtener_analiticas",
            new_callable=AsyncMock,
        ) as mock_analiticas:
            mock_analiticas.return_value = []
            result = await predecir_demanda()
            assert result == []


class TestNuevosEndpoints:
    def test_dnrpa(self, cliente):
        respuesta = cliente.get("/v1/dnrpa/AB123CD")
        assert respuesta.status_code == 200
        data = respuesta.json()
        assert data["patente"] == "AB123CD"
        assert "marca" in data

    def test_infracciones_emitir_validation(self, cliente, headers):
        respuesta = cliente.post(
            "/v1/infracciones/emitir",
            json={"patente": "12345", "tipo_infraccion": "sin_registro", "legajo_inspector": "INSP-01"},
            headers=headers,
        )
        assert respuesta.status_code == 422

    def test_multas_ciudadano_route(self, cliente):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = []
            mock_get.return_value = mock_resp
            respuesta = cliente.get("/v1/infracciones/multas/AB123CD")
            assert respuesta.status_code == 200

    def test_portal_qr_route(self, cliente):
        with patch("httpx.AsyncClient.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{
                "id": 1, "patente": "AB123CD", "monto_final": 700, "estado": "activo",
            }]
            mock_get.return_value = mock_resp
            respuesta = cliente.get("/p/1")
            assert respuesta.status_code == 200
            assert "AB123CD" in respuesta.text

    def test_pwa(self, cliente):
        respuesta = cliente.get("/inspector/")
        assert respuesta.status_code == 200
        assert "SEM Express" in respuesta.text
