from datetime import date, datetime

FERIADOS_FIJOS = [
    "2026-01-01",
    "2026-02-24",
    "2026-03-02",
    "2026-03-24",
    "2026-04-02",
    "2026-04-17",
    "2026-05-01",
    "2026-05-25",
    "2026-06-17",
    "2026-06-20",
    "2026-07-09",
    "2026-08-17",
    "2026-10-12",
    "2026-11-23",
    "2026-12-08",
    "2026-12-25",
]


def es_feriado(fecha: date) -> bool:
    return fecha.isoformat() in FERIADOS_FIJOS


def es_horario_cobrable(fecha_hora: datetime) -> bool:
    dia_semana = fecha_hora.weekday()
    hora = fecha_hora.time()
    hora_actual = hora.hour + hora.minute / 60.0

    if hora_actual >= 22.0 or hora_actual < 5.0:
        return True

    if es_feriado(fecha_hora.date()):
        return False

    if dia_semana <= 4 and 7.0 <= hora_actual < 21.0:
        return True

    return dia_semana == 5 and 7.0 <= hora_actual < 14.0
