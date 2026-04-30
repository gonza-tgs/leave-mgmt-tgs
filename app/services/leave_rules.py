from datetime import date, timedelta
from datetime import datetime
import holidays
from app.config import MIN_ANTICIPATION_DAYS


def _to_date(value) -> date:
    """Convierte string ISO o date a date."""
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def get_chilean_holidays(year: int):
    """Retorna los feriados de Chile para un año específico."""
    return holidays.Chile(years=[year])


def is_blocked_day(
    check_date: date, feriados_internos: list | None = None
) -> tuple[bool, str]:
    """
    Verifica si un día no es hábil para solicitar permisos:
    - Fin de semana (sábado/domingo)
    - Feriado nacional chileno
    - Feriado interno definido por admin
    Retorna (bloqueado, razon).
    """
    if check_date.weekday() >= 5:
        return (
            True,
            "No se pueden solicitar permisos en fin de semana (sábado o domingo).",
        )

    cl_holidays = get_chilean_holidays(check_date.year)
    if check_date in cl_holidays:
        nombre = cl_holidays.get(check_date, "Feriado nacional")
        return True, f"La fecha seleccionada es feriado nacional: {nombre}."

    if feriados_internos:
        for f in feriados_internos:
            if str(f["fecha"]) == str(check_date):
                desc = f.get("descripcion") or "Día no laborable interno"
                return True, f"Día no laborable: {desc}."

    return False, ""


def is_prohibited_day(check_date: date) -> tuple[bool, str]:
    """
    Verifica si un día está prohibido para permisos administrativos.
    Retorna (es_prohibido, razon).
    """
    if check_date.weekday() == 0:
        return True, "Los lunes son días prohibidos para permisos administrativos."
    if check_date.weekday() == 4:
        return True, "Los viernes son días prohibidos para permisos administrativos."

    cl_holidays = get_chilean_holidays(check_date.year)

    if check_date in cl_holidays:
        return True, "La fecha seleccionada es un día feriado."

    tomorrow = check_date + timedelta(days=1)
    if tomorrow in cl_holidays:
        return True, "No se permiten permisos en vísperas de feriado."

    yesterday = check_date - timedelta(days=1)
    if yesterday in cl_holidays:
        return True, "No se permiten permisos el día posterior a un feriado."

    return False, ""


def check_anticipation(fecha_inicio: date) -> tuple[bool, str]:
    """
    Verifica que la solicitud se haga con al menos MIN_ANTICIPATION_DAYS de anticipación.
    Retorna (valido, razon). True = pasa la validación.
    """
    fecha_inicio = _to_date(fecha_inicio)
    today = date.today()
    min_date = today + timedelta(days=MIN_ANTICIPATION_DAYS)
    if fecha_inicio < min_date:
        dias_restantes = (fecha_inicio - today).days
        return (
            False,
            f"El permiso debe solicitarse con al menos {MIN_ANTICIPATION_DAYS} días de anticipación. "
            f"Faltan {dias_restantes} día(s) para la fecha solicitada."
        )
    return True, ""


def is_in_blocked_period(check_date: date, periodos: list | None = None) -> tuple[bool, str]:
    """
    Verifica si una fecha cae dentro de algún periodo bloqueado.
    Retorna (es_bloqueado, razon).
    """
    if not periodos:
        return False, ""
    check_date = _to_date(check_date)
    for p in periodos:
        inicio = _to_date(p["fecha_inicio"])
        fin = _to_date(p["fecha_fin"])
        if inicio <= check_date <= fin:
            desc = p.get("descripcion") or "Periodo bloqueado"
            return True, f"La fecha solicitada está dentro de un periodo sin autorización de permisos: {desc}."
    return False, ""


def evaluate_auto_approval(
    user_id: str,
    fecha_inicio: date,
    jornada: str,
    user_solicitudes: list,
    all_solicitudes: list,
) -> tuple[str, str]:
    """
    Evalúa las reglas de validación para permisos administrativos.
    Ya no aprueba automáticamente: si pasa todas las reglas va a pendiente.
    Retorna (estado, razon).
    """
    fecha_inicio = _to_date(fecha_inicio)
    current_year = fecha_inicio.year

    used_days = 0.0
    for sol in user_solicitudes:
        if (
            sol["tipo_permiso"] == "administrativo"
            and sol["estado"] in ["aprobado_auto", "aprobado_manual"]
            and _to_date(sol["fecha_inicio"]).year == current_year
        ):
            used_days += 1.0 if sol["jornada"] == "completa" else 0.5

    new_request_value = 1.0 if jornada == "completa" else 0.5
    if used_days + new_request_value > 3.0:
        return (
            "rechazado",
            f"Cupo anual excedido. Has usado {used_days} días de los 3 días administrativos permitidos.",
        )

    prohibited, reason = is_prohibited_day(fecha_inicio)
    if prohibited:
        return "rechazado", reason

    for sol in user_solicitudes:
        if sol["estado"] in ["aprobado_auto", "aprobado_manual"]:
            diff = abs((_to_date(sol["fecha_inicio"]) - fecha_inicio).days)
            if diff == 1:
                return (
                    "pendiente",
                    "No se permiten permisos administrativos en días consecutivos. Requiere revisión por parte de la Dirección.",
                )

    institutional_count = 0
    for sol in all_solicitudes:
        if _to_date(sol["fecha_inicio"]) == fecha_inicio and sol["estado"] in [
            "aprobado_auto",
            "aprobado_manual",
        ]:
            institutional_count += 1

    if institutional_count >= 2:
        return (
            "pendiente",
            "Se ha alcanzado el límite de 2 permisos institucionales para este día. Requiere revisión por parte de la Dirección.",
        )

    return (
        "pendiente",
        "Solicitud enviada para revisión. Cumple todas las restricciones iniciales.",
    )
