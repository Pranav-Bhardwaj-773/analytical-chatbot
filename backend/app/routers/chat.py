from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_internal_api_key
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_followups import try_meta_followup
from app.services.dashboard import EMPTY_ANSWER_HINT, answer_from_rows, build_dashboard
from app.services.intent_handlers import plan_to_validated_sql, try_deterministic_plan
from app.services.llm import (
    GeminiApiError,
    generate_query_plan,
    generate_query_plan_retry,
)
from app.services.query_normalize import (
    EMPTY_RESULT_RETRY_HINT,
    normalize_question_text,
    normalize_sql_year_literals,
)
from app.services.sql_validator import SqlValidationError, validate_select_sql

router = APIRouter(tags=["chat"])


def _plain(value):
    if isinstance(value, Decimal):
        return float(value)
    return value


def _run_validated_sql(db: Session, raw_sql: str) -> tuple[str, list[dict]]:
    normalized = normalize_sql_year_literals(raw_sql)
    safe_sql = validate_select_sql(normalized)
    result = db.execute(text(safe_sql)).mappings().all()
    rows = [{key: _plain(value) for key, value in row.items()} for row in result]
    return safe_sql, rows


def _retry_empty_results(
    db: Session,
    question: str,
    *,
    failed_sql: str,
    title: str,
    chart: str,
) -> tuple[str, list[dict], str, str]:
    try:
        fix_plan = generate_query_plan_retry(
            question,
            failed_sql=failed_sql,
            db_error=EMPTY_RESULT_RETRY_HINT,
        )
    except GeminiApiError:
        return failed_sql, [], title, chart

    fixed_sql = str(fix_plan.get("sql") or "").strip()
    if not fixed_sql:
        return failed_sql, [], title, chart

    new_title = str(fix_plan["title"]) if fix_plan.get("title") else title
    new_chart = str(fix_plan["chart"]) if fix_plan.get("chart") else chart
    try:
        safe_sql, rows = _run_validated_sql(db, fixed_sql)
    except (SqlValidationError, Exception):
        db.rollback()
        return failed_sql, [], title, chart
    return safe_sql, rows, new_title, new_chart


def _respond(
    db: Session,
    question: str,
    *,
    raw_sql: str,
    title: str,
    chart: str,
) -> ChatResponse:
    safe_sql = raw_sql
    rows: list[dict] = []

    try:
        safe_sql, rows = _run_validated_sql(db, raw_sql)
    except SqlValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        db.rollback()
        try:
            fix_plan = generate_query_plan_retry(
                question,
                failed_sql=raw_sql,
                db_error=str(exc),
            )
        except GeminiApiError as gem_exc:
            status = 429 if gem_exc.status_code == 429 else 502
            raise HTTPException(
                status_code=status,
                detail=f"Query failed and retry could not reach the model: {gem_exc}",
            ) from gem_exc
        except Exception as retry_exc:
            raise HTTPException(
                status_code=400,
                detail=f"Query failed: {exc}. Retry failed: {retry_exc}",
            ) from retry_exc

        fixed_sql = str(fix_plan.get("sql") or "").strip()
        if not fixed_sql:
            raise HTTPException(
                status_code=400,
                detail=f"Query failed: {exc}. Model did not return fixed SQL.",
            ) from exc

        if fix_plan.get("title"):
            title = str(fix_plan["title"])
        if fix_plan.get("chart"):
            chart = str(fix_plan["chart"])

        try:
            safe_sql, rows = _run_validated_sql(db, fixed_sql)
        except SqlValidationError as val_exc:
            raise HTTPException(
                status_code=400,
                detail=f"Query failed: {exc}. Fixed SQL invalid: {val_exc}",
            ) from val_exc
        except Exception as exc2:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=f"Query failed after retry: {exc2}",
            ) from exc2

    if not rows:
        safe_sql, rows, title, chart = _retry_empty_results(
            db,
            question,
            failed_sql=safe_sql,
            title=title,
            chart=chart,
        )

    empty_hint = EMPTY_ANSWER_HINT if not rows else None
    return ChatResponse(
        answer=answer_from_rows(title, rows, empty_hint=empty_hint),
        sql=safe_sql,
        dashboard=build_dashboard(title, chart, rows),
    )


@router.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_internal_api_key)])
def chat(body: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    question = normalize_question_text(body.message)

    meta = try_meta_followup(db, question, last_sql=body.last_sql)
    if meta is not None:
        return meta

    deterministic = try_deterministic_plan(question)
    if deterministic:
        try:
            raw_sql = plan_to_validated_sql(deterministic)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return _respond(
            db,
            question,
            raw_sql=raw_sql,
            title=deterministic.title,
            chart=deterministic.chart,
        )

    history = (
        [{"role": t.role, "content": t.content} for t in body.history]
        if body.history
        else None
    )
    try:
        plan = generate_query_plan(
            question,
            history=history,
            last_sql=body.last_sql,
        )
    except GeminiApiError as exc:
        status = 429 if exc.status_code == 429 else 502
        raise HTTPException(status_code=status, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Model request failed: {exc}") from exc

    if plan.get("clarification") and not plan.get("sql"):
        return ChatResponse(answer=str(plan["clarification"]))

    raw_sql = str(plan.get("sql") or "").strip()
    if not raw_sql:
        raise HTTPException(status_code=502, detail="Model did not return SQL")

    title = str(plan.get("title") or "Result")
    chart = str(plan.get("chart") or "bar")
    return _respond(db, question, raw_sql=raw_sql, title=title, chart=chart)
