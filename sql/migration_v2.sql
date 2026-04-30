-- ============================================================
-- QUIERO MI PERMISO! — Migración v2
-- Agrega: material_entregado a solicitudes + tabla periodos_bloqueados
-- Ejecutar en Supabase SQL Editor con privilegios de superadmin
-- ============================================================

-- 1. Agregar columna material_entregado a solicitudes
ALTER TABLE solicitudes
ADD COLUMN IF NOT EXISTS material_entregado BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Nueva tabla: periodos_bloqueados (rangos de fechas sin permisos)
CREATE TABLE IF NOT EXISTS periodos_bloqueados (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha_inicio    DATE        NOT NULL,
    fecha_fin       DATE        NOT NULL,
    descripcion     TEXT,
    created_by      UUID        REFERENCES profiles(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT check_fecha_rango CHECK (fecha_fin >= fecha_inicio)
);

-- 3. Índices
CREATE INDEX IF NOT EXISTS idx_periodos_fechas ON periodos_bloqueados(fecha_inicio, fecha_fin);

-- 4. Row Level Security
ALTER TABLE periodos_bloqueados ENABLE ROW LEVEL SECURITY;

CREATE POLICY all_users_read_periodos
    ON periodos_bloqueados FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY admins_manage_periodos
    ON periodos_bloqueados FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid()
            AND p.rol = 'admin'
        )
    );
