import streamlit as st
from datetime import date
from app.database import (
    get_feriados_internos, add_feriado_interno, delete_feriado_interno,
    get_periodos_bloqueados, add_periodo_bloqueado, delete_periodo_bloqueado
)


def render_admin_feriados(user):
    """Página para que el admin gestione los días no laborables internos y periodos bloqueados."""
    st.header("📅 Días No Laborables Internos")
    st.caption(
        "Define fechas específicas en las que no se permite solicitar permisos "
        "(ej. cierre de año, feriados propios del establecimiento)."
    )

    is_read_only = user.get("rol") == "admin_read_only"
    feriados = get_feriados_internos()

    if feriados:
        st.subheader("Días registrados")
        for f in feriados:
            col_fecha, col_desc, col_btn = st.columns([2, 5, 1])
            col_fecha.write(f["fecha"])
            col_desc.write(f.get("descripcion") or "—")
            if col_btn.button("🗑️", key=f"del_{f['id']}", help="Eliminar", disabled=is_read_only):
                delete_feriado_interno(f["id"])
                st.rerun()
    else:
        st.info("No hay días no laborables internos registrados.")

    st.divider()

    st.subheader("Agregar día no laborable")
    with st.form("form_feriado"):
        nueva_fecha = st.date_input(
            "Fecha",
            min_value=date.today(),
            max_value=date(date.today().year + 2, 12, 31),
            disabled=is_read_only
        )
        descripcion = st.text_input("Descripción (opcional)", max_chars=100,
                                    placeholder="ej. Cierre fin de año escolar",
                                    disabled=is_read_only)
        guardar = st.form_submit_button("Guardar", icon="💾", disabled=is_read_only)

        if guardar:
            fechas_existentes = {f["fecha"] for f in feriados}
            if str(nueva_fecha) in fechas_existentes:
                st.error("Esa fecha ya está registrada.")
            else:
                add_feriado_interno(str(nueva_fecha), descripcion.strip(), user["id"])
                st.success(f"Día no laborable {nueva_fecha} agregado correctamente.")
                st.rerun()

    st.divider()

    # --- Periodos Bloqueados (Rangos de Fechas) ---
    st.header("🚫 Periodos Bloqueados")
    st.caption(
        "Define rangos de fechas en los que no se autoriza ningún permiso "
        "(ej. del 15 al 30 de diciembre)."
    )

    periodos = get_periodos_bloqueados()

    if periodos:
        st.subheader("Periodos registrados")
        for p in periodos:
            col_rango, col_desc, col_btn = st.columns([3, 4, 1])
            col_rango.write(f"{p['fecha_inicio']} → {p['fecha_fin']}")
            col_desc.write(p.get("descripcion") or "—")
            if col_btn.button("🗑️", key=f"delp_{p['id']}", help="Eliminar", disabled=is_read_only):
                delete_periodo_bloqueado(p["id"])
                st.rerun()
    else:
        st.info("No hay periodos bloqueados registrados.")

    st.divider()

    st.subheader("Agregar periodo bloqueado")
    with st.form("form_periodo"):
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            fecha_inicio = st.date_input(
                "Fecha inicio",
                min_value=date.today(),
                max_value=date(date.today().year + 2, 12, 31),
                disabled=is_read_only,
                key="periodo_inicio"
            )
        with col_f2:
            fecha_fin = st.date_input(
                "Fecha fin",
                min_value=date.today(),
                max_value=date(date.today().year + 2, 12, 31),
                disabled=is_read_only,
                key="periodo_fin"
            )
        desc_periodo = st.text_input("Descripción (opcional)", max_chars=100,
                                     placeholder="ej. Vacaciones de invierno",
                                     disabled=is_read_only,
                                     key="periodo_desc")
        guardar_periodo = st.form_submit_button("Guardar Periodo", icon="💾", disabled=is_read_only)

        if guardar_periodo:
            if fecha_fin < fecha_inicio:
                st.error("La fecha fin debe ser posterior o igual a la fecha inicio.")
            else:
                add_periodo_bloqueado(str(fecha_inicio), str(fecha_fin), desc_periodo.strip(), user["id"])
                st.success(f"Periodo bloqueado agregado correctamente.")
                st.rerun()
