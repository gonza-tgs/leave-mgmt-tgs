import streamlit as st
from app.auth import is_authenticated, render_login_page, handle_auth_callback

# Configuración de la página (Debe ser el primer comando de Streamlit)
st.set_page_config(
    page_title="Quiero mi Permiso!",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Manejo de callback de auth si existe
handle_auth_callback()

if not is_authenticated():
    render_login_page()
    st.stop()

# Si está autenticado, mostramos la navegación
user = st.session_state["user"]
st.sidebar.title(f"Bienvenido, {user.get('full_name', 'Usuario')}")

# Opciones de navegación basadas en el rol
nav_options = ["🏠 Mi Historial", "📝 Solicitar Permiso"]

if user.get("rol") in ["admin", "admin_read_only"]:
    st.sidebar.divider()
    st.sidebar.subheader("Panel de Administración")
    nav_options += ["✅ Gestión de Permisos", "📊 Reportes"]
    if user.get("rol") == "admin":
        nav_options += ["👥 Usuarios", "📅 Días No Laborables"]

page = st.sidebar.radio("Navegación", nav_options)

from app.pages.dashboard import render_dashboard
from app.pages.submit_request import render_submit_request
from app.pages.admin_panel import render_admin_panel
from app.pages.admin_reports import render_admin_reports
from app.pages.admin_users import render_admin_users
from app.pages.admin_feriados import render_admin_feriados


# Routing de páginas
if page == "🏠 Mi Historial":
    render_dashboard(user)
elif page == "📝 Solicitar Permiso":
    render_submit_request(user)
elif page == "✅ Gestión de Permisos":
    render_admin_panel(user)
elif page == "📊 Reportes":
    render_admin_reports()
elif page == "👥 Usuarios":
    render_admin_users()
elif page == "📅 Días No Laborables":
    render_admin_feriados(user)

st.sidebar.divider()
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()
