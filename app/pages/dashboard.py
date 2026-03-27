import streamlit as st
import pandas as pd
from app.database import get_user_solicitudes
from app.constants import TIPO_PERMISO_LABELS, ESTADO_LABELS, JORNADA_LABELS

def render_dashboard(user):
    """Renderiza el historial personal y métricas del usuario."""
    st.header(f"Bienvenido, {user.get('full_name')}")
    
    # Obtener solicitudes
    solicitudes = get_user_solicitudes(user["id"])
    
    # Calcular días administrativos usados (aprobados + pendientes)
    current_year = pd.Timestamp.now().year
    approved_days = 0.0
    pending_days = 0.0

    for sol in solicitudes:
        if (sol["tipo_permiso"] == "administrativo" and
                pd.to_datetime(sol["fecha_inicio"]).year == current_year):
            value = 1.0 if sol["jornada"] == "completa" else 0.5
            if sol["estado"] in ["aprobado_auto", "aprobado_manual"]:
                approved_days += value
            elif sol["estado"] == "pendiente":
                pending_days += value

    used_days = approved_days + pending_days
    remaining_days = max(0.0, 3.0 - used_days)

    # Mostrar métricas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Días admin. disponibles", f"{remaining_days} / 3.0")
    with col2:
        st.metric("Días usados (aprobados)", f"{approved_days}")
    with col3:
        st.metric("Días en revisión", f"{pending_days}")

    st.divider()
    
    if not solicitudes:
        st.info("Aún no tienes solicitudes registradas.")
        return

    # Preparar DataFrame para visualización
    df = pd.DataFrame(solicitudes)
    
    # Mapear labels en español
    df["Tipo"] = df["tipo_permiso"].map(TIPO_PERMISO_LABELS)
    df["Estado"] = df["estado"].map(ESTADO_LABELS)
    df["Jornada"] = df["jornada"].map(JORNADA_LABELS)
    df["Fecha Inicio"] = pd.to_datetime(df["fecha_inicio"]).dt.strftime('%d/%m/%Y')
    
    # Seleccionar y renombrar columnas
    display_df = df[["Fecha Inicio", "Tipo", "Jornada", "Estado", "motivo"]].copy()
    display_df.columns = ["Fecha", "Tipo de Permiso", "Jornada", "Estado", "Motivo"]
    
    # Manejar valores nulos para evitar bug de visualización
    display_df = display_df.fillna("-")
    
    st.subheader("Mi Historial")
    st.dataframe(display_df, width='stretch', hide_index=True)
