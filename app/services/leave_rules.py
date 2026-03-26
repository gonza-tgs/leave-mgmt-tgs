from datetime import date, timedelta
import holidays

def get_chilean_holidays(year: int):
    """Retorna los feriados de Chile para un año específico."""
    return holidays.Chile(years=[year])

def is_prohibited_day(check_date: date) -> tuple[bool, str]:
    """
    Verifica si un día está prohibido para permisos administrativos automáticos.
    Retorna (es_prohibido, razon).
    """
    # 1. Lunes (0) o Viernes (4)
    if check_date.weekday() == 0:
        return True, "Los lunes son días prohibidos para permisos automáticos."
    if check_date.weekday() == 4:
        return True, "Los viernes son días prohibidos para permisos automáticos."
    
    # 2. Feriados y sus adyacencias
    cl_holidays = get_chilean_holidays(check_date.year)
    
    if check_date in cl_holidays:
        return True, "La fecha seleccionada es un día feriado."
        
    # Víspera de feriado
    tomorrow = check_date + timedelta(days=1)
    if tomorrow in cl_holidays:
        return True, "No se permiten permisos en vísperas de feriado."
        
    # Día posterior a feriado
    yesterday = check_date - timedelta(days=1)
    if yesterday in cl_holidays:
        return True, "No se permiten permisos el día posterior a un feriado."
        
    return False, ""

def evaluate_auto_approval(
    user_id: str,
    fecha_inicio: date,
    jornada: str,
    user_solicitudes: list,
    all_solicitudes: list
) -> tuple[str, str]:
    """
    Evalúa si una solicitud de permiso administrativo califica para aprobación automática.
    Retorna (estado, razon).
    """
    # 1. Validar cupo anual (3 días máximo)
    # Jornada completa = 1.0, mañana/tarde = 0.5
    current_year = fecha_inicio.year
    used_days = 0.0
    for sol in user_solicitudes:
        # Solo contar aprobados del año actual y de tipo administrativo
        if (sol["tipo_permiso"] == "administrativo" and 
            sol["estado"] in ["aprobado_auto", "aprobado_manual"] and 
            sol["fecha_inicio"].year == current_year):
            used_days += 1.0 if sol["jornada"] == "completa" else 0.5
            
    new_request_value = 1.0 if jornada == "completa" else 0.5
    if used_days + new_request_value > 3.0:
        return "rechazado", f"Cupo anual excedido. Has usado {used_days} días de los 3 permitidos."

    # 2. Validar días prohibidos
    prohibited, reason = is_prohibited_day(fecha_inicio)
    if prohibited:
        return "rechazado", reason

    # 3. Validar días consecutivos (No pueden ser días seguidos)
    for sol in user_solicitudes:
        if sol["estado"] in ["aprobado_auto", "aprobado_manual"]:
            diff = abs((sol["fecha_inicio"] - fecha_inicio).days)
            if diff == 1:
                return "pendiente", "No se permiten permisos administrativos en días consecutivos. Requiere revisión manual."

    # 4. Validar límite institucional (Máximo 2 por día en toda la institución)
    institutional_count = 0
    for sol in all_solicitudes:
        if (sol["fecha_inicio"] == fecha_inicio and 
            sol["estado"] in ["aprobado_auto", "aprobado_manual"]):
            institutional_count += 1
            
    if institutional_count >= 2:
        return "pendiente", "Se ha alcanzado el límite de 2 permisos institucionales para este día. Requiere revisión manual."

    # 5. Todo OK -> Aprobación automática
    return "aprobado_auto", "Solicitud aprobada automáticamente por cumplir todas las reglas de negocio."
