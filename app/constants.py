TIPO_PERMISO_LABELS = {
    "administrativo": "Permiso Administrativo",
    "con_goce":       "Con Goce de Sueldo",
    "sin_goce":       "Sin Goce de Sueldo",
}

ESTADO_LABELS = {
    "pendiente":       "Pendiente",
    "aprobado_auto":   "Aprobado",
    "aprobado_manual": "Aprobado",
    "rechazado":       "Rechazado",
}

JORNADA_LABELS = {
    "completa": "Jornada Completa",
    "manana":   "Mañana",
    "tarde":    "Tarde",
}

ROL_LABELS = {
    "user": "Usuario",
    "admin": "Administrador",
    "admin_read_only": "Administrador (Solo Lectura)",
}


# --- Textos informativos para el usuario ---

CONDICIONES_GENERALES = """
### Condiciones generales (aplican a todos los permisos)

- **Anticipación:** La solicitud debe hacerse con al menos **14 días** de anticipación. Solicitudes con menos tiempo serán rechazadas automáticamente.
- **Días bloqueados:** No se permiten permisos en fines de semana, feriados nacionales, días no laborables internos definidos por la administración, ni dentro de periodos bloqueados.
"""

CONDICIONES_ADMINISTRATIVO = """
### Permiso Administrativo

- **Cupo anual:** Máximo **3 días** por año. Media jornada cuenta como 0.5 días.
- **Días prohibidos:** No se permiten permisos administrativos los días **lunes**, **viernes**, vísperas de feriado ni días posteriores a un feriado.
- **Días consecutivos:** No se permiten permisos administrativos en días consecutivos a otros ya aprobados. Si ocurre, la solicitud queda pendiente de revisión.
- **Límite institucional:** Máximo **2 permisos administrativos** por día en toda la institución. Si se alcanza, la solicitud queda pendiente de revisión.
- **Material de reemplazo:** Debes entregar material para el día solicitado. La administradora verificará este requisito.
"""

CONDICIONES_CON_GOCE = """
### Permiso Con Goce de Sueldo

Debes indicar el **motivo específico** por el cual solicitas este permiso. Las condiciones legales para acceder son:

**Fallecimiento de familiares directos** (días corridos desde el fallecimiento):
- Hijo/a: **10 días**
- Cónyuge o conviviente civil: **7 días**
- Hijo/a en gestación: **7 días hábiles** (con certificado de defunción fetal)
- Padre, madre o hermano/a: **4 días hábiles**

**Permisos parentales:**
- Nacimiento (padre): **5 días** pagados, continuos o distribuidos dentro del primer mes
- Emergencias TEA: tutores de menores con trastorno del espectro autista para emergencias en el establecimiento educacional

**Salud y prevención:**
- Exámenes preventivos (próstata, mamografía, Papanicolaou): **medio día** al año (aviso con 1 semana de anticipación y comprobante posterior)
- Vacunación en campañas públicas: **medio día** (aviso con 2 días de anticipación)
"""

CONDICIONES_SIN_GOCE = """
### Permiso Sin Goce de Sueldo

Para situaciones personales que no califican en las categorías anteriores. Debes indicar claramente el **motivo** de tu solicitud.
"""

# --- Sugerencias para rechazos automáticos ---

SUGERENCIA_RECHAZO_ANTICIPACION = """
💡 **Sugerencia:** Los permisos requieren al menos 14 días de anticipación. Si tu situación es urgente y califica dentro de las causales de *Con Goce de Sueldo* (fallecimiento, parental, salud) o necesitas un *Sin Goce de Sueldo*, puedes intentar con esos tipos de permiso indicando claramente el motivo.
"""

SUGERENCIA_RECHAZO_BLOQUEO = """
💡 **Sugerencia:** La fecha seleccionada no está disponible para permisos. Intenta seleccionar un día hábil que no sea feriado ni esté dentro de un periodo bloqueado por la administración.
"""

SUGERENCIA_RECHAZO_ADMIN = """
💡 **Sugerencia:** Este permiso no califica como *Administrativo*. Si tu situación corresponde a una de las causales de *Con Goce de Sueldo* (fallecimiento de familiar, nacimiento, salud, vacunación), selecciona esa opción. De lo contrario, puedes solicitar un permiso *Sin Goce de Sueldo* indicando el motivo.
"""

SUGERENCIA_RECHAZO_GENERAL = """
💡 **Sugerencia:** Revisa las condiciones en la sección *Requisitos y condiciones* al inicio del formulario. Si tu situación corresponde a una causal de *Con Goce de Sueldo* o *Sin Goce de Sueldo*, intenta con ese tipo de permiso.
"""
