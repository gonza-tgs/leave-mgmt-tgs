import streamlit as st
import pandas as pd
from app.database import get_supabase_admin
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS

def render_admin_panel():
    """Renderiza el panel de gestión de permisos para administradores."""
    st.header("✅ Gestión de Solicitudes Pendientes")
    
    supabase = get_supabase_admin()
    
    # Query de solicitudes pendientes con información del perfil
    # En una implementación real, se usaría un Join o una vista
    result = supabase.table("solicitudes")\
        .select("*, profiles(full_name, email, area)")\
        .eq("estado", "pendiente")\
        .order("fecha_inicio")\
        .execute()
    
    pendientes = result.data
    
    if not pendientes:
        st.success("No hay solicitudes pendientes de revisión.")
        return

    st.write(f"Hay {len(pendientes)} solicitudes esperando tu revisión.")
    
    for sol in pendientes:
        profile = sol.get("profiles", {})
        with st.expander(f"📝 {profile.get('full_name')} - {sol['fecha_inicio']}"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Email:** {profile.get('email')}")
                st.write(f"**Área:** {profile.get('area', 'No definida')}")
                st.write(f"**Tipo:** {TIPO_PERMISO_LABELS.get(sol['tipo_permiso'])}")
            
            with col2:
                st.write(f"**Fecha:** {sol['fecha_inicio']}")
                st.write(f"**Jornada:** {JORNADA_LABELS.get(sol['jornada'])}")
                st.write(f"**Motivo:** {sol.get('motivo', 'Sin motivo')}")
            
            st.divider()
            
            # Opción de Pago (Solo para Con Goce / Sin Goce)
            es_pagado = sol["es_pagado"]
            if sol["tipo_permiso"] in ["con_goce", "sin_goce"]:
                es_pagado = st.toggle(
                    "Procesar con Pago (Remunerado)", 
                    value=sol["es_pagado"], 
                    key=f"pay_{sol['id']}"
                )
            
            admin_nota = st.text_input("Nota administrativa (opcional)", key=f"note_{sol['id']}")
            
            btn_col1, btn_col2, _ = st.columns([1, 1, 2])
            
            if btn_col1.button("Aprobar", key=f"approve_{sol['id']}", type="primary"):
                update_data = {
                    "estado": "aprobado_manual",
                    "es_pagado": es_pagado,
                    "admin_nota": admin_nota
                }
                supabase.table("solicitudes").update(update_data).eq("id", sol["id"]).execute()
                st.success("Solicitud APROBADA.")
                st.rerun()
                
            if btn_col2.button("Rechazar", key=f"reject_{sol['id']}", type="secondary"):
                update_data = {
                    "estado": "rechazado",
                    "admin_nota": admin_nota
                }
                supabase.table("solicitudes").update(update_data).eq("id", sol["id"]).execute()
                st.error("Solicitud RECHAZADA.")
                st.rerun()
