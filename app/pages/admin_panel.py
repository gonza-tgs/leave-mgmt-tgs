import streamlit as st
import pandas as pd
from app.database import get_supabase_admin, get_user_solicitudes
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS
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
        return

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

            if btn_col2.button(
                "Rechazar",
                key=f"reject_{sol['id']}",
                type="secondary",
                disabled=is_read_only,
            ):
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
