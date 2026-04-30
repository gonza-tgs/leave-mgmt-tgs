# GEMINI.md - Leave Management App (Colegio TGS)

## Project Overview 🛩️
The **Leave Management App** is a web-based platform designed for **Colegio TGS** to automate and manage employee leave requests. It handles different types of leave (Administrative, Paid, and Unpaid) with manual approval workflow for all types.

### Key Technologies
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Authentication:** Google OAuth via Supabase (restricted to `@colegiotgs.cl`)
- **Notifications:** SMTP for email alerts in Spanish
- **Environment Management:** [uv](https://github.com/astral-sh/uv)

### Architecture
The project follows a modular structure to separate concerns:
- `main.py`: Main entry point, authentication gate, and routing.
- `app/config.py`: Configuration and environment variable loading.
- `app/auth.py`: Google OAuth integration and domain validation.
- `app/database.py`: Centralized Supabase client and data access layer.
- `app/notifications.py`: SMTP service for sending approval/rejection emails.
- `app/services/leave_rules.py`: Pure Python business logic for leave validation rules.
- `app/pages/`: UI components for different user roles (Dashboard, Request Form, Admin Panels).
- `sql/migrations/`: Database migration scripts for schema evolution.

---

## Building and Running

### Prerequisites
- Python >= 3.14
- `uv` installed (`curl -LsSf https://astral.sh/uv/install.sh | sh`)

### Setup
1. **Install Dependencies:**
   ```bash
   uv sync
   ```

2. **Environment Variables:**
   Create a `.env` file in the root directory based on the following template:
   ```env
   SUPABASE_URL=https://<your-project>.supabase.co
   SUPABASE_KEY=<anon-public-key>
   SUPABASE_SERVICE_KEY=<service-role-key>
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=notificaciones@colegiotgs.cl
   SMTP_PASSWORD=<app-password>
   SMTP_FROM=notificaciones@colegiotgs.cl
   ```

### Running the Application
```bash
uv run streamlit run main.py
```

---

## Development Conventions

### Language and Localization
- **UI & Notifications:** All user-facing strings, labels, and emails MUST be in **Spanish**.
- **Enum Mapping:** Use `app/constants.py` to map database enums to Spanish labels (e.g., `administrativo` -> "Permiso Administrativo").

### Coding Standards
- **Modular Logic:** Keep business rules (e.g., `leave_rules.py`) separate from Streamlit UI code to facilitate testing.
- **Null Safety:** Always use `.get()` for dictionary access and `df.fillna("")` before displaying dataframes to avoid UI bugs with `None` values.
- **Performance:** Use `@st.cache_data` for frequent database reads (e.g., fetching holidays or user profiles).
- **Security:** Never expose `SUPABASE_SERVICE_KEY` or `es_pagado` / `admin_nota` fields to non-admin users.

### Database Schema (Supabase)
- **Tables:** `profiles` (extends auth users), `solicitudes` (leave requests), `feriados_internos` (single-day holidays), `periodos_bloqueados` (date ranges with no permissions allowed).
- **RLS:** Row Level Security must be strictly enforced (users can only read/write their own data; admins have full access).
- **Triggers:** Automatic `updated_at` updates and profile creation on user signup.
- **Migrations:** Run `sql/migration_v2.sql` for the latest schema additions (`material_entregado`, `periodos_bloqueados`).

---

## Business Rules (Core Logic)

### Global Rules (apply to all leave types)
- **Advance Notice:** Requests must be submitted at least 14 days before the leave date. Otherwise → auto-rejected.
- **Blocked Days:** Weekends, national holidays, and admin-defined `feriados_internos` (single dates) are blocked.
- **Blocked Periods:** Admin-defined date ranges in `periodos_bloqueados` block all leave requests during those periods.

### Administrative Leave Rules
- **Quota:** 3 days per year (Half-days count as 0.5).
- **Prohibited Days:** Mondays, Fridays, eve of holidays, or day after a holiday → auto-rejected.
- **Constraints:** No consecutive days → sent to `pendiente`; maximum 2 institutional approvals per day → sent to `pendiente`.
- **Flow:** All administrative leave goes to `pendiente` (passes initial validations) or `rechazado` (fails any hard rule). An admin must manually approve → `aprobado_manual` or reject → `rechazado`.
- **Material Replacement:** Before approving, the admin marks whether the teacher delivered replacement material (`material_entregado` toggle).
