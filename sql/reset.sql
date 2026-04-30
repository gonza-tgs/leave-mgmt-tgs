-- ============================================================
-- QUIERO MI PERMISO! — Script de Reset Completo
-- Ejecutar en Supabase SQL Editor con privilegios de superadmin
-- ⚠️  ADVERTENCIA: Elimina TODOS los datos existentes
-- ============================================================


-- ============================================================
-- 1. LIMPIEZA (orden inverso de dependencias)
-- ============================================================

DROP TRIGGER IF EXISTS on_auth_user_created            ON auth.users;
DROP TRIGGER IF EXISTS set_es_pagado_on_insert         ON solicitudes;
DROP TRIGGER IF EXISTS update_profiles_updated_at      ON profiles;
DROP TRIGGER IF EXISTS update_solicitudes_updated_at   ON solicitudes;

DROP FUNCTION IF EXISTS handle_new_user()              CASCADE;
DROP FUNCTION IF EXISTS set_es_pagado_default()        CASCADE;
DROP FUNCTION IF EXISTS update_updated_at_column()     CASCADE;
DROP FUNCTION IF EXISTS insert_solicitud_with_limit    CASCADE;

DROP TABLE IF EXISTS solicitudes        CASCADE;
DROP TABLE IF EXISTS feriados_internos  CASCADE;
DROP TABLE IF EXISTS periodos_bloqueados CASCADE;
DROP TABLE IF EXISTS profiles           CASCADE;

DROP TYPE IF EXISTS tipo_permiso_enum   CASCADE;
DROP TYPE IF EXISTS jornada_enum        CASCADE;
DROP TYPE IF EXISTS estado_enum         CASCADE;
DROP TYPE IF EXISTS rol_enum            CASCADE;


-- ============================================================
-- 2. TIPOS ENUM
-- ============================================================

CREATE TYPE rol_enum          AS ENUM ('user', 'admin', 'admin_read_only');
CREATE TYPE tipo_permiso_enum AS ENUM ('administrativo', 'con_goce', 'sin_goce');
CREATE TYPE jornada_enum      AS ENUM ('completa', 'manana', 'tarde');
CREATE TYPE estado_enum       AS ENUM ('pendiente', 'aprobado_auto', 'aprobado_manual', 'rechazado');


-- ============================================================
-- 3. TABLAS
-- ============================================================

CREATE TABLE profiles (
    id          UUID        PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    email       TEXT        NOT NULL UNIQUE,
    full_name   TEXT,
    rol         rol_enum    NOT NULL DEFAULT 'user',
    area        TEXT,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE solicitudes (
    id              UUID              PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID              NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    tipo_permiso    tipo_permiso_enum NOT NULL,
    fecha_inicio    DATE              NOT NULL,
    jornada         jornada_enum      NOT NULL DEFAULT 'completa',
    estado          estado_enum       NOT NULL DEFAULT 'pendiente',
    es_pagado       BOOLEAN           NOT NULL DEFAULT FALSE,
    material_entregado BOOLEAN        NOT NULL DEFAULT FALSE,
    notificado      BOOLEAN           NOT NULL DEFAULT FALSE,
    motivo          TEXT,
    admin_nota      TEXT,
    created_at      TIMESTAMPTZ       NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ       NOT NULL DEFAULT NOW()
);

CREATE TABLE feriados_internos (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha       DATE        NOT NULL UNIQUE,
    descripcion TEXT,
    created_by  UUID        REFERENCES profiles(id) ON DELETE SET NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE periodos_bloqueados (
    id              UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    fecha_inicio    DATE        NOT NULL,
    fecha_fin       DATE        NOT NULL,
    descripcion     TEXT,
    created_by      UUID        REFERENCES profiles(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT check_fecha_rango CHECK (fecha_fin >= fecha_inicio)
);


-- ============================================================
-- 4. FUNCIONES Y TRIGGERS
-- ============================================================

-- 4a. handle_new_user: crea perfil mínimo al registrarse con Google/OAuth
--     La asignación de rol admin (primer usuario) la gestiona la app Python.
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER SET search_path = public
AS $$
BEGIN
    INSERT INTO public.profiles (id, email, full_name)
    VALUES (
        NEW.id,
        NEW.email,
        COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email)
    )
    ON CONFLICT (id) DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION handle_new_user();


-- 4b. update_updated_at: actualiza el timestamp en cada UPDATE
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.updated_at := NOW();
    RETURN NEW;
END;
$$;

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_solicitudes_updated_at
    BEFORE UPDATE ON solicitudes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();


-- ============================================================
-- 5. ÍNDICES
-- ============================================================

CREATE INDEX idx_solicitudes_user_id      ON solicitudes(user_id);
CREATE INDEX idx_solicitudes_fecha_inicio ON solicitudes(fecha_inicio);
CREATE INDEX idx_solicitudes_estado       ON solicitudes(estado);
CREATE INDEX idx_solicitudes_user_fecha   ON solicitudes(user_id, fecha_inicio);
CREATE INDEX idx_periodos_fechas          ON periodos_bloqueados(fecha_inicio, fecha_fin);


-- ============================================================
-- 6. ROW LEVEL SECURITY (RLS)
-- ============================================================
-- Nota: la app usa SUPABASE_SERVICE_KEY que bypasea RLS.
-- Estas políticas protegen accesos directos vía anon/user keys.

-- profiles
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_read_own_profile
    ON profiles FOR SELECT
    USING (auth.uid() = id);

CREATE POLICY admins_read_all_profiles
    ON profiles FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid()
            AND p.rol IN ('admin', 'admin_read_only')
        )
    );

CREATE POLICY admins_update_profiles
    ON profiles FOR UPDATE
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid()
            AND p.rol = 'admin'
        )
    );

-- solicitudes
ALTER TABLE solicitudes ENABLE ROW LEVEL SECURITY;

CREATE POLICY users_insert_own_solicitudes
    ON solicitudes FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY users_read_own_solicitudes
    ON solicitudes FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY admins_all_solicitudes
    ON solicitudes FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid()
            AND p.rol IN ('admin', 'admin_read_only')
        )
    );

-- feriados_internos
ALTER TABLE feriados_internos ENABLE ROW LEVEL SECURITY;

CREATE POLICY all_users_read_feriados
    ON feriados_internos FOR SELECT
    USING (auth.role() = 'authenticated');

CREATE POLICY admins_manage_feriados
    ON feriados_internos FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM profiles p
            WHERE p.id = auth.uid()
            AND p.rol = 'admin'
        )
    );

-- periodos_bloqueados
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


-- ============================================================
-- 7. RPC: INSERCIÓN ATÓMICA CON LÍMITE INSTITUCIONAL
-- ============================================================
-- Previene race condition donde dos usuarios concurrentes pasan
-- el chequeo de límite de 2 permisos administrativos por día.
-- Si ya hay >= 2 aprobados para esa fecha, anota la derivación
-- en admin_nota pero igual inserta (el admin decide).

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

    IF p_tipo_permiso = 'administrativo' AND p_estado = 'pendiente' THEN
        SELECT COUNT(*) INTO v_admin_count
        FROM solicitudes
        WHERE fecha_inicio = p_fecha_inicio
          AND tipo_permiso = 'administrativo'
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
