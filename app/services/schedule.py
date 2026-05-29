from datetime import datetime


def es_horario_cobrable(fecha_hora: datetime) -> bool:
    dia_semana = fecha_hora.weekday()
    hora = fecha_hora.time()
    hora_actual = hora.hour + hora.minute / 60.0

    if hora_actual >= 22.0 or hora_actual < 5.0:
        return True

    if dia_semana <= 4 and 7.0 <= hora_actual < 21.0:
        return True

    return dia_semana == 5 and 7.0 <= hora_actual < 14.0
