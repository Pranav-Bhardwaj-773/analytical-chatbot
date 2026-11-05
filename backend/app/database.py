from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

_BACKEND_DIR = Path(__file__).resolve().parent.parent
SQL_DIR = _BACKEND_DIR / "sql"


class Base(DeclarativeBase):
    pass


def normalize_database_url(url: str) -> str:
    if not url:
        return url
    if url.startswith("sqlite"):
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+" not in url.split("://", 1)[0]:
        return url.replace("postgresql://", "postgresql+psycopg2://", 1)
    return url


def _engine_kwargs() -> dict:
    url = settings.database_url
    if not url:
        raise RuntimeError("DATABASE_URL is not set. Add it to backend/.env")
    if url.startswith("sqlite"):
        return {"connect_args": {"check_same_thread": False}}
    return {"pool_pre_ping": True, "pool_recycle": 300}


engine = create_engine(normalize_database_url(settings.database_url), **_engine_kwargs())

if normalize_database_url(settings.database_url).startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _sqlite_pragma(dbapi_conn, _connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()


SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def run_sql_file(path: Path, *, password_replace: str | None = None) -> None:
    sql = path.read_text(encoding="utf-8")
    if password_replace is not None:
        sql = sql.replace("__CHATBOT_READONLY_PASSWORD__", password_replace.replace("'", "''"))
    with engine.begin() as conn:
        conn.execute(text(sql))


def run_migrations() -> None:
    run_sql_file(SQL_DIR / "001_schema.sql")
    run_sql_file(SQL_DIR / "002_views.sql")
    run_sql_file(
        SQL_DIR / "003_readonly_role.sql",
        password_replace=settings.chatbot_readonly_password,
    )
