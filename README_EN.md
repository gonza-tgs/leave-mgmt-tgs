# Quiero mi Permiso! — Colegio TGS

Web system named **"Quiero mi Permiso!"** for employee leave management at Colegio TGS, developed with **Streamlit** and **Supabase**.

## Features
- **Institutional Authentication:** Google OAuth login restricted to the `@colegiotgs.cl` domain.
- **Manual Workflow:** All requests require manual admin approval (no auto-approval).
- **Rules Engine:** Python validation of annual quotas, calendar restrictions (Mondays/Fridays, national holidays, eve/after holidays), consecutive days, and institutional limit of 2 administrative leaves per day.
- **Atomic Limit:** Postgres RPC function (`insert_solicitud_with_limit`) re-checks the institutional limit at insert time to prevent race conditions.
- **Day Blocking:** Absolute restriction for weekends, national holidays, internal holidays, and admin-defined blocked date ranges.
- **Admin Panel:** Request management, dynamic reports, role administration (including **Read-Only Admin**), internal holidays, and blocked periods.
- **Replacement Material:** Toggle to mark whether the teacher delivered material for the leave day.
- **Notifications:** Automated approval/rejection emails via SMTP.

## Tech Stack
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Dependency Management:** [uv](https://github.com/astral-sh/uv)
- **Calendar:** `holidays` (Chile)

## Local Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure Secrets:**
   Create a `.streamlit/secrets.toml` file in the project root:
   ```toml
   SUPABASE_URL = "https://your-project.supabase.co"
   SUPABASE_KEY = "sb_publishable"
   SUPABASE_SERVICE_KEY = "sb_secret"

   SMTP_HOST = "smtp.gmail.com"
   SMTP_PORT = 587
   SMTP_USER = "your-email@colegiotgs.cl"
   SMTP_PASSWORD = "your-app-password"
   SMTP_FROM = "your-email@colegiotgs.cl"
   ```

3. **Database Setup:**
   Run the SQL scripts in this order in the Supabase SQL Editor:
   - `sql/reset.sql` — Full schema (tables, enums, triggers, RLS, indexes, RPC)
   - `sql/migration_v2.sql` — `material_entregado` column + `periodos_bloqueados` table
   - `sql/migration_add_admin_read_only.sql` — `admin_read_only` role enum
   - `sql/migration_rpc_insert_with_limit.sql` — RPC for atomic institutional limit
   - `sql/migration_drop_es_pagado_trigger.sql` — Remove obsolete `es_pagado` trigger

4. **Run the App:**
   ```bash
   uv run streamlit run main.py
   ```

## Deployment and Service Configuration

### 1. Database (Supabase)
1. **Project:** Create a project on [Supabase](https://supabase.com/).
2. **Tables and RLS:** Run all SQL scripts from the `sql/` directory in order.
3. **Google Auth:** Enable the Google provider in `Authentication > Providers`.

### 2. Google Authentication (GCP)
1. **Project:** Create a project in [Google Cloud Console](https://console.cloud.google.com/).
2. **OAuth Consent Screen:** Set to **Internal** mode to restrict access to `@colegiotgs.cl`.
3. **Credentials:** Create an "OAuth 2.0 Client ID" (Web Application).
4. **Redirection:** Add the callback URL provided by Supabase.

### 3. Notifications (SMTP)
1. **Account:** Create a dedicated email account (e.g., `notifications@colegiotgs.cl`).
2. **Security:** Enable "2-Step Verification" on the Google account.
3. **App Password:** Generate an **App password** for the mail service.

### 4. Hosting (Streamlit Cloud)
1. Push the repository to GitHub.
2. Connect your account to [Streamlit Cloud](https://share.streamlit.io/).
3. **Secrets:** Paste your `.streamlit/secrets.toml` content into the Streamlit dashboard.

## Project Structure
```
leave-mgmt-tgs/
├── main.py                          # Entry point, auth gate and routing
├── app/
│   ├── __init__.py
│   ├── auth.py                      # Google OAuth and domain validation
│   ├── config.py                    # Secrets loading and constants
│   ├── constants.py                 # Spanish labels and info texts
│   ├── database.py                  # Supabase client and data access layer
│   ├── notifications.py             # SMTP notification service
│   ├── pages/
│   │   ├── __init__.py
│   │   ├── dashboard.py             # User history and metrics
│   │   ├── submit_request.py        # New request form
│   │   ├── admin_panel.py           # Pending request approval/rejection
│   │   ├── admin_reports.py         # Reports with dynamic filters
│   │   ├── admin_users.py           # User role management
│   │   └── admin_feriados.py        # Internal holidays and blocked periods
│   └── services/
│       ├── __init__.py
│       └── leave_rules.py           # Business rules engine (no Streamlit)
└── sql/
    ├── reset.sql                     # Full schema
    ├── migration_v2.sql              # material_entregado + periodos_bloqueados
    ├── migration_add_admin_read_only.sql
    ├── migration_rpc_insert_with_limit.sql  # RPC for atomic institutional limit
    └── migration_drop_es_pagado_trigger.sql # Remove obsolete trigger
```

## User Roles
| Role | Permissions |
|------|-------------|
| **user** | Submit leave requests, view own history and quota |
| **admin** | Approve/reject, manage users, holidays, blocked periods, reports |
| **admin_read_only** | View everything but cannot approve/reject/modify |
