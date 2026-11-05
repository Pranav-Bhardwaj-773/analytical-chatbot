CREATE OR REPLACE VIEW v_student_enrollment AS
SELECT
    s.student_id,
    s.student_name,
    s.gender,
    e.enrollment_id,
    e.enrollment_status,
    ay.academic_year_id,
    ay.year_label,
    ay.start_date,
    ay.end_date,
    c.class_id,
    c.class_name,
    sec.section_id,
    sec.section_name,
    b.block_id,
    b.block_name,
    b.block_type,
    sch.school_id,
    sch.school_name
FROM enrollments e
JOIN students s ON s.student_id = e.student_id
JOIN academic_years ay ON ay.academic_year_id = e.academic_year_id
JOIN classes c ON c.class_id = e.class_id
JOIN sections sec ON sec.section_id = e.section_id
JOIN blocks b ON b.block_id = e.block_id
JOIN schools sch ON sch.school_id = b.school_id;

CREATE OR REPLACE VIEW v_block_facilities AS
SELECT
    sch.school_id,
    sch.school_name,
    b.block_id,
    b.block_name,
    b.block_type,
    f.facility_id,
    f.facility_name,
    f.facility_type,
    f.capacity
FROM facilities f
JOIN blocks b ON b.block_id = f.block_id
JOIN schools sch ON sch.school_id = b.school_id;

CREATE OR REPLACE VIEW v_exam_outcomes AS
SELECT
    er.exam_result_id,
    er.student_id,
    s.student_name,
    er.exam_id,
    ex.exam_name,
    ex.exam_date,
    ay.academic_year_id,
    ay.year_label,
    c.class_id,
    c.class_name,
    er.total_marks,
    er.percentage,
    er.final_status,
    er.rank
FROM exam_results er
JOIN students s ON s.student_id = er.student_id
JOIN exams ex ON ex.exam_id = er.exam_id
JOIN academic_years ay ON ay.academic_year_id = ex.academic_year_id
JOIN classes c ON c.class_id = ex.class_id;

CREATE OR REPLACE VIEW v_subject_marks AS
SELECT
    em.exam_mark_id,
    em.marks_obtained,
    em.maximum_marks,
    sub.subject_id,
    sub.subject_name,
    er.exam_result_id,
    er.student_id,
    s.student_name,
    ex.exam_id,
    ex.exam_name,
    ay.year_label,
    c.class_name
FROM exam_marks em
JOIN exam_results er ON er.exam_result_id = em.exam_result_id
JOIN subjects sub ON sub.subject_id = em.subject_id
JOIN students s ON s.student_id = er.student_id
JOIN exams ex ON ex.exam_id = er.exam_id
JOIN academic_years ay ON ay.academic_year_id = ex.academic_year_id
JOIN classes c ON c.class_id = ex.class_id;

CREATE OR REPLACE VIEW v_sports_activity AS
SELECT
    sp.participation_id,
    sp.student_id,
    s.student_name,
    sp.event_id,
    se.event_name,
    se.event_date,
    se.competition_level,
    sp.participation_status,
    sp.qualification_level,
    sp.medal,
    sp.position,
    sp_sport.sport_id,
    sp_sport.sport_name,
    ay.academic_year_id,
    ay.year_label
FROM sports_participation sp
JOIN students s ON s.student_id = sp.student_id
JOIN sports_events se ON se.event_id = sp.event_id
JOIN sports sp_sport ON sp_sport.sport_id = se.sport_id
JOIN academic_years ay ON ay.academic_year_id = se.academic_year_id;

CREATE OR REPLACE VIEW v_house_roster AS
SELECT
    shm.membership_id,
    shm.student_id,
    s.student_name,
    h.house_id,
    h.house_name,
    ay.academic_year_id,
    ay.year_label
FROM student_house_memberships shm
JOIN students s ON s.student_id = shm.student_id
JOIN houses h ON h.house_id = shm.house_id
JOIN academic_years ay ON ay.academic_year_id = shm.academic_year_id;

CREATE OR REPLACE VIEW v_competitive_qualifiers AS
SELECT
    cer.result_id,
    cer.student_id,
    s.student_name,
    ce.competitive_exam_id,
    ce.exam_name,
    ce.exam_category,
    ay.academic_year_id,
    ay.year_label,
    cer.qualification_status,
    cer.rank,
    cer.score
FROM competitive_exam_results cer
JOIN students s ON s.student_id = cer.student_id
JOIN competitive_exams ce ON ce.competitive_exam_id = cer.competitive_exam_id
JOIN academic_years ay ON ay.academic_year_id = cer.academic_year_id;

CREATE OR REPLACE VIEW v_student_daily_attendance AS
SELECT
    a.attendance_id,
    a.student_id,
    s.student_name,
    s.gender,
    ay.academic_year_id,
    ay.year_label,
    a.attendance_date,
    a.status,
    c.class_name,
    sec.section_name,
    b.block_name
FROM student_daily_attendance a
JOIN students s ON s.student_id = a.student_id
JOIN academic_years ay ON ay.academic_year_id = a.academic_year_id
JOIN enrollments e
    ON e.student_id = a.student_id
    AND e.academic_year_id = a.academic_year_id
JOIN classes c ON c.class_id = e.class_id
JOIN sections sec ON sec.section_id = e.section_id
JOIN blocks b ON b.block_id = e.block_id;

CREATE OR REPLACE VIEW v_student_monthly_attendance AS
SELECT
    s.student_id,
    s.student_name,
    s.gender,
    ay.year_label,
    date_trunc('month', a.attendance_date)::date AS attendance_month,
    c.class_name,
    sec.section_name,
    b.block_name,
    COUNT(*) FILTER (WHERE a.status = 'Present')::int AS present_days,
    COUNT(*) FILTER (WHERE a.status = 'Absent')::int AS absent_days,
    COUNT(*) FILTER (WHERE a.status = 'Late')::int AS late_days,
    COUNT(*)::int AS total_days,
    ROUND(
        (
            100.0 * COUNT(*) FILTER (WHERE a.status IN ('Present', 'Late'))
            / NULLIF(COUNT(*), 0)
        )::numeric,
        2
    ) AS attendance_percentage
FROM student_daily_attendance a
JOIN students s ON s.student_id = a.student_id
JOIN academic_years ay ON ay.academic_year_id = a.academic_year_id
JOIN enrollments e
    ON e.student_id = a.student_id
    AND e.academic_year_id = a.academic_year_id
JOIN classes c ON c.class_id = e.class_id
JOIN sections sec ON sec.section_id = e.section_id
JOIN blocks b ON b.block_id = e.block_id
GROUP BY
    s.student_id,
    s.student_name,
    s.gender,
    ay.year_label,
    date_trunc('month', a.attendance_date)::date,
    c.class_name,
    sec.section_name,
    b.block_name;

CREATE OR REPLACE VIEW v_student_session_fees AS
SELECT
    ssf.session_fee_id,
    ssf.student_id,
    s.student_name,
    s.gender,
    ay.academic_year_id,
    ay.year_label,
    ssf.fee_amount,
    ssf.paid_amount,
    ssf.dues_amount,
    ssf.payment_status
FROM student_session_fees ssf
JOIN students s ON s.student_id = ssf.student_id
JOIN academic_years ay ON ay.academic_year_id = ssf.academic_year_id;

CREATE OR REPLACE VIEW v_student_monthly_fees AS
SELECT
    smf.monthly_fee_id,
    smf.student_id,
    s.student_name,
    s.gender,
    ay.academic_year_id,
    ay.year_label,
    smf.billing_month,
    smf.fee_amount,
    smf.paid_amount,
    smf.dues_amount,
    smf.payment_status
FROM student_monthly_fees smf
JOIN students s ON s.student_id = smf.student_id
JOIN academic_years ay ON ay.academic_year_id = smf.academic_year_id;
