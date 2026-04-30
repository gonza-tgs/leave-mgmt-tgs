# AGENTS.md — Leave Management App (Colegio TGS)

## Project Overview
The **Leave Management App** is a web-based platform designed for **Colegio TGS** to automate and manage employee leave requests. It handles different types of leave (Administrative, Paid, and Unpaid) with **manual approval workflow for all types** — no auto-approval.

### Key Technologies
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Authentication:** Google OAuth via Supabase (restricted to `@colegiotgs.cl`)
- **Notifications:** SMTP for email alerts in Spanish
- **Environment Management:** [uv](https://github.com/astral-sh/uv)

### Architecture
The project follows a modular structure to separate concerns:
- `main.py`: Main entry point, authentication gate, and routing.
- `app/config.py`: Configuration and environment variable loading via `st.secrets`.
- `app/auth.py`: Google OAuth integration and domain validation.
- `app/database.py`: Centralized Supabase client and data access layer.
- `app/notifications.py`: SMTP service for sending approval/rejection emails.
- `app/services/leave_rules.py`: Pure Python business logic for leave validation rules.
- `app/pages/`: UI components for different user roles (Dashboard, Request Form, Admin Panels).
- `app/constants.py`: Spanish-language label mappings and informational text blocks.
- `sql/`: Database migration scripts for schema evolution and RPC functions.

### User Roles
- **user** — Request leave, view own history and quota
- **admin** — Approve/reject requests, manage users, feriados, blocked periods, reports
- **admin_read_only** — View everything but cannot approve/reject/modify (read-only admin access)

---

## Building and Running

### Prerequisites
- Python >= 3.12
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Setup
1. **Install Dependencies:**
   ```bash
   uv sync
   ```

2. **Environment Variables:**
   Create a `.streamlit/secrets.toml` file in the root directory:
   ```toml
   SUPABASE_URL = "https://<your-project>.supabase.co"
   SUPABASE_KEY = "<anon-public-key>"
   SUPABASE_SERVICE_KEY = "<service-role-key>"
   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = 587
   SMTP_USER = "notificaciones@colegiotgs.cl"
   SMTP_PASSWORD = "<app-password>"
   SMTP_FROM = "notificaciones@colegiotgs.cl"
   ```

3. **Database Setup:**
   Run the SQL scripts in this order in the Supabase SQL Editor:
   - `sql/reset.sql` — Full schema (tables, enums, triggers, RLS, indexes, RPC)
   - `sql/migration_v2.sql` — `material_entregado` column + `periodos_bloqueados` table
   - `sql/migration_add_admin_read_only.sql` — `admin_read_only` role enum value
   - `sql/migration_rpc_insert_with_limit.sql` — RPC for atomic institutional limit check
   - `sql/migration_drop_es_pagado_trigger.sql` — Removes `es_pagado` DB trigger (Python handles it now)

### Running the Application
```bash
uv run streamlit run main.py
```

---

## Development Conventions

### Language and Localization
- **UI & Notifications:** All user-facing strings, labels, and emails MUST be in **Spanish**.
- **Enum Mapping:** Use `app/constants.py` to map database enums to Spanish labels (e.g., `administrativo` → "Permiso Administrativo").

### Coding Standards
- **Modular Logic:** Keep business rules (e.g., `leave_rules.py`) separate from Streamlit UI code to facilitate testing.
- **Null Safety:** Always use `.get()` for dictionary access and `df.fillna("")` before displaying dataframes to avoid UI bugs with `None` values.
- **Performance:** Use `@st.cache_data` for frequent database reads (e.g., fetching holidays or user profiles).
- **Security:** Never expose `SUPABASE_SERVICE_KEY` or `es_pagado` / `admin_nota` fields to non-admin users.
- **Resource Management:** Use context managers (`with`) for SMTP connections and other resources.
- **Error Handling:** Log exceptions via `logging.getLogger(__name__).error()` before showing user-facing errors.

### Database Schema (Supabase)
- **Tables:** `profiles` (extends auth users), `solicitudes` (leave requests), `feriados_internos` (single-day holidays), `periodos_bloqueados` (date ranges with no permissions allowed).
- **RLS:** Row Level Security must be strictly enforced (users can only read/write their own data; admins have full access).
- **Triggers:** Automatic `updated_at` updates on both tables, profile creation on user signup. (The `es_pagado` default trigger was removed — Python handles this logic.)
- **RPC Functions:** `insert_solicitud_with_limit` — atomic insert with institutional daily limit re-check to prevent race conditions.
- **Migrations:** All SQL changes go in `sql/` directory and must be run in Supabase SQL Editor.

---

## Business Rules (Core Logic)

### Global Rules (apply to all leave types)
- **Advance Notice:** Requests must be submitted at least 14 days before the leave date. Otherwise → auto-rejected.
- **Blocked Days:** Weekends, national holidays, and admin-defined `feriados_internos` (single dates) are blocked.
- **Blocked Periods:** Admin-defined date ranges in `periodos_bloqueados` block all leave requests during those periods.

### Administrative Leave Rules
- **Quota:** 3 days per year (Half-days count as 0.5).
- **Prohibited Days:** Mondays, Fridays, eve of holidays, or day after a holiday → auto-rejected.
- **Constraints:** No consecutive days → sent to `pendiente`; maximum 2 institutional approvals per day → sent to `pendiente` (enforced atomically by RPC at insert time).
- **Flow:** All administrative leave goes to `pendiente` (passes initial validations) or `rechazado` (fails any hard rule). An admin must manually approve → `aprobado_manual` or reject → `rechazado`.
- **Material Replacement:** Before approving, the admin marks whether the teacher delivered replacement material (`material_entregado` toggle).

### Paid / Unpaid Leave Rules
- **Flow:** Always require manual admin approval (`pendiente` → `aprobado_manual` or `rechazado`).
- **Paid Status:** Admin can toggle `es_pagado` for `con_goce` and `sin_goce` requests.
