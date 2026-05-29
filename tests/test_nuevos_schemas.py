from app.models.schemas import (
    PeticionCrearPago,
    PeticionCrearZona,
    PeticionIniciarEstacionamiento,
    PeticionLogin,
    PeticionRegistrarCiudadano,
)


class TestNuevosSchemas:
    def test_login_schema(self):
        data = PeticionLogin(legajo="INSP-01", password="test123")
        assert data.legajo == "INSP-01"

    def test_crear_zona_schema(self):
        data = PeticionCrearZona(nombre="Microcentro", tarifa_auto=700, tarifa_moto=300)
        assert data.nombre == "Microcentro"
        assert data.capacidad_maxima == 50
        assert data.activa is True

    def test_crear_pago_schema(self):
        data = PeticionCrearPago(patente="AB123CD", email="test@test.com")
        assert data.patente == "AB123CD"

    def test_registrar_ciudadano_schema(self):
        data = PeticionRegistrarCiudadano(
            telegram_chat_id=123, nombre="Juan", patentes=["AB123CD"]
        )
        assert data.telegram_chat_id == 123
        assert "AB123CD" in data.patentes

    def test_iniciar_con_gps(self):
        data = PeticionIniciarEstacionamiento(
            patente="AB123CD",
            tipo_vehiculo="auto",
            legajo_permisionario="INSP-01",
            lat=-24.7883,
            lon=-65.4105,
            zona_id=1,
        )
        assert data.lat == -24.7883
        assert data.lon == -65.4105
        assert data.zona_id == 1
