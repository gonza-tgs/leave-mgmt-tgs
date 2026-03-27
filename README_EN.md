# Leave Management App — Colegio TGS

Web system for the automated and manual management of employee leave requests for Colegio TGS, developed with **Streamlit** and **Supabase**.

## 🚀 Features
- **Institutional Authentication:** Google OAuth login restricted to the `@colegiotgs.cl` domain.
- **Rules Engine:** Automated approval of administrative leave based on annual quotas and calendar restrictions (holidays, eves, etc.).
- **Admin Panel:** Management of pending requests, reports with dynamic filters, and user role administration.
- **Notifications:** Automated approval/rejection emails via SMTP.
- **Reporting:** Export histories to CSV for administrative analysis.

## 🛠️ Tech Stack
- **Frontend/Backend:** [Streamlit](https://streamlit.io/)
- **Database:** [Supabase](https://supabase.com/) (PostgreSQL)
- **Dependency Management:** [uv](https://github.com/astral-sh/uv)
- **Calendar:** `holidays` (Chile)

## 📋 Local Setup

1. **Install dependencies:**
   ```bash
   uv sync
   ```

2. **Configure Secrets:**
   Create a `.streamlit/secrets.toml` file in the project root with the following keys:
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
   Run the SQL script included in `Plan_Implementacion_Leave_MGMT_App_TGS.md` in the Supabase SQL Editor to create tables, enums, and Row Level Security (RLS) policies.

4. **Run the App:**
   ```bash
   uv run streamlit run main.py
   ```

## 🚀 Deployment and Service Configuration

To make the application fully functional, you need to configure the following external services:

### 1. Database (Supabase)
1. **Project:** Create a project on [Supabase](https://supabase.com/).
2. **Tables and RLS:** Execute the SQL script provided in the implementation plan.
3. **Google Auth:** Enable the Google provider in `Authentication > Providers`. You will need the Client ID and Secret from GCP.

### 2. Google Authentication (GCP)
1. **Project:** Create a project in the [Google Cloud Console](https://console.cloud.google.com/).
2. **OAuth Consent Screen:** Set it to **Internal** mode to restrict access exclusively to the `@colegiotgs.cl` domain.
3. **Credentials:** Create an "OAuth 2.0 Client ID" (Web Application).
4. **Redirection:** Add the callback URL provided by Supabase in its Google configuration panel.

### 3. Notifications (SMTP)
1. **Account:** Create a dedicated email account (e.g., `notifications@colegiotgs.cl`).
2. **Security:** Enable "2-Step Verification" on the Google account.
3. **App Password:** Generate an **App password** specifically for the mail service. This key should be used in the Secrets, not the account's personal password.

### 4. Hosting (Streamlit Cloud)
1. Push the repository to GitHub.
2. Connect your account to [Streamlit Cloud](https://share.streamlit.io/).
3. **Secrets:** Configure the secrets in the Streamlit dashboard by pasting the content of your `.streamlit/secrets.toml`.

## 📂 Project Structure
- `main.py`: Entry point and routing.
- `app/auth.py`: Authentication and session logic.
- `app/database.py`: Supabase client and queries.
- `app/services/leave_rules.py`: Business rules engine.
- `app/pages/`: UI pages (Dashboard, Request, Admin).
- `app/constants.py`: Enum mapping and Spanish labels.
- `GEMINI.md`: Technical context for AI-assisted development.
