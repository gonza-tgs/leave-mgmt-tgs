# GEMINI.md - Leave Management App (Colegio TGS)

## Project Overview 🛩️
The **Leave Management App** is a web-based platform designed for **Colegio TGS** to automate and manage employee leave requests. It handles different types of leave (Administrative, Paid, and Unpaid) with automated business rules for administrative days and a manual approval workflow for others.

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
- `app/services/leave_rules.py`: Pure Python business logic for automated leave approvals.
- `app/pages/`: UI components for different user roles (Dashboard, Request Form, Admin Panels).

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
- **Tables:** `profiles` (extends auth users), `solicitudes` (leave requests).
- **RLS:** Row Level Security must be strictly enforced (users can only read/write their own data; admins have full access).
- **Triggers:** Automatic `updated_at` updates and profile creation on user signup.

---

## Business Rules for Administrative Leave (Core Logic)
- **Quota:** 3 days per year (Half-days count as 0.5).
- **Prohibited Days:** Mondays, Fridays, eve of holidays, or day after a holiday.
- **Constraints:** No consecutive days; maximum 2 institutional approvals per day.
- **Flow:** If all rules pass -> `aprobado_auto`. Otherwise -> `pendiente` or `rechazado`.
