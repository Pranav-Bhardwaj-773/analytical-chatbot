import json
import re

import httpx

from app.config import settings
from app.services.schema_catalog import catalog_prompt_text

_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

# New Google AI Studio keys cannot use retired 2.x flash IDs (404 for "new users").
DEFAULT_MODEL_FALLBACKS = (
    "gemini-3.1-flash-lite",
    "gemini-3.5-flash-lite",
    "gemini-3-flash-preview",
    "gemini-flash-lite-latest",
)


class GeminiApiError(RuntimeError):
    """Gemini HTTP/API failure with a user-safe explanation."""

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


def _models_to_try() -> list[str]:
    configured = (settings.gemini_model or "").strip()
    seen: set[str] = set()
    ordered: list[str] = []
    for name in [configured, *DEFAULT_MODEL_FALLBACKS]:
        if not name or name in seen:
            continue
        seen.add(name)
        ordered.append(name)
    return ordered


def _explain_http_error(status_code: int, body_text: str) -> str:
    try:
        err = json.loads(body_text).get("error", {})
        message = str(err.get("message") or body_text)
        code = err.get("code", status_code)
    except json.JSONDecodeError:
        message = body_text[:400]
        code = status_code

    lower = message.lower()
    if status_code == 429 or "quota" in lower or "rate limit" in lower:
        return (
            f"Gemini rate limit or quota reached (HTTP {status_code}). "
            "Wait a few minutes or check billing/limits in Google AI Studio. "
            f"Details: {message}"
        )
    if status_code == 503 or "high demand" in lower or "unavailable" in lower:
        return (
            f"Gemini is temporarily overloaded (HTTP {status_code}), not a usage limit on your key. "
            "Retry in a minute or switch GEMINI_MODEL to gemini-3.1-flash-lite. "
            f"Details: {message}"
        )
    if status_code == 404:
        return (
            f"Gemini model not available for your API key (HTTP {code}). "
            "Set GEMINI_MODEL=gemini-3.1-flash-lite in backend/.env and restart uvicorn. "
            f"Details: {message}"
        )
    if status_code in (401, 403):
        return f"Gemini API key rejected (HTTP {status_code}). Create a new key in Google AI Studio. Details: {message}"
    return f"Gemini request failed (HTTP {status_code}): {message}"


def _call_gemini(model: str, prompt: str) -> dict:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    response = httpx.post(
        url,
        headers={
            "x-goog-api-key": settings.gemini_api_key,
            "Content-Type": "application/json",
        },
        json={
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
        },
        timeout=60,
    )
    if response.is_error:
        raise GeminiApiError(
            _explain_http_error(response.status_code, response.text),
            status_code=response.status_code,
        )
    payload = response.json()
    try:
        text = payload["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise GeminiApiError("Gemini returned an unexpected response shape") from exc
    cleaned = _FENCE.sub("", text.strip())
    plan = json.loads(cleaned)
    if not isinstance(plan, dict):
        raise GeminiApiError("Model did not return a JSON object")
    return plan


def generate_query_plan(question: str) -> dict:
    if not settings.gemini_api_key:
        raise GeminiApiError("GEMINI_API_KEY is missing in backend/.env")

    prompt = f"""
You write PostgreSQL for a school analytics database.
Schema catalog:
{catalog_prompt_text()}

User question:
{question}

Additional rules:
- Never use year_label values outside the catalog list (short form only, e.g. 2020-21).
- School-wide topper: ORDER BY percentage DESC LIMIT 1 on v_exam_outcomes; do NOT filter on rank.
- rank on v_exam_outcomes is per class exam, not school-wide.
- Bottom / lowest performer: ORDER BY percentage ASC with OFFSET when needed.
- Do not filter student_name unless the user gave an exact name.

Reply with JSON only, no markdown:
{{"sql":"SELECT ...","title":"short chart title","chart":"bar"}}

chart must be one of: bar, line, pie, table, none.
If the question cannot be answered from this database, reply:
{{"clarification":"what you need to know"}}
"""

    last_error: GeminiApiError | None = None
    for model in _models_to_try():
        try:
            return _call_gemini(model, prompt)
        except GeminiApiError as exc:
            last_error = exc
            # Retry on wrong model or temporary overload only
            if exc.status_code in (404, 503):
                continue
            raise

    if last_error:
        raise last_error
    raise GeminiApiError("No Gemini model configured")


def generate_query_plan_retry(
    question: str,
    *,
    failed_sql: str,
    db_error: str,
) -> dict:
    """Ask Gemini to fix SQL after Postgres rejected the first attempt."""
    if not settings.gemini_api_key:
        raise GeminiApiError("GEMINI_API_KEY is missing in backend/.env")

    # Keep error text short for the model
    error_snippet = db_error.strip()
    if len(error_snippet) > 800:
        error_snippet = error_snippet[:800] + "..."

    prompt = f"""
You write PostgreSQL for a school analytics database.
Schema catalog (ONLY use columns listed for each view):
{catalog_prompt_text()}

Original user question:
{question}

The following SQL failed when executed on PostgreSQL:
{failed_sql}

Database error:
{error_snippet}

Fix the SQL. Rules:
- Use only columns that exist on the chosen view/table in the catalog.
- Single-school MVP: do NOT filter by school_name unless that column is listed for that view.
- v_exam_outcomes does NOT have school_name.
- One SELECT only.

Reply with JSON only, no markdown:
{{"sql":"SELECT ...","title":"short chart title","chart":"bar"}}

chart must be one of: bar, line, pie, table, none.
"""

    last_error: GeminiApiError | None = None
    for model in _models_to_try():
        try:
            return _call_gemini(model, prompt)
        except GeminiApiError as exc:
            last_error = exc
            if exc.status_code in (404, 503):
                continue
            raise

    if last_error:
        raise last_error
    raise GeminiApiError("No Gemini model configured")