import uuid
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from app.models import (
    db, MaterialApprovalDossier, LearningMaterial, CourseMaterial, Notification,
    CourseSection, SectionEnrollment, User,
)
from app.auth import role_required, get_current_user
from app.routes.support import get_primary_academic_manager

approval_bp = Blueprint('approval', __name__)

@approval_bp.route('/approvals')
@role_required('ACADEMIC_ADMIN', 'ADMIN')
def view_approvals():
    current_user = get_current_user()
    dossiers = MaterialApprovalDossier.query.order_by(MaterialApprovalDossier.submitted_at.desc()).all()
    pending_course_materials = CourseMaterial.query.filter_by(
        publication_status='PENDING_REVIEW'
    ).order_by(CourseMaterial.created_at.asc()).all()
    manager = get_primary_academic_manager()
    return render_template(
        'approval.html',
        dossiers=dossiers,
        pending_course_materials=pending_course_materials,
        can_review_course_materials=bool(manager and manager.id == current_user.id),
        current_nav='approvals'
    )


def _require_course_material_reviewer():
    user = get_current_user()
    manager = get_primary_academic_manager()
    if user.role != 'ACADEMIC_ADMIN' or not manager or manager.id != user.id:
        abort(403)
    return user


def _notify_course_material_uploader(material, reviewer, approved):
    if not material.uploaded_by_user_id:
        return
    status_text = 'đã được phê duyệt và chia sẻ cho các lớp học phần' if approved else 'bị từ chối'
    db.session.add(Notification(
        recipient_user_id=material.uploaded_by_user_id,
        notification_type='COURSE_MATERIAL_APPROVED' if approved else 'COURSE_MATERIAL_REJECTED',
        title='Kết quả duyệt học liệu môn học',
        message=f'{material.course.course_code} · {material.title} {status_text}.' +
                (f' Ý kiến: {material.review_comment}' if material.review_comment else ''),
        target_url=url_for('shared_repo.view_shared_repo', course_id=material.course_id),
        reference_id=f'{material.id}-{uuid.uuid4().hex[:14]}',
    ))


def _notify_course_material_students(material):
    enrollments = SectionEnrollment.query.join(
        CourseSection, CourseSection.id == SectionEnrollment.section_id
    ).join(
        User, User.id == SectionEnrollment.student_user_id
    ).filter(
        CourseSection.course_id == material.course_id,
        User.role == 'STUDENT', User.is_active.is_(True),
    ).all()
    notified_student_ids = set()
    event_ref = f'{material.id}-published-{uuid.uuid4().hex[:10]}'
    for enrollment in enrollments:
        student_id = enrollment.student_user_id
        if student_id in notified_student_ids:
            continue
        notified_student_ids.add(student_id)
        db.session.add(Notification(
            recipient_user_id=student_id,
            notification_type='COURSE_MATERIAL_PUBLISHED',
            title='Học liệu môn học mới đã được duyệt',
            message=f'{material.course.course_code}: {material.title} đã được chia sẻ cho lớp học phần.',
            target_url=url_for('curriculum.view_curriculum', section_id=enrollment.section_id),
            reference_id=event_ref,
        ))


@approval_bp.route('/approvals/course-materials/<material_id>/approve', methods=['POST'])
@role_required('ACADEMIC_ADMIN')
def approve_course_material(material_id):
    reviewer = _require_course_material_reviewer()
    material = CourseMaterial.query.get_or_404(material_id)
    if material.publication_status != 'PENDING_REVIEW':
        flash('Học liệu này không còn ở trạng thái chờ phê duyệt.', 'warning')
        return redirect(url_for('approval.view_approvals'))
    material.publication_status = 'PUBLISHED'
    material.reviewed_by_user_id = reviewer.id
    material.reviewed_at = datetime.utcnow()
    material.review_comment = request.form.get('comment', '').strip() or None
    _notify_course_material_uploader(material, reviewer, approved=True)
    _notify_course_material_students(material)
    db.session.commit()
    flash(f'Đã phê duyệt học liệu “{material.title}”. Tài liệu sẽ hiển thị trong các lớp học phần của môn.', 'success')
    return redirect(url_for('approval.view_approvals'))


@approval_bp.route('/approvals/course-materials/<material_id>/reject', methods=['POST'])
@role_required('ACADEMIC_ADMIN')
def reject_course_material(material_id):
    reviewer = _require_course_material_reviewer()
    material = CourseMaterial.query.get_or_404(material_id)
    if material.publication_status != 'PENDING_REVIEW':
        flash('Học liệu này không còn ở trạng thái chờ phê duyệt.', 'warning')
        return redirect(url_for('approval.view_approvals'))
    comment = request.form.get('comment', '').strip()
    if not comment:
        flash('Nhập lý do từ chối để giảng viên biết nội dung cần chỉnh sửa.', 'danger')
        return redirect(url_for('approval.view_approvals'))
    material.publication_status = 'REJECTED'
    material.reviewed_by_user_id = reviewer.id
    material.reviewed_at = datetime.utcnow()
    material.review_comment = comment[:4000]
    _notify_course_material_uploader(material, reviewer, approved=False)
    db.session.commit()
    flash(f'Đã từ chối học liệu “{material.title}” và gửi lý do cho giảng viên.', 'success')
    return redirect(url_for('approval.view_approvals'))

@approval_bp.route('/approvals/<dossier_id>/approve', methods=['POST'])
@role_required('ACADEMIC_ADMIN', 'ADMIN')
def approve_dossier(dossier_id):
    current_user = get_current_user()
    dos = MaterialApprovalDossier.query.get_or_404(dossier_id)
    dos.status = 'APPROVED_PUBLISHED'
    dos.current_step = 4
    dos.reviewer_user_id = current_user.id
    dos.reviewer_comment = request.form.get('comment', 'Hồ sơ đạt tiêu chuẩn chất lượng và bản quyền. Đã phê duyệt phát hành toàn viện.')
    db.session.commit()
    flash(f"Đã duyệt và công bố hồ sơ {dos.id} thành công!", "success")
    return redirect(url_for('approval.view_approvals'))

@approval_bp.route('/approvals/<dossier_id>/request-change', methods=['POST'])
@role_required('ACADEMIC_ADMIN', 'ADMIN')
def request_change_dossier(dossier_id):
    current_user = get_current_user()
    dos = MaterialApprovalDossier.query.get_or_404(dossier_id)
    dos.status = 'ACTION_REQUIRED'
    dos.reviewer_user_id = current_user.id
    dos.reviewer_comment = request.form.get('comment', 'Hồ sơ cần bổ sung trích dẫn bản quyền và cập nhật lại phiên bản tài liệu trước khi xuất bản.')
    db.session.commit()
    flash(f"Đã yêu cầu giảng viên chỉnh sửa hồ sơ {dos.id}.", "warning")
    return redirect(url_for('approval.view_approvals'))

@approval_bp.route('/approvals/<dossier_id>/reject', methods=['POST'])
@role_required('ACADEMIC_ADMIN', 'ADMIN')
def reject_dossier(dossier_id):
    current_user = get_current_user()
    dos = MaterialApprovalDossier.query.get_or_404(dossier_id)
    dos.status = 'REJECTED'
    dos.reviewer_user_id = current_user.id
    dos.reviewer_comment = request.form.get('comment', 'Hồ sơ không đáp ứng chuẩn học liệu số hoặc vi phạm bản quyền.')
    db.session.commit()
    flash(f"Đã từ chối hồ sơ {dos.id}.", "danger")
    return redirect(url_for('approval.view_approvals'))
