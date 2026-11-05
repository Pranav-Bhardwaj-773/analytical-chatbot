-- School management schema (20 tables)
-- Safe re-run: drops app objects in dependency order

DROP VIEW IF EXISTS v_student_monthly_attendance CASCADE;
DROP VIEW IF EXISTS v_student_daily_attendance CASCADE;
DROP VIEW IF EXISTS v_competitive_qualifiers CASCADE;
DROP VIEW IF EXISTS v_house_roster CASCADE;
DROP VIEW IF EXISTS v_sports_activity CASCADE;
DROP VIEW IF EXISTS v_subject_marks CASCADE;
DROP VIEW IF EXISTS v_exam_outcomes CASCADE;
DROP VIEW IF EXISTS v_block_facilities CASCADE;
DROP VIEW IF EXISTS v_student_enrollment CASCADE;
DROP VIEW IF EXISTS v_student_session_fees CASCADE;
DROP VIEW IF EXISTS v_student_monthly_fees CASCADE;

DROP TABLE IF EXISTS student_daily_attendance CASCADE;
DROP TABLE IF EXISTS student_monthly_fees CASCADE;
DROP TABLE IF EXISTS student_session_fees CASCADE;
DROP TABLE IF EXISTS competitive_exam_results CASCADE;
DROP TABLE IF EXISTS competitive_exams CASCADE;
DROP TABLE IF EXISTS sports_participation CASCADE;
DROP TABLE IF EXISTS sports_events CASCADE;
DROP TABLE IF EXISTS sports CASCADE;
DROP TABLE IF EXISTS exam_marks CASCADE;
DROP TABLE IF EXISTS exam_results CASCADE;
DROP TABLE IF EXISTS exams CASCADE;
DROP TABLE IF EXISTS subjects CASCADE;
DROP TABLE IF EXISTS student_house_memberships CASCADE;
DROP TABLE IF EXISTS houses CASCADE;
DROP TABLE IF EXISTS enrollments CASCADE;
DROP TABLE IF EXISTS students CASCADE;
DROP TABLE IF EXISTS sections CASCADE;
DROP TABLE IF EXISTS classes CASCADE;
DROP TABLE IF EXISTS facilities CASCADE;
DROP TABLE IF EXISTS blocks CASCADE;
DROP TABLE IF EXISTS academic_years CASCADE;
DROP TABLE IF EXISTS schools CASCADE;

CREATE TABLE schools (
    school_id SERIAL PRIMARY KEY,
    school_name VARCHAR(200) NOT NULL,
    address TEXT
);

CREATE TABLE blocks (
    block_id SERIAL PRIMARY KEY,
    school_id INT NOT NULL REFERENCES schools(school_id),
    block_name VARCHAR(50) NOT NULL,
    block_type VARCHAR(100)
);

CREATE TABLE facilities (
    facility_id SERIAL PRIMARY KEY,
    block_id INT NOT NULL REFERENCES blocks(block_id),
    facility_name VARCHAR(150) NOT NULL,
    facility_type VARCHAR(100),
    capacity INT
);

CREATE TABLE academic_years (
    academic_year_id SERIAL PRIMARY KEY,
    year_label VARCHAR(20) NOT NULL UNIQUE,
    start_date DATE,
    end_date DATE
);

CREATE TABLE classes (
    class_id SERIAL PRIMARY KEY,
    class_name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE sections (
    section_id SERIAL PRIMARY KEY,
    class_id INT NOT NULL REFERENCES classes(class_id),
    section_name VARCHAR(20) NOT NULL,
    UNIQUE(class_id, section_name)
);

CREATE TABLE students (
    student_id SERIAL PRIMARY KEY,
    student_name VARCHAR(150) NOT NULL,
    gender VARCHAR(20) NOT NULL
        CHECK (gender IN ('Male', 'Female', 'Other')),
    date_of_birth DATE,
    admission_date DATE
);

CREATE TABLE student_session_fees (
    session_fee_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    fee_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    dues_amount NUMERIC(12,2) GENERATED ALWAYS AS (fee_amount - paid_amount) STORED,
    payment_status VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN (fee_amount - paid_amount) <= 0 THEN 'CLEAR'
            WHEN paid_amount <= 0 THEN 'DUE'
            ELSE 'PARTIAL'
        END
    ) STORED,
    notes TEXT,
    UNIQUE (student_id, academic_year_id)
);

CREATE TABLE student_monthly_fees (
    monthly_fee_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    billing_month DATE NOT NULL,
    fee_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    paid_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
    dues_amount NUMERIC(12,2) GENERATED ALWAYS AS (fee_amount - paid_amount) STORED,
    payment_status VARCHAR(20) GENERATED ALWAYS AS (
        CASE
            WHEN (fee_amount - paid_amount) <= 0 THEN 'CLEAR'
            WHEN paid_amount <= 0 THEN 'DUE'
            ELSE 'PARTIAL'
        END
    ) STORED,
    UNIQUE (student_id, academic_year_id, billing_month)
);

CREATE TABLE student_daily_attendance (
    attendance_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    attendance_date DATE NOT NULL,
    status VARCHAR(20) NOT NULL
        CHECK (status IN ('Present', 'Absent', 'Late')),
    UNIQUE (student_id, attendance_date)
);

CREATE TABLE enrollments (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    class_id INT NOT NULL REFERENCES classes(class_id),
    section_id INT NOT NULL REFERENCES sections(section_id),
    block_id INT NOT NULL REFERENCES blocks(block_id),
    enrollment_status VARCHAR(30) DEFAULT 'ACTIVE',
    UNIQUE(student_id, academic_year_id)
);

CREATE TABLE houses (
    house_id SERIAL PRIMARY KEY,
    house_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE student_house_memberships (
    membership_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    house_id INT NOT NULL REFERENCES houses(house_id),
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    UNIQUE(student_id, academic_year_id)
);

CREATE TABLE subjects (
    subject_id SERIAL PRIMARY KEY,
    subject_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE exams (
    exam_id SERIAL PRIMARY KEY,
    exam_name VARCHAR(150) NOT NULL,
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    class_id INT NOT NULL REFERENCES classes(class_id),
    exam_date DATE
);

CREATE TABLE exam_results (
    exam_result_id SERIAL PRIMARY KEY,
    exam_id INT NOT NULL REFERENCES exams(exam_id),
    student_id INT NOT NULL REFERENCES students(student_id),
    total_marks NUMERIC(8,2),
    percentage NUMERIC(5,2),
    final_status VARCHAR(20),
    rank INT,
    UNIQUE(exam_id, student_id)
);

CREATE TABLE exam_marks (
    exam_mark_id SERIAL PRIMARY KEY,
    exam_result_id INT NOT NULL REFERENCES exam_results(exam_result_id),
    subject_id INT NOT NULL REFERENCES subjects(subject_id),
    marks_obtained NUMERIC(6,2),
    maximum_marks NUMERIC(6,2),
    UNIQUE(exam_result_id, subject_id)
);

CREATE TABLE sports (
    sport_id SERIAL PRIMARY KEY,
    sport_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE sports_events (
    event_id SERIAL PRIMARY KEY,
    sport_id INT NOT NULL REFERENCES sports(sport_id),
    event_name VARCHAR(150) NOT NULL,
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    competition_level VARCHAR(30),
    event_date DATE
);

CREATE TABLE sports_participation (
    participation_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    event_id INT NOT NULL REFERENCES sports_events(event_id),
    participation_status VARCHAR(30),
    qualification_level VARCHAR(30),
    medal VARCHAR(20),
    position INT,
    UNIQUE(student_id, event_id)
);

CREATE TABLE competitive_exams (
    competitive_exam_id SERIAL PRIMARY KEY,
    exam_name VARCHAR(150) NOT NULL,
    exam_category VARCHAR(100)
);

CREATE TABLE competitive_exam_results (
    result_id SERIAL PRIMARY KEY,
    student_id INT NOT NULL REFERENCES students(student_id),
    competitive_exam_id INT NOT NULL REFERENCES competitive_exams(competitive_exam_id),
    academic_year_id INT NOT NULL REFERENCES academic_years(academic_year_id),
    qualification_status VARCHAR(30),
    rank INT,
    score NUMERIC(8,2)
);

CREATE INDEX idx_daily_attendance_year_date
    ON student_daily_attendance(academic_year_id, attendance_date);
CREATE INDEX idx_daily_attendance_student
    ON student_daily_attendance(student_id, attendance_date);
CREATE INDEX idx_session_fees_year_status
    ON student_session_fees(academic_year_id, payment_status);
CREATE INDEX idx_monthly_fees_year_month
    ON student_monthly_fees(academic_year_id, billing_month);
CREATE INDEX idx_monthly_fees_student_year
    ON student_monthly_fees(student_id, academic_year_id);
CREATE INDEX idx_enrollments_year_block ON enrollments(academic_year_id, block_id);
CREATE INDEX idx_exam_results_student ON exam_results(student_id);
CREATE INDEX idx_exams_year_class ON exams(academic_year_id, class_id);
CREATE INDEX idx_sports_events_year_level ON sports_events(academic_year_id, competition_level);
CREATE INDEX idx_competitive_results_year ON competitive_exam_results(academic_year_id, qualification_status);
