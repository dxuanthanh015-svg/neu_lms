import json
import os
import uuid
from datetime import datetime, timedelta
from werkzeug.utils import secure_filename
from flask import Blueprint, current_app, render_template, request, redirect, url_for, flash, send_from_directory, abort
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import func
from app.models import (
    db, Course, CourseSyllabus, SyllabusChapter, Lesson,
    LearningMaterial, DrmSecurityPolicy, CourseLearningOutcome,
    CourseSection, Department, QuestionBank, SectionEnrollment,
    SectionInstructor, SectionWeek, Assignment, AssignmentAttachment,
    AssignmentSubmission, AssignmentSubmissionAttachment, CourseMaterial,
    Notification,
)
from app.auth import login_required, get_current_user

curriculum_bp = Blueprint('curriculum', __name__)

@curriculum_bp.route('/curriculum')
@login_required
def view_curriculum():
    current_user = get_current_user()
    if current_user.role == 'LECTURER':
        instructor_section_ids = [row.section_id for row in SectionInstructor.query.filter_by(user_id=current_user.id).all()]
        sections = CourseSection.query.filter(CourseSection.id.in_(instructor_section_ids)).order_by(CourseSection.section_code).all()
        section_id = request.args.get('section_id', '').strip()
        selected_section = next((row for row in sections if row.id == section_id), None) if section_id else None
        weeks = []
        course_materials = []
        can_manage_course_materials = False
        if selected_section:
            weeks = SectionWeek.query.filter_by(section_id=selected_section.id).order_by(SectionWeek.week_number).all()
            can_manage_course_materials = selected_section.course.created_by_user_id == current_user.id
            course_materials = CourseMaterial.query.filter_by(
                course_id=selected_section.course_id,
                publication_status='PUBLISHED'
            ).order_by(CourseMaterial.created_at.desc()).all()
            existing_numbers = {week.week_number for week in weeks}
            for week_number in range(1, 16):
                if week_number not in existing_numbers:
                    db.session.add(SectionWeek(
                        id=f'week_{uuid.uuid4().hex[:16]}',
                        section_id=selected_section.id,
                        week_number=week_number,
                        start_date=None,
                        end_date=None,
                        title=f'Tuần {week_number}',
                        status='UPCOMING',
                        materials_count=0,
                        assignments_count=0
                    ))
            if len(existing_numbers) < 15:
                db.session.commit()
                weeks = SectionWeek.query.filter_by(section_id=selected_section.id).order_by(SectionWeek.week_number).all()
        return render_template(
            'lecturer_sections.html',
            sections=sections,
            selected_section=selected_section,
            selected_course=selected_section.course if selected_section else None,
            weeks=weeks,
            course_materials=course_materials,
            can_manage_course_materials=False,
            current_nav='curriculum'
        )

    if current_user.role == 'STUDENT':
        enrollments = SectionEnrollment.query.filter_by(
            student_user_id=current_user.id
        ).order_by(SectionEnrollment.enrolled_at.desc()).all()
        completed_week_rows = db.session.query(
            SectionWeek.section_id,
            func.count(func.distinct(SectionWeek.id))
        ).join(
            Assignment, Assignment.section_week_id == SectionWeek.id
        ).join(
            AssignmentSubmission, AssignmentSubmission.assignment_id == Assignment.id
        ).filter(
            AssignmentSubmission.student_user_id == current_user.id,
            AssignmentSubmission.submission_status.in_(['SUBMITTED', 'LATE', 'GRADED']),
            SectionWeek.section_id.in_([enrollment.section_id for enrollment in enrollments])
        ).group_by(SectionWeek.section_id).all() if enrollments else []
        completed_weeks_by_section = {section_id: min(int(count), 15) for section_id, count in completed_week_rows}
        course_progress = {
            enrollment.section_id: {
                'completed': completed_weeks_by_section.get(enrollment.section_id, 0),
                'percent': round(completed_weeks_by_section.get(enrollment.section_id, 0) * 100 / 15)
            }
            for enrollment in enrollments
        }
        section_id = request.args.get('section_id', '').strip()
        selected_enrollment = next(
            (enrollment for enrollment in enrollments if enrollment.section_id == section_id),
            None
        ) if section_id else None
        materials = []
        weeks = []
        week_materials = []
        unassigned_materials = []
        course_materials = []
        selected_course = None
        assignments_by_week = {}
        if selected_enrollment:
            weeks = SectionWeek.query.filter_by(
                section_id=selected_enrollment.section_id
            ).order_by(SectionWeek.week_number).all()
            materials = LearningMaterial.query.filter_by(
                section_id=selected_enrollment.section_id,
                publication_status='PUBLISHED'
            ).order_by(LearningMaterial.title).all()
            materials_by_week = {}
            for material in materials:
                if material.section_week_id:
                    materials_by_week.setdefault(material.section_week_id, []).append(material)
                else:
                    unassigned_materials.append(material)
            week_materials = [(week, materials_by_week.get(week.id, [])) for week in weeks]
            week_assignments = [(week, Assignment.query.filter_by(section_week_id=week.id).order_by(Assignment.deadline_time).all()) for week in weeks]
            assignments_by_week = {week.id: assignments for week, assignments in week_assignments}
            selected_course = selected_enrollment.section.course
            course_materials = CourseMaterial.query.filter_by(
                course_id=selected_course.id, publication_status='PUBLISHED'
            ).order_by(CourseMaterial.created_at.desc()).all()
        else:
            week_assignments = []
        return render_template(
            'student_course_sections.html',
            enrollments=enrollments,
            course_progress=course_progress,
            selected_enrollment=selected_enrollment,
            materials=materials,
            week_materials=week_materials,
            week_assignments=week_assignments,
            assignments_by_week=assignments_by_week,
            course_materials=course_materials,
            selected_course=selected_course,
            can_manage_course_materials=False,
            unassigned_materials=unassigned_materials,
            current_nav='curriculum'
        )

    all_courses = Course.query.order_by(Course.course_code).all()
    req_course_id = request.args.get('course_id')
    course = None
    if req_course_id:
        course = Course.query.filter((Course.id == req_course_id) | (Course.course_code == req_course_id)).first()
    if not course:
        course = Course.query.filter_by(id='INT3110').first() or Course.query.first()

    syllabus = None
    section = None
    if course:
        syllabus = CourseSyllabus.query.filter_by(course_id=course.id).first()
        section = CourseSection.query.filter_by(course_id=course.id).first()

    chapters = []
    if syllabus:
        chapters = SyllabusChapter.query.filter_by(syllabus_id=syllabus.id)\
            .order_by(SyllabusChapter.chapter_order).all()

    # Bài học đang chọn
    lesson_id = request.args.get('lesson_id')
    active_lesson = None
    if lesson_id and syllabus:
        active_lesson = Lesson.query.join(
            SyllabusChapter, Lesson.chapter_id == SyllabusChapter.id
        ).filter(
            Lesson.id == lesson_id,
            SyllabusChapter.syllabus_id == syllabus.id
        ).first()

    if not active_lesson:
        if chapters and chapters[0].lessons:
            active_lesson = chapters[0].lessons[0]

    # Danh sách học liệu của bài học đang chọn
    materials = []
    if active_lesson:
        materials = LearningMaterial.query.filter_by(lesson_id=active_lesson.id).all()

    # Chính sách DRM
    drm_policy = None
    for m in materials:
        if m.drm_policy:
            drm_policy = m.drm_policy
            break

    # Parse learning goals
    goals = []
    if active_lesson and active_lesson.learning_goals_json:
        try:
            goals = json.loads(active_lesson.learning_goals_json)
        except Exception:
            goals = [active_lesson.learning_goals_json]

    # Chuẩn đầu ra
    clos = []
    if course:
        clos = CourseLearningOutcome.query.filter_by(course_id=course.id).all()

    total_lessons = sum(len(ch.lessons) for ch in chapters) if chapters else 0
    materials_count = LearningMaterial.query.filter_by(section_id=section.id).count() if section else 0
    questions_count = QuestionBank.query.filter_by(course_id=course.id).count() if course else 0

    return render_template(
        'curriculum.html',
        course=course,
        all_courses=all_courses,
        syllabus=syllabus,
        section=section,
        chapters=chapters,
        active_lesson=active_lesson,
        materials=materials,
        drm_policy=drm_policy,
        goals=goals,
        clos=clos,
        total_lessons=total_lessons,
        materials_count=materials_count,
        questions_count=questions_count,
        current_nav='curriculum'
    )


ALLOWED_WEEK_MATERIAL_EXTENSIONS = {
    'png': 'IMAGE', 'jpg': 'IMAGE', 'jpeg': 'IMAGE', 'gif': 'IMAGE', 'webp': 'IMAGE',
    'doc': 'DOCUMENT_WORD', 'docx': 'DOCUMENT_WORD',
    'xls': 'SPREADSHEET_EXCEL', 'xlsx': 'SPREADSHEET_EXCEL',
    'ppt': 'PRESENTATION_POWERPOINT', 'pptx': 'PRESENTATION_POWERPOINT',
    'pdf': 'DOCUMENT_PDF'
}

ALLOWED_ASSIGNMENT_EXTENSIONS = set(ALLOWED_WEEK_MATERIAL_EXTENSIONS) | {'zip', 'rar', 'txt', 'csv', 'py', 'java', 'js', 'html', 'css', 'sql', 'ipynb'}


def _parse_local_datetime(value):
    try:
        return datetime.strptime(value, '%Y-%m-%dT%H:%M')
    except (TypeError, ValueError):
        return None


def _can_manage_section(user, section_id):
    if user.role in ['ADMIN', 'ACADEMIC_ADMIN']:
        return True
    return user.role == 'LECTURER' and SectionInstructor.query.filter_by(user_id=user.id, section_id=section_id).first() is not None


def _assignment_files(files):
    validated = []
    for file in files:
        if not file or not file.filename:
            continue
        safe_name = secure_filename(file.filename)
        ext = os.path.splitext(safe_name)[1].lower().lstrip('.')
        if not safe_name or ext not in ALLOWED_ASSIGNMENT_EXTENSIONS:
            raise ValueError('Định dạng tệp không được hỗ trợ.')
        validated.append((file, safe_name, ext.upper()))
    return validated


def _store_assignment_files(items, folder):
    root = os.path.join(current_app.root_path, 'private_uploads', folder)
    os.makedirs(root, exist_ok=True)
    stored = []
    try:
        for file, safe_name, ext in items:
            stored_name = f'{uuid.uuid4().hex}_{safe_name}'
            path = os.path.join(root, stored_name)
            file.save(path)
            stored.append((path, os.path.join(folder, stored_name).replace(os.sep, '/'), safe_name, ext, os.path.getsize(path)))
    except Exception:
        for path, *_ in stored:
            if os.path.exists(path):
                os.remove(path)
        raise
    return stored


@curriculum_bp.route('/sections/<section_id>/weeks/<week_id>/update', methods=['POST'])
@login_required
def update_section_week(section_id, week_id):
    current_user = get_current_user()
    assigned = SectionInstructor.query.filter_by(
        user_id=current_user.id, section_id=section_id
    ).first() if current_user.role == 'LECTURER' else None
    if not assigned and current_user.role not in ['ADMIN', 'ACADEMIC_ADMIN']:
        abort(403)

    week = SectionWeek.query.filter_by(id=week_id, section_id=section_id).first_or_404()
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    uploaded_files = [file for file in request.files.getlist('files') if file and file.filename]
    if not title:
        flash('Tiêu đề tuần học không được để trống.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))
    if request.content_length and request.content_length > 50 * 1024 * 1024:
        flash('Tổng dung lượng tải lên vượt quá 50 MB.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))

    validated_files = []
    for uploaded_file in uploaded_files:
        safe_name = secure_filename(uploaded_file.filename or '')
        extension = os.path.splitext(safe_name)[1].lower().lstrip('.')
        material_type = ALLOWED_WEEK_MATERIAL_EXTENSIONS.get(extension)
        if not safe_name or not material_type:
            flash('Chỉ hỗ trợ ảnh, Word, Excel, PowerPoint và PDF.', 'danger')
            return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))
        validated_files.append((uploaded_file, safe_name, material_type))

    section = CourseSection.query.get_or_404(section_id)
    week.title = title[:255]
    week.content = content or None
    LearningMaterial.query.filter_by(section_week_id=week.id).update(
        {LearningMaterial.summary_desc: week.content}, synchronize_session=False
    )

    upload_root = os.path.join(current_app.root_path, 'private_uploads')
    safe_section_code = secure_filename(section.section_code) or section.id
    relative_directory = os.path.join('sections', safe_section_code, f'week-{week.week_number:02d}')
    absolute_directory = os.path.join(upload_root, relative_directory)
    os.makedirs(absolute_directory, exist_ok=True)
    saved_paths = []
    try:
        for uploaded_file, safe_name, material_type in validated_files:
            stored_name = f'{uuid.uuid4().hex}_{safe_name}'
            absolute_path = os.path.join(absolute_directory, stored_name)
            uploaded_file.save(absolute_path)
            saved_paths.append(absolute_path)
            db.session.add(LearningMaterial(
                id=f'mat_{uuid.uuid4().hex[:16]}',
                section_id=section_id,
                section_week_id=week.id,
                title=os.path.basename(uploaded_file.filename),
                material_type=material_type,
                file_url=os.path.join(relative_directory, stored_name).replace(os.sep, '/'),
                file_size_bytes=os.path.getsize(absolute_path),
                author_name=current_user.full_name,
                source_origin=f'Giảng viên phụ trách lớp {section.section_code}',
                publication_status='PUBLISHED',
                summary_desc=week.content
            ))
        week.materials_count = LearningMaterial.query.filter_by(section_week_id=week.id).count() + len(validated_files)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)
        current_app.logger.exception('Không lưu được thay đổi Tuần %s của lớp %s.', week.week_number, section_id)
        flash('Không lưu được thay đổi. Vui lòng thử lại.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))

    flash(f'Đã lưu tất cả thay đổi Tuần {week.week_number} ({len(validated_files)} tệp mới).', 'success')
    return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))


@curriculum_bp.route('/course-materials/<material_id>')
@login_required
def download_course_material(material_id):
    current_user = get_current_user()
    material = LearningMaterial.query.get_or_404(material_id)
    if current_user.role == 'STUDENT':
        allowed = SectionEnrollment.query.filter_by(
            student_user_id=current_user.id, section_id=material.section_id
        ).first() is not None
        if material.publication_status != 'PUBLISHED' or not allowed:
            abort(404)
    elif current_user.role == 'LECTURER':
        allowed = SectionInstructor.query.filter_by(
            user_id=current_user.id, section_id=material.section_id
        ).first() is not None
        if not allowed:
            abort(404)
    elif current_user.role not in ['ACADEMIC_ADMIN', 'ADMIN']:
        abort(404)

    if material.file_url.startswith(('https://', 'http://')):
        return redirect(material.file_url)
    if material.file_url.startswith('/static/'):
        return send_from_directory(
            current_app.static_folder,
            material.file_url.removeprefix('/static/'),
            as_attachment=False,
            download_name=material.title
        )
    upload_root = os.path.join(current_app.root_path, 'private_uploads')
    return send_from_directory(
        upload_root,
        material.file_url,
        as_attachment=False,
        download_name=material.title
    )


@curriculum_bp.route('/sections/<section_id>/weeks/<week_id>/assignments/create', methods=['POST'])
@login_required
def create_week_assignment(section_id, week_id):
    user = get_current_user()
    week = SectionWeek.query.filter_by(id=week_id, section_id=section_id).first_or_404()
    if not _can_manage_section(user, section_id):
        abort(403)
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    deadline = _parse_local_datetime(request.form.get('deadline'))
    if not title or not content or not deadline or deadline <= datetime.now():
        flash('Vui lòng nhập tiêu đề, nội dung và deadline hợp lệ.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))
    if request.content_length and request.content_length > 50 * 1024 * 1024:
        flash('Tổng dung lượng tải lên vượt quá 50 MB.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))
    try:
        files = _assignment_files(request.files.getlist('files'))
    except ValueError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))
    assignment = Assignment(
        id=f'asg_{uuid.uuid4().hex[:16]}', section_week_id=week.id,
        assignment_type='LAB_INDIVIDUAL', title=title[:255], instructions_markdown=content,
        open_time=datetime.now(), deadline_time=deadline, cutoff_hard_deadline=deadline + timedelta(days=30),
        allow_late_submission=True, allowed_submission_formats='["FILE_UPLOAD"]'
    )
    folder = os.path.join('assignments', assignment.id, 'instructions')
    stored = _store_assignment_files(files, folder)
    try:
        db.session.add(assignment)
        for _, relative, name, ext, size in stored:
            db.session.add(AssignmentAttachment(
                id=f'asgf_{uuid.uuid4().hex[:16]}', assignment_id=assignment.id,
                file_name=name, file_size_bytes=size, file_type=ext, download_url=relative
            ))
        section = week.section
        course = section.course
        lecturer_name = user.full_name
        deadline_label = deadline.strftime('%d/%m/%Y %H:%M')
        for enrollment in SectionEnrollment.query.filter_by(section_id=section.id).all():
            db.session.add(Notification(
                recipient_user_id=enrollment.student_user_id,
                notification_type='ASSIGNMENT_POSTED',
                title='Bài tập mới',
                message=(
                    f'{lecturer_name} đã đăng assignment “{assignment.title}” '
                    f'cho môn {course.course_code} – {course.title_vi}, lớp {section.section_code}, '
                    f'Tuần {week.week_number}. Hạn nộp: {deadline_label}.'
                ),
                target_url=url_for(
                    'curriculum.view_curriculum', section_id=section.id,
                    open_week=week.id, pane='assignment'
                ),
                reference_id=assignment.id,
            ))
        week.assignments_count = Assignment.query.filter_by(section_week_id=week.id).count() + 1
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        for path, *_ in stored:
            if os.path.exists(path):
                os.remove(path)
        current_app.logger.exception('Không lưu được bài tập tuần %s.', week.week_number)
        flash('Không lưu được bài tập. Vui lòng thử lại.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id))
    flash('Đã tạo assignment cho tuần học.', 'success')
    return redirect(url_for('curriculum.view_curriculum', section_id=section_id, open_week=week.id, pane='assignment'))


@curriculum_bp.route('/assignments/<assignment_id>/submit', methods=['POST'])
@login_required
def submit_assignment(assignment_id):
    user = get_current_user()
    if user.role != 'STUDENT':
        abort(403)
    assignment = Assignment.query.get_or_404(assignment_id)
    week = assignment.section_week
    enrollment = SectionEnrollment.query.filter_by(section_id=week.section_id, student_user_id=user.id).first()
    if not enrollment:
        abort(404)
    if request.content_length and request.content_length > 50 * 1024 * 1024:
        flash('Tổng dung lượng tải lên vượt quá 50 MB.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=week.section_id, open_week=week.id))
    try:
        files = _assignment_files(request.files.getlist('files'))
    except ValueError as exc:
        flash(str(exc), 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=week.section_id, open_week=week.id))
    note = request.form.get('student_note', '').strip()
    existing = AssignmentSubmission.query.filter_by(assignment_id=assignment.id, student_user_id=user.id).first()
    if not files and not note and not (existing and existing.files):
        flash('Chọn ít nhất một tệp bài làm hoặc nhập ghi chú.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=week.section_id, open_week=week.id))
    if datetime.now() > assignment.cutoff_hard_deadline:
        flash('Đã quá thời hạn nhận bài tập.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=week.section_id, open_week=week.id))
    folder = os.path.join('assignments', assignment.id, 'submissions', user.id)
    stored = _store_assignment_files(files, folder)
    try:
        submission = existing or AssignmentSubmission(
            id=f'sub_{uuid.uuid4().hex[:16]}', assignment_id=assignment.id, student_user_id=user.id
        )
        submission.student_note = note or submission.student_note
        submission.is_late = datetime.now() > assignment.deadline_time
        submission.submission_status = 'LATE' if submission.is_late else 'SUBMITTED'
        if not existing:
            db.session.add(submission)
            db.session.flush()
        for _, relative, name, ext, size in stored:
            db.session.add(AssignmentSubmissionAttachment(
                id=f'subf_{uuid.uuid4().hex[:16]}', submission_id=submission.id,
                file_name=name, file_size_bytes=size, file_type=ext, file_url=relative
            ))
            submission.submitted_file_name = name
            submission.submitted_file_url = relative
        submission.submitted_at = datetime.now()
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        for path, *_ in stored:
            if os.path.exists(path):
                os.remove(path)
        current_app.logger.exception('Không lưu được bài nộp assignment %s của sinh viên %s.', assignment.id, user.id)
        flash('Không lưu được bài nộp. Vui lòng thử lại.', 'danger')
        return redirect(url_for('curriculum.view_curriculum', section_id=week.section_id, open_week=week.id))
    flash('Đã gửi bài tập.', 'success')
    return redirect(url_for('curriculum.view_curriculum', section_id=week.section_id, open_week=week.id, pane='assignment'))


@curriculum_bp.route('/assignments/<assignment_id>')
@login_required
def view_assignment(assignment_id):
    user = get_current_user()
    assignment = Assignment.query.get_or_404(assignment_id)
    week = assignment.section_week
    if user.role == 'STUDENT':
        if not SectionEnrollment.query.filter_by(section_id=week.section_id, student_user_id=user.id).first():
            abort(404)
        return redirect(url_for('curriculum.view_curriculum', section_id=week.section_id, open_week=week.id, pane='assignment'))
    if not _can_manage_section(user, week.section_id):
        abort(403)
    enrollments = SectionEnrollment.query.filter_by(section_id=week.section_id).order_by(SectionEnrollment.student_user_id).all()
    submissions = {row.student_user_id: row for row in AssignmentSubmission.query.filter_by(assignment_id=assignment.id).all()}
    roster = [(enrollment.student, submissions.get(enrollment.student_user_id)) for enrollment in enrollments]
    submitted_count = sum(1 for _, submission in roster if submission)
    return render_template('assignment_detail.html', assignment=assignment, week=week, section=week.section, roster=roster, submitted_count=submitted_count, current_nav='curriculum')


@curriculum_bp.route('/assignment-files/<file_id>')
@login_required
def download_assignment_file(file_id):
    user = get_current_user()
    teacher_file = AssignmentAttachment.query.get(file_id)
    student_file = AssignmentSubmissionAttachment.query.get(file_id)
    if teacher_file:
        assignment = teacher_file.assignment
        week = assignment.section_week
        if user.role == 'STUDENT':
            if not SectionEnrollment.query.filter_by(section_id=week.section_id, student_user_id=user.id).first():
                abort(404)
        elif not _can_manage_section(user, week.section_id):
            abort(403)
        relative_path, name = teacher_file.download_url, teacher_file.file_name
    elif student_file:
        assignment = student_file.submission.assignment
        week = assignment.section_week
        if user.role == 'STUDENT':
            if student_file.submission.student_user_id != user.id:
                abort(404)
        elif not _can_manage_section(user, week.section_id):
            abort(403)
        relative_path, name = student_file.file_url, student_file.file_name
    else:
        abort(404)
    return send_from_directory(os.path.join(current_app.root_path, 'private_uploads'), relative_path, as_attachment=True, download_name=name)


@curriculum_bp.route('/courses/create', methods=['POST'])
@login_required
def create_course():
    current_user = get_current_user()
    if current_user.role not in ['LECTURER', 'ACADEMIC_ADMIN', 'ADMIN']:
        flash("Bạn không có quyền tạo môn học mới.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))

    course_code = request.form.get('course_code', '').strip().upper()
    title_vi = request.form.get('title_vi', '').strip()
    title_en = request.form.get('title_en', '').strip() or None
    try:
        credits = int(request.form.get('credits') or 3)
        theory_hours = int(request.form.get('theory_hours') or 30)
        practical_hours = int(request.form.get('practical_hours') or 15)
    except ValueError:
        flash("Số tín chỉ và số giờ phải là số nguyên hợp lệ.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))
    cdio_standard = request.form.get('cdio_standard', '').strip()

    if not course_code or not title_vi:
        flash("Vui lòng điền đầy đủ Mã học phần và Tên môn học.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))

    existing = Course.query.filter_by(course_code=course_code).first()
    if existing:
        flash(f"Môn học với mã '{course_code}' đã tồn tại trong CSDL!", "danger")
        return redirect(url_for('curriculum.view_curriculum', course_id=existing.id))

    try:
        dept = Department.query.first()
        if not dept:
            dept = Department(
                id='dept_unassigned',
                code='UNASSIGNED',
                name='Chưa phân đơn vị',
                faculty_name='Đại học Kinh tế Quốc dân'
            )
            db.session.add(dept)
            db.session.flush()

        new_course = Course(
            id=course_code,
            course_code=course_code,
            title_vi=title_vi,
            title_en=title_en,
            credits=credits,
            theory_hours=theory_hours,
            practical_hours=practical_hours,
            department_id=dept.id,
            cdio_standard=cdio_standard,
            created_by_user_id=current_user.id if current_user.role == 'LECTURER' else None
        )
        db.session.add(new_course)
        db.session.flush()

        # Tạo đề cương nháp rỗng để người dùng bổ sung thông tin thật sau.
        new_syl = CourseSyllabus(
            id=f"syl_{course_code.lower()}_v1",
            course_id=new_course.id,
            version_label='Bản nháp',
            academic_year='Chưa xác định',
            semester='Chưa xác định',
            approval_status='DRAFT',
            digitized_progress_percentage=0,
            approved_by_user_id=None
        )
        db.session.add(new_syl)
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        current_app.logger.exception('Không lưu được môn học %s vào CSDL.', course_code)
        flash("Không lưu được môn học vào CSDL. Hãy kiểm tra mã môn học và cấu hình database.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))

    flash(f"Đã lưu môn học {course_code} - {title_vi} vào CSDL. Đề cương đang ở trạng thái nháp.", "success")
    return redirect(url_for('curriculum.view_curriculum', course_id=course_code))


@curriculum_bp.route('/chapters/create', methods=['POST'])
@login_required
def create_chapter():
    current_user = get_current_user()
    if current_user.role not in ['LECTURER', 'ACADEMIC_ADMIN', 'ADMIN']:
        flash("Bạn không có quyền thêm chương mới.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))

    syllabus_id = request.form.get('syllabus_id')
    title = request.form.get('title', '').strip()
    allocated_periods = int(request.form.get('allocated_periods', 6))

    if not syllabus_id or not title:
        flash("Vui lòng nhập đầy đủ tên chương.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))

    syllabus = CourseSyllabus.query.get_or_404(syllabus_id)
    existing_count = SyllabusChapter.query.filter_by(syllabus_id=syllabus_id).count()
    chapter_order = existing_count + 1

    chap_id = f"chap_{syllabus.course_id.lower()}_c{chapter_order}_{uuid.uuid4().hex[:4]}"
    new_chap = SyllabusChapter(
        id=chap_id,
        syllabus_id=syllabus.id,
        chapter_order=chapter_order,
        title=title,
        total_lessons_count=0,
        allocated_periods=allocated_periods,
        completion_metric='Chưa bắt đầu'
    )
    db.session.add(new_chap)
    db.session.commit()

    flash(f"Đã thêm chương '{title}' vào đề cương thành công!", "success")
    return redirect(url_for('curriculum.view_curriculum', course_id=syllabus.course_id))


@curriculum_bp.route('/lessons/create', methods=['POST'])
@login_required
def create_lesson():
    current_user = get_current_user()
    if current_user.role not in ['LECTURER', 'ACADEMIC_ADMIN', 'ADMIN']:
        flash("Bạn không có quyền thêm bài học mới.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))

    chapter_id = request.form.get('chapter_id')
    lesson_number = request.form.get('lesson_number', '1.2').strip()
    title = request.form.get('title', '').strip()
    lesson_type = request.form.get('lesson_type', 'THEORY')
    duration = int(request.form.get('duration_minutes', 30))
    goals_text = request.form.get('goals', '').strip()

    if not chapter_id or not title:
        flash("Vui lòng nhập đầy đủ thông tin bài học.", "danger")
        return redirect(url_for('curriculum.view_curriculum'))

    chapter = SyllabusChapter.query.get_or_404(chapter_id)
    les_id = f"les_{chapter.id}_{uuid.uuid4().hex[:4]}"

    goals_list = [g.strip() for g in goals_text.split('\n') if g.strip()] if goals_text else ["Hoàn thành bài giảng theo đề cương"]

    new_lesson = Lesson(
        id=les_id,
        chapter_id=chapter.id,
        lesson_number=lesson_number,
        title=title,
        lesson_type=lesson_type,
        duration_minutes=duration,
        learning_goals_json=json.dumps(goals_list)
    )
    db.session.add(new_lesson)
    db.session.commit()

    flash(f"Đã thêm bài học '{title}' vào CSDL thành công!", "success")
    return redirect(url_for('curriculum.view_curriculum', lesson_id=new_lesson.id))

