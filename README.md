# Quiero mi Permiso! — Colegio TGS

[English version (README_EN.md)](README_EN.md)

Sistema web denominado **"Quiero mi Permiso!"** para la gestión de permisos laborales del Colegio TGS, desarrollado con **Streamlit** y **Supabase**.

## Caracteristicas
- **Autenticacion Institucional:** Login con Google OAuth restringido al dominio `@colegiotgs.cl`.
- **Flujo Manual:** Todas las solicitudes requieren aprobacion manual de la Direccion (no hay auto-aprobacion).
- **Motor de Reglas:** Validacion en Python de cupos anuales, restricciones de calendario (lunes/viernes, feriados nacionales, visperas/dias posteriores a feriados), dias consecutivos y limite institucional de 2 permisos administrativos por dia.
- **Limite Atomico:** Funcion RPC en Postgres (`insert_solicitud_with_limit`) que re-chequea el limite institucional en insercion para prevenir condiciones de carrera.
- **Bloqueo de Dias:** Restriccion absoluta para fines de semana, feriados nacionales, feriados internos y periodos bloqueados definidos por admin.
- **Panel de Administracion:** Gestion de solicitudes, reportes dinamicos, administracion de roles (incluyendo **Administrador de Solo Lectura**), gestion de dias no laborables y periodos bloqueados.
- **Material de Reemplazo:** Toggle para marcar si el docente entrego material para el dia del permiso.
- **Notificaciones:** Envio automatico de correos de aprobacion/rechazo via SMTP.

## Stack Tecnologico
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Base de Datos:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Gestion de Dependencias:** [uv](https://github.com/astral-sh/uv)
- **Calendario:** `holidays` (Chile)

## Configuracion Local

1. **Instalar dependencias:**
   ```bash
   uv sync
   ```

2. **Configurar Secretos:**
   Crea un archivo `.streamlit/secrets.toml` en la raiz del proyecto con las siguientes claves:
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
   Ejecuta los scripts SQL en este orden en el Editor SQL de Supabase:
   - `sql/reset.sql` — Schema completo (tablas, enums, triggers, RLS, indices)
   - `sql/migration_v2.sql` — Columna `material_entregado` + tabla `periodos_bloqueados`
   - `sql/migration_add_admin_read_only.sql` — Valor `admin_read_only` en enum de roles
   - `sql/migration_rpc_insert_with_limit.sql` — Funcion RPC para limite atomico

4. **Ejecutar la App:**
   ```bash
   uv run streamlit run main.py
   ```

## Despliegue y Configuracion de Servicios

### 1. Base de Datos (Supabase)
1. **Proyecto:** Crea un proyecto en [Supabase](https://supabase.com/).
2. **Tablas y RLS:** Ejecuta los scripts SQL del directorio `sql/` en orden.
3. **Google Auth:** Habilita el proveedor Google en `Authentication > Providers`.

### 2. Autenticacion Google (GCP)
1. **Proyecto:** Crea un proyecto en [Google Cloud Console](https://console.cloud.google.com/).
2. **OAuth Consent Screen:** Configurala en modo **Interno** (Internal) para restringir el acceso al dominio `@colegiotgs.cl`.
3. **Credenciales:** Crea un "ID de cliente de OAuth 2.0" (Aplicacion Web).
4. **Redireccion:** Agrega la URL de callback que te proporciona Supabase.

### 3. Notificaciones (SMTP)
1. **Cuenta:** Crea una cuenta de correo dedicada (ej: `notificaciones@colegiotgs.cl`).
2. **Seguridad:** Habilita la "Verificacion en 2 pasos" en la cuenta de Google.
3. **Clave de Aplicacion:** Genera una **Contrasena de aplicacion** para el servicio de correo.

### 4. Hosting (Streamlit Cloud)
1. Sube el repositorio a GitHub.
2. Conecta tu cuenta en [Streamlit Cloud](https://share.streamlit.io/).
3. **Secrets:** Configura los secretos pegando el contenido de `.streamlit/secrets.toml`.

## Estructura del Proyecto
```
leave-mgmt-tgs/
├── main.py                          # Punto de entrada, auth gate y routing
├── app/
│   ├── __init__.py
│   ├── auth.py                      # Google OAuth y validacion de dominio
│   ├── config.py                    # Carga de secretos y constantes
│   ├── constants.py                 # Labels en espanol y textos informativos
│   ├── database.py                  # Cliente Supabase y data access layer
│   ├── notifications.py             # Servicio SMTP de notificaciones
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard.py             # Historial y metricas del usuario
│   │   ├── submit_request.py        # Formulario de nueva solicitud
│   │   ├── admin_panel.py           # Aprobacion/rechazo de pendientes
│   │   ├── admin_reports.py         # Reportes con filtros dinamicos
│   │   ├── admin_users.py           # Gestion de roles de usuario
│   │   └── admin_feriados.py        # Feriados internos y periodos bloqueados
│   └── services/
│       ├── __init__.py
│       └── leave_rules.py           # Motor de reglas de negocio (sin Streamlit)
└── sql/
    ├── reset.sql                     # Schema completo
    ├── migration_v2.sql              # material_entregado + periodos_bloqueados
    ├── migration_add_admin_read_only.sql
    └── migration_rpc_insert_with_limit.sql  # RPC para limite atomico
```

## Roles de Usuario
| Rol | Permisos |
|-----|----------|
| **user** | Solicitar permisos, ver historial y cupo propio |
| **admin** | Aprobar/rechazar, gestionar usuarios, feriados, periodos bloqueados, reportes |
| **admin_read_only** | Ver todo pero sin aprobar/rechazar/modificar |
