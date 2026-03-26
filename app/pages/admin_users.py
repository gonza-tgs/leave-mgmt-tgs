import streamlit as st
from app.database import get_supabase_admin
from app.constants import ROL_LABELS

def render_admin_users():
    """Renderiza el panel de gestión de usuarios y roles."""
    st.header("👥 Gestión de Usuarios y Roles")
    
    supabase = get_supabase_admin()
    
    # Query de perfiles
    result = supabase.table("profiles").select("*").order("full_name").execute()
    users = result.data
    
    if not users:
        st.warning("No se encontraron usuarios en el sistema.")
        return

    st.write(f"Mostrando {len(users)} usuarios registrados.")
    
    # Contar administradores para prevenir degradar al último
    admins_count = len([u for u in users if u["rol"] == "admin"])
    
    for u in users:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 2])
            
            with col1:
                st.write(f"**{u['full_name']}**")
                st.caption(f"{u['email']} | Área: {u.get('area', 'Sin asignar')}")
                
            with col2:
                # Selector de Rol
                new_rol = st.selectbox(
                    "Rol",
                    options=list(ROL_LABELS.keys()),
                    format_func=lambda x: ROL_LABELS[x],
                    index=list(ROL_LABELS.keys()).index(u["rol"]),
                    key=f"rol_{u['id']}"
                )
            
            with col3:
                # Botón Guardar si el rol cambió
                if new_rol != u["rol"]:
                    # Validar si es el último admin
                    if u["rol"] == "admin" and admins_count <= 1 and new_rol != "admin":
                        st.error("No puedes quitar el rol de administrador al último administrador del sistema.")
                    else:
                        if st.button("Guardar", key=f"save_{u['id']}", type="primary"):
                            supabase.table("profiles").update({"rol": new_rol}).eq("id", u["id"]).execute()
                            st.success("Rol actualizado.")
                            st.rerun()
            st.divider()
