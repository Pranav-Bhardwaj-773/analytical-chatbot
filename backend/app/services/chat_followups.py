import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.chat import ChatResponse
from app.services.dashboard import answer_from_rows, build_dashboard
from app.services.query_normalize import ALLOWED_YEAR_LABELS, extract_year_label
from app.services.sql_validator import validate_select_sql

_DEFAULT_YEAR = "2024-25"

_COUNT_CHALLENGE = re.compile(
    r"\b(how|why)\b.{0,40}\b(count(?:ing)?|number|figure|total)\b|"
    r"\bwhy\b.{0,40}\bsay\b|"
    r"\bexplain\b.{0,30}\b(previous|prior|that|420|\d+)\b|"
    r"\bso\s+how\s+(?:are\s+you|did\s+you)\b",
    re.IGNORECASE,
)


def _looks_like_count_challenge(question: str) -> bool:
    return bool(_COUNT_CHALLENGE.search(question))


def _sports_context(question: str, last_sql: str | None) -> bool:
    lower = question.lower()
    if re.search(r"\bsports?\b", lower):
        return True
    if re.search(r"\bparticipat", lower):
        return True
    if re.search(r"\b420\b", lower):
        return True
    if last_sql and "v_sports_activity" in last_sql.lower():
        return True
    return False


def _sports_metrics_sql(year: str) -> str:
    if year not in ALLOWED_YEAR_LABELS:
        raise ValueError("year_label not allowed")
    return f"""
        SELECT
            COUNT(DISTINCT student_name) AS unique_students,
            COUNT(*) AS participation_records
        FROM v_sports_activity
        WHERE year_label = '{year}'
    """.strip()


def try_meta_followup(
    db: Session,
    question: str,
    *,
    last_sql: str | None,
) -> ChatResponse | None:
    if not _looks_like_count_challenge(question):
        return None
    if not _sports_context(question, last_sql):
        return None

    year = extract_year_label(question) or _DEFAULT_YEAR
    if year not in ALLOWED_YEAR_LABELS:
        year = _DEFAULT_YEAR

    raw_sql = _sports_metrics_sql(year)
    safe_sql = validate_select_sql(raw_sql)
    row = db.execute(text(safe_sql)).mappings().first()
    if not row:
        return None

    unique = int(row["unique_students"])
    records = int(row["participation_records"])
    title = f"Sports participation ({year})"
    answer = (
        f"In {year}, {unique} different students joined at least one sport. "
        f"The {records} figure is the total number of sports sign-ups across all "
        f"events—if someone plays cricket and football, they are counted twice. "
        f"So {records} is not how many students there are; {unique} is."
    )
    rows = [
        {
            "metric": "Students in sports",
            "value": unique,
        },
        {
            "metric": "Total event sign-ups",
            "value": records,
        },
    ]
    return ChatResponse(
        answer=answer,
        sql=safe_sql,
        dashboard=build_dashboard(title, "bar", rows),
    )
