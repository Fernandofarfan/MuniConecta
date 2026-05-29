from datetime import datetime, timedelta, timezone

from app.services.schedule import es_horario_cobrable

TZ_ARG = timezone(timedelta(hours=-3))


def _fecha(dia: int, hora: int, minuto: int = 0) -> datetime:
    return datetime(2026, 5, dia, hora, minuto, tzinfo=TZ_ARG)


class TestHorarioCobrable:
    def test_lunes_10am_cobrable(self):
        assert es_horario_cobrable(_fecha(4, 10, 0)) is True

    def test_lunes_6am_no_cobrable(self):
        assert es_horario_cobrable(_fecha(4, 6, 0)) is False

    def test_lunes_21_30_cobrable(self):
        assert es_horario_cobrable(_fecha(4, 21, 30)) is False

    def test_sabado_13pm_cobrable(self):
        assert es_horario_cobrable(_fecha(9, 13, 0)) is True

    def test_sabado_15pm_no_cobrable(self):
        assert es_horario_cobrable(_fecha(9, 15, 0)) is False

    def test_domingo_10am_no_cobrable(self):
        assert es_horario_cobrable(_fecha(10, 10, 0)) is False

    def test_nocturno_23pm_cobrable(self):
        assert es_horario_cobrable(_fecha(4, 23, 0)) is True

    def test_nocturno_3am_cobrable(self):
        assert es_horario_cobrable(_fecha(4, 3, 0)) is True

    def test_sabado_14pm_no_cobrable(self):
        assert es_horario_cobrable(_fecha(9, 14, 0)) is False

    def test_viernes_20pm_cobrable(self):
        assert es_horario_cobrable(_fecha(8, 20, 0)) is True
