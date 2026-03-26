# Leave Management App — Colegio TGS

Sistema web para la gestión automatizada y manual de permisos laborales del Colegio TGS, desarrollado con **Streamlit** y **Supabase**.

## 🚀 Características
- **Autenticación Institucional:** Login con Google OAuth restringido al dominio `@colegiotgs.cl`.
- **Motor de Reglas:** Aprobación automática de permisos administrativos basada en cupos anuales y restricciones de calendario (feriados, vísperas, etc.).
- **Panel de Administración:** Gestión de solicitudes pendientes, reportes con filtros dinámicos y administración de roles de usuario.
- **Notificaciones:** Envío automático de correos de aprobación vía SMTP.
- **Reportabilidad:** Exportación de historiales a CSV para análisis administrativo.

## 🛠️ Stack Tecnológico
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Base de Datos:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Gestión de Dependencias:** [uv](https://github.com/astral-sh/uv)
- **Calendario:** `holidays` (Chile)

## 📋 Configuración Local

1. **Instalar dependencias:**
   ```bash
   uv sync
   ```

2. **Configurar Secretos:**
   Crea un archivo `.streamlit/secrets.toml` en la raíz del proyecto con las siguientes claves:
   ```toml
   SUPABASE_URL = "https://tu-proyecto.supabase.co"
   SUPABASE_KEY = "tu-anon-key"
   SUPABASE_SERVICE_KEY = "tu-service-role-key"

   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = 587
   SMTP_USER = "tu-correo@colegiotgs.cl"
   SMTP_PASSWORD = "tu-app-password"
   SMTP_FROM = "tu-correo@colegiotgs.cl"
   ```

3. **Base de Datos:**
   Ejecuta el script SQL incluido en `Plan_Implementacion_Leave_MGMT_App_TGS.md` en el Editor SQL de Supabase para crear las tablas, enums y políticas de seguridad (RLS).

4. **Ejecutar la App:**
   ```bash
   uv run streamlit run main.py
   ```

## 🌐 Despliegue en Streamlit Cloud
1. Sube el repositorio a GitHub.
2. Conecta tu cuenta en [Streamlit Cloud](https://share.streamlit.io/).
3. Configura los **Secrets** en el panel de control de Streamlit pegando el contenido de tu `secrets.toml`.

## 📂 Estructura del Proyecto
- `main.py`: Punto de entrada y enrutamiento.
- `app/auth.py`: Lógica de autenticación y sesiones.
- `app/database.py`: Cliente y queries de Supabase.
- `app/services/leave_rules.py`: Motor de reglas de negocio.
- `app/pages/`: Páginas de la interfaz (Dashboard, Solicitud, Admin).
- `app/constants.py`: Mapeo de enums y labels en español.
- `GEMINI.md`: Contexto técnico para desarrollo asistido por IA.
