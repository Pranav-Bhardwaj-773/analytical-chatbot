import re
from dataclasses import dataclass

from app.services.query_normalize import ALLOWED_YEAR_LABELS, extract_year_label

_WORD_TO_N: dict[str, int] = {
    "one": 1,
    "first": 1,
    "1st": 1,
    "two": 2,
    "second": 2,
    "2nd": 2,
    "three": 3,
    "third": 3,
    "3rd": 3,
    "four": 4,
    "fourth": 4,
    "4th": 4,
    "five": 5,
    "fifth": 5,
    "5th": 5,
    "six": 6,
    "sixth": 6,
    "6th": 6,
    "seven": 7,
    "seventh": 7,
    "7th": 7,
    "eight": 8,
    "eighth": 8,
    "8th": 8,
    "nine": 9,
    "ninth": 9,
    "9th": 9,
    "ten": 10,
    "tenth": 10,
    "10th": 10,
}

_TOPPER = re.compile(
    r"\b(topper|top\s+student|highest\s+(?:scor|mark|percent)|best\s+student)\b",
    re.IGNORECASE,
)
_BOTTOM = re.compile(
    r"\b(?:from\s+)?(?:the\s+)?bottom\b|\b(?:lowest|worst)\s+(?:scor|student|mark|percent)",
    re.IGNORECASE,
)
_N_FROM_BOTTOM = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    r"1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th)\b"
    r"(?:\s+\w+){0,6}\s*(?:from\s+)?(?:the\s+)?bottom",
    re.IGNORECASE,
)
_ALL_YEARS = re.compile(
    r"\b(?:every|each|all)\s+(?:session|year|academic\s+year)s?\b|"
    r"\bfrom\s+(?:the\s+)?(?:school(?:s)?\s+)?start\b|"
    r"\btill\s+now\b|\buntil\s+now\b|\bacross\s+all\s+years\b",
    re.IGNORECASE,
)
_TOP_N = re.compile(
    r"\btop\s+(\d+|one|two|three|four|five|six|seven|eight|nine|ten)\b",
    re.IGNORECASE,
)
_N_FROM_TOP = re.compile(
    r"\b(\d+|one|two|three|four|five|six|seven|eight|nine|ten|"
    r"first|second|third|fourth|fifth|sixth|seventh|eighth|ninth|tenth|"
    r"1st|2nd|3rd|4th|5th|6th|7th|8th|9th|10th)\b"
    r"(?:\s+\w+){0,6}\s*(?:from\s+)?(?:the\s+)?top\b",
    re.IGNORECASE,
)
_CLASS = re.compile(r"\bclass\s+(\d{1,2})\b", re.IGNORECASE)


def _extract_n_from_top(question: str) -> int | None:
    match = _N_FROM_TOP.search(question)
    if match:
        return _parse_n(match.group(1))
    if re.search(r"\bfrom\s+(?:the\s+)?top\b", question, re.IGNORECASE):
        loose = re.search(
            r"\b(\d+|fifth|fourth|third|second|first|five|four|three|two|one)\b",
            question,
            re.IGNORECASE,
        )
        if loose:
            return _parse_n(loose.group(1))
    return None


_PROGRESS = re.compile(
    r"\bprogress\b|\bprogress\s+report|\bover\s+time\b",
    re.IGNORECASE,
)
_PASS_FAIL = re.compile(
    r"\bpass\b.*\bfail\b|\bfail\b.*\bpass\b",
    re.IGNORECASE,
)


def _match_progress_over_time(question: str) -> bool:
    if not _PROGRESS.search(question):
        return False
    if _top_n_per_all_years(question) is not None:
        return False
    return bool(
        _ALL_YEARS.search(question)
        or re.search(r"\bprogress\b", question, re.IGNORECASE)
    )


def _match_pass_fail_pie(question: str) -> bool:
    return bool(_PASS_FAIL.search(question))


def _top_n_per_all_years(question: str) -> int | None:
    if not _ALL_YEARS.search(question):
        return None
    match = _TOP_N.search(question)
    if match:
        return _parse_n(match.group(1))
    if re.search(r"\btoppers?\b", question, re.IGNORECASE):
        return 5
    return None


@dataclass(frozen=True)
class DeterministicPlan:
    sql: str
    title: str
    chart: str
    params: dict[str, object]


def _parse_n(token: str) -> int | None:
    token = token.lower()
    if token.isdigit():
        n = int(token)
        return n if n >= 1 else None
    return _WORD_TO_N.get(token)


def _extract_n_from_bottom(question: str) -> int | None:
    match = _N_FROM_BOTTOM.search(question)
    if match:
        return _parse_n(match.group(1))
    if not _BOTTOM.search(question):
        return None
    # "fifth student from bottom" with word before bottom
    loose = re.search(
        r"\b(\d+|fifth|fourth|third|second|first|five|four|three|two|one)\b",
        question,
        re.IGNORECASE,
    )
    if loose and _BOTTOM.search(question):
        return _parse_n(loose.group(1))
    return None


def _class_filter(question: str) -> tuple[str, dict[str, object]]:
    match = _CLASS.search(question)
    if not match:
        return "", {}
    class_name = f"Class {match.group(1)}"
    return " AND class_name = :class_name", {"class_name": class_name}


def plan_to_validated_sql(plan: DeterministicPlan) -> str:
    """Build a literal SQL string safe for validate_select_sql (params are allowlisted)."""
    mode = plan.params.get("mode")
    if mode == "top_n_per_year":
        n = int(plan.params["top_n"])
        if n < 1 or n > 20:
            raise ValueError("top_n out of range")
        return f"""
            SELECT year_label, student_name, percentage, year_rank
            FROM (
              SELECT year_label, student_name, percentage,
                     ROW_NUMBER() OVER (
                       PARTITION BY year_label ORDER BY percentage DESC
                     ) AS year_rank
              FROM v_exam_outcomes
            ) ranked
            WHERE year_rank <= {n}
            ORDER BY year_label, year_rank
        """.strip()

    if mode == "progress_over_time":
        return """
            SELECT year_label,
                   ROUND(AVG(percentage)::numeric, 2) AS average_percentage
            FROM v_exam_outcomes
            GROUP BY year_label
            ORDER BY year_label
        """.strip()

    if mode == "monthly_attendance_trend":
        year = str(plan.params["year_label"])
        if year not in ALLOWED_YEAR_LABELS:
            raise ValueError("year_label not allowed")
        return f"""
            SELECT attendance_month,
                   ROUND(AVG(attendance_percentage)::numeric, 2) AS attendance_percentage
            FROM v_student_monthly_attendance
            WHERE year_label = '{year}'
            GROUP BY attendance_month
            ORDER BY attendance_month
        """.strip()

    if mode == "pass_fail_pie":
        year = str(plan.params["year_label"])
        if year not in ALLOWED_YEAR_LABELS:
            raise ValueError("year_label not allowed")
        return f"""
            SELECT final_status AS label, COUNT(*) AS value
            FROM v_exam_outcomes
            WHERE year_label = '{year}'
            GROUP BY final_status
            ORDER BY final_status
        """.strip()

    year = str(plan.params["year_label"])
    if year not in ALLOWED_YEAR_LABELS:
        raise ValueError("year_label not allowed")

    class_clause = ""
    if "class_name" in plan.params:
        class_name = str(plan.params["class_name"])
        if not re.fullmatch(r"Class \d{1,2}", class_name):
            raise ValueError("class_name not allowed")
        class_clause = f" AND class_name = '{class_name}'"

    base = (
        f"SELECT student_name, percentage FROM v_exam_outcomes "
        f"WHERE year_label = '{year}'{class_clause}"
    )
    if "offset" in plan.params:
        offset = int(plan.params["offset"])
        if offset < 0:
            raise ValueError("invalid offset")
        if plan.params.get("sort") == "desc":
            return f"{base} ORDER BY percentage DESC OFFSET {offset} LIMIT 1"
        return f"{base} ORDER BY percentage ASC OFFSET {offset} LIMIT 1"
    return f"{base} ORDER BY percentage DESC LIMIT 1"


_ATTENDANCE = re.compile(r"\battendance\b", re.IGNORECASE)
_MONTHLY_ATTENDANCE = re.compile(
    r"\bmonthly\b|\bmonth[- ]over[- ]month\b|\btrend\b",
    re.IGNORECASE,
)
_THIS_YEAR = re.compile(r"\bthis\s+(?:academic\s+)?year\b", re.IGNORECASE)
_DEFAULT_YEAR = "2024-25"


def try_deterministic_plan(question: str) -> DeterministicPlan | None:
    if _ATTENDANCE.search(question) and _MONTHLY_ATTENDANCE.search(question):
        year = extract_year_label(question)
        if year is None and _THIS_YEAR.search(question):
            year = _DEFAULT_YEAR
        if year is None:
            year = _DEFAULT_YEAR
        if year in ALLOWED_YEAR_LABELS:
            return DeterministicPlan(
                sql="",
                title=f"Monthly attendance trend ({year})",
                chart="line",
                params={"mode": "monthly_attendance_trend", "year_label": year},
            )

    if _match_progress_over_time(question):
        return DeterministicPlan(
            sql="",
            title="Average student progress over time",
            chart="line",
            params={"mode": "progress_over_time"},
        )

    top_n_all = _top_n_per_all_years(question)
    if top_n_all is not None:
        return DeterministicPlan(
            sql="",
            title=f"Top {top_n_all} students per academic year",
            chart="table",
            params={"mode": "top_n_per_year", "top_n": top_n_all},
        )

    year = extract_year_label(question)
    if year and year in ALLOWED_YEAR_LABELS and _match_pass_fail_pie(question):
        return DeterministicPlan(
            sql="",
            title=f"Pass vs Fail ({year})",
            chart="pie",
            params={"mode": "pass_fail_pie", "year_label": year},
        )

    if not year or year not in ALLOWED_YEAR_LABELS:
        return None

    lower = question.lower()
    class_clause, class_params = _class_filter(question)

    n_top = _extract_n_from_top(question)
    if n_top is not None:
        title = f"{_ordinal(n_top)} from top ({year})"
        params = {"year_label": year, "offset": n_top - 1, "sort": "desc", **class_params}
        return DeterministicPlan(
            sql="",
            title=title,
            chart="none",
            params=params,
        )

    if _TOPPER.search(lower) and not _TOP_N.search(lower):
        title = f"Topper of {year}"
        if class_params:
            title = f"Topper in {class_params['class_name']} ({year})"
        sql = f"""
            SELECT student_name, percentage
            FROM v_exam_outcomes
            WHERE year_label = :year_label{class_clause}
            ORDER BY percentage DESC
            LIMIT 1
        """
        params: dict[str, object] = {"year_label": year, **class_params}
        return DeterministicPlan(sql=sql.strip(), title=title, chart="none", params=params)

    n = _extract_n_from_bottom(question)
    if n is not None:
        title = f"{_ordinal(n)} from bottom ({year})"
        sql = f"""
            SELECT student_name, percentage
            FROM v_exam_outcomes
            WHERE year_label = :year_label{class_clause}
            ORDER BY percentage ASC
            OFFSET :offset LIMIT 1
        """
        params = {"year_label": year, "offset": n - 1, **class_params}
        return DeterministicPlan(sql=sql.strip(), title=title, chart="none", params=params)

    return None


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix} student"
