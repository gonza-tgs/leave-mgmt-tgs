# Especificaciones Tecnicas: Quiero mi Permiso!

## 1. Vision General

Desarrollo de una aplicacion web denominada **"Quiero mi Permiso!"** para la gestion de permisos laborales del Colegio TGS. La plataforma permite a los empleados solicitar permisos (administrativos, con goce o sin goce de sueldo) y a la Direccion gestionar dichas solicitudes bajo reglas de negocio validadas automaticamente con aprobacion manual.

## 2. Stack Tecnologico

* **Frontend/Backend:** Streamlit.
* **Base de Datos:** Supabase (PostgreSQL).
* **Autenticacion:** Google OAuth (Restringido al dominio @colegiotgs.cl).
* **Notificaciones:** Sistema de envio de correos (SMTP).
* **Gestion de Dependencias:** uv.
* **Calendario:** holidays (Chile).

## 3. Perfiles y Permisos

### 3.1 Perfil Usuario (user)

* Solicitar permisos administrativos, con goce de sueldo o sin goce de sueldo (Formulario).
  * **Motivo:** Campo obligatorio con selector de opciones (Tramites, Medicos, Personal, Otro) y validacion de texto libre si se elige "Otro".
* Visualizar historial de solicitudes personales.
* Ver estado de los dias administrativos restantes (disponibles, usados y en revision).

### 3.2 Perfil Administrador (admin)

* Acceso a todas las funciones del Perfil Usuario.
* Panel de gestion: Aprobar/Rechazar permisos pendientes.
* Marcar material de reemplazo entregado para permisos administrativos.
* Toggle de pago (es_pagado) para permisos con/sin goce.
* Configuracion de usuarios: Definir roles (admin / user / admin_read_only).
* Panel de reportes: Filtrado por usuario, ano y estado, agrupacion y ordenacion de registros, exportacion CSV.
* Gestion de calendario: Dias no laborables internos y periodos bloqueados.

### 3.3 Perfil Administrador Solo Lectura (admin_read_only)

* Visualiza solicitudes pendientes, reportes y configuracion.
* No puede aprobar, rechazar ni modificar registros.

## 4. Reglas de Negocio (Core Logic)

### 4.1 Reglas Globales (aplican a todos los tipos de permiso)

* **Anticipacion:** La solicitud debe hacerse con al menos 14 dias de anticipacion. Menos tiempo → rechazo automatico.
* **Dias Bloqueados:** No se permiten permisos en fines de semana, feriados nacionales, feriados internos ni dentro de periodos bloqueados definidos por admin.

### 4.2 Permisos Administrativos

* **Cupo:** Maximo 3 dias al ano (media jornada = 0.5).
* **Dias Prohibidos:** Lunes, Viernes, visperas de feriado o dia posterior a un feriado → rechazo automatico.
* **Dias Consecutivos:** No permitidos. Si se detectan → pendiente de revision.
* **Limite Institucional:** Maximo 2 permisos administrativos aprobados por dia en toda la institucion. Si se alcanza → pendiente de revision. Enforced atomicamente por RPC en Postgres (`insert_solicitud_with_limit`).
* **Material de Reemplazo:** El admin debe marcar si el docente entrego material para el dia solicitado.
* **Flujo:** Todas las solicitudes administrativas van a pendiente (si pasan validaciones) o rechazado (si fallan reglas duras). No hay auto-aprobacion.

### 4.3 Permisos Con Goce de Sueldo

* **Cupo:** Sin limite definido por sistema.
* **Flujo:** Siempre requiere aprobacion manual (pendiente → aprobado_manual o rechazado).
* **Atributo Interno:** Admin puede togglear si el permiso se procesa con pago (es_pagado). No visible para el usuario.

### 4.4 Permisos Sin Goce de Sueldo

* **Cupo:** Sin limite definido por sistema.
* **Flujo:** Siempre requiere aprobacion manual (pendiente → aprobado_manual o rechazado).
* **Atributo Interno:** Admin puede togglear si el permiso se procesa con pago (es_pagado). No visible para el usuario.

## 5. Esquema de Base de Datos (Supabase)

### Tablas Principales

* **profiles:** Extiende auth.users. Campos: id, email, full_name, rol (user/admin/admin_read_only), area, created_at, updated_at.
* **solicitudes:** Solicitudes de permiso. Campos: id, user_id (FK profiles), tipo_permiso (administrativo/con_goce/sin_goce), fecha_inicio, jornada (completa/manana/tarde), estado (pendiente/aprobado_auto/aprobado_manual/rechazado), es_pagado, material_entregado, notificado, motivo, admin_nota, created_at, updated_at.
* **feriados_internos:** Dias no laborables definidos por admin. Campos: id, fecha (DATE UNIQUE), descripcion, created_by, created_at.
* **periodos_bloqueados:** Rangos de fechas bloqueados. Campos: id, fecha_inicio, fecha_fin, descripcion, created_by, created_at.

### Triggers
* **handle_new_user:** Crea perfil al registrarse con Google.
* **set_es_pagado_default:** Asigna es_pagado = true para administrativo y con_goce, false para sin_goce.
* **update_updated_at:** Actualiza timestamp en cada UPDATE.

### RPC Functions
* **insert_solicitud_with_limit:** Inserta una solicitud con chequeo atomico del limite institucional de 2 permisos por dia. Previene race conditions.

### Row Level Security (RLS)
* Usuarios solo leen/escriben sus propios datos.
* Admins tienen acceso completo a todas las tablas.
* admin_read_only tiene acceso de solo lectura.

## 6. Sistema de Notificaciones

### 6.1 Notificaciones de Solicitud
* Al ingresar una solicitud que queda pendiente, se envia correo a todos los administradores con los detalles y el motivo de la derivacion.

### 6.2 Notificaciones de Resolucion
* Al aprobarse o rechazarse un permiso, se envia correo al usuario solicitante con la decision y nota del admin.
* Idioma: 100% Espanol.

## 7. Seguridad y Acceso

* **Validacion de Dominio:** Bloqueo estricto para correos que no pertenezcan a @colegiotgs.cl.
* **Service Key:** Operaciones administrativas usan SUPABASE_SERVICE_KEY (bypasea RLS). No expuesta al frontend.
* **Campos Ocultos:** es_pagado y admin_nota no son visibles para usuarios regulares en su historial.
* **Cache:** Optimizacion mediante st.cache_data y st.cache_resource para mitigar latencia.
