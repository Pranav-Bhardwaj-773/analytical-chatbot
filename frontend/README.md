# Frontend — School Analytics Chat

Next.js UI with **Auth.js** (email/password + optional Google). Authentication uses **Prisma + PostgreSQL** only — not Supabase Auth.

## Setup

```powershell
cd frontend
copy .env.example .env.local
```

Set at minimum:

- `DATABASE_URL` — Postgres connection (same database as the backend; auth uses `auth_*` tables in `public`)
- `AUTH_SECRET` — run `openssl rand -base64 32` or any long random string
- `AUTH_URL` — `http://localhost:3000` in development

Apply auth tables (do **not** use `db:push` on the shared school database):

```powershell
npx prisma db execute --file prisma/auth_schema.sql --schema prisma/schema.prisma
```

Or paste `prisma/auth_schema.sql` into the Supabase SQL editor.

Optional:

- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google sign-in
- `RESEND_API_KEY` / `EMAIL_FROM` — **required for real inbox email** (see below)
- `INTERNAL_API_KEY` — must match the backend when you lock down FastAPI

### Verification email (Gmail / inbox)

The app sends verification mail via **SMTP (Gmail)** or **Resend**. Without one of these, no message is sent to your inbox.

**Gmail (recommended for local dev)**

1. Turn on 2-Step Verification for your Google account.
2. Create an **App Password**: [Google App Passwords](https://myaccount.google.com/apppasswords).
3. In `.env.local`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your@gmail.com
   SMTP_PASS=xxxx xxxx xxxx xxxx
   EMAIL_FROM=your@gmail.com
   ```
4. Restart `npm run dev`, then use **Resend verification email** on `/verify-email`.

**Resend**

1. API key from [resend.com](https://resend.com).
2. `RESEND_API_KEY=re_...` and `EMAIL_FROM=onboarding@resend.dev` (testing) or your verified domain.

Start the app (backend must be running for chat):

```powershell
npm run dev
```

## Flow

1. Register at `/register` → verification link on `/verify-email` in dev, or email when Resend/SMTP is configured.
2. Open the link → `/login?verified=1`.
3. **Forgot password:** `/forgot-password` → email link → `/reset-password?token=...` (1-hour link; credentials accounts only).
4. Sign in → `/` chat and insights.
5. Chat calls `/api/chat`, which requires a session and proxies to FastAPI.

## Getting Started (Next.js)

See [Next.js documentation](https://nextjs.org/docs).
