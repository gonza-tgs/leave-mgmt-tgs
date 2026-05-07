import streamlit as st
from supabase import create_client
from app.database import get_user_profile, create_user_profile
from app.config import ALLOWED_DOMAIN, SUPABASE_URL, SUPABASE_KEY

def _get_session_auth_client():
    """Obtiene (o crea) un cliente Supabase por sesión para OAuth.
    PKCE requiere que el mismo objeto que generó la URL también intercambie el código."""
    if "supabase_auth_client" not in st.session_state:
        st.session_state["supabase_auth_client"] = create_client(SUPABASE_URL, SUPABASE_KEY)
    return st.session_state["supabase_auth_client"]

def validate_domain(email: str) -> bool:
    """Verifica si el correo pertenece al dominio permitido."""
    return email.split("@")[-1] == ALLOWED_DOMAIN

def _get_oauth_url() -> str | None:
    """Genera y cachea la URL OAuth en session_state para esta sesión."""
    if "oauth_url" not in st.session_state:
        supabase = _get_session_auth_client()
        redirect_url = st.secrets.get("REDIRECT_URL", "http://localhost:8501")
        response = supabase.auth.sign_in_with_oauth({
            "provider": "google",
            "options": {
                "redirect_to": redirect_url,
                "query_params": {"access_type": "offline", "prompt": "consent"},
            }
        })
        if response and hasattr(response, "url") and response.url:
            st.session_state["oauth_url"] = response.url
        else:
            return None
    return st.session_state["oauth_url"]

def handle_auth_callback():
    """Maneja el retorno de OAuth desde la URL (flujo PKCE con code)."""
    if "user" in st.session_state:
        return

    query_params = st.query_params
    code = query_params.get("code")

    if not code:
        return

    try:
        supabase = _get_session_auth_client()
        session_response = supabase.auth.exchange_code_for_session({"auth_code": code})
        user = session_response.user if session_response else None

        if not user:
            st.error("No se pudo obtener la sesión de usuario desde Supabase.")
            return

        if not validate_domain(user.email):
            st.error(f"El correo '{user.email}' no pertenece al dominio institucional '@{ALLOWED_DOMAIN}'.")
            supabase.auth.sign_out()
            return

        profile = get_user_profile(user.id)
        if not profile:
            full_name = (user.user_metadata or {}).get("full_name") or (user.user_metadata or {}).get("name") or user.email
            profile = create_user_profile(user.id, user.email, full_name)
        if not profile:
            st.error("No se pudo crear tu perfil. Contacta al administrador.")
            return

        st.session_state["user"] = profile
        # Limpiar el código de la URL para no reprocesarlo en recargas
        st.query_params.clear()
        st.rerun()

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Error en autenticación: %s", e, exc_info=True)
        st.error(f"Error al procesar la autenticación: {e}")
        # Limpiar query params para evitar reintentos con un code inválido
        if st.query_params:
            st.query_params.clear()
            st.rerun()

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
    st.title("🏫 Quiero mi Permiso!")
    st.subheader("Colegio TGS")
    st.write("Por favor, inicia sesión con tu cuenta institucional para continuar.")

    oauth_url = _get_oauth_url()
    if oauth_url:
        st.link_button("🔑 Iniciar sesión con Google", url=oauth_url, use_container_width=True)
    else:
        st.error("No se pudo iniciar el flujo de autenticación. Verifica la configuración de Supabase.")
