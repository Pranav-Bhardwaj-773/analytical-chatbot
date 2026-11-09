import re
from decimal import Decimal
from collections import defaultdict

EMPTY_ANSWER_HINT = (
    "Try the short year form (e.g. 2020-21 instead of 2020-2021)."
)

# User-facing numbers: at most this many decimal places (chat + dashboard).
MAX_DISPLAY_DECIMALS = 2


def _number(value) -> float:
    if isinstance(value, Decimal):
        return float(value)
    return float(value)


def _metric_column(columns: list[str]) -> str | None:
    skip = {"year_label", "year_rank", "student_name", "exam_name", "class_name"}
    for col in columns:
        if col in skip:
            continue
        return col
    return columns[1] if len(columns) > 1 else None


def _is_time_series(rows: list[dict]) -> bool:
    if not rows or "year_label" not in rows[0]:
        return False
    if "student_name" in rows[0] or "year_rank" in rows[0]:
        return False
    per_year: dict[str, int] = defaultdict(int)
    for row in rows:
        per_year[str(row["year_label"])] += 1
    return bool(per_year) and all(count == 1 for count in per_year.values())


def _is_ranking_table(rows: list[dict]) -> bool:
    if not rows:
        return False
    if "year_rank" in rows[0] and "student_name" in rows[0]:
        return True
    if "student_name" not in rows[0] or "year_label" not in rows[0]:
        return False
    per_year: dict[str, int] = defaultdict(int)
    for row in rows:
        per_year[str(row["year_label"])] += 1
    return any(count > 1 for count in per_year.values())


def _row_kpi_label(row: dict, label_key: str) -> str:
    year = row.get("year_label")
    name = row.get("student_name")
    rank = row.get("year_rank")
    if year is not None and name is not None:
        if rank is not None:
            return f"{year} #{rank} {name}"
        return f"{year} — {name}"
    if year is not None and "student_name" not in row:
        metric = _metric_column(list(row.keys()))
        if metric and metric in row:
            return str(year)
    return str(row[label_key])


def _normalize_display_value(value):
    if value is None or isinstance(value, (str, bool)):
        return value
    try:
        number = float(_number(value))
    except (TypeError, ValueError):
        return value
    if _is_whole_number(number):
        return int(round(number))
    return round(number, MAX_DISPLAY_DECIMALS)


def _resolve_chart_type(chart: str, rows: list[dict], *, time_series: bool) -> str:
    if chart in {"bar", "line", "pie"}:
        resolved = chart
    elif chart in ("table", "none"):
        return chart
    else:
        resolved = "bar"
    if time_series and resolved == "bar":
        return "line"
    return resolved


def build_dashboard(title: str, chart: str, rows: list[dict]) -> dict:
    if not rows:
        return {"title": title, "kpis": [], "chart": None, "table": {"columns": [], "rows": []}}

    columns = list(rows[0].keys())
    label_key = columns[0]
    value_key = columns[1] if len(columns) > 1 else columns[0]
    time_series = _is_time_series(rows)
    ranking_table = _is_ranking_table(rows)

    if time_series:
        metric = _metric_column(columns) or value_key
        label_key = "year_label"
        value_key = metric or value_key

    kpis = []
    points = []
    numeric = True
    sorted_rows = (
        sorted(rows, key=lambda r: str(r.get("year_label", ""))) if time_series else rows
    )

    for index, row in enumerate(sorted_rows):
        label = _row_kpi_label(row, label_key)
        if time_series and "year_label" in row:
            label = str(row["year_label"])
        raw_value = row.get(value_key) if value_key in row else row[label_key]
        try:
            number = _number(raw_value)
        except (TypeError, ValueError):
            numeric = False
            number = None
        display_value = (
            _normalize_display_value(number) if number is not None else raw_value
        )
        kpis.append(
            {
                "id": f"{index}-{label}",
                "label": label,
                "value": display_value,
            }
        )

    build_chart = chart not in ("none", "table") and not ranking_table
    if build_chart and numeric:
        if time_series:
            for row in sorted_rows:
                y = _normalize_display_value(_number(row[value_key]))
                points.append({"x": str(row["year_label"]), "y": y})
        elif chart == "pie" or (
            len(rows) <= 8 and label_key.lower() in ("label", "final_status", "status")
        ):
            for row in rows:
                lk = label_key if label_key in row else columns[0]
                vk = value_key if value_key in row else columns[1]
                points.append({"x": str(row[lk]), "y": _normalize_display_value(_number(row[vk]))})
        else:
            for row in rows:
                lk = columns[0]
                vk = columns[1] if len(columns) > 1 else columns[0]
                try:
                    points.append({"x": str(row[lk]), "y": _normalize_display_value(_number(row[vk]))})
                except (TypeError, ValueError):
                    numeric = False
                    points.clear()
                    break

    chart_spec = None
    resolved = _resolve_chart_type(chart, rows, time_series=time_series)
    if build_chart and numeric and points and resolved in {"bar", "line", "pie"}:
        chart_spec = {
            "type": resolved,
            "title": title,
            "points": points,
        }

    preview = []
    for row in rows[:50]:
        normalized: dict = {}
        for key, val in row.items():
            if isinstance(val, Decimal):
                normalized[key] = _normalize_display_value(val)
            elif isinstance(val, (int, float)):
                normalized[key] = _normalize_display_value(val)
            else:
                normalized[key] = val
        preview.append(normalized)

    return {
        "title": title,
        "kpis": kpis[:12],
        "chart": chart_spec,
        "table": {"columns": columns, "rows": preview},
    }


def _year_from_title(title: str) -> str | None:
    match = re.search(r"\((\d{4}-\d{2})\)", title)
    return match.group(1) if match else None


def _is_whole_number(value: float) -> bool:
    return abs(value - round(value)) < 1e-9


def _format_display_number(value, *, as_integer: bool = False) -> str:
    try:
        number = float(_number(value))
    except (TypeError, ValueError):
        return str(value)
    if as_integer or _is_whole_number(number):
        whole = int(round(number))
        return f"{whole:,}" if abs(whole) >= 1000 else str(whole)
    rounded = round(number, MAX_DISPLAY_DECIMALS)
    text = f"{rounded:.{MAX_DISPLAY_DECIMALS}f}".rstrip("0").rstrip(".")
    return text


def _format_count(value) -> str:
    return _format_display_number(value, as_integer=True)


def _scalar_uses_integer(key: str, title: str) -> bool:
    key_lower = key.lower()
    title_lower = title.lower()
    if any(
        token in key_lower
        for token in ("count", "total_students", "unique_students", "student_count")
    ):
        return True
    if "participation" in key_lower and "score" not in key_lower:
        return True
    if any(token in key_lower for token in ("score", "percentage", "average", "avg")):
        return False
    if any(token in title_lower for token in ("score", "percentage", "average", "avg")):
        return False
    return False


def _format_single_scalar(title: str, key: str, value) -> str:
    year = _year_from_title(title)
    prefix = f"In {year}, " if year else ""
    title_lower = title.lower()
    key_lower = key.lower()
    count = _format_display_number(value, as_integer=_scalar_uses_integer(key, title))

    if key_lower in ("student_count", "unique_students", "total_students"):
        if "sport" in title_lower:
            return (
                f"{prefix}{count} students took part in at least one sport "
                f"this session."
            )
        if "active" in title_lower or "enrollment" in title_lower:
            return f"{prefix}there are {count} students with active enrollment."
        return f"{prefix}there are {count} students."

    if key_lower in ("participation_records", "participation_count"):
        return (
            f"{prefix}students signed up for sports events {count} times in total "
            f"(including students who joined more than one sport)."
        )

    clean_title = re.sub(r"\s*\(\d{4}-\d{2}\)\s*", "", title).strip()
    return f"{prefix}{clean_title}: {count}."


def _format_row_snippet(row: dict) -> str:
    if "label" in row and "value" in row:
        label = str(row["label"])
        val = _format_display_number(
            row["value"],
            as_integer=_is_whole_number(float(_number(row["value"]))),
        )
        return f"{label}: {val}"
    if "metric" in row and "value" in row:
        return f"{row['metric']}: {_format_count(row['value'])}"
    if "sport_name" in row:
        name = row["sport_name"]
        if "participation_count" in row:
            return f"{name}: {int(_number(row['participation_count']))} sign-ups"
        if "unique_students" in row:
            return f"{name}: {int(_number(row['unique_students']))} students"
    if "student_name" in row and "percentage" in row:
        rank = row.get("year_rank")
        prefix = f"#{rank} " if rank is not None else ""
        pct = _format_display_number(row["percentage"])
        return f"{prefix}{row['student_name']}: {pct}"
    if "year_label" in row and len(row) >= 2:
        metric = _metric_column(list(row.keys()))
        if metric and metric in row and "student_name" not in row:
            return f"{row['year_label']}: {_format_display_number(row[metric])}"
    items = list(row.items())
    if len(items) >= 2:
        return f"{items[0][1]}: {items[1][1]}"
    return str(items[0][1])


def answer_from_rows(
    title: str,
    rows: list[dict],
    *,
    empty_hint: str | None = None,
) -> str:
    if not rows:
        msg = "I could not find any data that matches that question."
        if empty_hint:
            return f"{msg} {empty_hint}"
        return msg
    if len(rows) == 1 and len(rows[0]) == 1:
        key, value = next(iter(rows[0].items()))
        return _format_single_scalar(title, key, value)

    if len(rows) == 1:
        row = rows[0]
        if "unique_students" in row and "participation_records" in row:
            year = _year_from_title(title) or "this session"
            students = int(_number(row["unique_students"]))
            signups = int(_number(row["participation_records"]))
            return (
                f"In {year}, {students} students took part in sports, with {signups} "
                f"total sign-ups across events (students in more than one sport are "
                f"counted again for each event)."
            )

    if _is_time_series(rows):
        metric = _metric_column(list(rows[0].keys())) or list(rows[0].keys())[1]
        ordered = sorted(rows, key=lambda r: str(r["year_label"]))
        snippets = [
            f"{r['year_label']}: {round(_number(r[metric]), 2)}" for r in ordered[:10]
        ]
        extra = "" if len(rows) <= 10 else " See the chart for all years."
        return f"{title}. " + ", ".join(snippets) + "." + extra

    if rows and "year_label" in rows[0] and "student_name" in rows[0]:
        by_year: dict[str, list[dict]] = defaultdict(list)
        for row in rows:
            by_year[str(row["year_label"])].append(row)
        sections = []
        for year in sorted(by_year.keys()):
            snippets = [_format_row_snippet(r) for r in by_year[year][:8]]
            sections.append(f"{year}: " + ", ".join(snippets))
        extra = "" if len(rows) <= 40 else " See the table for the full list."
        return f"{title}. " + " | ".join(sections) + "." + extra

    if len(rows) <= 6 and rows[0]:
        cols = list(rows[0].keys())
        if cols[0].lower() in ("label", "final_status") or "value" in cols:
            parts = [_format_row_snippet(row) for row in rows]
            return f"{title}. " + ", ".join(parts) + "."

    parts = [_format_row_snippet(row) for row in rows[:8]]
    extra = "" if len(rows) <= 8 else f" Here are the first 8 of {len(rows)} results."
    return f"{title}. " + ", ".join(parts) + "." + extra
