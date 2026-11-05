# School analytics backend

PostgreSQL (Supabase) schema, seed data, and analytics views for the analytical chatbot MVP. No vector database.

## Prerequisites

- Python 3.12+
- `DATABASE_URL` in `.env` (admin / `postgres` user for migrations and seeding)
- Optional: `CHATBOT_READONLY_PASSWORD` for `sql/003_readonly_role.sql` (default in `.env.example`)

## Setup

```powershell
cd backend
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

Copy `.env.example` to `.env` and set your Supabase connection string.

### Migrate + seed (one command)

```powershell
.venv\Scripts\python -m app.setup_db --force --verify
```

- `--force` — reload reference data and regenerated enrollments/exams/sports from `school_seed.json`
- `--verify` — prints student counts by block and pass/fail for the latest academic year
- `--skip-migrate` — only re-run seed (schema already applied)

### Separate commands

```powershell
.venv\Scripts\python -m app.migrate
.venv\Scripts\python -m app.seed --force --verify
```

## Data layout

| Path | Purpose |
|------|--------|
| `sql/001_schema.sql` | 20 tables + indexes |
| `sql/002_views.sql` | Analytics views for Text-to-SQL |
| `sql/003_readonly_role.sql` | `chatbot_readonly` role |
| `school_seed.json` | School, blocks, facilities, years, classes, sports templates |
| `app/seed.py` | Loads JSON + generates students, enrollments, exams, sports |

## Analytics views

- `v_student_enrollment`
- `v_block_facilities`
- `v_exam_outcomes`
- `v_subject_marks`
- `v_sports_activity`
- `v_house_roster`
- `v_competitive_qualifiers`
- `v_student_daily_attendance`
- `v_student_monthly_attendance`

## MVP checkpoint query (Supabase SQL editor)

```sql
SELECT block_name, COUNT(DISTINCT student_id) AS student_count
FROM v_student_enrollment
WHERE year_label = '2024-25' AND enrollment_status = 'ACTIVE'
GROUP BY block_name
ORDER BY block_name;
```

After setup, point the FastAPI runtime at a **readonly** connection URL using role `chatbot_readonly` (not the admin URL).
