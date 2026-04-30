import streamlit as st
from app.database import get_supabase_admin, get_user_solicitudes, get_profiles_for_admin
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS, ESTADO_LABELS
from app.notifications import send_approval_email, send_rejection_email


def render_admin_panel(user):
    """Renderiza el panel de gestión de permisos para administradores."""
    st.header("✅ Gestión de Solicitudes Pendientes")

    is_read_only = user.get("rol") == "admin_read_only"
    if is_read_only:
        st.info("Modo Solo Lectura: No puedes aprobar o rechazar solicitudes.")

    supabase = get_supabase_admin()

    result = (
        supabase.table("solicitudes")
        .select("*, profiles(full_name, email, area)")
        .eq("estado", "pendiente")
        .order("fecha_inicio")
        .execute()
    )

    pendientes = result.data

    if not pendientes:
        st.success("No hay solicitudes pendientes de revisión.")
    else:
        st.write(f"Hay {len(pendientes)} solicitudes esperando tu revisión.")

        for sol in pendientes:
            # FIXED: #3 — guard against profiles being None from Supabase join
            profile = sol.get("profiles") or {}
            tipo_label = TIPO_PERMISO_LABELS.get(sol['tipo_permiso'], sol['tipo_permiso'])
            with st.expander(f"📝 {profile.get('full_name')} - {sol['fecha_inicio']} ({tipo_label})"):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Email:** {profile.get('email')}")
                    st.write(f"**Área:** {profile.get('area', 'No definida')}")
                    st.write(f"**Tipo:** {TIPO_PERMISO_LABELS.get(sol['tipo_permiso'])}")

                with col2:
                    st.write(f"**Fecha:** {sol['fecha_inicio']}")
                    st.write(f"**Jornada:** {JORNADA_LABELS.get(sol['jornada'])}")
                    st.write(f"**Motivo Usuario:** {sol.get('motivo', 'Sin motivo')}")

                if sol.get("admin_nota") and sol["admin_nota"].startswith("SISTEMA:"):
                    st.warning(
                        f"⚠️ **Derivación Automática:** {sol['admin_nota'].replace('SISTEMA: ', '')}"
                    )

                st.divider()

                col_mat, col_pago = st.columns(2)

                with col_mat:
                    material_entregado = st.toggle(
                        "Material de reemplazo entregado",
                        value=sol.get("material_entregado", False),
                        key=f"mat_{sol['id']}",
                        disabled=is_read_only,
                        help="Marca si el docente entregó el material de reemplazo para el día del permiso."
                    )

                with col_pago:
                    es_pagado = sol["es_pagado"]
                    if sol["tipo_permiso"] in ["con_goce", "sin_goce"]:
                        es_pagado = st.toggle(
                            "Procesar con Pago (Remunerado)",
                            value=sol["es_pagado"],
                            key=f"pay_{sol['id']}",
                            disabled=is_read_only,
                        )

                admin_nota_input = st.text_input(
                    "Nota administrativa (opcional)",
                    key=f"note_{sol['id']}",
                    disabled=is_read_only,
                    placeholder="Escribe aquí el motivo de la decisión...",
                )

                btn_col1, btn_col2, _ = st.columns([1, 1, 2])

                if btn_col1.button(
                    "Aprobar",
                    key=f"approve_{sol['id']}",
                    type="primary",
                    disabled=is_read_only,
                ):
                    try:
                        update_data = {
                            "estado": "aprobado_manual",
                            "es_pagado": es_pagado,
                            "material_entregado": material_entregado,
                            "admin_nota": admin_nota_input,
                        }
                        supabase.table("solicitudes").update(update_data).eq(
                            "id", sol["id"]
                        ).execute()
                        get_user_solicitudes.clear()
                        if profile.get("email"):
                            send_approval_email(sol, profile)
                        st.success("Solicitud APROBADA.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al aprobar: {e}")

                if btn_col2.button(
                    "Rechazar",
                    key=f"reject_{sol['id']}",
                    type="secondary",
                    disabled=is_read_only,
                ):
                    try:
                        update_data = {
                            "estado": "rechazado",
                            "material_entregado": material_entregado,
                            "admin_nota": admin_nota_input,
                        }
                        supabase.table("solicitudes").update(update_data).eq(
                            "id", sol["id"]
                        ).execute()
                        get_user_solicitudes.clear()
                        if profile.get("email"):
                            send_rejection_email(sol, profile, admin_nota_input)
                        st.error("Solicitud RECHAZADA.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error al rechazar: {e}")

    # --- Registrar Permiso Histórico (backfill) ---
    st.divider()
    with st.expander("📋 Registrar Permiso Ya Otorgado (histórico)", expanded=False):
        st.caption(
            "Usa esta sección para registrar permisos que fueron otorgados antes de "
            "poner la app en producción. No se aplican validaciones ni se envían notificaciones."
        )

        if is_read_only:
            st.warning("Modo Solo Lectura: No puedes registrar permisos históricos.")
        else:
            users_profiles = get_profiles_for_admin()
            users_map = {f"{u['full_name']} ({u['email']})": u["id"] for u in users_profiles}

            with st.form("form_historico"):
                selected_user_label = st.selectbox("Usuario *", options=list(users_map.keys()))
                tipo_permiso_hist = st.selectbox(
                    "Tipo de Permiso *",
                    options=list(TIPO_PERMISO_LABELS.keys()),
                    format_func=lambda x: TIPO_PERMISO_LABELS[x],
                )
                fecha_hist = st.date_input("Fecha del Permiso *", value=None)
                jornada_hist = st.selectbox(
                    "Jornada *",
                    options=list(JORNADA_LABELS.keys()),
                    format_func=lambda x: JORNADA_LABELS[x],
                )
                estado_hist = st.selectbox(
                    "Estado *",
                    options=["aprobado_manual", "rechazado", "pendiente"],
                    format_func=lambda x: ESTADO_LABELS.get(x, x),
                    index=0,
                    help='"Aprobado" para permisos ya otorgados; "Rechazado" para solicitudes denegadas; "Pendiente" si aún requiere revisión.',
                )
                motivo_hist = st.text_area("Motivo", placeholder="Motivo del permiso...")
                admin_nota_hist = st.text_input("Nota administrativa (opcional)", placeholder="Registro histórico — abril 2025")
                col_pago_hist, col_mat_hist = st.columns(2)
                with col_pago_hist:
                    es_pagado_hist = st.checkbox("Permiso Remunerado (es_pagado)", value=tipo_permiso_hist in ["administrativo", "con_goce"])
                with col_mat_hist:
                    material_entregado_hist = st.checkbox("Material de reemplazo entregado", value=False)

                submitted_hist = st.form_submit_button("Registrar Permiso", icon="📋")

                if submitted_hist:
                    if not fecha_hist:
                        st.error("Debes seleccionar una fecha.")
                    else:
                        target_user_id = users_map[selected_user_label]
                        insert_data = {
                            "user_id": target_user_id,
                            "tipo_permiso": tipo_permiso_hist,
                            "fecha_inicio": str(fecha_hist),
                            "jornada": jornada_hist,
                            "estado": estado_hist,
                            "es_pagado": es_pagado_hist,
                            "material_entregado": material_entregado_hist,
                            "motivo": motivo_hist.strip() or None,
                            "admin_nota": admin_nota_hist.strip() or None,
                        }
                        try:
                            supabase.table("solicitudes").insert(insert_data).execute()
                            get_user_solicitudes.clear()
                            st.success("Permiso histórico registrado correctamente.")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar permiso histórico: {e}")
