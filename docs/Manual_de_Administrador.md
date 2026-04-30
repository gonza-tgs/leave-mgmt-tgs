# Manual de Usuario: Administrador del Sistema de Permisos (Colegio TGS)

Este documento ha sido disenado para la Direccion y la Gestion Administrativa del Colegio TGS. Su objetivo es explicar el funcionamiento, las reglas y el uso de la aplicacion de gestion de permisos.

---

## 1. Introduccion y Proposito

La aplicacion de **Gestion de Permisos TGS** es una herramienta digital disenada para centralizar, automatizar y transparentar el proceso de solicitud de permisos y licencias del personal.

### Roles en el Sistema
1.  **Administradora (Usted):** Encargada de la toma de decisiones finales, aprobacion de todos los permisos y supervision general.
2.  **Administradora Solo Lectura:** Puede revisar solicitudes y reportes, pero no puede aprobar ni rechazar. Util para quienes necesitan supervisar sin tomar decisiones.
3.  **Soporte Tecnico (Informatica):** Encargado de mantener la plataforma activa, gestionar usuarios y resolver problemas tecnicos.
4.  **Usuario (Personal del Colegio):** Profesores y asistentes de la educacion que solicitan permisos a traves de su cuenta institucional.

---

## 2. Acceso y Disponibilidad

La aplicacion se encuentra alojada en la nube, lo que permite acceder desde cualquier lugar con conexion a internet.

*   **URL de Acceso:** [https://gestion-permisos-tgs.streamlit.app](https://gestion-permisos-tgs.streamlit.app)
*   **Plataforma:** El sistema utiliza tecnologia de **Streamlit Cloud** para la interfaz, **Supabase** para el almacenamiento seguro de datos y **Google Cloud Platform (GCP)** para la validacion de identidad institucional.

### Acceso Seguro
El acceso esta restringido exclusivamente a correos con el dominio `@colegiotgs.cl`. El sistema utiliza la cuenta de Google institucional para validar la identidad del usuario de forma segura, eliminando la necesidad de recordar contrasenas adicionales.

---

## 3. Conceptos Basicos y Funcionamiento

La aplicacion no requiere instalacion; funciona directamente en el navegador web (Chrome, Edge, Safari).

### Estructura de Datos
Toda la informacion (quien pidio permiso, cuando y por que) se almacena en una base de datos centralizada y segura. Esto permite generar reportes historicos y asegurar que las reglas se apliquen de forma justa para todos.

---

## 4. Normas de Gestion de Permisos (Reglas de Negocio)

### Permisos Administrativos (3 dias al ano)
El sistema controla un cupo de **3 dias habiles** por ano calendario para cada funcionario. Las solicitudes pueden ser por jornada completa (1.0 dia) o media jornada (0.5 dia). **Todos los permisos administrativos requieren aprobacion manual de la Direccion.**

#### Reglas de Validacion Automatica:
Al momento de enviar la solicitud, el sistema valida:

*   **Anticipacion:** La solicitud debe hacerse con al menos **14 dias** de anticipacion. Solicitudes con menos tiempo son rechazadas automaticamente.
*   **Dias Prohibidos:** No se permiten permisos administrativos los lunes, viernes, visperas de feriado o el dia posterior a un feriado. Si se intenta, el sistema rechaza automaticamente.
*   **Dias Bloqueados:** No se permiten permisos en fines de semana, feriados nacionales, dias no laborables internos, ni dentro de periodos bloqueados.
*   **Cupo Anual:** Si el funcionario ya uso sus 3 dias, la solicitud es rechazada.

**Solicitudes que pasan las validaciones:** Quedan en estado **"Pendiente"** para su revision. El sistema le indicara si la solicitud fue derivada por alguna razon especial:

*   **Dias consecutivos:** Si el funcionario solicita un dia adyacente a otro permiso ya aprobado.
*   **Limite institucional:** Si ya hay 2 o mas permisos administrativos aprobados para esa misma fecha en todo el colegio.

### Otros Permisos (Con o Sin Goce de Sueldo)
Estos permisos siempre requieren su revision manual. El sistema le permitira indicar si el permiso es remunerado o no al momento de aprobarlo.

---

## 5. Guia de Uso de los Paneles Administrativos

Usted dispone de cuatro herramientas principales en el menu lateral:

### A. Gestion de Solicitudes (Admin Panel)
Es su centro de trabajo diario. Aqui vera una lista de todas las peticiones que requieren su decision.
*   **Revisar:** Al expandir una solicitud, vera el nombre, email, area, tipo de permiso, fecha, jornada y motivo del usuario.
*   **Sistema de Derivacion:** Si aparece un aviso naranja con "Derivacion Automatica", el sistema le explica por que esa solicitud requiere su atencion especial (ej. "limite institucional alcanzado", "dias consecutivos").
*   **Material de Reemplazo:** Para permisos administrativos, encontrara un toggle "Material de reemplazo entregado". Marque esta casilla si el docente entrego el material correspondiente al dia del permiso.
*   **Procesar con Pago:** Para permisos Con Goce y Sin Goce de Sueldo, puede marcar si el permiso se procesa como remunerado. Este campo queda registrado internamente y no es visible para el usuario.
*   **Nota Administrativa:** Puede escribir una nota opcional que sera visible tanto en el sistema como en el correo de notificacion al usuario.
*   **Decision:** Presione **Aprobar** o **Rechazar**. El sistema envia automaticamente un correo electronico al solicitante con su decision.

### B. Gestion de Dias No Laborables (Admin Feriados)
Permite gestionar dos tipos de bloqueos:

1.  **Dias No Laborables Internos:** Fechas especificas donde no se permite ningun permiso (ej. Aniversario del colegio, jornada de planificacion).
2.  **Periodos Bloqueados:** Rangos de fechas donde no se autoriza ningun permiso (ej. del 15 al 30 de diciembre, vacaciones de invierno).

### C. Gestion de Usuarios y Roles (Admin Users)
Permite ver quienes estan registrados en la plataforma y asignar roles.
*   Roles disponibles: **Usuario**, **Administrador**, **Administrador Solo Lectura**.
*   **Importante:** El sistema no permite quitar el rol de administrador al ultimo administrador del sistema para evitar quedarse sin acceso.

### D. Reportes y Estadisticas (Admin Reports)
Permite visualizar la "fotografia" del colegio en cuanto a ausencias.
*   Filtros por usuario, por ano y por estado.
*   Opcion de agrupar por usuario y ordenar por fecha (ascendente/descendente).
*   Boton para descargar la informacion a CSV (compatible con Excel).

---

## 6. Requisitos y Recomendaciones

*   **Navegador:** Se recomienda el uso de Google Chrome actualizado.
*   **Soporte:** Ante cualquier duda sobre el funcionamiento o si un usuario no puede ingresar, contacte al soporte tecnico para verificar que el correo institucional este correctamente configurado.
*   **Privacidad:** La informacion de los motivos de los permisos es sensible. Se recomienda acceder a los paneles administrativos solo desde equipos de uso personal o de oficina protegidos.

---

**Colegio TGS**
*Sistema de Gestion de Permisos - Version 1.0*
