from fastapi import Header, HTTPException

from app.config import settings


def require_internal_api_key(
    x_internal_key: str | None = Header(default=None, alias="X-Internal-Key"),
) -> None:
    expected = settings.internal_api_key.strip()
    if not expected:
        return
    if x_internal_key != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
