import streamlit as st
from datetime import date, timedelta
from app.database import insert_solicitud, get_user_solicitudes, get_supabase_admin, get_admin_emails, get_feriados_internos
from app.services.leave_rules import evaluate_auto_approval, is_blocked_day
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS
from app.notifications import send_new_request_email, send_approval_email, send_rejection_email

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
        
        # Motivo (obligatorio)
        MOTIVO_OPCIONES = ["Trámites", "Médicos", "Personal", "Otro"]
        motivo_tipo = st.selectbox("Motivo *", options=MOTIVO_OPCIONES)

        motivo_detalle = ""
        if motivo_tipo == "Otro":
            motivo_detalle = st.text_input("Especificar motivo *", max_chars=300)

        submit_button = st.form_submit_button("Enviar Solicitud", icon="📤")

        if submit_button:
            if motivo_tipo == "Otro" and not motivo_detalle.strip():
                st.error("Por favor especifica el motivo.")
                st.stop()

            feriados = get_feriados_internos()
            bloqueado, razon_bloqueo = is_blocked_day(fecha_inicio, feriados)
            if bloqueado:
                st.error(f"Fecha no válida: {razon_bloqueo}")
                st.stop()

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
                    admin_nota = ""
                    if tipo_permiso == "administrativo":
                        estado, razon = evaluate_auto_approval(
                            user["id"], fecha_inicio, jornada, user_solicitudes, all_solicitudes
                        )
                        if estado == "pendiente":
                            admin_nota = f"SISTEMA: {razon}"
                    
                    # Preparar datos para insertar
                    # Determinar es_pagado por defecto
                    # administrativo/con_goce -> true; sin_goce -> false
                    es_pagado = tipo_permiso in ["administrativo", "con_goce"]
                    
                    motivo = motivo_tipo if motivo_tipo != "Otro" else f"Otro: {motivo_detalle.strip()}"

                    solicitud_data = {
                        "user_id": user["id"],
                        "tipo_permiso": tipo_permiso,
                        "fecha_inicio": str(fecha_inicio),
                        "jornada": jornada,
                        "estado": estado,
                        "es_pagado": es_pagado,
                        "motivo": motivo,
                        "admin_nota": admin_nota
                    }
                    
                    insert_solicitud(solicitud_data)

                    # Notificaciones por correo
                    if estado == "aprobado_auto":
                        send_approval_email(solicitud_data, user)
                    elif estado == "pendiente":
                        admin_emails = get_admin_emails()
                        send_new_request_email(solicitud_data, user, admin_emails)
                    elif estado == "rechazado":
                        send_rejection_email(solicitud_data, user, razon)

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
