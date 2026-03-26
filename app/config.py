import streamlit as st

# Configuración de Supabase
# st.secrets funciona tanto localmente (.streamlit/secrets.toml) como en Streamlit Cloud
SUPABASE_URL = st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("SUPABASE_KEY")
SUPABASE_SERVICE_KEY = st.secrets.get("SUPABASE_SERVICE_KEY")

# Configuración SMTP
SMTP_HOST = st.secrets.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(st.secrets.get("SMTP_PORT", 587))
SMTP_USER = st.secrets.get("SMTP_USER")
SMTP_PASSWORD = st.secrets.get("SMTP_PASSWORD")
SMTP_FROM = st.secrets.get("SMTP_FROM")

# Constantes de Negocio
ALLOWED_DOMAIN = "colegiotgs.cl"
MAX_ADMIN_DAYS = 3.0

# Validación básica (opcional para logs)
if not SUPABASE_URL:
    st.warning("⚠️ SUPABASE_URL no configurado en secrets.")
