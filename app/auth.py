import hashlib
import base64
import secrets
from urllib.parse import urlencode
import streamlit as st
from app.database import get_supabase_auth, get_user_profile, create_user_profile
from app.config import ALLOWED_DOMAIN, SUPABASE_URL

def validate_domain(email: str) -> bool:
    """Verifica si el correo pertenece al dominio permitido."""
    return email.split("@")[-1] == ALLOWED_DOMAIN

def _pkce_pair() -> tuple[str, str]:
    verifier = base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode()
    challenge = base64.urlsafe_b64encode(
        hashlib.sha256(verifier.encode()).digest()
    ).rstrip(b"=").decode()
    return verifier, challenge

def _get_oauth_url() -> str | None:
    """Genera y cachea la URL OAuth PKCE. El code_verifier viaja en el redirect_to
    como respaldo para sobrevivir la nueva sesión de Streamlit."""
    if "oauth_url" not in st.session_state:
        verifier, challenge = _pkce_pair()
        # Guardar en session_state como respaldo principal
        st.session_state["pkce_verifier"] = verifier
        
        redirect_url = st.secrets.get("REDIRECT_URL", "http://localhost:8501")
        # Supabase preserva los query params del redirect_to al redirigir de vuelta
        redirect_with_cv = f"{redirect_url}?pkce_cv={verifier}"
        
        params = urlencode({
            "provider": "google",
            "redirect_to": redirect_with_cv,
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "access_type": "offline",
            "prompt": "consent",
        })
        st.session_state["oauth_url"] = f"{SUPABASE_URL}/auth/v1/authorize?{params}"
    return st.session_state["oauth_url"]

def handle_auth_callback():
    """Maneja el retorno de OAuth desde la URL (flujo PKCE con code)."""
    if "user" in st.session_state:
        return

    query_params = st.query_params
    
    # 1. Manejo de errores explícitos de Supabase en la URL
    error = query_params.get("error")
    if error:
        desc = query_params.get("error_description", "sin descripción")
        st.session_state["_auth_error"] = f"Error OAuth: {error} — {desc}"
        st.query_params.clear()
        st.rerun()
        return

    # 2. Verificar si hay un código de autenticación
    code = query_params.get("code")
    if not code:
        return

    # 3. Obtener el verifier (de la URL o del session_state)
    code_verifier = query_params.get("pkce_cv") or st.session_state.get("pkce_verifier")

    if not code_verifier:
        st.session_state["_auth_error"] = (
            "Falta el verificador de código (PKCE). Esto suele ocurrir si la REDIRECT_URL "
            "configurada en los secrets no coincide con la URL permitida en Supabase, "
            "causando que los parámetros se pierdan en la redirección."
        )
        st.query_params.clear()
        st.rerun()
        return

    try:
        supabase = get_supabase_auth()
        session_response = supabase.auth.exchange_code_for_session({
            "auth_code": code,
            "code_verifier": code_verifier,
        })
        user = session_response.user if session_response else None

        if not user:
            st.session_state["_auth_error"] = "No se pudo obtener la sesión de usuario desde Supabase."
            st.query_params.clear()
            st.rerun()
            return

        if not validate_domain(user.email):
            st.session_state["_auth_error"] = f"El correo '{user.email}' no pertenece al dominio institucional '@{ALLOWED_DOMAIN}'."
            supabase.auth.sign_out()
            st.query_params.clear()
            st.rerun()
            return

        profile = get_user_profile(user.id)
        if not profile:
            full_name = (user.user_metadata or {}).get("full_name") or (user.user_metadata or {}).get("name") or user.email
            profile = create_user_profile(user.id, user.email, full_name)
        
        if not profile:
            st.session_state["_auth_error"] = "No se pudo crear o recuperar tu perfil. Contacta al administrador."
            st.query_params.clear()
            st.rerun()
            return

        # Éxito: Guardar usuario y limpiar todo
        st.session_state["user"] = profile
        if "pkce_verifier" in st.session_state:
            del st.session_state["pkce_verifier"]
        if "oauth_url" in st.session_state:
            del st.session_state["oauth_url"]
            
        st.query_params.clear()
        st.rerun()

    except Exception as e:
        import logging
        logging.getLogger(__name__).error("Error en autenticación: %s", e, exc_info=True)
        st.session_state["_auth_error"] = f"Error inesperado: {str(e)}"
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

    if "_auth_error" in st.session_state:
        st.error(f"Error de autenticación: {st.session_state.pop('_auth_error')}")

    oauth_url = _get_oauth_url()
    if oauth_url:
        st.link_button("🔑 Iniciar sesión con Google", url=oauth_url, use_container_width=True)
    else:
        st.error("No se pudo iniciar el flujo de autenticación. Verifica la configuración de Supabase.")
