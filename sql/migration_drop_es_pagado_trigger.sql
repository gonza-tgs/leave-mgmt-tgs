-- ============================================================
-- QUIERO MI PERMISO! — Migración: eliminar trigger set_es_pagado_default
-- El código Python ya asigna es_pagado correctamente en todos los flujos.
-- El trigger sobrescribía el valor explícito enviado por la app,
-- impidiendo que el admin pudiera registrar permisos históricos con
-- es_pagado distinto al valor por defecto del tipo (ej. sin_goce pagado).
-- Ejecutar en Supabase SQL Editor.
-- ============================================================

DROP TRIGGER IF EXISTS set_es_pagado_on_insert ON solicitudes;
DROP FUNCTION IF EXISTS set_es_pagado_default() CASCADE;
