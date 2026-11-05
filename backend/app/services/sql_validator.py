import sqlglot
from sqlglot import exp
from sqlglot.errors import SqlglotError

ALLOWED_RELATIONS = {
    "schools",
    "blocks",
    "facilities",
    "academic_years",
    "classes",
    "sections",
    "students",
    "enrollments",
    "houses",
    "student_house_memberships",
    "subjects",
    "exams",
    "exam_results",
    "exam_marks",
    "sports",
    "sports_events",
    "sports_participation",
    "competitive_exams",
    "competitive_exam_results",
    "student_session_fees",
    "student_monthly_fees",
    "student_daily_attendance",
    "v_student_enrollment",
    "v_block_facilities",
    "v_exam_outcomes",
    "v_subject_marks",
    "v_sports_activity",
    "v_house_roster",
    "v_competitive_qualifiers",
    "v_student_session_fees",
    "v_student_monthly_fees",
    "v_student_daily_attendance",
    "v_student_monthly_attendance",
}

BLOCKED_FUNCTIONS = {
    "pg_sleep",
    "pg_read_file",
    "pg_ls_dir",
    "lo_import",
    "lo_export",
    "dblink",
}

DEFAULT_LIMIT = 500


class SqlValidationError(ValueError):
    pass


def validate_select_sql(sql: str, *, limit: int = DEFAULT_LIMIT) -> str:
    raw = (sql or "").strip()
    if not raw:
        raise SqlValidationError("SQL is empty")

    try:
        statements = sqlglot.parse(raw, dialect="postgres")
    except SqlglotError as exc:
        raise SqlValidationError(f"SQL could not be parsed: {exc}") from exc

    statements = [stmt for stmt in statements if stmt is not None]
    if len(statements) != 1:
        raise SqlValidationError("Only one SQL statement is allowed")

    tree = statements[0]
    if not isinstance(tree, exp.Query):
        raise SqlValidationError("Only SELECT queries are allowed")
    if isinstance(tree, (exp.Insert, exp.Update, exp.Delete, exp.Merge)):
        raise SqlValidationError("Write statements are not allowed")

    cte_names = {
        cte.alias_or_name.lower()
        for cte in tree.find_all(exp.CTE)
        if cte.alias_or_name
    }

    for table in tree.find_all(exp.Table):
        name = (table.name or "").lower()
        if not name or name in cte_names:
            continue
        if name not in ALLOWED_RELATIONS:
            raise SqlValidationError(f"Relation is not allowed: {table.name}")

    for func in tree.find_all(exp.Func):
        func_name = (func.name or "").lower()
        if func_name in BLOCKED_FUNCTIONS:
            raise SqlValidationError(f"Function is not allowed: {func.name}")

    if tree.args.get("limit") is None:
        tree = tree.limit(limit)

    return tree.sql(dialect="postgres")