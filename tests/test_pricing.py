from datetime import datetime, timedelta, timezone

from app.services.pricing import calcular_costo

TZ_ARG = timezone(timedelta(hours=-3))


def _inicio_y_fin(minutos_atras: int) -> tuple[str, datetime]:
    ahora = datetime.now(TZ_ARG)
    inicio = ahora - timedelta(minutes=minutos_atras)
    return inicio.isoformat(), ahora


class TestCalcularCosto:
    def test_tolerancia_menos_de_5_minutos(self):
        inicio, fin = _inicio_y_fin(2)
        costo, minutos, _ = calcular_costo("auto", inicio, hora_fin=fin)
        assert costo == 0.0
        assert minutos < 5

    def test_primera_hora_completa_auto(self):
        inicio, fin = _inicio_y_fin(30)
        costo, minutos, _ = calcular_costo("auto", inicio, hora_fin=fin)
        assert costo == 700.0

    def test_primera_hora_completa_moto(self):
        inicio, fin = _inicio_y_fin(45)
        costo, _, _ = calcular_costo("moto", inicio, hora_fin=fin)
        assert costo == 300.0

    def test_hora_y_media_auto(self):
        inicio, fin = _inicio_y_fin(90)
        costo, _, _ = calcular_costo("auto", inicio, hora_fin=fin)
        assert costo == 1050.0

    def test_dos_horas_auto(self):
        inicio, fin = _inicio_y_fin(120)
        costo, _, _ = calcular_costo("auto", inicio, hora_fin=fin)
        assert costo == 1400.0

    def test_descuento_digital(self):
        inicio, fin = _inicio_y_fin(30)
        costo, _, _ = calcular_costo("auto", inicio, "digital", hora_fin=fin)
        assert costo == 560.0

    def test_descuento_digital_no_aplica_si_tolerancia(self):
        inicio, fin = _inicio_y_fin(2)
        costo, _, _ = calcular_costo("auto", inicio, "digital", hora_fin=fin)
        assert costo == 0.0

    def test_fraccion_15_minutos_adicionales(self):
        inicio, fin = _inicio_y_fin(80)
        costo, _, _ = calcular_costo("auto", inicio, hora_fin=fin)
        assert costo == 1050.0

    def test_fraccion_redondea_hacia_arriba(self):
        inicio, fin = _inicio_y_fin(76)
        costo, _, _ = calcular_costo("auto", inicio, hora_fin=fin)
        assert costo == 1050.0

    def test_tipo_vehiculo_invalido_levanta_error(self):
        inicio, fin = _inicio_y_fin(30)
        try:
            calcular_costo("camion", inicio, hora_fin=fin)
            raise AssertionError("Debio levantar ValueError")
        except ValueError:
            pass
