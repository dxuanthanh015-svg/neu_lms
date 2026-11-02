import os
import uuid
from datetime import datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename

from app.auth import get_current_user, login_required
from app.models import Course, CourseMaterial, CourseSection, SectionEnrollment, SectionInstructor, Notification, db
from app.routes.support import get_primary_academic_manager

shared_repo_bp = Blueprint('shared_repo', __name__)

ALLOWED_COURSE_MATERIAL_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx',
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'txt', 'csv', 'zip', 'rar'
}


def _visible_courses(user):
    query = Course.query
    if user.role == 'LECTURER':
        return query.filter_by(created_by_user_id=user.id).order_by(Course.course_code).all()
    if user.role == 'STUDENT':
        return query.join(CourseSection, CourseSection.course_id == Course.id).join(
            SectionEnrollment, SectionEnrollment.section_id == CourseSection.id
        ).filter(SectionEnrollment.student_user_id == user.id).distinct().order_by(Course.course_code).all()
    if user.role in ['ADMIN', 'ACADEMIC_ADMIN']:
        return query.order_by(Course.course_code).all()
    abort(403)


def _can_manage_course(user, course):
    return user.role == 'LECTURER' and course.created_by_user_id == user.id


def _can_view_course(user, course):
    if user.role in ['ADMIN', 'ACADEMIC_ADMIN']:
        return True
    if user.role == 'LECTURER':
        return course.created_by_user_id == user.id or SectionInstructor.query.join(
            CourseSection, CourseSection.id == SectionInstructor.section_id
        ).filter(
            SectionInstructor.user_id == user.id,
            CourseSection.course_id == course.id,
        ).first() is not None
    if user.role == 'STUDENT':
        return SectionEnrollment.query.join(
            CourseSection, SectionEnrollment.section_id == CourseSection.id
        ).filter(
            SectionEnrollment.student_user_id == user.id,
            CourseSection.course_id == course.id
        ).first() is not None
    return False


@shared_repo_bp.route('/shared-repo')
@login_required
def view_shared_repo():
    user = get_current_user()
    courses = _visible_courses(user)
    requested_id = request.args.get('course_id', '').strip()
    selected_course = next((course for course in courses if course.id == requested_id), None)
    material_query = CourseMaterial.query.filter_by(course_id=selected_course.id) if selected_course else None
    if selected_course and user.role == 'STUDENT':
        material_query = material_query.filter_by(publication_status='PUBLISHED')
    materials = material_query.order_by(CourseMaterial.created_at.desc()).all() if material_query is not None else []
    return render_template(
        'shared_repo.html',
        courses=courses,
        selected_course=selected_course,
        course_materials=materials,
        can_manage_course_materials=bool(selected_course and _can_manage_course(user, selected_course)),
        current_nav='shared_repo'
    )


@shared_repo_bp.route('/shared-repo/courses/<course_id>/materials/upload', methods=['POST'])
@login_required
def upload_course_material(course_id):
    user = get_current_user()
    course = Course.query.get_or_404(course_id)
    if not _can_manage_course(user, course):
        abort(403)
    manager = get_primary_academic_manager()
    if not manager:
        flash('Không thể gửi học liệu đi duyệt: hệ thống cần đúng một cán bộ quản lý đang hoạt động.', 'danger')
        return redirect(url_for('shared_repo.view_shared_repo', course_id=course.id))
    uploaded_files = [item for item in request.files.getlist('files') if item and item.filename]
    if not uploaded_files:
        flash('Chọn ít nhất một tệp học liệu để tải lên.', 'danger')
        return redirect(url_for('shared_repo.view_shared_repo', course_id=course.id))
    if request.content_length and request.content_length > 50 * 1024 * 1024:
        flash('Tổng dung lượng tải lên vượt quá 50 MB.', 'danger')
        return redirect(url_for('shared_repo.view_shared_repo', course_id=course.id))

    validated = []
    for item in uploaded_files:
        filename = secure_filename(item.filename or '')
        extension = os.path.splitext(filename)[1].lower().lstrip('.')
        if not filename or extension not in ALLOWED_COURSE_MATERIAL_EXTENSIONS:
            flash('Chỉ hỗ trợ PDF, Word, Excel, PowerPoint, ảnh, TXT, CSV, ZIP và RAR.', 'danger')
            return redirect(url_for('shared_repo.view_shared_repo', course_id=course.id))
        validated.append((item, filename, extension.upper()))

    description = request.form.get('description', '').strip() or None
    title_override = request.form.get('title', '').strip()
    root = os.path.join(current_app.root_path, 'private_uploads', 'course-materials', secure_filename(course.course_code))
    os.makedirs(root, exist_ok=True)
    saved_paths = []
    try:
        for item, filename, file_type in validated:
            material_id = f'cm_{uuid.uuid4().hex[:18]}'
            stored_name = f'{uuid.uuid4().hex}_{filename}'
            absolute_path = os.path.join(root, stored_name)
            item.save(absolute_path)
            saved_paths.append(absolute_path)
            relative_path = os.path.join('course-materials', secure_filename(course.course_code), stored_name).replace(os.sep, '/')
            db.session.add(CourseMaterial(
                id=material_id,
                course_id=course.id,
                uploaded_by_user_id=user.id,
                title=title_override[:255] if title_override else filename,
                description=description,
                file_name=filename,
                file_url=relative_path,
                file_size_bytes=os.path.getsize(absolute_path),
                file_type=file_type,
                publication_status='PENDING_REVIEW',
                created_at=datetime.utcnow()
            ))
        db.session.add(Notification(
            recipient_user_id=manager.id,
            notification_type='COURSE_MATERIAL_REVIEW_REQUEST',
            title='Học liệu môn học chờ phê duyệt',
            message=f'{course.course_code}: {len(validated)} tệp học liệu mới cần xem xét.',
            target_url=url_for('approval.view_approvals'),
            reference_id=f'course-material-upload-{uuid.uuid4().hex[:20]}',
        ))
        db.session.commit()
    except (OSError, SQLAlchemyError):
        db.session.rollback()
        for path in saved_paths:
            if os.path.exists(path):
                os.remove(path)
        current_app.logger.exception('Không tải được học liệu lên môn %s.', course.id)
        flash('Không lưu được học liệu. Vui lòng thử lại.', 'danger')
        return redirect(url_for('shared_repo.view_shared_repo', course_id=course.id))

    flash(f'Đã gửi {len(validated)} tệp học liệu môn {course.course_code} tới cán bộ quản lý để phê duyệt.', 'success')
    return redirect(url_for('shared_repo.view_shared_repo', course_id=course.id))


@shared_repo_bp.route('/shared-repo/course-materials/<material_id>/update', methods=['POST'])
@login_required
def update_course_material(material_id):
    user = get_current_user()
    material = CourseMaterial.query.get_or_404(material_id)
    if not _can_manage_course(user, material.course):
        abort(403)
    manager = get_primary_academic_manager()
    if not manager:
        flash('Không thể gửi thay đổi đi duyệt: hệ thống cần đúng một cán bộ quản lý đang hoạt động.', 'danger')
        return redirect(url_for('shared_repo.view_shared_repo', course_id=material.course_id))
    title = request.form.get('title', '').strip()
    if not title:
        flash('Tên học liệu không được để trống.', 'danger')
        return redirect(url_for('shared_repo.view_shared_repo', course_id=material.course_id))
    replacement = request.files.get('file')
    stored_path = None
    new_relative_path = None
    new_name = None
    new_file_name = None
    new_type = None
    new_size = None
    if replacement and replacement.filename:
        filename = secure_filename(replacement.filename)
        extension = os.path.splitext(filename)[1].lower().lstrip('.')
        if not filename or extension not in ALLOWED_COURSE_MATERIAL_EXTENSIONS:
            flash('Định dạng tệp học liệu không được hỗ trợ.', 'danger')
            return redirect(url_for('shared_repo.view_shared_repo', course_id=material.course_id))
        if request.content_length and request.content_length > 50 * 1024 * 1024:
            flash('Tệp tải lên vượt quá 50 MB.', 'danger')
            return redirect(url_for('shared_repo.view_shared_repo', course_id=material.course_id))
        course_folder = secure_filename(material.course.course_code) or material.course_id
        root = os.path.join(current_app.root_path, 'private_uploads', 'course-materials', course_folder)
        os.makedirs(root, exist_ok=True)
        new_name = f'{uuid.uuid4().hex}_{filename}'
        new_file_name = filename
        stored_path = os.path.join(root, new_name)
        replacement.save(stored_path)
        new_relative_path = os.path.join('course-materials', course_folder, new_name).replace(os.sep, '/')
        new_type = extension.upper()
        new_size = os.path.getsize(stored_path)

    old_path = os.path.join(current_app.root_path, 'private_uploads', material.file_url)
    try:
        material.title = title[:255]
        material.description = request.form.get('description', '').strip() or None
        material.publication_status = 'PENDING_REVIEW'
        material.reviewed_by_user_id = None
        material.review_comment = None
        material.reviewed_at = None
        if new_relative_path:
            material.file_url = new_relative_path
            material.file_name = new_file_name[:255]
            material.file_type = new_type
            material.file_size_bytes = new_size
        db.session.add(Notification(
            recipient_user_id=manager.id,
            notification_type='COURSE_MATERIAL_REVIEW_REQUEST',
            title='Học liệu cập nhật chờ phê duyệt',
            message=f'{material.course.course_code}: {material.title}',
            target_url=url_for('approval.view_approvals'),
            reference_id=f'course-material-update-{uuid.uuid4().hex[:20]}',
        ))
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        if stored_path and os.path.exists(stored_path):
            os.remove(stored_path)
        current_app.logger.exception('Không cập nhật được học liệu %s.', material_id)
        flash('Không lưu được thay đổi học liệu.', 'danger')
        return redirect(url_for('shared_repo.view_shared_repo', course_id=material.course_id))
    if new_relative_path and os.path.exists(old_path):
        os.remove(old_path)
    flash('Đã gửi thay đổi học liệu tới cán bộ quản lý để phê duyệt.', 'success')
    return redirect(url_for('shared_repo.view_shared_repo', course_id=material.course_id))


@shared_repo_bp.route('/shared-repo/course-materials/<material_id>')
@login_required
def download_course_material(material_id):
    user = get_current_user()
    material = CourseMaterial.query.get_or_404(material_id)
    if not _can_view_course(user, material.course):
        abort(404)
    if user.role == 'STUDENT' and material.publication_status != 'PUBLISHED':
        abort(404)
    return send_from_directory(
        os.path.join(current_app.root_path, 'private_uploads'),
        material.file_url,
        as_attachment=True,
        download_name=material.file_name
    )
