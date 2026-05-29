from unittest.mock import AsyncMock, patch

_ROUTER = "app.routers.estacionamiento"
_DB = f"{_ROUTER}.EstacionamientoDB"


def _mock_db(method: str, **kwargs):
    return patch(f"{_DB}.{method}", new_callable=AsyncMock, **kwargs)


def _mock_schedule(return_value=True):
    return patch(f"{_ROUTER}.es_horario_cobrable", return_value=return_value)


def _mock_geofence():
    return patch(f"{_ROUTER}.detectar_zona_por_gps", new_callable=AsyncMock, return_value=None)


def _mock_capacity(return_value=True):
    return patch(f"{_ROUTER}.verificar_capacidad", new_callable=AsyncMock, return_value=(return_value, 10, 50))


def _mock_abono(return_value=None):
    return patch(f"{_ROUTER}.verificar_abono_activo", new_callable=AsyncMock, return_value=return_value)


def _mock_auditoria():
    return patch(f"{_ROUTER}.registrar_auditoria", new_callable=AsyncMock)


class TestIniciarEstacionamiento:
    def test_tipo_vehiculo_invalido(self, cliente, headers):
        respuesta = cliente.post(
            "/v1/estacionamiento/iniciar",
            json={"patente": "AB123CD", "tipo_vehiculo": "camion", "legajo_permisionario": "INSP-01"},
            headers=headers,
        )
        assert respuesta.status_code == 422

    def test_patente_vieja_formato_valido(self, cliente, headers):
        with _mock_schedule(), \
             _mock_db("buscar_activo_por_patente", return_value=None), \
             _mock_geofence(), _mock_capacity(), _mock_abono(), \
             _mock_db("crear"), _mock_auditoria(), \
             patch(f"{_ROUTER}.manager.broadcast", new_callable=AsyncMock):
            respuesta = cliente.post(
                "/v1/estacionamiento/iniciar",
                json={"patente": "AAA000", "tipo_vehiculo": "auto", "legajo_permisionario": "INSP-01"},
                headers=headers,
            )
            assert respuesta.status_code == 200

    def test_iniciar_con_gps(self, cliente, headers):
        with _mock_schedule(), \
             _mock_db("buscar_activo_por_patente", return_value=None), \
             _mock_geofence(), _mock_capacity(), _mock_abono(), \
             _mock_db("crear"), _mock_auditoria(), \
             patch(f"{_ROUTER}.manager.broadcast", new_callable=AsyncMock):
            respuesta = cliente.post(
                "/v1/estacionamiento/iniciar",
                json={
                    "patente": "AB123CD", "tipo_vehiculo": "auto",
                    "legajo_permisionario": "INSP-01",
                    "lat": -24.7883, "lon": -65.4105, "zona_id": 1,
                },
                headers=headers,
            )
            assert respuesta.status_code == 200

    def test_patente_formato_invalido(self, cliente, headers):
        respuesta = cliente.post(
            "/v1/estacionamiento/iniciar",
            json={"patente": "12345", "tipo_vehiculo": "auto", "legajo_permisionario": "INSP-01"},
            headers=headers,
        )
        assert respuesta.status_code == 422

    def test_patente_vacia(self, cliente, headers):
        respuesta = cliente.post(
            "/v1/estacionamiento/iniciar",
            json={"patente": "", "tipo_vehiculo": "auto", "legajo_permisionario": "INSP-01"},
            headers=headers,
        )
        assert respuesta.status_code == 422

    def test_legajo_vacio(self, cliente, headers):
        respuesta = cliente.post(
            "/v1/estacionamiento/iniciar",
            json={"patente": "AB123CD", "tipo_vehiculo": "auto", "legajo_permisionario": ""},
            headers=headers,
        )
        assert respuesta.status_code == 422

    def test_fuera_de_horario_cobrable(self, cliente, headers):
        with _mock_schedule(return_value=False):
            respuesta = cliente.post(
                "/v1/estacionamiento/iniciar",
                json={"patente": "AB123CD", "tipo_vehiculo": "auto", "legajo_permisionario": "INSP-01"},
                headers=headers,
            )
            assert respuesta.status_code == 400
            assert "libre y gratuito" in respuesta.json()["detail"]

    def test_vehiculo_ya_activo(self, cliente, headers):
        with _mock_schedule(), _mock_db("buscar_activo_por_patente", return_value={"id": 1}):
            respuesta = cliente.post(
                "/v1/estacionamiento/iniciar",
                json={"patente": "AB123CD", "tipo_vehiculo": "auto", "legajo_permisionario": "INSP-01"},
                headers=headers,
            )
            assert respuesta.status_code == 400
            assert "activo en curso" in respuesta.json()["detail"]


class TestCalcularCobro:
    def test_sin_auth(self, cliente):
        respuesta = cliente.post(
            "/v1/estacionamiento/cobrar",
            json={"patente": "AB123CD", "metodo_pago": "efectivo"},
        )
        assert respuesta.status_code in [401, 422]

    def test_metodo_pago_invalido(self, cliente, headers):
        respuesta = cliente.post(
            "/v1/estacionamiento/cobrar",
            json={"patente": "AB123CD", "metodo_pago": "cripto"},
            headers=headers,
        )
        assert respuesta.status_code == 422

    def test_patente_formato_invalido(self, cliente, headers):
        respuesta = cliente.post(
            "/v1/estacionamiento/cobrar",
            json={"patente": "XYZ", "metodo_pago": "efectivo"},
            headers=headers,
        )
        assert respuesta.status_code == 422

    def test_no_hay_activo(self, cliente, headers):
        with _mock_db("buscar_activo_por_patente_o_error") as mock_buscar:
            from fastapi import HTTPException
            mock_buscar.side_effect = HTTPException(
                status_code=404, detail="No se encontro un estacionamiento activo para esta patente"
            )
            respuesta = cliente.post(
                "/v1/estacionamiento/cobrar",
                json={"patente": "AB123CD", "metodo_pago": "efectivo"},
                headers=headers,
            )
            assert respuesta.status_code == 404

    def test_cobro_exitoso_efectivo(self, cliente, headers):
        with _mock_db("buscar_activo_por_patente_o_error") as mock_buscar, \
             patch(f"{_ROUTER}.calcular_costo") as mock_calcular, \
             _mock_db("actualizar_activo_por_patente"), \
             patch(f"{_ROUTER}.manager.broadcast", new_callable=AsyncMock):
            from datetime import datetime

            from app.config import TZ_ARG

            mock_buscar.return_value = {
                "id": 1, "patente": "AB123CD", "tipo_vehiculo": "auto",
                "hora_inicio": datetime.now(TZ_ARG).isoformat(),
            }
            mock_calcular.return_value = (700.0, 45.2, datetime.now(TZ_ARG))
            respuesta = cliente.post(
                "/v1/estacionamiento/cobrar",
                json={"patente": "AB123CD", "metodo_pago": "efectivo"},
                headers=headers,
            )
            assert respuesta.status_code == 200
            assert respuesta.json()["monto_final"] == 700.0


class TestConsultarDeuda:
    def test_patente_formato_valido(self, cliente, headers):
        with _mock_db("buscar_activo_por_patente_o_error") as mock_buscar, \
             patch(f"{_ROUTER}.calcular_costo") as mock_calcular:
            from datetime import datetime

            from app.config import TZ_ARG

            mock_buscar.return_value = {
                "id": 1, "patente": "AB123CD", "tipo_vehiculo": "auto",
                "hora_inicio": datetime.now(TZ_ARG).isoformat(),
            }
            mock_calcular.return_value = (560.0, 60.0, datetime.now(TZ_ARG))
            respuesta = cliente.post(
                "/v1/estacionamiento/deuda",
                json={"patente": "AB123CD"},
                headers=headers,
            )
            assert respuesta.status_code == 200
            assert "monto_total" in respuesta.json()


class TestOCR:
    def test_ocr_mock(self, cliente, headers):
        respuesta = cliente.post("/v1/escanear_patente", json={"imagen_base64": "datos_falsos"})
        assert respuesta.status_code == 200
        data = respuesta.json()
        assert "patente_detectada" in data
        assert data["patente_detectada"] == "AB123CD"


class TestCierreDiario:
    def test_cierre_diario_sin_activos(self, cliente, headers):
        mock_result = {"procesados": 0, "errores": 0, "total_proyectado": 0}
        with patch("app.routers.admin.procesar_cierre_diario", new_callable=AsyncMock, return_value=mock_result):
            respuesta = cliente.post("/v1/cierre_diario_forzado", headers=headers)
            assert respuesta.status_code == 200
            assert "segundo plano" in respuesta.json()["mensaje"]
