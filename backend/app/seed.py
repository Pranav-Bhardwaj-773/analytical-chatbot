import argparse
import json
import logging
import random
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

from sqlalchemy.orm import Session

from app.models import (
    AcademicYear,
    Block,
    ClassRoom,
    CompetitiveExam,
    CompetitiveExamResult,
    Enrollment,
    Exam,
    ExamMark,
    ExamResult,
    Facility,
    House,
    School,
    Section,
    Sport,
    SportsEvent,
    SportsParticipation,
    Student,
    StudentHouseMembership,
    StudentDailyAttendance,
    StudentMonthlyFee,
    StudentSessionFee,
    Subject,
)

logger = logging.getLogger(__name__)

CLASS_NUMBERS = {
    "Class 6": 6,
    "Class 7": 7,
    "Class 8": 8,
    "Class 9": 9,
    "Class 10": 10,
    "Class 11": 11,
    "Class 12": 12,
}


def get_seed_json_path() -> Path:
    candidates = [
        Path(__file__).resolve().parent.parent / "school_seed.json",
        Path.cwd() / "school_seed.json",
        Path.cwd() / "backend" / "school_seed.json",
    ]
    for path in candidates:
        if path.is_file():
            return path
    return candidates[0]


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    y, m, d = value.split("-")
    return date(int(y), int(m), int(d))


def _month_starts(start: date, count: int) -> list[date]:
    months: list[date] = []
    year, month = start.year, start.month
    for _ in range(count):
        months.append(date(year, month, 1))
        month += 1
        if month > 12:
            month = 1
            year += 1
    return months


def _school_days(start: date, end: date) -> list[date]:
    days: list[date] = []
    current = start
    while current <= end:
        if current.weekday() < 5:
            days.append(current)
        current += timedelta(days=1)
    return days


def _attendance_status(rng: random.Random) -> str:
    roll = rng.random()
    if roll < 0.90:
        return "Present"
    if roll < 0.96:
        return "Absent"
    return "Late"


def _sample_paid_amount(rng: random.Random, fee_amount: Decimal) -> Decimal:
    roll = rng.random()
    if roll < 0.5:
        return fee_amount
    if roll < 0.75:
        return Decimal("0")
    fraction = Decimal(str(round(rng.uniform(0.2, 0.8), 2)))
    return (fee_amount * fraction).quantize(Decimal("0.01"))


def _build_student_roster(gen: dict, count: int, rng: random.Random) -> list[tuple[str, str]]:
    first_m = list(gen.get("first_names_male") or ["Arjun"])
    first_f = list(gen.get("first_names_female") or ["Ananya"])
    last_names = list(gen.get("last_names") or ["Sharma"])
    used: set[str] = set()
    roster: list[tuple[str, str]] = []
    for i in range(1, count + 1):
        gender = "Male" if rng.random() < 0.52 else "Female"
        pool = first_m if gender == "Male" else first_f
        for attempt in range(200):
            first = rng.choice(pool)
            last = rng.choice(last_names)
            name = f"{first} {last}"
            if name in used:
                name = f"{first} {last} {i}" if attempt > 50 else name
            if name not in used:
                used.add(name)
                roster.append((name, gender))
                break
        else:
            fallback = f"{rng.choice(pool)} {rng.choice(last_names)} {i}"
            used.add(fallback)
            roster.append((fallback, gender))
    return roster


def load_seed_document(path: Path | None = None) -> dict:
    json_path = path or get_seed_json_path()
    if not json_path.exists():
        raise FileNotFoundError(f"school_seed.json not found at {json_path}")
    with open(json_path, encoding="utf-8") as handle:
        return json.load(handle)


def seed_if_empty(db: Session, force: bool = False, json_path: Path | None = None) -> None:
    if force or db.query(School).first() is None:
        if force and db.query(School).first() is not None:
            logger.info("Force reseed: clearing transactional data.")
            _clear_transactional_data(db)
        _load_from_json(db, load_seed_document(json_path))
        logger.info("School seed completed.")
    else:
        logger.info("School already seeded; skipping (use --force to reload).")


def _clear_transactional_data(db: Session) -> None:
    db.query(CompetitiveExamResult).delete()
    db.query(SportsParticipation).delete()
    db.query(ExamMark).delete()
    db.query(ExamResult).delete()
    db.query(Exam).delete()
    db.query(StudentDailyAttendance).delete()
    db.query(StudentMonthlyFee).delete()
    db.query(StudentSessionFee).delete()
    db.query(StudentHouseMembership).delete()
    db.query(Enrollment).delete()
    db.query(Student).delete()
    db.query(SportsEvent).delete()
    db.query(Facility).delete()
    db.query(Section).delete()
    db.query(Block).delete()
    db.query(School).delete()
    db.query(AcademicYear).delete()
    db.query(ClassRoom).delete()
    db.query(House).delete()
    db.query(Subject).delete()
    db.query(Sport).delete()
    db.query(CompetitiveExam).delete()
    db.commit()


def _load_from_json(db: Session, doc: dict) -> None:
    opts = doc.get("seed_options", {})
    rng = random.Random(int(opts.get("random_seed", 42)))
    pass_rate = float(opts.get("pass_rate", 0.88))
    national_rate = float(opts.get("national_qualifier_rate", 0.06))
    competitive_rate = float(opts.get("competitive_qualified_rate", 0.12))

    school_row = doc["school"]
    school = School(
        school_name=school_row["school_name"],
        address=school_row.get("address"),
    )
    db.add(school)
    db.flush()

    block_by_key: dict[str, Block] = {}
    for item in doc["blocks"]:
        block = Block(
            school_id=school.school_id,
            block_name=item["block_name"],
            block_type=item.get("block_type"),
        )
        db.add(block)
        db.flush()
        block_by_key[item["key"]] = block

    for item in doc["facilities"]:
        db.add(
            Facility(
                block_id=block_by_key[item["block_key"]].block_id,
                facility_name=item["facility_name"],
                facility_type=item.get("facility_type"),
                capacity=item.get("capacity"),
            )
        )

    year_by_label: dict[str, AcademicYear] = {}
    years_ordered: list[AcademicYear] = []
    for item in doc["academic_years"]:
        year = AcademicYear(
            year_label=item["year_label"],
            start_date=_parse_date(item.get("start_date")),
            end_date=_parse_date(item.get("end_date")),
        )
        db.add(year)
        db.flush()
        year_by_label[item["year_label"]] = year
        years_ordered.append(year)

    class_by_name: dict[str, ClassRoom] = {}
    for class_name in doc["classes"]:
        classroom = ClassRoom(class_name=class_name)
        db.add(classroom)
        db.flush()
        class_by_name[class_name] = classroom

    section_by_key: dict[tuple[str, str], Section] = {}
    for class_name, classroom in class_by_name.items():
        for section_name in doc["sections_per_class"]:
            section = Section(class_id=classroom.class_id, section_name=section_name)
            db.add(section)
            db.flush()
            section_by_key[(class_name, section_name)] = section

    house_list: list[House] = []
    for house_name in doc["houses"]:
        house = House(house_name=house_name)
        db.add(house)
        db.flush()
        house_list.append(house)

    subject_list: list[Subject] = []
    for subject_name in doc["subjects"]:
        subject = Subject(subject_name=subject_name)
        db.add(subject)
        db.flush()
        subject_list.append(subject)

    sport_by_name: dict[str, Sport] = {}
    for sport_name in doc["sports"]:
        sport = Sport(sport_name=sport_name)
        db.add(sport)
        db.flush()
        sport_by_name[sport_name] = sport

    competitive_by_name: dict[str, CompetitiveExam] = {}
    for item in doc["competitive_exams"]:
        exam = CompetitiveExam(
            exam_name=item["exam_name"],
            exam_category=item.get("exam_category"),
        )
        db.add(exam)
        db.flush()
        competitive_by_name[item["exam_name"]] = exam

    block_list = list(block_by_key.values())
    class_names = doc["classes"]
    section_names = doc["sections_per_class"]

    gen = doc["student_generation"]
    student_count = int(gen.get("count", 120))
    admission_start = int(gen.get("admission_start_year", 2015))
    fee_opts = doc.get("fee_options", {})
    session_fee_amount = Decimal(str(fee_opts.get("session_fee_amount", 48000)))
    monthly_fee_amount = Decimal(str(fee_opts.get("monthly_fee_amount", 4500)))

    roster = _build_student_roster(gen, student_count, rng)
    students: list[Student] = []
    for i, (student_name, gender) in enumerate(roster, start=1):
        admission_year = admission_start + (i % 8)
        dob_year = admission_year - 11 - (i % 3)
        students.append(
            Student(
                student_name=student_name,
                gender=gender,
                date_of_birth=date(dob_year, 5, 1 + (i % 20)),
                admission_date=date(admission_year, 4, 10 + (i % 15)),
            )
        )
    db.add_all(students)
    db.flush()

    sports_events_by_year: dict[int, list[SportsEvent]] = {}
    all_events: list[SportsEvent] = []
    for year in years_ordered:
        events: list[SportsEvent] = []
        for template in doc["sports_event_templates"]:
            sport = sport_by_name[template["sport_name"]]
            month = 8 + (hash(template["event_name"]) % 4)
            event = SportsEvent(
                sport_id=sport.sport_id,
                event_name=f"{template['event_name']} {year.year_label}",
                academic_year_id=year.academic_year_id,
                competition_level=template.get("competition_level"),
                event_date=date(int(year.start_date.year), month, 15) if year.start_date else None,
            )
            events.append(event)
            all_events.append(event)
        sports_events_by_year[year.academic_year_id] = events
    db.add_all(all_events)
    db.flush()

    exams_by_year_class: dict[tuple[int, int], Exam] = {}
    all_exams: list[Exam] = []
    for year in years_ordered:
        for class_name, classroom in class_by_name.items():
            exam = Exam(
                exam_name=f"Annual Examination {year.year_label} — {class_name}",
                academic_year_id=year.academic_year_id,
                class_id=classroom.class_id,
                exam_date=date(int(year.end_date.year), 2, 20) if year.end_date else None,
            )
            all_exams.append(exam)
            exams_by_year_class[(year.academic_year_id, classroom.class_id)] = exam
    db.add_all(all_exams)
    db.flush()

    exam_marks_batch: list[ExamMark] = []
    sports_batch: list[SportsParticipation] = []
    competitive_batch: list[CompetitiveExamResult] = []
    session_fees_batch: list[StudentSessionFee] = []
    monthly_fees_batch: list[StudentMonthlyFee] = []
    attendance_buffer: list[dict] = []
    core_subjects = subject_list[:6]
    school_days_by_year = {
        year.academic_year_id: _school_days(year.start_date, year.end_date)
        for year in years_ordered
        if year.start_date and year.end_date
    }

    def flush_attendance() -> None:
        if not attendance_buffer:
            return
        db.bulk_insert_mappings(StudentDailyAttendance, attendance_buffer)
        attendance_buffer.clear()

    for year in years_ordered:
        year_enrollments: list[Enrollment] = []
        year_houses: list[StudentHouseMembership] = []
        results_by_exam: dict[int, list[ExamResult]] = {}

        for student_idx, student in enumerate(students):
            start_class_num = 6 + (student_idx % 3)
            admission_year = student.admission_date.year if student.admission_date else admission_start
            if year.start_date and year.start_date.year < admission_year:
                continue

            years_since_admission = max(0, year.start_date.year - admission_year)
            class_num = min(12, start_class_num + years_since_admission)
            class_name = f"Class {class_num}"
            classroom = class_by_name[class_name]
            section_name = section_names[student_idx % len(section_names)]
            section = section_by_key[(class_name, section_name)]
            block = block_list[student_idx % len(block_list)]
            house = house_list[student_idx % len(house_list)]

            status = "ACTIVE"
            if class_num == 12 and years_since_admission > 6:
                status = "GRADUATED" if rng.random() < 0.7 else "ACTIVE"

            year_enrollments.append(
                Enrollment(
                    student_id=student.student_id,
                    academic_year_id=year.academic_year_id,
                    class_id=classroom.class_id,
                    section_id=section.section_id,
                    block_id=block.block_id,
                    enrollment_status=status,
                )
            )
            session_fees_batch.append(
                StudentSessionFee(
                    student_id=student.student_id,
                    academic_year_id=year.academic_year_id,
                    fee_amount=session_fee_amount,
                    paid_amount=_sample_paid_amount(rng, session_fee_amount),
                )
            )
            if year.start_date:
                for billing_month in _month_starts(year.start_date, 12):
                    monthly_fees_batch.append(
                        StudentMonthlyFee(
                            student_id=student.student_id,
                            academic_year_id=year.academic_year_id,
                            billing_month=billing_month,
                            fee_amount=monthly_fee_amount,
                            paid_amount=_sample_paid_amount(rng, monthly_fee_amount),
                        )
                    )
            for school_day in school_days_by_year.get(year.academic_year_id, []):
                attendance_buffer.append(
                    {
                        "student_id": student.student_id,
                        "academic_year_id": year.academic_year_id,
                        "attendance_date": school_day,
                        "status": _attendance_status(rng),
                    }
                )
                if len(attendance_buffer) >= 4000:
                    flush_attendance()
            year_houses.append(
                StudentHouseMembership(
                    student_id=student.student_id,
                    house_id=house.house_id,
                    academic_year_id=year.academic_year_id,
                )
            )

            exam = exams_by_year_class[(year.academic_year_id, classroom.class_id)]
            pct = Decimal(str(round(rng.uniform(42, 98), 2)))
            if rng.random() > pass_rate:
                pct = Decimal(str(round(rng.uniform(28, 39), 2)))
            final_status = "Pass" if pct >= 40 else "Fail"
            result = ExamResult(
                exam_id=exam.exam_id,
                student_id=student.student_id,
                total_marks=pct,
                percentage=pct,
                final_status=final_status,
                rank=None,
            )
            results_by_exam.setdefault(exam.exam_id, []).append(result)

            year_events = sports_events_by_year[year.academic_year_id]
            for event in rng.sample(year_events, k=min(3, len(year_events))):
                level = event.competition_level or "School"
                qual = "Qualified" if rng.random() < 0.35 else "Participated"
                if level == "National" and rng.random() < national_rate:
                    qual = "National Qualifier"
                medal = None
                position = None
                if qual == "National Qualifier":
                    medal = rng.choice(["Gold", "Silver", "Bronze", None])
                    position = rng.randint(1, 20)
                sports_batch.append(
                    SportsParticipation(
                        student_id=student.student_id,
                        event_id=event.event_id,
                        participation_status="Completed",
                        qualification_level=qual,
                        medal=medal,
                        position=position,
                    )
                )

            if rng.random() < competitive_rate:
                comp_exam = rng.choice(list(competitive_by_name.values()))
                qualified = rng.random() < 0.55
                competitive_batch.append(
                    CompetitiveExamResult(
                        student_id=student.student_id,
                        competitive_exam_id=comp_exam.competitive_exam_id,
                        academic_year_id=year.academic_year_id,
                        qualification_status="Qualified" if qualified else "Not Qualified",
                        rank=rng.randint(1, 500) if qualified else None,
                        score=Decimal(str(round(rng.uniform(45, 99), 2))),
                    )
                )

        db.add_all(year_enrollments)
        db.add_all(year_houses)
        for exam_results in results_by_exam.values():
            db.add_all(exam_results)
        db.flush()

        for exam_results in results_by_exam.values():
            for result in exam_results:
                for subject in core_subjects:
                    max_marks = Decimal("100")
                    obtained = (result.percentage / Decimal("100") * max_marks).quantize(Decimal("0.01"))
                    exam_marks_batch.append(
                        ExamMark(
                            exam_result_id=result.exam_result_id,
                            subject_id=subject.subject_id,
                            marks_obtained=obtained,
                            maximum_marks=max_marks,
                        )
                    )

    db.add_all(exam_marks_batch)
    db.add_all(sports_batch)
    db.add_all(competitive_batch)
    db.add_all(session_fees_batch)
    db.add_all(monthly_fees_batch)
    flush_attendance()
    db.flush()
    _assign_exam_ranks(db)
    db.commit()


def _assign_exam_ranks(db: Session) -> None:
    exams = db.query(Exam).all()
    for exam in exams:
        results = (
            db.query(ExamResult)
            .filter(ExamResult.exam_id == exam.exam_id)
            .order_by(ExamResult.percentage.desc())
            .all()
        )
        for rank, result in enumerate(results, start=1):
            result.rank = rank


def verify_checkpoint(db: Session) -> dict:
    from sqlalchemy import func, text

    latest = (
        db.query(AcademicYear)
        .order_by(AcademicYear.end_date.desc())
        .first()
    )
    if not latest:
        return {"error": "no academic years"}

    rows = db.execute(
        text(
            """
            SELECT block_name, COUNT(DISTINCT student_id) AS student_count
            FROM v_student_enrollment
            WHERE year_label = :year_label AND enrollment_status = 'ACTIVE'
            GROUP BY block_name
            ORDER BY block_name
            """
        ),
        {"year_label": latest.year_label},
    ).mappings().all()

    totals = db.execute(
        text(
            """
            SELECT final_status, COUNT(*) AS cnt
            FROM v_exam_outcomes
            WHERE year_label = :year_label
            GROUP BY final_status
            """
        ),
        {"year_label": latest.year_label},
    ).mappings().all()

    return {
        "latest_year": latest.year_label,
        "students_by_block_active": [dict(r) for r in rows],
        "pass_fail": [dict(r) for r in totals],
        "schools": db.query(func.count(School.school_id)).scalar(),
        "students": db.query(func.count(Student.student_id)).scalar(),
    }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    from app.database import SessionLocal

    parser = argparse.ArgumentParser(description="Seed school database from school_seed.json")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Clear school data and reload from school_seed.json",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Print MVP checkpoint queries after seeding",
    )
    args = parser.parse_args()

    session = SessionLocal()
    try:
        seed_if_empty(session, force=args.force)
        if args.verify:
            summary = verify_checkpoint(session)
            print("MVP checkpoint:", json.dumps(summary, indent=2, default=str))
        else:
            count = session.query(Student).count()
            print(f"Database seeded successfully. Students in DB: {count}")
    finally:
        session.close()
