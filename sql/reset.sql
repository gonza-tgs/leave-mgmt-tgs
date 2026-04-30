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


-- 4b. set_es_pagado_default: asigna es_pagado según tipo de permiso en INSERT
CREATE OR REPLACE FUNCTION set_es_pagado_default()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NEW.tipo_permiso IN ('administrativo', 'con_goce') THEN
        NEW.es_pagado := TRUE;
    ELSE
        NEW.es_pagado := FALSE;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER set_es_pagado_on_insert
    BEFORE INSERT ON solicitudes
    FOR EACH ROW EXECUTE FUNCTION set_es_pagado_default();


-- 4c. update_updated_at: actualiza el timestamp en cada UPDATE
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
