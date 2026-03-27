# Leave Management App — Colegio TGS

[English version (README_EN.md)](README_EN.md)

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
   SUPABASE_KEY = "sb_publishable"
   SUPABASE_SERVICE_KEY = "sb_secret"

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

## 🚀 Despliegue y Configuración de Servicios

Para que la aplicación sea plenamente funcional, es necesario configurar los siguientes servicios externos:

### 1. Base de Datos (Supabase)
1. **Proyecto:** Crea un proyecto en [Supabase](https://supabase.com/).
2. **Tablas y RLS:** Ejecuta el script SQL incluido en `Plan_Implementacion_Leave_MGMT_App_TGS.md` en el Editor SQL de Supabase.
3. **Google Auth:** Habilita el proveedor Google en `Authentication > Providers`. Necesitarás el Client ID y Secret de GCP.

### 2. Autenticación Google (GCP)
1. **Proyecto:** Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/).
2. **OAuth Consent Screen:** Configúrala en modo **Interno** (Internal) para restringir el acceso exclusivamente al dominio `@colegiotgs.cl`.
3. **Credenciales:** Crea un "ID de cliente de OAuth 2.0" (Aplicación Web).
4. **Redirección:** Añade la URL de callback que te proporciona Supabase en su panel de configuración de Google.

### 3. Notificaciones (SMTP)
1. **Cuenta:** Crea una cuenta de correo dedicada (ej: `notificaciones@colegiotgs.cl`).
2. **Seguridad:** Habilita la "Verificación en 2 pasos" en la cuenta de Google.
3. **Clave de Aplicación:** Genera una **Contraseña de aplicación** específica para el servicio de correo. Esta clave es la que debe usarse en los Secrets, no la contraseña personal de la cuenta.

### 4. Hosting (Streamlit Cloud)
1. Sube el repositorio a GitHub.
2. Conecta tu cuenta en [Streamlit Cloud](https://share.streamlit.io/).
3. **Secrets:** Configura los secretos en el panel de control de Streamlit pegando el contenido de tu `.streamlit/secrets.toml`.

## 📂 Estructura del Proyecto
- `main.py`: Punto de entrada y enrutamiento.
- `app/auth.py`: Lógica de autenticación y sesiones.
- `app/database.py`: Cliente y queries de Supabase.
- `app/services/leave_rules.py`: Motor de reglas de negocio.
- `app/pages/`: Páginas de la interfaz (Dashboard, Solicitud, Admin).
- `app/constants.py`: Mapeo de enums y labels en español.
- `GEMINI.md`: Contexto técnico para desarrollo asistido por IA.
