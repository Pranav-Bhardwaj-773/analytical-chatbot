from fastapi import APIRouter, Depends, Query
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import require_internal_api_key
from app.schemas.analytics import (
    BlockStudentCount,
    HouseStudentCount,
    LatestYearSummary,
    PassFailCount,
)

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_internal_api_key)],
)

LATEST_YEAR_SQL = text(
    """
    SELECT year_label
    FROM academic_years
    ORDER BY end_date DESC NULLS LAST
    LIMIT 1
    """
)

STUDENTS_BY_BLOCK_SQL = text(
    """
    SELECT block_name, COUNT(DISTINCT student_id)::int AS student_count
    FROM v_student_enrollment
    WHERE year_label = :year_label AND enrollment_status = 'ACTIVE'
    GROUP BY block_name
    ORDER BY block_name
    """
)

PASS_FAIL_SQL = text(
    """
    SELECT final_status, COUNT(*)::int AS cnt
    FROM v_exam_outcomes
    WHERE year_label = :year_label
    GROUP BY final_status
    ORDER BY final_status
    """
)

STUDENTS_BY_HOUSE_SQL = text(
    """
    SELECT house_name, COUNT(DISTINCT student_id)::int AS student_count
    FROM v_house_roster
    WHERE year_label = :year_label
    GROUP BY house_name
    ORDER BY house_name
    """
)


def _resolve_year(db: Session, year_label: str | None) -> str:
    if year_label:
        return year_label
    row = db.execute(LATEST_YEAR_SQL).mappings().first()
    if not row:
        raise ValueError("No academic years in database")
    return row["year_label"]


@router.get("/latest-year/summary", response_model=LatestYearSummary)
def latest_year_summary(
    year_label: str | None = Query(None, description="Defaults to latest academic year"),
    db: Session = Depends(get_db),
) -> LatestYearSummary:
    year = _resolve_year(db, year_label)

    blocks = db.execute(STUDENTS_BY_BLOCK_SQL, {"year_label": year}).mappings().all()
    pass_fail = db.execute(PASS_FAIL_SQL, {"year_label": year}).mappings().all()
    houses = db.execute(STUDENTS_BY_HOUSE_SQL, {"year_label": year}).mappings().all()

    return LatestYearSummary(
        year_label=year,
        students_by_block=[BlockStudentCount(**r) for r in blocks],
        pass_fail=[
            PassFailCount(final_status=r["final_status"], count=r["cnt"]) for r in pass_fail
        ],
        students_by_house=[HouseStudentCount(**r) for r in houses],
    )


@router.get("/students-by-block", response_model=list[BlockStudentCount])
def students_by_block(
    year_label: str | None = None,
    db: Session = Depends(get_db),
) -> list[BlockStudentCount]:
    year = _resolve_year(db, year_label)
    rows = db.execute(STUDENTS_BY_BLOCK_SQL, {"year_label": year}).mappings().all()
    return [BlockStudentCount(**r) for r in rows]