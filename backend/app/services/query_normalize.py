import re

ALLOWED_YEAR_LABELS = frozenset(
    {
        "2015-16",
        "2016-17",
        "2017-18",
        "2018-19",
        "2019-20",
        "2020-21",
        "2021-22",
        "2022-23",
        "2023-24",
        "2024-25",
    }
)

_LONG_YEAR = re.compile(r"\b(20\d{2})\s*[-/–]\s*(20\d{2})\b")


def short_year_label(start_year: str, end_year: str) -> str:
    return f"{start_year}-{end_year[-2:]}"


def normalize_academic_years(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        return short_year_label(match.group(1), match.group(2))

    return _LONG_YEAR.sub(repl, text)


def normalize_question_text(question: str) -> str:
    text = normalize_academic_years(question.strip())
    return re.sub(r"\bsession\b", "year", text, flags=re.IGNORECASE)


def normalize_sql_year_literals(sql: str) -> str:
    def repl(match: re.Match[str]) -> str:
        label = short_year_label(match.group(1), match.group(2))
        return f"'{label}'"

    return re.sub(
        r"'(20\d{2})\s*[-/–]\s*(20\d{2})'",
        repl,
        sql,
        flags=re.IGNORECASE,
    )


def extract_year_label(text: str) -> str | None:
    normalized = normalize_question_text(text)
    for match in re.finditer(r"\b(20\d{2}-\d{2})\b", normalized):
        label = match.group(1)
        if label in ALLOWED_YEAR_LABELS:
            return label
    return None


EMPTY_RESULT_RETRY_HINT = (
    "Query returned 0 rows. A filter value does not exist. "
    "Valid year_label values: 2015-16, 2016-17, 2017-18, 2018-19, 2019-20, "
    "2020-21, 2021-22, 2022-23, 2023-24, 2024-25. "
    "Rewrite 2020-2021 to 2020-21. "
    "School-wide topper: ORDER BY percentage DESC LIMIT 1 on v_exam_outcomes. "
    "Do not filter on rank or student_name. "
    "Nth from bottom: ORDER BY percentage ASC OFFSET (n-1) LIMIT 1."
)
