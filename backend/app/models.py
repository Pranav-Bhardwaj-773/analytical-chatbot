from datetime import date
from decimal import Decimal

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class School(Base):
    __tablename__ = "schools"

    school_id: Mapped[int] = mapped_column(primary_key=True)
    school_name: Mapped[str] = mapped_column(String(200))
    address: Mapped[str | None] = mapped_column(Text)


class Block(Base):
    __tablename__ = "blocks"

    block_id: Mapped[int] = mapped_column(primary_key=True)
    school_id: Mapped[int] = mapped_column(ForeignKey("schools.school_id"))
    block_name: Mapped[str] = mapped_column(String(50))
    block_type: Mapped[str | None] = mapped_column(String(100))


class Facility(Base):
    __tablename__ = "facilities"

    facility_id: Mapped[int] = mapped_column(primary_key=True)
    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.block_id"))
    facility_name: Mapped[str] = mapped_column(String(150))
    facility_type: Mapped[str | None] = mapped_column(String(100))
    capacity: Mapped[int | None] = mapped_column(Integer)


class AcademicYear(Base):
    __tablename__ = "academic_years"

    academic_year_id: Mapped[int] = mapped_column(primary_key=True)
    year_label: Mapped[str] = mapped_column(String(20), unique=True)
    start_date: Mapped[date | None] = mapped_column(Date)
    end_date: Mapped[date | None] = mapped_column(Date)


class ClassRoom(Base):
    __tablename__ = "classes"

    class_id: Mapped[int] = mapped_column(primary_key=True)
    class_name: Mapped[str] = mapped_column(String(50), unique=True)


class Section(Base):
    __tablename__ = "sections"
    __table_args__ = (UniqueConstraint("class_id", "section_name"),)

    section_id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.class_id"))
    section_name: Mapped[str] = mapped_column(String(20))


class Student(Base):
    __tablename__ = "students"

    student_id: Mapped[int] = mapped_column(primary_key=True)
    student_name: Mapped[str] = mapped_column(String(150))
    gender: Mapped[str] = mapped_column(String(20))
    date_of_birth: Mapped[date | None] = mapped_column(Date)
    admission_date: Mapped[date | None] = mapped_column(Date)


class StudentSessionFee(Base):
    __tablename__ = "student_session_fees"
    __table_args__ = (UniqueConstraint("student_id", "academic_year_id"),)

    session_fee_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    notes: Mapped[str | None] = mapped_column(Text)


class StudentMonthlyFee(Base):
    __tablename__ = "student_monthly_fees"
    __table_args__ = (UniqueConstraint("student_id", "academic_year_id", "billing_month"),)

    monthly_fee_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))
    billing_month: Mapped[date] = mapped_column(Date)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=0)


class StudentDailyAttendance(Base):
    __tablename__ = "student_daily_attendance"
    __table_args__ = (UniqueConstraint("student_id", "attendance_date"),)

    attendance_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))
    attendance_date: Mapped[date] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(20))


class Enrollment(Base):
    __tablename__ = "enrollments"
    __table_args__ = (UniqueConstraint("student_id", "academic_year_id"),)

    enrollment_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.class_id"))
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.section_id"))
    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.block_id"))
    enrollment_status: Mapped[str | None] = mapped_column(String(30))


class House(Base):
    __tablename__ = "houses"

    house_id: Mapped[int] = mapped_column(primary_key=True)
    house_name: Mapped[str] = mapped_column(String(100), unique=True)


class StudentHouseMembership(Base):
    __tablename__ = "student_house_memberships"
    __table_args__ = (UniqueConstraint("student_id", "academic_year_id"),)

    membership_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    house_id: Mapped[int] = mapped_column(ForeignKey("houses.house_id"))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))


class Subject(Base):
    __tablename__ = "subjects"

    subject_id: Mapped[int] = mapped_column(primary_key=True)
    subject_name: Mapped[str] = mapped_column(String(100), unique=True)


class Exam(Base):
    __tablename__ = "exams"

    exam_id: Mapped[int] = mapped_column(primary_key=True)
    exam_name: Mapped[str] = mapped_column(String(150))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.class_id"))
    exam_date: Mapped[date | None] = mapped_column(Date)


class ExamResult(Base):
    __tablename__ = "exam_results"
    __table_args__ = (UniqueConstraint("exam_id", "student_id"),)

    exam_result_id: Mapped[int] = mapped_column(primary_key=True)
    exam_id: Mapped[int] = mapped_column(ForeignKey("exams.exam_id"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    total_marks: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    final_status: Mapped[str | None] = mapped_column(String(20))
    rank: Mapped[int | None] = mapped_column(Integer)


class ExamMark(Base):
    __tablename__ = "exam_marks"
    __table_args__ = (UniqueConstraint("exam_result_id", "subject_id"),)

    exam_mark_id: Mapped[int] = mapped_column(primary_key=True)
    exam_result_id: Mapped[int] = mapped_column(ForeignKey("exam_results.exam_result_id"))
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.subject_id"))
    marks_obtained: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))
    maximum_marks: Mapped[Decimal | None] = mapped_column(Numeric(6, 2))


class Sport(Base):
    __tablename__ = "sports"

    sport_id: Mapped[int] = mapped_column(primary_key=True)
    sport_name: Mapped[str] = mapped_column(String(100), unique=True)


class SportsEvent(Base):
    __tablename__ = "sports_events"

    event_id: Mapped[int] = mapped_column(primary_key=True)
    sport_id: Mapped[int] = mapped_column(ForeignKey("sports.sport_id"))
    event_name: Mapped[str] = mapped_column(String(150))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))
    competition_level: Mapped[str | None] = mapped_column(String(30))
    event_date: Mapped[date | None] = mapped_column(Date)


class SportsParticipation(Base):
    __tablename__ = "sports_participation"
    __table_args__ = (UniqueConstraint("student_id", "event_id"),)

    participation_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    event_id: Mapped[int] = mapped_column(ForeignKey("sports_events.event_id"))
    participation_status: Mapped[str | None] = mapped_column(String(30))
    qualification_level: Mapped[str | None] = mapped_column(String(30))
    medal: Mapped[str | None] = mapped_column(String(20))
    position: Mapped[int | None] = mapped_column(Integer)


class CompetitiveExam(Base):
    __tablename__ = "competitive_exams"

    competitive_exam_id: Mapped[int] = mapped_column(primary_key=True)
    exam_name: Mapped[str] = mapped_column(String(150))
    exam_category: Mapped[str | None] = mapped_column(String(100))


class CompetitiveExamResult(Base):
    __tablename__ = "competitive_exam_results"

    result_id: Mapped[int] = mapped_column(primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.student_id"))
    competitive_exam_id: Mapped[int] = mapped_column(ForeignKey("competitive_exams.competitive_exam_id"))
    academic_year_id: Mapped[int] = mapped_column(ForeignKey("academic_years.academic_year_id"))
    qualification_status: Mapped[str | None] = mapped_column(String(30))
    rank: Mapped[int | None] = mapped_column(Integer)
    score: Mapped[Decimal | None] = mapped_column(Numeric(8, 2))
