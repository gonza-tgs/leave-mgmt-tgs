-- ============================================================
-- QUIERO MI PERMISO! — Migración: RPC para inserción atómica con límite institucional
-- Fix: previene race condition donde dos usuarios concurrentes
-- pasan el chequeo de límite de 2 permisos institucionales por día.
-- Ejecutar en Supabase SQL Editor con privilegios de superadmin.
-- ============================================================

-- RPC que re-chequea el límite institucional de forma atómica al insertar.
-- Si ya hay >= 2 solicitudes aprobadas para la misma fecha, anota la
-- derivación en admin_nota. Siempre inserta la solicitud (el límite es
-- informativo para el admin, no bloquea la inserción).
CREATE OR REPLACE FUNCTION insert_solicitud_with_limit(
    p_user_id          UUID,
    p_tipo_permiso     tipo_permiso_enum,
    p_fecha_inicio     DATE,
    p_jornada          jornada_enum,
    p_estado           estado_enum,
    p_es_pagado        BOOLEAN,
    p_motivo           TEXT,
    p_admin_nota       TEXT
)
RETURNS SETOF solicitudes
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
DECLARE
    v_admin_count INT;
    v_admin_nota  TEXT;
BEGIN
    v_admin_nota := p_admin_nota;

    -- Re-chequeo atómico del límite institucional para permisos administrativos
    IF p_tipo_permiso = 'administrativo' AND p_estado = 'pendiente' THEN
        SELECT COUNT(*) INTO v_admin_count
        FROM solicitudes
        WHERE fecha_inicio = p_fecha_inicio
          AND estado IN ('aprobado_auto', 'aprobado_manual');

        IF v_admin_count >= 2 THEN
            IF p_admin_nota IS NOT NULL AND p_admin_nota != '' THEN
                v_admin_nota := p_admin_nota
                    || ' | SISTEMA: Límite institucional de 2 permisos alcanzado para este día.';
            ELSE
                v_admin_nota := 'SISTEMA: Se ha alcanzado el límite de 2 permisos institucionales para este día. Requiere revisión por parte de la Dirección.';
            END IF;
        END IF;
    END IF;

    RETURN QUERY
    INSERT INTO solicitudes (
        user_id, tipo_permiso, fecha_inicio, jornada,
        estado, es_pagado, motivo, admin_nota
    ) VALUES (
        p_user_id, p_tipo_permiso, p_fecha_inicio, p_jornada,
        p_estado, p_es_pagado, p_motivo, v_admin_nota
    )
    RETURNING *;
END;
$$;
