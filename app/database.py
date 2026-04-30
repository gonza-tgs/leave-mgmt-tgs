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
    supabase = get_supabase_admin()
    try:
        result = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
        return result.data
    except Exception:
        import logging
        logging.getLogger(__name__).error("No se pudo obtener el perfil del usuario %s", user_id, exc_info=True)
        return None

def create_user_profile(user_id: str, email: str, full_name: str) -> dict:
    """Crea un perfil nuevo. Si no hay usuarios, asigna rol admin."""
    supabase = get_supabase_admin()
    count_result = supabase.table("profiles").select("id", count="exact").execute()
    is_first_user = (count_result.count or 0) == 0
    rol = "admin" if is_first_user else "user"
    profile_data = {"id": user_id, "email": email, "full_name": full_name, "rol": rol}
    result = supabase.table("profiles").upsert(profile_data, ignore_duplicates=True).execute()
    get_user_profile.clear()
    # Si upsert no retornó datos (perfil ya existía), lo buscamos directamente
    if result.data:
        return result.data[0]
    fresh = supabase.table("profiles").select("*").eq("id", user_id).single().execute()
    return fresh.data

def get_admin_emails() -> list:
    """Retorna los emails de todos los administradores (admin y admin_read_only)."""
    supabase = get_supabase_admin()
    result = supabase.table("profiles").select("email").in_("rol", ["admin", "admin_read_only"]).execute()
    return [r["email"] for r in result.data] if result.data else []

@st.cache_data(ttl=300)
def get_profiles_for_admin():
    """Retorna todos los perfiles para uso exclusivo de admins."""
    supabase = get_supabase_admin()
    result = supabase.table("profiles").select("id, full_name, email").order("full_name").execute()
    return result.data or []

# --- Consultas de Solicitudes ---

@st.cache_data(ttl=60)
def get_user_solicitudes(user_id: str, year: int | None = None):
    """Obtiene las solicitudes de un usuario. Si se pasa year, filtra por ese año."""
    supabase = get_supabase_admin()
    query = supabase.table("solicitudes").select("*").eq("user_id", user_id)
    if year is not None:
        query = query.gte("fecha_inicio", f"{year}-01-01").lte("fecha_inicio", f"{year}-12-31")
    result = query.order("fecha_inicio", desc=True).execute()
    return result.data

def insert_solicitud(solicitud_data: dict):
    """Inserta una nueva solicitud de permiso."""
    supabase = get_supabase_admin()
    result = supabase.table("solicitudes").insert(solicitud_data).execute()
    get_user_solicitudes.clear()
    return result.data

# FIXED: #4 — atomic insert with institutional limit re-check via RPC
def insert_solicitud_with_limit(solicitud_data: dict):
    """Inserta una solicitud con chequeo atómico de límite institucional vía RPC."""
    supabase = get_supabase_admin()
    result = supabase.rpc("insert_solicitud_with_limit", {
        "p_user_id":      solicitud_data["user_id"],
        "p_tipo_permiso": solicitud_data["tipo_permiso"],
        "p_fecha_inicio": solicitud_data["fecha_inicio"],
        "p_jornada":      solicitud_data["jornada"],
        "p_estado":       solicitud_data["estado"],
        "p_es_pagado":    solicitud_data["es_pagado"],
        "p_motivo":       solicitud_data.get("motivo") or "",
        "p_admin_nota":   solicitud_data.get("admin_nota") or "",
    }).execute()
    get_user_solicitudes.clear()
    return result.data

# --- Feriados Internos ---

@st.cache_data(ttl=3600)
def get_feriados_internos() -> list:
    """Retorna todos los feriados internos definidos por el admin."""
    supabase = get_supabase_admin()
    result = supabase.table("feriados_internos").select("*").order("fecha").execute()
    return result.data or []

def add_feriado_interno(fecha: str, descripcion: str, created_by: str):
    """Agrega un feriado interno."""
    supabase = get_supabase_admin()
    result = supabase.table("feriados_internos").insert({
        "fecha": fecha,
        "descripcion": descripcion,
        "created_by": created_by
    }).execute()
    get_feriados_internos.clear()
    return result.data[0] if result.data else None

def delete_feriado_interno(feriado_id: str):
    """Elimina un feriado interno por ID."""
    supabase = get_supabase_admin()
    supabase.table("feriados_internos").delete().eq("id", feriado_id).execute()
    get_feriados_internos.clear()


# --- Periodos Bloqueados ---

@st.cache_data(ttl=3600)
def get_periodos_bloqueados() -> list:
    """Retorna todos los periodos bloqueados (rangos de fechas)."""
    supabase = get_supabase_admin()
    result = supabase.table("periodos_bloqueados").select("*").order("fecha_inicio").execute()
    return result.data or []


def add_periodo_bloqueado(fecha_inicio: str, fecha_fin: str, descripcion: str, created_by: str):
    """Agrega un periodo bloqueado (rango de fechas)."""
    supabase = get_supabase_admin()
    result = supabase.table("periodos_bloqueados").insert({
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "descripcion": descripcion,
        "created_by": created_by
    }).execute()
    get_periodos_bloqueados.clear()
    return result.data[0] if result.data else None


def delete_periodo_bloqueado(periodo_id: str):
    """Elimina un periodo bloqueado por ID."""
    supabase = get_supabase_admin()
    supabase.table("periodos_bloqueados").delete().eq("id", periodo_id).execute()
    get_periodos_bloqueados.clear()
