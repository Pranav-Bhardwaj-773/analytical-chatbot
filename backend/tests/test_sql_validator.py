import pytest

from app.services.sql_validator import SqlValidationError, validate_select_sql


def test_select_on_view_is_allowed():
    sql = validate_select_sql(
        """
        SELECT block_name, COUNT(DISTINCT student_id) AS student_count
        FROM v_student_enrollment
        WHERE year_label = '2024-25' AND enrollment_status = 'ACTIVE'
        GROUP BY block_name
        """
    )
    assert "v_student_enrollment" in sql
    assert "LIMIT 500" in sql.upper()


def test_existing_limit_is_kept():
    sql = validate_select_sql("SELECT student_name FROM students LIMIT 10")
    assert "LIMIT 10" in sql.upper()


def test_delete_is_rejected():
    with pytest.raises(SqlValidationError):
        validate_select_sql("DELETE FROM students")


def test_two_statements_are_rejected():
    with pytest.raises(SqlValidationError):
        validate_select_sql("SELECT 1; DROP TABLE students")


def test_window_top_n_per_year_sql_is_allowed():
    from app.services.intent_handlers import DeterministicPlan, plan_to_validated_sql

    plan = DeterministicPlan(
        sql="",
        title="Top 5 per year",
        chart="table",
        params={"mode": "top_n_per_year", "top_n": 5},
    )
    sql = validate_select_sql(plan_to_validated_sql(plan))
    assert "v_exam_outcomes" in sql


def test_attendance_views_are_allowed():
    sql = validate_select_sql(
        """
        SELECT attendance_date, status
        FROM v_student_daily_attendance
        WHERE year_label = '2024-25'
        """
    )
    assert "v_student_daily_attendance" in sql


def test_unknown_table_is_rejected():
    with pytest.raises(SqlValidationError):
        validate_select_sql("SELECT * FROM pg_catalog.pg_tables")