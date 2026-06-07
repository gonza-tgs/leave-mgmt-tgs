import streamlit as st
from datetime import timedelta
from app.database import get_supabase_admin, get_user_solicitudes, get_profiles_for_admin, get_feriados_internos
from app.constants import TIPO_PERMISO_LABELS, JORNADA_LABELS, ESTADO_LABELS
from app.notifications import send_approval_email, send_rejection_email
from app.services.leave_rules import is_blocked_day


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
        # Optimización: Obtener aprobaciones previas en lote para las fechas en cuestión
        fechas_pendientes = list(set([p["fecha_inicio"] for p in pendientes]))
        aprobados_por_fecha = {}
        try:
            aprobados_res = (
                supabase.table("solicitudes")
                .select("fecha_inicio")
                .eq("tipo_permiso", "administrativo")
                .in_("fecha_inicio", fechas_pendientes)
                .in_("estado", ["aprobado_auto", "aprobado_manual"])
                .execute()
            )
            for a in aprobados_res.data:
                f = a["fecha_inicio"]
                aprobados_por_fecha[f] = aprobados_por_fecha.get(f, 0) + 1
        except Exception as e:
            import logging
            logging.getLogger(__name__).error("Error al obtener aprobaciones agrupadas: %s", e)

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

                if sol["tipo_permiso"] == "administrativo":
                    aprobados_hoy = aprobados_por_fecha.get(sol["fecha_inicio"], 0)
                    if aprobados_hoy >= 2:
                        st.error(
                            f"🚨 **¡Atención!** Ya se han aprobado **{aprobados_hoy}** permisos administrativos para el día **{sol['fecha_inicio']}**. "
                            "Si apruebas esta solicitud, se superará el límite institucional sugerido de 2 permisos diarios."
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
            users_map = {f"{u.get('full_name') or 'Sin Nombre'} ({u['email']})": u["id"] for u in users_profiles}

            # Selección de tipo de registro
            tipo_registro_hist = st.radio(
                "Tipo de Registro *",
                options=["Día Único", "Rango de Fechas"],
                horizontal=True,
                key="tipo_registro_hist"
            )

            selected_user_label = st.selectbox("Usuario *", options=list(users_map.keys()), key="user_hist")
            tipo_permiso_hist = st.selectbox(
                "Tipo de Permiso *",
                options=list(TIPO_PERMISO_LABELS.keys()),
                format_func=lambda x: TIPO_PERMISO_LABELS[x],
                key="tipo_permiso_hist"
            )

            if tipo_registro_hist == "Día Único":
                fecha_hist = st.date_input("Fecha del Permiso *", value=None, key="fecha_hist")
                fecha_inicio_hist = None
                fecha_fin_hist = None
                excluir_bloqueados_hist = False
            else:
                fecha_hist = None
                col_ini, col_f = st.columns(2)
                with col_ini:
                    fecha_inicio_hist = st.date_input("Fecha de Inicio *", value=None, key="fecha_inicio_hist")
                with col_f:
                    fecha_fin_hist = st.date_input("Fecha de Fin *", value=None, key="fecha_fin_hist")
                excluir_bloqueados_hist = st.checkbox(
                    "Excluir fines de semana y feriados (nacionales e internos)",
                    value=True,
                    help="Si está marcado, solo se registrarán permisos en días hábiles (lunes a viernes, excluyendo feriados nacionales e internos). Si está desmarcado, se registrará un permiso para todos los días dentro del rango.",
                    key="excluir_bloqueados_hist"
                )

            jornada_hist = st.selectbox(
                "Jornada *",
                options=list(JORNADA_LABELS.keys()),
                format_func=lambda x: JORNADA_LABELS[x],
                key="jornada_hist"
            )
            estado_hist = st.selectbox(
                "Estado *",
                options=["aprobado_manual", "rechazado", "pendiente"],
                format_func=lambda x: ESTADO_LABELS.get(x, x),
                index=0,
                help='"Aprobado" para permisos ya otorgados; "Rechazado" para solicitudes denegadas; "Pendiente" si aún requiere revisión.',
                key="estado_hist"
            )
            motivo_hist = st.text_area("Motivo", placeholder="Motivo del permiso...", key="motivo_hist")
            admin_nota_hist = st.text_input("Nota administrativa (opcional)", placeholder="Registro histórico — abril 2025", key="admin_nota_hist")
            col_pago_hist, col_mat_hist = st.columns(2)
            with col_pago_hist:
                es_pagado_hist = st.checkbox("Permiso Remunerado (es_pagado)", value=tipo_permiso_hist in ["administrativo", "con_goce"], key="es_pagado_hist")
            with col_mat_hist:
                material_entregado_hist = st.checkbox("Material de reemplazo entregado", value=False, key="material_entregado_hist")

            submitted_hist = st.button("📋 Revisar y Confirmar", type="primary", key="btn_submitted_hist")

            if submitted_hist:
                if tipo_registro_hist == "Día Único" and not fecha_hist:
                    st.error("Debes seleccionar una fecha.")
                elif tipo_registro_hist == "Rango de Fechas" and (not fecha_inicio_hist or not fecha_fin_hist):
                    st.error("Debes seleccionar ambas fechas del rango.")
                elif tipo_registro_hist == "Rango de Fechas" and (fecha_inicio_hist > fecha_fin_hist):
                    st.error("La fecha de inicio no puede ser posterior a la fecha de fin.")
                else:
                    target_user_id = users_map[selected_user_label]
                    
                    # Generar las fechas a insertar
                    dates_to_insert = []
                    if tipo_registro_hist == "Día Único":
                        dates_to_insert = [fecha_hist]
                    else:
                        curr = fecha_inicio_hist
                        feriados = get_feriados_internos() if excluir_bloqueados_hist else []
                        while curr <= fecha_fin_hist:
                            if excluir_bloqueados_hist:
                                bloqueado, _ = is_blocked_day(curr, feriados)
                                if not bloqueado:
                                    dates_to_insert.append(curr)
                            else:
                                dates_to_insert.append(curr)
                            curr += timedelta(days=1)
                    
                    if not dates_to_insert:
                        st.error("No hay días válidos para registrar en el rango seleccionado bajo la configuración actual.")
                    else:
                        # Store pending data in session state for confirmation step
                        st.session_state["hist_pending"] = {
                            "target_user_id": target_user_id,
                            "tipo_permiso": tipo_permiso_hist,
                            "jornada": jornada_hist,
                            "estado": estado_hist,
                            "es_pagado": es_pagado_hist,
                            "material_entregado": material_entregado_hist,
                            "motivo": motivo_hist.strip() or None,
                            "admin_nota": admin_nota_hist.strip() or None,
                            "dates_to_insert": [str(d) for d in dates_to_insert],
                            "selected_user_label": selected_user_label,
                        }
                        st.rerun()

            # --- Confirmation step ---
            if st.session_state.get("hist_pending"):
                pending = st.session_state["hist_pending"]
                dates = pending["dates_to_insert"]
                n_days = len(dates)
                first_date = min(dates)
                last_date = max(dates)

                st.warning("⚠️ **Revisa los datos antes de confirmar la carga de permisos históricos.**")
                st.markdown(
                    f"""
| Campo | Valor |
|---|---|
| **Usuario** | {pending['selected_user_label']} |
| **Tipo de permiso** | {TIPO_PERMISO_LABELS.get(pending['tipo_permiso'], pending['tipo_permiso'])} |
| **Jornada** | {JORNADA_LABELS.get(pending['jornada'], pending['jornada'])} |
| **Estado** | {ESTADO_LABELS.get(pending['estado'], pending['estado'])} |
| **Días a registrar** | {n_days} |
| **Rango de fechas** | {first_date} → {last_date} |
| **Permiso remunerado** | {'✅ Sí' if pending['es_pagado'] else '❌ No'} |
| **Material de reemplazo** | {'✅ Entregado' if pending['material_entregado'] else '❌ No entregado'} |
"""
                )
                if n_days > 1:
                    st.info(f"Se registrará **1 permiso por cada día hábil** dentro del rango ({n_days} registros en total).")

                col_conf, col_cancel = st.columns(2)
                with col_conf:
                    if st.button("✅ Confirmar Registro", type="primary", key="btn_confirm_hist"):
                        try:
                            insert_data_list = []
                            for d in dates:
                                insert_data_list.append({
                                    "user_id": pending["target_user_id"],
                                    "tipo_permiso": pending["tipo_permiso"],
                                    "fecha_inicio": d,
                                    "jornada": pending["jornada"],
                                    "estado": pending["estado"],
                                    "es_pagado": pending["es_pagado"],
                                    "material_entregado": pending["material_entregado"],
                                    "motivo": pending["motivo"],
                                    "admin_nota": pending["admin_nota"],
                                })
                            supabase.table("solicitudes").insert(insert_data_list).execute()
                            get_user_solicitudes.clear()
                            del st.session_state["hist_pending"]
                            st.success(f"✅ Permiso histórico registrado correctamente ({n_days} días registrados para {pending['selected_user_label']}).")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error al registrar permiso histórico: {e}")
                with col_cancel:
                    if st.button("❌ Cancelar", key="btn_cancel_hist"):
                        del st.session_state["hist_pending"]
                        st.rerun()

    # --- Eliminar o Cancelar Permisos Registrados ---
    st.divider()
    with st.expander("🗑️ Eliminar o Cancelar Permisos Registrados", expanded=False):
        st.caption(
            "Usa esta sección para eliminar de forma definitiva cualquier permiso registrado en la base de datos "
            "(ya sea pendiente, aprobado o rechazado). Esta acción no se puede deshacer."
        )

        if is_read_only:
            st.warning("Modo Solo Lectura: No puedes eliminar permisos.")
        else:
            # Obtener lista de usuarios para búsqueda
            users_profiles = get_profiles_for_admin()
            users_map_del = {f"{u.get('full_name') or 'Sin Nombre'} ({u['email']})": u["id"] for u in users_profiles}
            
            selected_user_del_label = st.selectbox(
                "Buscar por Funcionario (opcional)", 
                options=["Todos"] + list(users_map_del.keys()),
                key="selectbox_del_user"
            )

            # Query de las últimas solicitudes
            try:
                query_del = supabase.table("solicitudes").select("*, profiles(full_name, email)")
                if selected_user_del_label != "Todos":
                    query_del = query_del.eq("user_id", users_map_del[selected_user_del_label])
                
                # Obtenemos las últimas 25 solicitudes registradas
                result_del = query_del.order("created_at", desc=True).limit(25).execute()
                recent_solicitudes = result_del.data or []

                if not recent_solicitudes:
                    st.info("No se encontraron solicitudes registradas.")
                else:
                    st.write(f"Mostrando los últimos {len(recent_solicitudes)} registros:")
                    for sol in recent_solicitudes:
                        profile = sol.get("profiles") or {}
                        tipo_label = TIPO_PERMISO_LABELS.get(sol['tipo_permiso'], sol['tipo_permiso'])
                        estado_label = ESTADO_LABELS.get(sol['estado'], sol['estado'])
                        
                        col_info, col_btn = st.columns([4, 1])
                        with col_info:
                            st.markdown(
                                f"**{profile.get('full_name') or 'Sin Nombre'}** — Fecha: **{sol['fecha_inicio']}** "
                                f"({JORNADA_LABELS.get(sol['jornada'], sol['jornada'])})  \n"
                                f"🏷️ *Tipo:* {tipo_label} | *Estado:* `{estado_label}`"
                            )
                            if sol.get("motivo"):
                                st.caption(f"💬 *Motivo:* {sol['motivo']}")
                            if sol.get("admin_nota"):
                                st.caption(f"📝 *Nota Admin:* {sol['admin_nota']}")
                        
                        with col_btn:
                            if st.button("Eliminar", key=f"btn_del_{sol['id']}", type="secondary", icon="🗑️"):
                                try:
                                    supabase.table("solicitudes").delete().eq("id", sol["id"]).execute()
                                    get_user_solicitudes.clear()
                                    st.success(f"Permiso eliminado correctamente.")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error al eliminar: {e}")
                        st.divider()
            except Exception as e:
                st.error(f"Error al cargar registros: {e}")
