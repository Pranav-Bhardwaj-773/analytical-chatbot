from app.services.dashboard import answer_from_rows, build_dashboard


def test_build_dashboard_rounds_long_decimals():
    rows = [{"year_label": "2015-16", "average_percentage": 70.274117647059}]
    dash = build_dashboard("Average Student Score Trend", "line", rows)
    assert dash["kpis"][0]["value"] == 70.27
    assert dash["table"]["rows"][0]["average_percentage"] == 70.27


def test_time_series_builds_line_chart():
    rows = [
        {"year_label": "2015-16", "average_percentage": 64.5},
        {"year_label": "2016-17", "average_percentage": 68.4},
    ]
    dash = build_dashboard("Progress", "line", rows)
    assert dash["chart"] is not None
    assert dash["chart"]["type"] == "line"
    assert len(dash["chart"]["points"]) == 2
    assert dash["chart"]["points"][0]["x"] == "2015-16"


def test_time_series_answer_text():
    rows = [
        {"year_label": "2020-21", "average_percentage": 68.48},
    ]
    text = answer_from_rows("Progress", rows)
    assert "2020-21: 68.48" in text
    assert "2020-21: 2020-21" not in text


def test_scalar_answer_preserves_decimal_scores():
    text = answer_from_rows(
        "Average Student Score (2024-25)",
        [{"average_score": 67.408}],
    )
    assert "67.41" in text
    assert "67.408" not in text


def test_scalar_answer_plain_english_not_column_names():
    text = answer_from_rows(
        "Total Unique Students Participating in Sports (2024-25)",
        [{"student_count": 140}],
    )
    assert "student_count" not in text
    assert "140" in text
    assert "students" in text.lower()


def test_ranking_table_skips_chart():
    rows = [
        {"year_label": "2020-21", "student_name": "Arjun Sharma", "percentage": 90, "year_rank": 1},
        {"year_label": "2020-21", "student_name": "Priya Patel", "percentage": 88, "year_rank": 2},
    ]
    dash = build_dashboard("Top students", "bar", rows)
    assert dash["chart"] is None
