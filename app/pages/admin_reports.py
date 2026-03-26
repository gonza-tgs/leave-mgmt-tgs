import streamlit as st
import pandas as pd
from app.database import get_supabase_admin
from app.constants import TIPO_PERMISO_LABELS, ESTADO_LABELS, JORNADA_LABELS

def render_admin_reports():
    """Renderiza el panel de reportes con filtros dinámicos."""
    st.header("📊 Reportes y Estadísticas")
    
    supabase = get_supabase_admin()
    
    # --- Filtros ---
    with st.expander("🔍 Filtros de Búsqueda", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        # 1. Obtener lista de usuarios para el filtro
        users_res = supabase.table("profiles").select("id, full_name").execute()
        users_list = {u["full_name"]: u["id"] for u in users_res.data}
        
        with col1:
            selected_user_name = st.selectbox("Usuario", options=["Todos"] + list(users_list.keys()))
            
        with col2:
            date_range = st.date_input("Rango de Fechas", value=[])
            
        with col3:
            selected_states = st.multiselect(
                "Estado", 
                options=list(ESTADO_LABELS.keys()), 
                format_func=lambda x: ESTADO_LABELS[x]
            )
            
        st.divider()
        col_sort1, col_sort2 = st.columns(2)
        with col_sort1:
            group_by_user = st.toggle("Agrupar por Usuario")
        with col_sort2:
            order_by = st.radio("Orden de Fecha", ["Descendente", "Ascendente"], horizontal=True)

    # --- Query Dinámica ---
    query = supabase.table("solicitudes").select("*, profiles(full_name, area)")
    
    # Aplicar Filtros
    if selected_user_name != "Todos":
        query = query.eq("user_id", users_list[selected_user_name])
    
    if len(date_range) == 2:
        query = query.gte("fecha_inicio", date_range[0]).lte("fecha_inicio", date_range[1])
    
    if selected_states:
        query = query.in_("estado", selected_states)
        
    order_asc = order_by == "Ascendente"
    query = query.order("fecha_inicio", desc=not order_asc)
    
    result = query.execute()
    data = result.data
    
    if not data:
        st.info("No hay registros que coincidan con los filtros seleccionados.")
        return

    # --- Procesamiento de Datos ---
    df = pd.json_normalize(data)
    
    # Mapear labels
    df["Tipo"] = df["tipo_permiso"].map(TIPO_PERMISO_LABELS)
    df["Estado"] = df["estado"].map(ESTADO_LABELS)
    df["Jornada"] = df["jornada"].map(JORNADA_LABELS)
    df["Fecha Inicio"] = pd.to_datetime(df["fecha_inicio"]).dt.strftime('%d/%m/%Y')
    
    # Renombrar columnas de perfil
    df.rename(columns={
        "profiles.full_name": "Funcionario",
        "profiles.area": "Área",
        "motivo": "Motivo",
        "admin_nota": "Nota Admin",
        "es_pagado": "Pagado"
    }, inplace=True)
    
    # Seleccionar columnas para visualización
    display_cols = ["Funcionario", "Fecha Inicio", "Tipo", "Jornada", "Estado", "Motivo", "Área", "Pagado", "Nota Admin"]
    display_df = df[display_cols].fillna("-")
    
    # --- Resultados ---
    st.subheader(f"Resultados: {len(display_df)} registros")
    
    if group_by_user:
        for user_name, user_df in display_df.groupby("Funcionario"):
            st.write(f"📂 **{user_name}**")
            st.dataframe(user_df.drop(columns="Funcionario"), use_container_width=True, hide_index=True)
    else:
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
    # --- Exportación ---
    csv = display_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        "📥 Descargar como CSV",
        data=csv,
        file_name="reporte_permisos_tgs.csv",
        mime="text/csv",
        icon="📊"
    )
