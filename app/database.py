import streamlit as st
from supabase import create_client, Client
from app.config import SUPABASE_URL, SUPABASE_KEY, SUPABASE_SERVICE_KEY

@st.cache_resource
def get_supabase() -> Client:
    """Retorna el cliente Supabase para operaciones del usuario."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        st.error("Error: SUPABASE_URL y SUPABASE_KEY deben estar configurados.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_resource
def get_supabase_admin() -> Client:
    """Retorna el cliente Supabase con privilegios de servicio."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        st.error("Error: SUPABASE_URL y SUPABASE_SERVICE_KEY deben estar configurados.")
        st.stop()
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)

# --- Consultas de Perfil ---

@st.cache_data(ttl=300)
def get_user_profile(user_id: str):
    """Obtiene el perfil del usuario por ID."""
    supabase = get_supabase()
    try:
        result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return result.data
    except Exception:
        return None

def create_user_profile(user_id: str, email: str, full_name: str) -> dict:
    """Crea un perfil nuevo. Si no hay usuarios, asigna rol admin."""
    supabase = get_supabase_admin()
    count_result = supabase.table("profiles").select("id", count="exact").execute()
    is_first_user = (count_result.count or 0) == 0
    rol = "admin" if is_first_user else "user"
    profile_data = {"id": user_id, "email": email, "full_name": full_name, "rol": rol}
    result = supabase.table("profiles").insert(profile_data).execute()
    return result.data[0] if result.data else None

# --- Consultas de Solicitudes ---

@st.cache_data(ttl=60)
def get_user_solicitudes(user_id: str):
    """Obtiene las solicitudes de un usuario específico."""
    supabase = get_supabase()
    # Usamos la vista pública para usuarios normales
    result = supabase.table("solicitudes").select("*").eq("user_id", user_id).order("fecha_inicio", desc=True).execute()
    return result.data

def insert_solicitud(solicitud_data: dict):
    """Inserta una nueva solicitud de permiso."""
    supabase = get_supabase()
    result = supabase.table("solicitudes").insert(solicitud_data).execute()
    return result.data
