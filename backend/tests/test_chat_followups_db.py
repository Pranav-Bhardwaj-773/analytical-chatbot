from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings
from app.services.chat_followups import try_meta_followup


def test_meta_followup_returns_distinct_vs_records():
    engine = create_engine(settings.database_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        resp = try_meta_followup(
            session,
            "so how you are counting 420",
            last_sql="SELECT COUNT(*) FROM v_sports_activity WHERE year_label = '2024-25'",
        )
        assert resp is not None
        assert "140" in resp.answer or "different students" in resp.answer.lower()
        assert "count(" not in resp.answer.lower()
        assert "distinct" not in resp.answer.lower() or "different" in resp.answer.lower()
        assert resp.sql and "COUNT(DISTINCT student_name)" in resp.sql
        assert resp.dashboard is not None
    finally:
        session.close()
