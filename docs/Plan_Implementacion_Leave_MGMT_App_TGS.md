# Plan de Implementación: Leave Management App — Colegio TGS

## Contexto

El Colegio TGS necesita una aplicación web para gestionar solicitudes de permisos laborales. Actualmente el proceso es manual. La app automatizará la aprobación de permisos administrativos según reglas de negocio definidas y proporcionará a la Dirección un panel para gestionar permisos manuales, reportes y configuración de usuarios.

### Stack Tecnológico
- **Frontend/Backend:** Streamlit
- **Base de Datos:** Supabase (PostgreSQL)
- **Autenticación:** Google OAuth via Supabase Auth (restringido a `@colegiotgs.cl`)
- **Notificaciones:** SMTP (correo en español)

### Decisiones de Diseño
| Aspecto | Decisión |
|---|---|
| Días adyacentes a feriados | Rechazo automático |
| Cupo medias jornadas | 0.5 días por media jornada (6 medias = 3 días de cupo) |
| Autenticación Google | Supabase Auth integrado |
| Encargado de Área (notificaciones) | Cualquier admin del mismo área del solicitante |

---

## 1. Estructura de Archivos

```
leave-mgmt/
├── main.py                          # Auth gate + routing principal
├── pyproject.toml                   # Dependencias del proyecto
├── .env                             # Secrets (gitignored)
├── .streamlit/
│   └── config.toml                  # Tema visual
│
├── app/
│   ├── __init__.py                  # Marcador de paquete
│   ├── config.py                    # Carga .env, constantes globales
│   ├── auth.py                      # Supabase Auth + validación de dominio
│   ├── database.py                  # Cliente Supabase, todas las queries
│   ├── notifications.py             # Lógica SMTP, plantillas en español
│   ├── constants.py                 # Labels en español para enums de BD
│   │
│   ├── pages/
│   │   ├── __init__.py              # Marcador de paquete
│   │   ├── login.py                 # Página de inicio de sesión
│   │   ├── dashboard.py             # Historial + días restantes (usuario)
│   │   ├── submit_request.py        # Formulario nueva solicitud
│   │   ├── admin_panel.py           # Aprobar/rechazar solicitudes pendientes
│   │   ├── admin_reports.py         # Reportes con filtros dinámicos
│   │   └── admin_users.py           # Gestión de roles de usuario
│   │
│   └── services/
│       ├── __init__.py              # Marcador de paquete
│       └── leave_rules.py           # Motor de reglas de negocio (sin Streamlit)
```

---

## 2. Base de Datos (Supabase)

### 2.1 Schema DDL

```sql
-- Enums
CREATE TYPE tipo_permiso_enum AS ENUM ('administrativo', 'con_goce', 'sin_goce');
CREATE TYPE jornada_enum      AS ENUM ('completa', 'manana', 'tarde');
CREATE TYPE estado_enum       AS ENUM ('pendiente', 'aprobado_auto', 'aprobado_manual', 'rechazado');
CREATE TYPE rol_enum          AS ENUM ('user', 'admin');

-- Perfiles de usuario (extiende auth.users de Supabase)
CREATE TABLE profiles (
    id          UUID PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT NOT NULL UNIQUE,
    full_name   TEXT,
    rol         rol_enum NOT NULL DEFAULT 'user',
    area        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Solicitudes de permiso
CREATE TABLE solicitudes (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    tipo_permiso    tipo_permiso_enum NOT NULL,
    fecha_inicio    DATE NOT NULL,
    jornada         jornada_enum NOT NULL DEFAULT 'completa',
    estado          estado_enum NOT NULL DEFAULT 'pendiente',
    es_pagado       BOOLEAN NOT NULL DEFAULT FALSE,  -- Solo visible para admins
    notificado      BOOLEAN NOT NULL DEFAULT FALSE,
    motivo          TEXT,
    admin_nota      TEXT,                             -- Solo visible para admins
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

### 2.2 Triggers

| Trigger | Tabla | Acción |
|---|---|---|
| `handle_new_user` | `auth.users` | Crea fila en `profiles` al registrarse con Google |
| `set_es_pagado_default` | `solicitudes` (INSERT) | `administrativo`/`con_goce` → `true`; `sin_goce` → `false` |
| `update_updated_at` | Ambas | Actualiza `updated_at` en cada UPDATE |

### 2.3 Row Level Security (RLS)

| Política | Tabla | Regla |
|---|---|---|
| `users_read_own_profile` | `profiles` | Usuario solo lee su propia fila |
| `admins_read_all_profiles` | `profiles` | Admin lee todas |
| `admins_update_profiles` | `profiles` | Solo admins pueden modificar roles |
| `users_insert_own_solicitudes` | `solicitudes` | Usuario solo inserta con su `user_id` |
| `users_read_own_solicitudes` | `solicitudes` | Usuario solo lee las suyas |
| `admins_all_solicitudes` | `solicitudes` | Admin tiene acceso completo |

### 2.4 Vistas

- **`solicitudes_publicas`**: Join con `profiles`, excluye `es_pagado` y `admin_nota`. Para queries de usuario.
- **`solicitudes_admin`**: Incluye todos los campos incluyendo los administrativos. Para queries de admin (service role key).

### 2.5 Índices

```sql
CREATE INDEX idx_solicitudes_user_id      ON solicitudes(user_id);
CREATE INDEX idx_solicitudes_fecha_inicio ON solicitudes(fecha_inicio);
CREATE INDEX idx_solicitudes_estado       ON solicitudes(estado);
CREATE INDEX idx_solicitudes_user_fecha   ON solicitudes(user_id, fecha_inicio);
```

---

## 3. Fases de Implementación

### Fase 1: Fundación — Configuración y Base de Datos

**Objetivo:** Proyecto ejecutable con conexión a Supabase.

1. Actualizar `pyproject.toml` con nuevas dependencias:
   - `holidays>=0.61` — Calendario feriados chilenos
   - `python-dotenv>=1.0.0` — Carga de variables de entorno

2. Crear `.env` (gitignored) con todas las credenciales.

3. Crear `app/config.py`:
   - Carga variables de entorno
   - Define constantes: `ALLOWED_DOMAIN = "colegiotgs.cl"`, `MAX_ADMIN_DAYS = 3`
   - Lanza error descriptivo si falta alguna variable requerida

4. Aplicar DDL completo en el dashboard de Supabase (tablas, triggers, RLS, vistas, índices).

5. Crear `app/database.py`:
   - Singleton del cliente Supabase (anon key para operaciones de usuario, service role para admin)
   - Todas las funciones de query centralizadas aquí
   - Aplicar `@st.cache_data(ttl=120)` en reads frecuentes

6. Crear `app/constants.py` con mapeos de labels en español:

```python
TIPO_PERMISO_LABELS = {
    "administrativo": "Permiso Administrativo",
    "con_goce":       "Con Goce de Sueldo",
    "sin_goce":       "Sin Goce de Sueldo",
}
ESTADO_LABELS = {
    "pendiente":       "Pendiente",
    "aprobado_auto":   "Aprobado",
    "aprobado_manual": "Aprobado",
    "rechazado":       "Rechazado",
}
JORNADA_LABELS = {
    "completa": "Jornada Completa",
    "manana":   "Mañana",
    "tarde":    "Tarde",
}
```

**Validación:** `uv run streamlit run main.py` inicia sin errores de importación.

---

### Fase 2: Autenticación con Supabase Auth + Google OAuth

**Objetivo:** Login con Google, validación de dominio, sesión persistente.

**Archivo principal:** `app/auth.py`

Flujo OAuth con Supabase:
1. Usuario hace clic en "Iniciar sesión con Google"
2. `supabase.auth.sign_in_with_oauth(provider='google')` redirige a Google
3. Google redirige de vuelta con `?code=` en la URL
4. `st.query_params` detecta el código → `supabase.auth.exchange_code_for_session(code)`
5. Se valida que el email sea `@colegiotgs.cl`
6. Se hace upsert en tabla `profiles`
7. Se guarda el usuario en `st.session_state["user"]`
8. `st.balloons()` como feedback visual de login exitoso

Funciones clave en `app/auth.py`:

```python
def sign_in_with_google() -> None
def handle_auth_callback() -> None
def validate_domain(email: str) -> bool
def get_or_create_profile(session) -> dict
def is_authenticated() -> bool
def require_role(role: str) -> None  # Llama st.stop() si no autorizado
def render_login_page() -> None
```

Routing en `main.py`:

```python
if "code" in st.query_params:
    handle_auth_callback()

if not is_authenticated():
    render_login_page()
    st.stop()

# Navegación por rol
user = st.session_state["user"]
nav_options = ["Mi Historial", "Solicitar Permiso"]

if user["rol"] in ["admin", "admin_read_only"]:
    nav_options += ["Gestión de Permisos", "Reportes"]
    if user["rol"] == "admin":
        nav_options += ["Usuarios", "Feriados Internos"]

page = st.sidebar.radio("Navegación", nav_options)
```

---

### Fase 3: Motor de Reglas de Negocio

**Objetivo:** Lógica de auto-aprobación de permisos administrativos, completamente testeable.

**Archivo principal:** `app/services/leave_rules.py`

> **Importante:** Este módulo no debe importar `streamlit` ni `supabase`. Solo Python puro + `holidays`.

```python
def is_prohibited_day(check_date: date) -> tuple[bool, str]:
    """
    Retorna (es_prohibido, razon).
    Días prohibidos:
    - Lunes (weekday == 0)
    - Viernes (weekday == 4)
    - Víspera de feriado (el día siguiente es feriado)
    - Día post-feriado (el día anterior es feriado)
    Usa holidays.Chile(years=[year])
    """

def evaluate_auto_approval(
    user_id: str,
    fecha: date,
    jornada: str,
    db_queries: dict  # callables inyectados desde database.py
) -> tuple[str, str]:
    """
    Retorna (estado, razon).
    Orden de evaluación:
    1. Cupo anual >= MAX_ADMIN_DAYS → "rechazado"
       (completa=1.0, manana/tarde=0.5)
    2. is_prohibited_day → "rechazado"
    3. Días consecutivos aprobados → "pendiente"
    4. Límite institucional >= 2 aprobaciones ese día → "pendiente"
    5. Todo OK → "aprobado_auto"
    """
```

El parámetro `db_queries` es un dict de funciones pasadas desde `database.py` (inyección de dependencias), lo que permite testear `leave_rules.py` con funciones mock sin necesidad de Supabase.

---

### Fase 4: Páginas de Usuario

**Objetivo:** El empleado puede solicitar permisos y ver su historial.

#### `app/pages/submit_request.py`

- `st.selectbox` → tipo de permiso (labels en español)
- `st.date_input` → fecha (min=hoy, max=hoy+90 días)
- `st.radio` → jornada (Completa / Mañana / Tarde)
- `st.text_area` → motivo (opcional)
- On submit con `st.spinner("Enviando solicitud...")`:
  - Si `tipo = administrativo`: llamar `evaluate_auto_approval()` → crear solicitud con estado resultante
  - Si `tipo = con_goce` o `sin_goce`: crear con `estado = 'pendiente'`
  - Si `estado = aprobado_auto`: llamar `notifications.send_approval_email()`
- `st.success()` / `st.error()` con mensajes en español

#### `app/pages/dashboard.py`

- `st.metric("Días administrativos restantes", valor)` → `3 - días_usados_año`
- `st.metric("Días en revisión", valor_pendientes)`
- `st.dataframe(width='stretch')` historial personal con labels en español.
- **Transparencia:** Incluye columna `admin_nota` ("Nota del Admin") para que el usuario vea feedback.
- Columnas **excluidas**: `es_pagado`, `notificado`, `user_id`
- `df.fillna("")` antes de mostrar (evita bug de visualización con valores `None`)

---

### Fase 5: Panel de Administración

**Objetivo:** La Dirección puede gestionar solicitudes, ver reportes y administrar usuarios.

#### `app/pages/admin_panel.py` — Gestión de Permisos

- Inicia con `render_admin_panel(user)`
- Detecta si es `admin_read_only` para deshabilitar botones y acciones de edición.
- Query a `solicitudes` con información de perfiles.
- Por cada solicitud pendiente, un `st.expander` con:
  - Nombre, email, área del solicitante
  - Tipo, fecha, jornada, motivo usuario.
  - **Motivo del sistema:** Mostrar en color de advertencia si la solicitud fue derivada automáticamente (ej. víspera de feriado).
  - Para `con_goce`/`sin_goce`: `st.toggle("Procesar con pago")` → persiste en `es_pagado` (deshabilitado si es solo lectura).
  - `st.columns(2)` con botones **Aprobar** y **Rechazar** (deshabilitados si es solo lectura).
  - `st.text_input` opcional para `admin_nota`.
- On Aprobar: `update_solicitud()` + `send_approval_email()` + `st.rerun()`
- On Rechazar: `update_solicitud()` + `send_rejection_email()` + `st.rerun()`
- `st.spinner` durante operaciones de DB

#### `app/pages/admin_reports.py` — Reportes

- Fila de filtros con `st.columns(4)`:
  - Selector de usuario (selectbox con "Todos" como opción)
  - Fecha desde / Fecha hasta (`st.date_input`)
  - Estado (`st.multiselect`)
- `st.toggle("Agrupar por usuario")`
- `st.radio("Ordenar por fecha", ["Descendente", "Ascendente"])`
- Resultados en `st.dataframe(width='stretch')`
- `st.download_button("Exportar CSV")` → `df.to_csv(index=False)`
- `es_pagado` solo visible en sección "Vista Administrativa" del panel

#### `app/pages/admin_users.py` — Gestión de Usuarios

- Tabla de todos los usuarios con su rol actual
- `st.selectbox` por fila para cambiar rol
- Botón Guardar → `database.update_user_role(user_id, new_role)`
- Advertencia si se intenta degradar al último administrador

#### `app/pages/admin_feriados.py` — Gestión de Calendario

- Panel para que el admin registre fechas como "Días No Laborables Internos".
- Listado de fechas con opción de eliminar.
- Formulario para añadir fecha + descripción.
- Estas fechas alimentan `is_blocked_day` para prevenir solicitudes en días cerrados.

---

### Fase 6: Sistema de Notificaciones SMTP

**Archivo principal:** `app/notifications.py`

```python
def send_approval_email(solicitud: dict, user_profile: dict) -> bool:
    """
    Destinatarios:
    - user_profile["email"]
    - Todos los admins del mismo área del solicitante

    Retorna True si el envío fue exitoso.
    En caso de error: loguea, no crashea la app.
    On success: actualiza solicitudes.notificado = True en DB.
    """
```

**Plantilla de correo:**

```
Asunto: Permiso Aprobado — [fecha_inicio]

Estimado/a [full_name],

Tu solicitud de permiso de tipo "[tipo_permiso_label]"
para el día [fecha_inicio] ([jornada_label]) ha sido APROBADA.

Este es un mensaje automático del Sistema de Gestión de Permisos
del Colegio TGS.
```

Implementación con `smtplib.SMTP` usando STARTTLS (puerto 587).

---

### Fase 7: Pulido y Hardening

**Objetivo:** App robusta, sin bugs de nulos, con manejo de errores y caché.

1. **Null safety:**
   - `df.fillna("")` en todos los `st.dataframe`
   - `.get(key, default)` en todas las respuestas de Supabase (nunca acceso directo por clave)

2. **Estrategia de caché** (`@st.cache_data`):
   | Función | TTL |
   |---|---|
   | `get_all_users()` | 300s |
   | `get_user_solicitudes(user_id)` | 60s |
   | `get_pending_solicitudes()` | 30s |
   | `get_chilean_holidays(year)` | 86400s (1 día) |

3. **Error handling:** Todos los calls a Supabase en try/except. On error: `st.error("Error de conexión. Por favor, intenta nuevamente.")` en español, sin traceback visible.

4. **Expiración de sesión:** Verificar expiración del token OAuth en cada render. Si expirado: limpiar `st.session_state` y redirigir al login.

5. **Tema visual** (`.streamlit/config.toml`):
   ```toml
   [theme]
   primaryColor = "#1a5276"
   backgroundColor = "#ffffff"
   secondaryBackgroundColor = "#f0f2f6"
   textColor = "#262730"
   ```

6. **Traducción completa:** Todos los strings visibles al usuario en español. Verificar especialmente:
   - "Unpaid" → "Sin Goce de Sueldo"
   - "Paid" → "Con Goce de Sueldo"
   - Mensajes de validación y error

---

## 4. Variables de Entorno Requeridas

Crear archivo `.env` en la raíz del proyecto (nunca commitear):

```env
# Supabase
SUPABASE_URL=https://<proyecto>.supabase.co
SUPABASE_KEY=<anon-public-key>
SUPABASE_SERVICE_KEY=<service-role-key>

# SMTP
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=notificaciones@colegiotgs.cl
SMTP_PASSWORD=<app-password>
SMTP_FROM=notificaciones@colegiotgs.cl
```

---

## 5. Dependencias a Agregar

Actualizar `pyproject.toml`:

```toml
dependencies = [
    "streamlit>=1.55.0",
    "supabase>=2.28.3",
    "holidays>=0.61",
    "python-dotenv>=1.0.0",
]
```

---

## 6. Verificación End-to-End

| # | Caso de prueba | Resultado esperado |
|---|---|---|
| 1 | `uv run streamlit run main.py` | App inicia sin errores |
| 2 | Login con `@colegiotgs.cl` | `st.balloons()`, redirige a dashboard |
| 3 | Login con email externo | Bloqueado, mensaje de error en español |
| 4 | Solicitar permiso admin en martes válido | Estado `aprobado_auto`, email enviado |
| 5 | Solicitar permiso admin en lunes | Estado `rechazado`, razón explicada |
| 6 | Solicitar permiso admin (cupo agotado) | Estado `rechazado`, razón explicada |
| 7 | Solicitar permiso `con_goce` | Estado `pendiente` (requiere aprobación manual) |
| 8 | Admin aprueba solicitud manual | Estado → `aprobado_manual`, email enviado |
| 9 | `es_pagado` visible para admin | Solo aparece en panel de admin |
| 10 | `es_pagado` invisible para usuario | No aparece en historial del usuario |
| 11 | Filtros en reportes | Resultados filtrados correctamente |
| 12 | Exportar CSV | Descarga archivo válido |
| 13 | Cambiar rol de usuario | Persiste en DB |
| 14 | Degradar último admin | App muestra advertencia, bloquea acción |

---

## 7. Resumen de Fases

| Fase | Enfoque | Entregable clave |
|---|---|---|
| 1 | Fundación | Config, cliente DB, DDL aplicado, app ejecuta |
| 2 | Autenticación | Login Google, validación dominio, sesión |
| 3 | Reglas de Negocio | Motor auto-aprobación `leave_rules.py` |
| 4 | Páginas Usuario | Formulario solicitud + historial personal |
| 5 | Panel Admin | Gestión, reportes, administración usuarios |
| 6 | Notificaciones | Emails SMTP en español |
| 7 | Hardening | Null safety, caché, errores, tema visual |
ración usuarios |
| 6 | Notificaciones | Emails SMTP en español |
| 7 | Hardening | Null safety, caché, errores, tema visual |
s, tema visual |
l |
| 7 | Hardening | Null safety, caché, errores, tema visual |
ración usuarios |
| 6 | Notificaciones | Emails SMTP en español |
| 7 | Hardening | Null safety, caché, errores, tema visual |
