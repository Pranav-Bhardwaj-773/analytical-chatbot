from app.services.chat_followups import _looks_like_count_challenge
from app.services.intent_handlers import plan_to_validated_sql, try_deterministic_plan


def test_pass_fail_for_sports_participants_not_whole_school():
    q = (
        "from the sports participants as you mentioned, how much students are passed "
        "in this session"
    )
    plan = try_deterministic_plan(q)
    assert plan is not None
    assert plan.params.get("mode") == "pass_fail_sports_participants"
    sql = plan_to_validated_sql(plan)
    assert "v_sports_activity" in sql
    assert "DISTINCT student_name" in sql
    assert "v_exam_outcomes" in sql


def test_pass_fail_pie_still_school_wide_without_sports():
    plan = try_deterministic_plan("pass vs fail pie chart for session 2020-2021")
    assert plan is not None
    assert plan.params.get("mode") == "pass_fail_pie"


def test_top_sports_by_participation():
    plan = try_deterministic_plan("Top 5 sports by participation this year")
    assert plan is not None
    assert plan.params.get("mode") == "top_sports_participation"
    assert plan.params.get("top_n") == 5
    sql = plan_to_validated_sql(plan)
    assert "GROUP BY sport_name" in sql
    assert "LIMIT 5" in sql


def test_sports_vs_all_students():
    plan = try_deterministic_plan(
        "does every students in this session will takes part in the sports"
    )
    assert plan is not None
    assert plan.params.get("mode") == "sports_enrollment_split"
    sql = plan_to_validated_sql(plan)
    assert "No sports participation" in sql
    assert "v_student_enrollment" in sql


def test_unique_sports_count_sql():
    plan = try_deterministic_plan("how many students participate in sports this year")
    assert plan is not None
    assert plan.params.get("mode") == "sports_unique_and_records"
    sql = plan_to_validated_sql(plan)
    assert "COUNT(DISTINCT student_name)" in sql


def test_count_challenge_detection():
    assert _looks_like_count_challenge("so how you are counting 420")
    assert _looks_like_count_challenge("why did you say 420 participants")
    assert not _looks_like_count_challenge("top 5 sports by participation")
