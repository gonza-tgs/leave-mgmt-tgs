# Manual de Usuario: Administrador del Sistema de Permisos (Colegio TGS)

Este documento ha sido diseñado para la Dirección y la Gestión Administrativa del Colegio TGS. Su objetivo es explicar el funcionamiento, las reglas y el uso de la aplicación de gestión de permisos.

---

## 1. Introducción y Propósito

La aplicación de **Gestión de Permisos TGS** es una herramienta digital diseñada para centralizar, automatizar y transparentar el proceso de solicitud de permisos y licencias del personal. 

### Roles en el Sistema
1.  **Administradora (Usted):** Encargada de la toma de decisiones finales, aprobación de casos excepcionales y supervisión general de la asistencia.
2.  **Administradora Solo Lectura:** Puede revisar solicitudes y reportes, pero no puede aprobar ni rechazar. Útil para quienes necesitan supervisar sin tomar decisiones.
3.  **Soporte Técnico (Informática):** Encargado de mantener la plataforma activa, gestionar usuarios y resolver problemas técnicos.
4.  **Usuario (Personal del Colegio):** Profesores y asistentes de la educación que solicitan permisos a través de su cuenta institucional.

---

## 2. Acceso y Disponibilidad

La aplicación se encuentra alojada en la nube, lo que permite acceder desde cualquier lugar con conexión a internet.

*   **URL de Acceso:** [https://gestion-permisos-tgs.streamlit.app](https://gestion-permisos-tgs.streamlit.app)
*   **Plataforma:** El sistema utiliza tecnología de **Streamlit Cloud** para la interfaz, **Supabase** para el almacenamiento seguro de datos y **Google Cloud Platform (GCP)** para la validación de identidad institucional.

### Acceso Seguro
El acceso está restringido exclusivamente a correos con el dominio `@colegiotgs.cl`. El sistema utiliza la cuenta de Google institucional para validar la identidad del usuario de forma segura, eliminando la necesidad de recordar contraseñas adicionales.

---

## 3. Conceptos Básicos y Funcionamiento

La aplicación no requiere instalación; funciona directamente en el navegador web (Chrome, Edge, Safari). 

### Estructura de Datos
Toda la información (quién pidió permiso, cuándo y por qué) se almacena en una base de datos centralizada y segura. Esto permite generar reportes históricos y asegurar que las reglas se apliquen de forma justa para todos.

---

## 4. Normas de Gestión de Permisos (Reglas de Negocio)

El sistema aplica automáticamente las políticas del colegio para los **Permisos Administrativos**.

### Permisos Administrativos (3 días al año)
El sistema controla un cupo de **3 días hábiles** por año calendario para cada funcionario. Las solicitudes pueden ser por jornada completa (1.0 día) o media jornada (0.5 día).

#### Restricciones para Aprobación Automática:
Para que un permiso se apruebe de forma inmediata (sin intervención de Dirección), debe cumplir:
*   **Días Prohibidos:** No puede ser lunes, viernes, víspera de feriado o el día posterior a un feriado.
*   **Consecutividad:** No se pueden solicitar dos permisos administrativos en días seguidos.
*   **Límite Institucional:** El sistema permite un máximo de **2 personas** con permiso administrativo el mismo día en todo el colegio para no afectar la operación.

**¿Qué pasa si no cumple las reglas?**
Depende de la infracción:

*   **Rechazo automático:** Si el día solicitado es un día prohibido (lunes, viernes, víspera o posterior a feriado) o si el funcionario ya agotó su cupo anual de 3 días, la solicitud de permiso administrativo queda **rechazada automáticamente**. El sistema notifica al usuario con el motivo. Si el funcionario considera que su situación es excepcional, puede volver a solicitar el mismo día eligiendo un **Permiso Con Goce de Sueldo** o **Sin Goce de Sueldo**, el cual siempre quedará en estado **"Pendiente"** para su evaluación.

*   **Derivación a revisión (Pendiente):** Si el funcionario solicita días consecutivos o si ya hay 2 personas con permiso el mismo día, la solicitud administrativa **no se rechaza**, sino que queda en estado **"Pendiente"** para que usted evalúe la excepcionalidad del caso.

### Otros Permisos (Con o Sin Goce de Sueldo)
Estos permisos siempre requieren su revisión manual. El sistema le permitirá indicar si el permiso es remunerado o no al momento de aprobarlo.

---

## 5. Guía de Uso de los Paneles Administrativos

Usted dispone de cuatro herramientas principales en el menú lateral:

### A. Gestión de Solicitudes (Admin Panel)
Es su centro de trabajo diario. Aquí verá una lista de todas las peticiones que requieren su decisión.
*   **Revisión:** Al expandir una solicitud, verá el motivo del usuario y, en caso de ser un permiso administrativo, el sistema le indicará por qué fue derivado a revisión (ej. "Es día lunes").
*   **Decisión:** Puede **Aprobar** o **Rechazar**. En ambos casos, puede escribir una nota aclaratoria que le llegará al funcionario.
*   **Notificación:** Al presionar el botón, el sistema envía automáticamente un correo electrónico al solicitante con su decisión.

### B. Gestión de Feriados Internos (Admin Feriados)
Permite bloquear fechas específicas para todo el colegio (ej. Aniversario, jornadas de planificación, cierres administrativos).
*   Al registrar un día aquí, ningún funcionario podrá solicitar permisos automáticos para esa fecha.

### C. Gestión de Usuarios y Roles (Admin Users)
Permite ver quiénes están registrados en la plataforma.
*   Aquí se asignan los perfiles (Usuario o Administrador).
*   **Importante:** Solo el soporte técnico debería modificar estos roles a menos que se requiera un cambio de jerarquía.

### D. Reportes y Estadísticas (Admin Reports)
Permite visualizar la "fotografía" del colegio en cuanto a ausencias.
*   Filtros por mes, por área o por tipo de permiso.
*   Botón para descargar la información a Excel para procesos de remuneraciones o registros internos.

---

## 6. Requisitos y Recomendaciones

*   **Navegador:** Se recomienda el uso de Google Chrome actualizado.
*   **Soporte:** Ante cualquier duda sobre el funcionamiento o si un usuario no puede ingresar, contacte al soporte técnico para verificar que el correo institucional esté correctamente configurado.
*   **Privacidad:** La información de los motivos de los permisos es sensible. Se recomienda acceder a los paneles administrativos solo desde equipos de uso personal o de oficina protegidos.

---

**Colegio TGS**  
*Sistema de Gestión de Permisos - Versión 1.0*
