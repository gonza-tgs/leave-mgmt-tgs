import streamlit as st
from app.database import get_supabase, get_user_profile
from app.config import ALLOWED_DOMAIN

def validate_domain(email: str) -> bool:
    """Verifica si el correo pertenece al dominio permitido."""
    return email.endswith(f"@{ALLOWED_DOMAIN}")

def sign_in_with_google():
    """Inicia el flujo de autenticación con Google."""
    supabase = get_supabase()
    # En producción se debe configurar la URL de redirección en Supabase
    response = supabase.auth.sign_in_with_oauth({
        "provider": "google",
        "options": {
            "redirect_to": st.secrets.get("REDIRECT_URL", "http://localhost:8501")
        }
    })
    if response:
        st.info("Redirigiendo a Google...")
        # Streamlit no puede redirigir automáticamente por seguridad, 
        # se suele usar un link o que el usuario sea redirigido por la respuesta del API.

def handle_auth_callback():
    """Maneja el retorno de OAuth desde la URL."""
    # Nota: Supabase Auth suele manejar la sesión en el cliente (browser)
    # Para Streamlit SSR, capturamos el access_token si viene en la URL o fragmento.
    query_params = st.query_params
    if "access_token" in query_params:
        # Aquí se debería intercambiar el token o establecer la sesión en el cliente Supabase
        pass

def is_authenticated() -> bool:
    """Verifica si hay un usuario autenticado en st.session_state."""
    return "user" in st.session_state

def require_role(role: str):
    """Asegura que el usuario tenga el rol requerido."""
    if not is_authenticated():
        st.error("Debes iniciar sesión.")
        st.stop()
    if st.session_state["user"].get("rol") != role:
        st.error("No tienes permisos para acceder a esta página.")
        st.stop()

def render_login_page():
    """Muestra la UI de inicio de sesión."""
    st.title("Bienvenido al Colegio TGS")
    st.subheader("Gestión de Permisos Laborales")
    st.write("Por favor, inicia sesión con tu cuenta institucional para continuar.")
    
    if st.button("Iniciar sesión con Google", icon="🔑"):
        sign_in_with_google()
