# **Especificaciones Técnicas: Quiero mi Permiso!**

## **1\. Visión General**

Desarrollo de una aplicación web denominada **"Quiero mi Permiso!"** para la gestión de permisos laborales del Colegio TGS. La plataforma permitirá a los empleados solicitar permisos (administrativos o sin goce de sueldo) y a la administración gestionar dichas solicitudes bajo reglas de negocio automatizadas y manuales.

## **2\. Stack Tecnológico**

* **Frontend/Backend:** Streamlit.  
* **Base de Datos:** Supabase (PostgreSQL).  
* **Autenticación:** Google OAuth (Restringido al dominio @colegiotgs.cl).  
* **Notificaciones:** Sistema de envío de correos (SMTP)

## **3\. Perfiles y Permisos**

### **3.1 Perfil Usuario**

* Solicitar permisos administrativos, con goce de sueldo o sin goce de sueldo (Formulario).  
  * **Motivo:** Campo obligatorio con selector de opciones (Trámites, Médicos, Personal, Otro) y validación de texto libre si se elige "Otro".
* Visualizar historial de solicitudes personales.  
* Ver estado de los días administrativos restantes.

### **3.2 Perfil Administrador**

* Acceso a todas las funciones del Perfil Usuario.  
* Panel de gestión: Autorizar/Rechazar permisos manuales.  
* Configuración de usuarios: Definir roles (Admin/User).  
* Panel de reportes: Filtrado (por fecha, rango de fecha y por usuario), agrupación y ordenación de registros.  
* Marcado interno de pagos (Campo oculto para el usuario).

## **4\. Reglas de Negocio (Core Logic)**

### **4.1 Permisos Administrativos (Paid)**

* **Cupo:** Máximo 3 días al año (no acumulables).  
* **Flexibilidad:** Permite jornada completa o media jornada.  
* **Restricciones de Aprobación Automática:**  
  * No pueden ser días consecutivos.  
  * Máximo 2 permisos otorgados por día para toda la institución.  
  * **Días Prohibidos:** Lunes, Viernes, vísperas de feriado o día posterior a un feriado.  
* **Flujo:** Si cumple todas las restricciones, se aprueba automáticamente. De lo contrario, requiere revisión manual o es rechazado por sistema.

### **4.2 Permisos Con Goce de Sueldo (Paid)**

* **Cupo:** Sin límite definido por sistema.  
* **Flexibilidad:** Permite jornada completa o media jornada.  
* **Flujo:** Siempre requiere aprobación manual de la Dirección.  
* **Atributo Interno:** La dirección puede marcar si el permiso finalmente se paga o se descuenta (este estado es solo para registros administrativos y no debe mostrarse al usuario).

### **4.3 Permisos Sin Goce de Sueldo (Unpaid)**

* **Cupo:** Sin límite definido por sistema.  
* **Flexibilidad:** Permite jornada completa o media jornada.  
* **Flujo:** Siempre requiere aprobación manual de la Dirección.  
* **Atributo Interno:** La dirección puede marcar si el permiso finalmente se paga o se descuenta (este estado es solo para registros administrativos y no debe mostrarse al usuario).

## **5\. Requerimientos de Datos (Supabase)**

### **Tabla solicitudes (Sugerida)**

* id: UUID.  
* user\_id: FK a perfil.  
* tipo\_permiso: Enum (administrativo, sin\_goce).  
* fecha\_inicio: Date.  
* jornada: Enum (completa, mañana, tarde).  
* estado: Enum (pendiente, aprobado\_auto, aprobado\_manual, rechazado).  
* es\_pagado: Boolean (Default: false para "sin goce", true para "admin". Modificable solo por admin).  
* notificado: Boolean.

## **6\. Interfaz y Experiencia de Usuario (UX)**

### **6.1 Feedback Visual**

* **Pantalla de Carga:** Implementar st.spinner o CSS custom mientras se validan credenciales y cargan datos de Supabase.  
* **Inicio de Sesión:** Mostrar st.balloons() tras un login exitoso.

### **6.2 Corrección de Errores Actuales**

* **Bug de Visualización:** Eliminar el mensaje tipo None \- unpaid (fecha) en el panel de Gestión de Permisos. Asegurar que los valores nulos se manejen correctamente en la UI.  
* **Traducción:** Todos los strings del sistema deben estar en español.  
  * Cambiar "Unpaid" por "Sin goce de sueldo".  
  * Cambiar "Paid" por "Con goce de sueldo".
* **Transparencia:** La nota del administrador (`admin_nota`) debe ser visible para el usuario en su historial para entender rechazos o condiciones.

## **7\. Sistema de Notificaciones**

### **7.1 Notificaciones de Solicitud**
* Al ingresar una solicitud que requiere revisión manual, el sistema envía un correo a todos los administradores con los detalles y el motivo de la derivación.

### **7.2 Notificaciones de Resolución**
Al autorizarse o rechazarse un permiso (automático o manual):
* **Destinatarios:** Usuario solicitante.
* **Idioma:** 100% Español.

## **8\. Administración y Reportabilidad**

### **8.1 Gestión de Registros y Filtros**

Para un control estricto, el panel de administración debe incluir:

* **Filtros Dinámicos:**  
  * **Por Usuario:** Selector para ver las solicitudes de un trabajador específico.  
  * **Por Fecha/Rango:** Selector de calendario para filtrar registros por día o periodo determinado.  
  * **Por Estado:** Filtrar por pendientes, aprobados o rechazados.  
* **Herramientas de Visualización:**  
  * Capacidad de agrupar por: **Usuario**.  
  * Capacidad de ordenar por: **Fecha** (descendente/ascendente).
* **Transparencia del Sistema:** Mostrar explícitamente el motivo por el cual una solicitud administrativa no fue aprobada automáticamente (ej: "Límite institucional alcanzado", "Día consecutivo", etc.).

### **8.2 Gestión de Calendario Interno**

* Panel dedicado para añadir/eliminar fechas donde no se permite ningún tipo de solicitud.
* Estas fechas se sincronizan con el motor de validación del formulario de solicitud.

### **8.3 Campo de Ajuste de Pago**

* En la vista de administrador, añadir un toggle o checkbox para definir si el permiso "Sin goce de sueldo" se procesará con o sin descuento.  
* **Importante:** Este campo debe persistir en la DB pero ser invisible en la vista de historial del usuario final.

## **9\. Seguridad y Acceso**

* **Validación de Dominio:** Bloqueo estricto para correos que no pertenezcan a @colegiotgs.cl.  
* **Persistencia:** Optimizar llamadas a Supabase mediante caché (st.cache\_data) para mitigar la latencia de la capa gratuita.

[image1]: <data:image/png;base64,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>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAmwAAABFCAYAAAD3qbryAAAD10lEQVR4Xu3cTaimYxgA4CE/o+SnHHHOd97v53xhzsbPZzEpP1H+SmlmaccKJTLZiBqSiNLMgiKFBRZDEaUTUxYs/JzQiBqlaBYWUieLUdNxP87z5OnpO5NxsvlcV92957nv+33e7d15v+fdtg0AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABmWa/XO6PruslgMLiurQEA0Iih6ZJ+v7/+D+Lb9t5/K/ZaK/u2NQAANtF13Q1pgIrruVNqH0Tt1Ta/FbHfawY2AIATMBgM9sYA9UmbT1It4qk2vxXxrCMGNgCAExDD08Gu654s6/n5+fNiPcq1JyLu+bt7a2KvHfmV6NQBEQCARgxOt6YBajwen1XlDh/vUEAa5qLnh4iXUrS9vV5vHPnPI/ZF7wtR31lq/fw6NOLeiP1Rey6uv9b3F4uLi1dHbSX3rEb8HLkr2z4AgJkWQ9DTeYB6JMdjEb/HkLS97U2itivi6GQyObXkoveVqr471dNp0Ly+K+rvVPW/XodGfFPl3ksHIMo659I+f5R11G/K9+2o+wAAZl4MQJ/mQSgNa/si3o1YafuSyF/R3zjluVqlT4r1nqrnWMR31fpAxOPVOj3rl4hhyaWBbzgcXlP1pNema5H/uOrZHrkjZQ0A8L/Qdd1teYA6WudjfX29LnJvGshW0unRiOfTHqWeX4Wux3B1QX1fLe+xq6yjd5ByU3rWY4i7uMo9GM+6r+4DAJh5MQQ9m4ejg3V+PB6fXq+L3HuozRdRu/N49STqx2JGO6da79lkYDvc5N6KuLzOAQDMvP7GwYD0H7G9bW2aPEi93+aL2OfuruveaPPFaDS6qH7NmcR+X5SBLWr3x+WU/Jz6228p91tcT47rhRG7qxoAwGyKoWeYB6MUU1+BtqJvf8TawsJCr+RiyLo94rK8TAPVj+XEaf7d2R3D4fDSfP/Lkbu53Bv5G9Pz0ydF4vp2xC25L/3G7UDeY2f8fSj15f2/jMGvK3sAAMykGHq+TwNQEx+1fa3l5eXTou/FiJ9ikHoz/47tobqnv3FoIQ1cH0Z8FX0PVLXP5ubmzizr9Oo16l9HfrX+fVrkrs17PJP3G0b90bi+HvFw6QMAYBNLS0vn199ta6VBLAasSZuP+xbb3Gg0Onsw5ZtvaY/2m2sxrF1VrwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACA/9Kf3yrlnnvyljMAAAAASUVORK5CYII=>l5eXTou/FiJ9ikHoz/47tobqnv3FoIQ1cH0Z8FX0PVLXP5ubmzizr9Oo16l9HfrX+fVrkrs17PJP3G0b90bi+HvFw6QMAYBNLS0vn199ta6VBLAasSZuP+xbb3Gg0Onsw5ZtvaY/2m2sxrF1VrwEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAACA/9Kf3yrlnnvyljMAAAAASUVORK5CYII=>