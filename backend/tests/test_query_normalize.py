from app.services.intent_handlers import plan_to_validated_sql, try_deterministic_plan
from app.services.query_normalize import (
    extract_year_label,
    normalize_academic_years,
    normalize_question_text,
    normalize_sql_year_literals,
)


def test_normalize_academic_years_in_question():
    assert normalize_academic_years("session 2020-2021") == "session 2020-21"
    assert normalize_academic_years("2020/2021") == "2020-21"


def test_normalize_question_maps_session():
    q = normalize_question_text("topper of session 2020-2021")
    assert "2020-21" in q
    assert "year" in q.lower()


def test_normalize_sql_year_literals():
    sql = "SELECT 1 FROM v_exam_outcomes WHERE year_label = '2020-2021'"
    fixed = normalize_sql_year_literals(sql)
    assert "'2020-21'" in fixed


def test_extract_year_label():
    assert extract_year_label("who is the topper of session 2020-2021") == "2020-21"


def test_deterministic_topper_plan():
    plan = try_deterministic_plan("who is the topper of session 2020-2021")
    assert plan is not None
    sql = plan_to_validated_sql(plan)
    assert "v_exam_outcomes" in sql
    assert "2020-21" in sql
    assert "ORDER BY percentage DESC" in sql


def test_deterministic_top_n_per_year():
    q = (
        "list out top 5 students who are toppers from every session "
        "from the schools starts to till now"
    )
    plan = try_deterministic_plan(q)
    assert plan is not None
    assert plan.params.get("mode") == "top_n_per_year"
    sql = plan_to_validated_sql(plan)
    assert "ROW_NUMBER()" in sql.upper()
    assert "year_rank <= 5" in sql


def test_deterministic_progress_over_time():
    plan = try_deterministic_plan(
        "progress reports of students from the starting of school to till now"
    )
    assert plan is not None
    assert plan.chart == "line"
    assert plan.params.get("mode") == "progress_over_time"
    sql = plan_to_validated_sql(plan)
    assert "GROUP BY year_label" in sql


def test_deterministic_pass_fail_pie():
    plan = try_deterministic_plan("pass vs fail pie chart for session 2020-2021")
    assert plan is not None
    assert plan.chart == "pie"
    sql = plan_to_validated_sql(plan)
    assert "final_status" in sql
    assert "2020-21" in sql


def test_deterministic_fifth_from_bottom():
    plan = try_deterministic_plan(
        "who is the fifth student from bottom in the session 2020-2021"
    )
    assert plan is not None
    sql = plan_to_validated_sql(plan)
    assert "OFFSET 4 LIMIT 1" in sql.upper()
    assert "ORDER BY PERCENTAGE ASC" in sql.upper()


def test_monthly_attendance_trend_uses_default_year():
    plan = try_deterministic_plan(
        "Show monthly student attendance trend for this academic year"
    )
    assert plan is not None
    assert plan.chart == "line"
    sql = plan_to_validated_sql(plan)
    assert "v_student_monthly_attendance" in sql
    assert "2024-25" in sql
    assert "AVG(attendance_percentage)" in sql
