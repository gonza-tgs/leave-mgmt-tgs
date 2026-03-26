import streamlit as st
from datetime import date, timedelta
from app.database import insert_solicitud, get_user_solicitudes, get_supabase_admin, get_admin_emails
from app.services.leave_rules import evaluate_auto_approval
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS
from app.notifications import send_new_request_email, send_approval_email

def render_submit_request(user):
    """Renderiza el formulario para nueva solicitud."""
    st.header("Nueva Solicitud de Permiso")
    
    with st.form("request_form"):
        # Selección de tipo de permiso
        tipo_permiso = st.selectbox(
            "Tipo de Permiso",
            options=list(TIPO_PERMISO_LABELS.keys()),
            format_func=lambda x: TIPO_PERMISO_LABELS[x]
        )
        
        # Selección de fecha (mínimo hoy, máximo +90 días)
        fecha_inicio = st.date_input(
            "Fecha del Permiso",
            min_value=date.today(),
            max_value=date.today() + timedelta(days=90),
            help="Puedes solicitar permisos hasta con 90 días de anticipación."
        )
        
        # Selección de jornada
        jornada = st.radio(
            "Jornada",
            options=list(JORNADA_LABELS.keys()),
            format_func=lambda x: JORNADA_LABELS[x],
            horizontal=True
        )
        
        # Motivo (opcional)
        motivo = st.text_area("Motivo o detalles (opcional)", max_chars=300)
        
        submit_button = st.form_submit_button("Enviar Solicitud", icon="📤")
        
        if submit_button:
            # Procesar solicitud
            with st.spinner("Procesando solicitud..."):
                try:
                    # Datos iniciales para evaluación
                    # Nota: Para evaluar reglas institucionales, necesitaríamos todas las solicitudes.
                    # En este paso, fetch de todas las solicitudes de la DB.
                    supabase_admin = get_supabase_admin()
                    all_solicitudes_raw = supabase_admin.table("solicitudes").select("*").execute()
                    all_solicitudes = all_solicitudes_raw.data
                    
                    user_solicitudes = [s for s in all_solicitudes if s["user_id"] == user["id"]]
                    
                    estado = "pendiente"
                    razon = "Solicitud enviada para revisión manual."
                    
                    # Si es administrativo, evaluar auto-aprobación
                    if tipo_permiso == "administrativo":
                        estado, razon = evaluate_auto_approval(
                            user["id"], fecha_inicio, jornada, user_solicitudes, all_solicitudes
                        )
                    
                    # Preparar datos para insertar
                    # Determinar es_pagado por defecto
                    # administrativo/con_goce -> true; sin_goce -> false
                    es_pagado = tipo_permiso in ["administrativo", "con_goce"]
                    
                    solicitud_data = {
                        "user_id": user["id"],
                        "tipo_permiso": tipo_permiso,
                        "fecha_inicio": str(fecha_inicio),
                        "jornada": jornada,
                        "estado": estado,
                        "es_pagado": es_pagado,
                        "motivo": motivo
                    }
                    
                    insert_solicitud(solicitud_data)

                    # Notificaciones por correo
                    if estado == "aprobado_auto":
                        send_approval_email(solicitud_data, user)
                    else:
                        admin_emails = get_admin_emails()
                        send_new_request_email(solicitud_data, user, admin_emails)

                    # Mostrar resultado
                    if estado == "aprobado_auto":
                        st.success(f"✅ ¡Solicitud Aprobada Automáticamente!\n\n{razon}")
                        st.balloons()
                    elif estado == "pendiente":
                        st.warning(f"⏳ Solicitud Enviada para Revisión.\n\n{razon}")
                    elif estado == "rechazado":
                        st.error(f"❌ Solicitud Rechazada.\n\n{razon}")
                        
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar tu solicitud: {str(e)}")
