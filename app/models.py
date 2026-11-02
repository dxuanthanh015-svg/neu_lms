from datetime import datetime
import uuid
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import CheckConstraint, Index, UniqueConstraint

db = SQLAlchemy()

def generate_uuid():
    return str(uuid.uuid4())

# ==========================================
# 1. AUTH & USERS (AUTH_USERS)
# ==========================================

class User(db.Model):
    __tablename__ = 'users'
    __table_args__ = (
        CheckConstraint(
            "role <> 'STUDENT' OR administrative_class_id IS NOT NULL",
            name='ck_student_has_administrative_class'
        ),
    )

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    user_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    role = db.Column(db.String(30), nullable=False)  # LECTURER, STUDENT, ACADEMIC_ADMIN, EXAMINER
    administrative_class_id = db.Column(
        db.String(50), db.ForeignKey('administrative_classes.id', ondelete='RESTRICT'), nullable=True
    )
    academic_title = db.Column(db.String(50), nullable=True)  # TS., ThS., PGS.TS., GS.TS.
    auth_provider = db.Column(db.String(30), nullable=False, default='NEU_SSO')
    two_factor_smart_id_enabled = db.Column(db.Boolean, nullable=False, default=True)
    avatar_url = db.Column(db.String(255), nullable=True)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    administrative_class = db.relationship('AdministrativeClass', foreign_keys=[administrative_class_id], backref='students')

    # Relationships
    enrollments = db.relationship('SectionEnrollment', backref='student', lazy=True, foreign_keys='SectionEnrollment.student_user_id')
    instructor_assignments = db.relationship('SectionInstructor', backref='instructor', lazy=True)
    submissions = db.relationship('AssignmentSubmission', backref='student', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_code': self.user_code,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'academic_title': self.academic_title,
            'auth_provider': self.auth_provider,
            'avatar_url': self.avatar_url,
            'is_active': self.is_active
        }


class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.String(50), primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    faculty_name = db.Column(db.String(150), nullable=False)
    head_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    head = db.relationship('User', foreign_keys=[head_user_id])
    classes = db.relationship('AdministrativeClass', backref='department', lazy=True)
    courses = db.relationship('Course', backref='department', lazy=True)


class AdministrativeClass(db.Model):
    __tablename__ = 'administrative_classes'

    id = db.Column(db.String(50), primary_key=True)
    class_code = db.Column(db.String(50), unique=True, nullable=False)
    department_id = db.Column(db.String(50), db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    program_name = db.Column(db.String(150), nullable=False)
    cohort = db.Column(db.String(20), nullable=False)
    total_students = db.Column(db.Integer, nullable=False, default=45)
    advisor_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    advisor = db.relationship('User', foreign_keys=[advisor_user_id])
    enrollments = db.relationship('SectionEnrollment', backref='administrative_class', lazy=True)


# ==========================================
# 2. CURRICULUM & CDIO (CURRICULUM_CDIO)
# ==========================================

class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.String(50), primary_key=True)
    course_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    title_vi = db.Column(db.String(200), nullable=False)
    title_en = db.Column(db.String(200), nullable=True)
    credits = db.Column(db.Integer, nullable=False, default=3)
    theory_hours = db.Column(db.Integer, nullable=False, default=30)
    practical_hours = db.Column(db.Integer, nullable=False, default=15)
    department_id = db.Column(db.String(50), db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    cdio_standard = db.Column(db.String(50), nullable=False, default='CDIO 2024')
    created_by_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    syllabi = db.relationship('CourseSyllabus', backref='course', lazy=True, cascade='all, delete-orphan')
    course_materials = db.relationship('CourseMaterial', backref='course', lazy=True, cascade='all, delete-orphan')
    sections = db.relationship('CourseSection', backref='course', lazy=True)
    clos = db.relationship('CourseLearningOutcome', backref='course', lazy=True, cascade='all, delete-orphan')
    questions = db.relationship('QuestionBank', backref='course', lazy=True)


class CourseMaterial(db.Model):
    __tablename__ = 'course_materials'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    course_id = db.Column(db.String(50), db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    uploaded_by_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(30), nullable=False)
    publication_status = db.Column(db.String(30), nullable=False, default='PENDING_REVIEW')
    reviewed_by_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    review_comment = db.Column(db.Text, nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    uploader = db.relationship('User', foreign_keys=[uploaded_by_user_id])
    reviewer = db.relationship('User', foreign_keys=[reviewed_by_user_id])


class CourseSyllabus(db.Model):
    __tablename__ = 'course_syllabi'

    id = db.Column(db.String(50), primary_key=True)
    course_id = db.Column(db.String(50), db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    version_label = db.Column(db.String(50), nullable=False)
    academic_year = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    approval_status = db.Column(db.String(50), nullable=False, default='APPROVED_FACULTY')
    digitized_progress_percentage = db.Column(db.Integer, nullable=False, default=78)
    approved_by_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    approver = db.relationship('User', foreign_keys=[approved_by_user_id])
    chapters = db.relationship('SyllabusChapter', backref='syllabus', lazy=True, order_by='SyllabusChapter.chapter_order', cascade='all, delete-orphan')
    sections = db.relationship('CourseSection', backref='syllabus', lazy=True)


class SyllabusChapter(db.Model):
    __tablename__ = 'syllabus_chapters'

    id = db.Column(db.String(50), primary_key=True)
    syllabus_id = db.Column(db.String(50), db.ForeignKey('course_syllabi.id', ondelete='CASCADE'), nullable=False)
    chapter_order = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    total_lessons_count = db.Column(db.Integer, nullable=False, default=3)
    allocated_periods = db.Column(db.Integer, nullable=False, default=6)
    completion_metric = db.Column(db.String(50), nullable=False, default='2/3 Đạt')

    lessons = db.relationship('Lesson', backref='chapter', lazy=True, cascade='all, delete-orphan')


class CourseLearningOutcome(db.Model):
    __tablename__ = 'course_learning_outcomes'

    id = db.Column(db.String(50), primary_key=True)
    course_id = db.Column(db.String(50), db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    clo_code = db.Column(db.String(30), nullable=False)
    target_bloom_level = db.Column(db.String(30), nullable=False)  # L1_REMEMBER, L2_UNDERSTAND, L3_APPLY, L4_ANALYZE
    description = db.Column(db.Text, nullable=False)


# ==========================================
# 3. SECTIONS & ENROLLMENT (SECTIONS_ENROLLMENT)
# ==========================================

class CourseSection(db.Model):
    __tablename__ = 'course_sections'

    id = db.Column(db.String(50), primary_key=True)
    section_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    course_id = db.Column(db.String(50), db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    syllabus_id = db.Column(db.String(50), db.ForeignKey('course_syllabi.id', ondelete='RESTRICT'), nullable=False)
    academic_year = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.String(50), nullable=False)
    display_name = db.Column(db.String(255), nullable=False)
    max_capacity = db.Column(db.Integer, nullable=False, default=60)
    current_enrollment_count = db.Column(db.Integer, nullable=False, default=58)
    day_of_week = db.Column(db.String(50), nullable=False)
    period_slot = db.Column(db.String(100), nullable=False)
    instruction_mode = db.Column(db.String(30), nullable=False, default='IN_PERSON')
    physical_room = db.Column(db.String(100), nullable=False)
    virtual_meeting_url = db.Column(db.String(255), nullable=True)
    allow_self_enrollment = db.Column(db.Boolean, nullable=False, default=True)
    current_week_index = db.Column(db.Integer, nullable=False, default=3)
    status = db.Column(db.String(30), nullable=False, default='ACTIVE_IN_PROGRESS')
    created_at = db.Column(db.DateTime, nullable=True, default=datetime.utcnow)

    instructors = db.relationship('SectionInstructor', backref='section', lazy=True, cascade='all, delete-orphan')
    enrollments = db.relationship('SectionEnrollment', backref='section', lazy=True, cascade='all, delete-orphan')
    weeks = db.relationship('SectionWeek', backref='section', lazy=True, order_by='SectionWeek.week_number', cascade='all, delete-orphan')
    materials = db.relationship('LearningMaterial', backref='section', lazy=True)


class SectionInstructor(db.Model):
    __tablename__ = 'section_instructors'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    section_id = db.Column(db.String(50), db.ForeignKey('course_sections.id', ondelete='CASCADE'), nullable=False)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    role_in_section = db.Column(db.String(30), nullable=False, default='PRIMARY_LECTURER')
    can_grade = db.Column(db.Boolean, nullable=False, default=True)
    can_take_attendance = db.Column(db.Boolean, nullable=False, default=True)


class SectionEnrollment(db.Model):
    __tablename__ = 'section_enrollments'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    section_id = db.Column(db.String(50), db.ForeignKey('course_sections.id', ondelete='CASCADE'), nullable=False)
    student_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    administrative_class_id = db.Column(db.String(50), db.ForeignKey('administrative_classes.id', ondelete='RESTRICT'), nullable=False)
    lab_group = db.Column(db.String(50), nullable=True)
    attendance_percentage = db.Column(db.Integer, nullable=False, default=100)
    consecutive_absences = db.Column(db.Integer, nullable=False, default=0)
    study_status = db.Column(db.String(30), nullable=False, default='ACTIVE')  # ACTIVE, WARNING, DISQUALIFIED
    tuition_cleared = db.Column(db.Boolean, nullable=False, default=True)
    enrolled_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


# ==========================================
# 4. LESSONS & MATERIALS (LESSONS_MATERIALS)
# ==========================================

class SectionWeek(db.Model):
    __tablename__ = 'section_weeks'

    id = db.Column(db.String(50), primary_key=True)
    section_id = db.Column(db.String(50), db.ForeignKey('course_sections.id', ondelete='CASCADE'), nullable=False)
    week_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(30), nullable=False, default='UPCOMING')  # COMPLETED, IN_PROGRESS, UPCOMING, LOCKED
    materials_count = db.Column(db.Integer, nullable=False, default=0)
    assignments_count = db.Column(db.Integer, nullable=False, default=0)

    lessons = db.relationship('Lesson', backref='section_week', lazy=True)
    materials = db.relationship('LearningMaterial', backref='section_week', lazy=True)
    assignments = db.relationship('Assignment', backref='section_week', lazy=True)


class Lesson(db.Model):
    __tablename__ = 'lessons'

    id = db.Column(db.String(50), primary_key=True)
    chapter_id = db.Column(db.String(50), db.ForeignKey('syllabus_chapters.id', ondelete='SET NULL'), nullable=True)
    section_week_id = db.Column(db.String(50), db.ForeignKey('section_weeks.id', ondelete='SET NULL'), nullable=True)
    lesson_number = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    lesson_type = db.Column(db.String(30), nullable=False, default='PRACTICE_LAB')  # THEORY, PRACTICE_LAB, QUIZ_REVIEW
    duration_minutes = db.Column(db.Integer, nullable=False, default=25)
    code_snippet_content = db.Column(db.Text, nullable=True)
    learning_goals_json = db.Column(db.Text, nullable=True)  # Store JSON as TEXT for universal MySQL/SQLite compatibility

    materials = db.relationship('LearningMaterial', backref='lesson', lazy=True, cascade='all, delete-orphan')


class LearningMaterial(db.Model):
    __tablename__ = 'learning_materials'

    id = db.Column(db.String(50), primary_key=True)
    section_id = db.Column(db.String(50), db.ForeignKey('course_sections.id', ondelete='CASCADE'), nullable=False)
    section_week_id = db.Column(db.String(50), db.ForeignKey('section_weeks.id', ondelete='SET NULL'), nullable=True)
    lesson_id = db.Column(db.String(50), db.ForeignKey('lessons.id', ondelete='CASCADE'), nullable=True)
    title = db.Column(db.String(255), nullable=False)
    material_type = db.Column(db.String(50), nullable=False)  # SLIDE_PRESENTATION, DOCUMENT_PDF, SOURCE_CODE_ZIP, VIDEO_RECORDING, WEBXR_3D, INTERACTIVE_SANDBOX
    file_url = db.Column(db.String(255), nullable=True)
    file_size_bytes = db.Column(db.BigInteger, nullable=True)
    version_tag = db.Column(db.String(20), nullable=False, default='v1.0')
    is_shared_institutional_repo = db.Column(db.Boolean, nullable=False, default=False)
    institutional_code = db.Column(db.String(50), nullable=True)

    # Thêm các trường nghiệp vụ quản lý bản quyền, tác giả và trạng thái công bố
    author_name = db.Column(db.String(150), nullable=True, default='Ban Giảng Huấn CNTT')
    source_origin = db.Column(db.String(255), nullable=True, default='Đại học Kinh tế Quốc dân')
    license_type = db.Column(db.String(50), nullable=False, default='CC_BY_NC_SA')  # CC_BY_NC_SA, ALL_RIGHTS_RESERVED, OPEN_ACCESS, EDUCATIONAL_USE
    publication_status = db.Column(db.String(30), nullable=False, default='PUBLISHED')  # DRAFT, PENDING_REVIEW, PUBLISHED, ARCHIVED
    summary_desc = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    drm_policy = db.relationship('DrmSecurityPolicy', backref='material', uselist=False, cascade='all, delete-orphan')
    approval_dossiers = db.relationship('MaterialApprovalDossier', backref='material', lazy=True, cascade='all, delete-orphan')
    telemetry_logs = db.relationship('LearningTelemetryLog', backref='material', lazy=True)
    course_links = db.relationship('MaterialCourseLink', backref='material', lazy=True, cascade='all, delete-orphan')


# ==========================================
# 5. DRM & APPROVAL (DRM_APPROVAL)
# ==========================================

class DrmSecurityPolicy(db.Model):
    __tablename__ = 'drm_security_policies'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    material_id = db.Column(db.String(50), db.ForeignKey('learning_materials.id', ondelete='CASCADE'), unique=True, nullable=False)
    view_online_only = db.Column(db.Boolean, nullable=False, default=True)
    dynamic_watermark_enabled = db.Column(db.Boolean, nullable=False, default=True)
    allow_offline_encrypted_study = db.Column(db.Boolean, nullable=False, default=False)
    author_digital_signature = db.Column(db.String(255), nullable=True)
    signed_at = db.Column(db.DateTime, nullable=True)


class MaterialApprovalDossier(db.Model):
    __tablename__ = 'material_approval_dossiers'

    id = db.Column(db.String(50), primary_key=True)
    material_id = db.Column(db.String(50), db.ForeignKey('learning_materials.id', ondelete='CASCADE'), nullable=False)
    submitter_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    current_step = db.Column(db.Integer, nullable=False, default=3)  # 1..4
    status = db.Column(db.String(50), nullable=False, default='PENDING_DEPARTMENT')  # PENDING_DEPARTMENT, ACTION_REQUIRED, APPROVED_PUBLISHED
    reviewer_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    reviewer_comment = db.Column(db.Text, nullable=True)
    sla_deadline_hours = db.Column(db.Integer, nullable=False, default=28)
    sla_remaining_hours = db.Column(db.Integer, nullable=False, default=16)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    submitter = db.relationship('User', foreign_keys=[submitter_user_id])
    reviewer = db.relationship('User', foreign_keys=[reviewer_user_id])


# ==========================================
# 6. ASSIGNMENTS & GRADING (ASSIGNMENTS_GRADING)
# ==========================================

class Assignment(db.Model):
    __tablename__ = 'assignments'

    id = db.Column(db.String(50), primary_key=True)
    section_week_id = db.Column(db.String(50), db.ForeignKey('section_weeks.id', ondelete='CASCADE'), nullable=False)
    assignment_type = db.Column(db.String(30), nullable=False, default='LAB_INDIVIDUAL')
    title = db.Column(db.String(255), nullable=False)
    instructions_markdown = db.Column(db.Text, nullable=False)
    open_time = db.Column(db.DateTime, nullable=False)
    deadline_time = db.Column(db.DateTime, nullable=False)
    cutoff_hard_deadline = db.Column(db.DateTime, nullable=False)
    allow_late_submission = db.Column(db.Boolean, nullable=False, default=True)
    late_penalty_percent_per_day = db.Column(db.Integer, nullable=False, default=10)
    auto_remind_setting = db.Column(db.String(30), nullable=False, default='24_6')
    max_score = db.Column(db.Numeric(4, 2), nullable=False, default=10.00)
    course_weight_percentage = db.Column(db.Numeric(4, 2), nullable=False, default=15.00)
    allowed_submission_formats = db.Column(db.Text, nullable=False, default='["FILE_UPLOAD", "GIT_REPO_URL"]')
    version_label = db.Column(db.String(20), nullable=False, default='v2.1')

    attachments = db.relationship('AssignmentAttachment', backref='assignment', lazy=True, cascade='all, delete-orphan')
    submissions = db.relationship('AssignmentSubmission', backref='assignment', lazy=True, cascade='all, delete-orphan')


class AssignmentAttachment(db.Model):
    __tablename__ = 'assignment_attachments'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    assignment_id = db.Column(db.String(50), db.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(30), nullable=False)
    download_url = db.Column(db.String(255), nullable=False)


class AssignmentSubmission(db.Model):
    __tablename__ = 'assignment_submissions'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    assignment_id = db.Column(db.String(50), db.ForeignKey('assignments.id', ondelete='CASCADE'), nullable=False)
    student_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    submission_status = db.Column(db.String(30), nullable=False, default='SUBMITTED')  # DRAFT, SUBMITTED, LATE, GRADED
    submitted_file_name = db.Column(db.String(255), nullable=True)
    submitted_file_url = db.Column(db.String(255), nullable=True)
    git_repo_url = db.Column(db.String(255), nullable=True)
    student_note = db.Column(db.Text, nullable=True)
    is_late = db.Column(db.Boolean, nullable=False, default=False)
    hours_late = db.Column(db.Numeric(6, 2), nullable=False, default=0.00)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    evaluation = db.relationship('AssignmentEvaluation', backref='submission', uselist=False, cascade='all, delete-orphan')
    files = db.relationship('AssignmentSubmissionAttachment', backref='submission', lazy=True, cascade='all, delete-orphan')


class AssignmentSubmissionAttachment(db.Model):
    __tablename__ = 'assignment_submission_attachments'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    submission_id = db.Column(db.String(50), db.ForeignKey('assignment_submissions.id', ondelete='CASCADE'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    file_size_bytes = db.Column(db.BigInteger, nullable=False)
    file_type = db.Column(db.String(30), nullable=False)
    file_url = db.Column(db.String(255), nullable=False)


class AssignmentEvaluation(db.Model):
    __tablename__ = 'assignment_evaluations'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    submission_id = db.Column(db.String(50), db.ForeignKey('assignment_submissions.id', ondelete='CASCADE'), unique=True, nullable=False)
    grader_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='RESTRICT'), nullable=False)
    raw_score = db.Column(db.Numeric(4, 2), nullable=False)
    late_penalty_deduction = db.Column(db.Numeric(4, 2), nullable=False, default=0.00)
    final_score = db.Column(db.Numeric(4, 2), nullable=False)
    instructor_feedback = db.Column(db.Text, nullable=False)
    graded_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    grader = db.relationship('User', foreign_keys=[grader_user_id])


# ==========================================
# 7. QUESTION BANK & AI (QUESTION_BANK_AI)
# ==========================================

class QuestionBank(db.Model):
    __tablename__ = 'question_banks'

    id = db.Column(db.String(50), primary_key=True)
    course_id = db.Column(db.String(50), db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    chapter_id = db.Column(db.String(50), db.ForeignKey('syllabus_chapters.id', ondelete='SET NULL'), nullable=True)
    bloom_level = db.Column(db.String(30), nullable=False)  # L1_REMEMBER, L2_UNDERSTAND, L3_APPLY, L4_ANALYZE
    topic_tag = db.Column(db.String(100), nullable=False)
    question_type = db.Column(db.String(30), nullable=False, default='MCQ_SINGLE')
    question_stem = db.Column(db.Text, nullable=False)
    default_points = db.Column(db.Numeric(4, 2), nullable=False, default=1.00)
    ai_generated = db.Column(db.Boolean, nullable=False, default=True)
    ai_confidence_score = db.Column(db.Numeric(4, 2), nullable=True)
    rfc_reference = db.Column(db.String(100), nullable=True)
    explanation_logic = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='AI_DRAFT')  # AI_DRAFT, APPROVED, REJECTED
    approved_by_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    usage_in_exams_count = db.Column(db.Integer, nullable=False, default=0)

    chapter = db.relationship('SyllabusChapter', foreign_keys=[chapter_id])
    approver = db.relationship('User', foreign_keys=[approved_by_user_id])
    options = db.relationship('QuestionOption', backref='question', lazy=True, cascade='all, delete-orphan')


class QuestionOption(db.Model):
    __tablename__ = 'question_options'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    question_id = db.Column(db.String(50), db.ForeignKey('question_banks.id', ondelete='CASCADE'), nullable=False)
    option_letter = db.Column(db.String(5), nullable=False)  # A, B, C, D
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    option_role = db.Column(db.String(30), nullable=False, default='DISTRACTOR')  # CORRECT_ANSWER, DISTRACTOR


# ==========================================
# 8. TELEMETRY & AUDIT (TELEMETRY_AUDIT)
# ==========================================

class LearningTelemetryLog(db.Model):
    __tablename__ = 'learning_telemetry_logs'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    student_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    material_id = db.Column(db.String(50), db.ForeignKey('learning_materials.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.String(50), db.ForeignKey('course_sections.id', ondelete='CASCADE'), nullable=False)
    accumulated_seconds = db.Column(db.Integer, nullable=False, default=1125)
    total_video_seconds = db.Column(db.Integer, nullable=False, default=1470)
    watermark_string = db.Column(db.String(150), nullable=False)
    client_ip = db.Column(db.String(50), nullable=False)
    network_speed_mbps = db.Column(db.Numeric(6, 2), nullable=False, default=12.40)
    milestone_80_percent_reached = db.Column(db.Boolean, nullable=False, default=False)
    last_heartbeat_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_user_id])
    section = db.relationship('CourseSection', foreign_keys=[section_id])


# ==========================================
# 9. LIÊN KẾT HỌC LIỆU DÙNG CHUNG LIÊN MÔN
# ==========================================

class MaterialCourseLink(db.Model):
    __tablename__ = 'material_course_links'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    material_id = db.Column(db.String(50), db.ForeignKey('learning_materials.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.String(50), db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False)
    section_id = db.Column(db.String(50), db.ForeignKey('course_sections.id', ondelete='CASCADE'), nullable=True)
    linked_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    notes = db.Column(db.String(255), nullable=True)
    linked_by_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)

    course = db.relationship('Course', foreign_keys=[course_id])
    section = db.relationship('CourseSection', foreign_keys=[section_id])
    linked_by = db.relationship('User', foreign_keys=[linked_by_user_id])


# ==========================================
# 10. PHÂN HỆ HỖ TRỢ NGƯỜI HỌC (STUDENT_SUPPORT)
# ==========================================

class SupportTicket(db.Model):
    __tablename__ = 'support_tickets'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    ticket_code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    student_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    course_id = db.Column(db.String(50), db.ForeignKey('courses.id', ondelete='SET NULL'), nullable=True)
    category = db.Column(db.String(50), nullable=False, default='ACADEMIC_MATERIAL')
    recipient_role = db.Column(db.String(30), nullable=True)  # LECTURER hoặc ACADEMIC_ADMIN (kênh tiếp nhận)
    # ACADEMIC_MATERIAL (Học liệu/Bài học), ASSIGNMENT_HELP (Bài tập/Nộp bài), TECHNICAL_ISSUE (Sự cố kỹ thuật/DRM), EXAM_REVIEW (Phúc khảo/Khảo thí), GENERAL (Chung)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(30), nullable=False, default='NEW')
    priority = db.Column(db.String(20), nullable=False, default='MEDIUM')  # LOW, MEDIUM, HIGH, URGENT
    assigned_staff_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    is_sensitive = db.Column(db.Boolean, nullable=False, default=False)
    sla_hours = db.Column(db.Integer, nullable=True)
    sla_due_at = db.Column(db.DateTime, nullable=True)
    accepted_at = db.Column(db.DateTime, nullable=True)
    resolved_at = db.Column(db.DateTime, nullable=True)
    closed_at = db.Column(db.DateTime, nullable=True)
    resolution = db.Column(db.Text, nullable=True)
    reopen_reason = db.Column(db.Text, nullable=True)
    satisfaction_speed = db.Column(db.Integer, nullable=True)
    satisfaction_attitude = db.Column(db.Integer, nullable=True)
    satisfaction_comment = db.Column(db.Text, nullable=True)
    rated_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('User', foreign_keys=[student_user_id], backref='support_tickets')
    assigned_staff = db.relationship('User', foreign_keys=[assigned_staff_user_id])
    course = db.relationship('Course', foreign_keys=[course_id])
    messages = db.relationship('TicketMessage', backref='ticket', lazy=True, cascade='all, delete-orphan', order_by='TicketMessage.created_at')


class TicketMessage(db.Model):
    __tablename__ = 'ticket_messages'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    ticket_id = db.Column(db.String(50), db.ForeignKey('support_tickets.id', ondelete='CASCADE'), nullable=False)
    sender_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_ai_bot = db.Column(db.Boolean, nullable=False, default=False)
    is_internal = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sender = db.relationship('User', foreign_keys=[sender_user_id])


class TicketAttachment(db.Model):
    __tablename__ = 'ticket_attachments'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    ticket_id = db.Column(db.String(50), db.ForeignKey('support_tickets.id', ondelete='CASCADE'), nullable=False, index=True)
    message_id = db.Column(db.String(50), db.ForeignKey('ticket_messages.id', ondelete='CASCADE'), nullable=False)
    uploader_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_size_bytes = db.Column(db.BigInteger, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ticket = db.relationship('SupportTicket', backref=db.backref('attachments', lazy=True, cascade='all, delete-orphan'))
    message = db.relationship('TicketMessage', backref=db.backref('attachments', lazy=True, cascade='all, delete-orphan'))
    uploader = db.relationship('User', foreign_keys=[uploader_user_id])


class TicketStatusHistory(db.Model):
    __tablename__ = 'ticket_status_history'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    ticket_id = db.Column(db.String(50), db.ForeignKey('support_tickets.id', ondelete='CASCADE'), nullable=False, index=True)
    actor_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    from_status = db.Column(db.String(30), nullable=True)
    to_status = db.Column(db.String(30), nullable=False)
    note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    ticket = db.relationship('SupportTicket', backref=db.backref('status_history', lazy=True, cascade='all, delete-orphan'))
    actor = db.relationship('User', foreign_keys=[actor_user_id])


class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = (
        UniqueConstraint(
            'recipient_user_id', 'notification_type', 'reference_id',
            name='uq_notification_recipient_event'
        ),
        Index('ix_notifications_recipient_created', 'recipient_user_id', 'created_at'),
    )

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    recipient_user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    notification_type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(180), nullable=False)
    message = db.Column(db.Text, nullable=False)
    target_url = db.Column(db.String(500), nullable=False)
    reference_id = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    read_at = db.Column(db.DateTime, nullable=True)

    recipient = db.relationship('User', foreign_keys=[recipient_user_id])


# ==========================================
# 11. HỆ THỐNG & CẤU HÌNH QUẢN TRỊ (SYSTEM_ADMIN)
# ==========================================

class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=False)
    description = db.Column(db.String(255), nullable=True)
    category = db.Column(db.String(50), nullable=False, default='GENERAL')
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'description': self.description,
            'category': self.category,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S') if self.updated_at else ''
        }


class SystemAuditLog(db.Model):
    __tablename__ = 'system_audit_logs'

    id = db.Column(db.String(50), primary_key=True, default=generate_uuid)
    user_id = db.Column(db.String(50), db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    target_entity = db.Column(db.String(100), nullable=True)
    details = db.Column(db.Text, nullable=True)
    ip_address = db.Column(db.String(50), nullable=True, default='127.0.0.1')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    actor = db.relationship('User', foreign_keys=[user_id])

