# SDMSMK aThon 2026 — Ideathon Registration Portal

Full Flask web app: landing page, batch-wise student registration/login,
organizing team registration/login, admin approval + payment marking +
confirmation email, and judge registration/login with round-wise scoring.

## 1. Setup

```bash
cd ideathon_app
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## 2. Configure email (Gmail SMTP)

1. Turn on 2-Step Verification on the sending Gmail account.
2. Create an **App Password**: Google Account → Security → 2-Step Verification → App Passwords.
3. Set environment variables before running the app:

```bash
export SMTP_EMAIL="youreventmail@gmail.com"
export SMTP_PASSWORD="your-16-char-app-password"
export ADMIN_USERNAME="admin"          # optional, defaults to admin
export ADMIN_PASSWORD="choose-a-strong-password"
export SECRET_KEY="a-long-random-string"
```

(On Windows CMD use `set VAR=value`, on PowerShell `$env:VAR="value"`.)

## 3. Run

```bash
python app.py
```

Visit http://127.0.0.1:5000

- Admin login: default username `admin`, password `admin@123` (change via env vars above).
- Student / Organizing Team / Judge accounts self-register and need **admin approval**
  before judges can log in (students/org can log in immediately but dashboards show
  "pending" status until approved).

## 4. Flow

1. Student scans the QR / clicks **Register Now**, fills the form, pays the fee, creates a login.
2. Admin logs in → **Students** tab → clicks **Approve**, then **Mark Paid** once payment is verified.
3. Admin clicks **Send Confirmation Email** → student receives a styled HTML confirmation email.
4. Student dashboard automatically shows "Approved" and "Payment Successful".
5. Admin creates **Rounds** (e.g. "Round 1 — Idea Pitch").
6. Approved judges log in and submit/update scores per round per participant.
7. Admin views the **Leaderboard** for any round (average of all judges' scores).

## 5. Notes

- Database: SQLite file `ideathon.db`, created automatically on first run.
- For production, replace the Flask dev server with gunicorn/waitress and set
  `debug=False` (already the default), plus move SECRET_KEY/ADMIN credentials
  to a proper `.env` file or secrets manager — never commit real credentials.
- The QR code, college logo, and Anitha Technologies logo are already placed in
  `static/images/`.
