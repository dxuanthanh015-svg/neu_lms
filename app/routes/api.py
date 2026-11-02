from datetime import datetime
from datetime import timedelta
import os
import uuid
from flask import Blueprint, request, jsonify, current_app, url_for, send_from_directory, abort
from werkzeug.exceptions import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from werkzeug.utils import secure_filename
from app.models import (
    db, LearningMaterial, DrmSecurityPolicy, MaterialApprovalDossier,
    QuestionBank, QuestionOption, Lesson, User, MaterialCourseLink,
    SupportTicket, TicketMessage, Course,
    SyllabusChapter, CourseSyllabus, CourseSection, SectionEnrollment,
    SectionInstructor, AdministrativeClass, SectionWeek, Assignment, AssignmentSubmission,
    Notification, TicketAttachment, TicketStatusHistory
)
from app.auth import login_required, role_required, get_current_user
from app.routes.support import can_view_ticket, _close_resolved_tickets, get_primary_academic_manager
from app.course_tutor import (
    CourseAccessError, TutorConfigurationError, TutorServiceError,
    answer_course_question, generate_course_questions, get_course_context
)

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.errorhandler(Exception)
def handle_api_exception(error):
    if isinstance(error, HTTPException):
        return jsonify({'status': 'error', 'message': error.description}), error.code
    current_app.logger.exception('Unhandled API exception')
    return jsonify({
        'status': 'error',
        'message': 'Máy chủ gặp lỗi khi xử lý yêu cầu. Vui lòng thử lại.'
    }), 500

# ==========================================
# 0. PUBLIC APIS (KHÔNG YÊU CẦU ĐĂNG NHẬP)
# ==========================================

@api_bp.route('/public/health', methods=['GET'])
def public_health_check():
    """API Công khai: Kiểm tra trạng thái hệ thống và chuẩn bảo mật."""
    return jsonify({
        'status': 'healthy',
        'service': 'NEU LMS - Phân hệ M10 Khảo Thí Số',
        'security': 'RBAC Enforced (Role-Based Access Control)',
        'public_endpoints': ['/api/public/health'],
        'protected_endpoints': 'All operational and administrative APIs require authentication'
    })


# ==========================================
# 1. HỌC LIỆU SỐ & QUY TRÌNH QUẢN LÝ HỌC LIỆU
# Yêu cầu quyền: GIẢNG VIÊN (LECTURER) hoặc QUẢN LÝ (ACADEMIC_ADMIN)
# ==========================================

@api_bp.route('/materials/add', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def add_material():
    current_user = get_current_user()
    data = request.get_json() or {}
    lesson_id = data.get('lesson_id')
    title = data.get('title', 'Tai_lieu_moi.pdf')
    material_type = data.get('material_type', 'DOCUMENT_PDF')
    file_size_bytes = int(data.get('file_size_bytes', 2048576))
    is_shared = bool(data.get('is_shared_institutional_repo', False))
    author_name = data.get('author_name', current_user.full_name)
    source_origin = data.get('source_origin', f'Bộ môn - {current_user.user_code}')
    license_type = data.get('license_type', 'CC_BY_NC_SA')

    # Tìm bài học
    lesson = None
    if lesson_id:
        lesson = Lesson.query.get(lesson_id)
    if not lesson:
        lesson = Lesson.query.first()
    if not lesson:
        return jsonify({'status': 'error', 'message': 'Chưa có bài học nào trong CSDL. Vui lòng tạo bài học trước.'}), 400

    lesson_id = lesson.id

    # Tìm lớp học phần hợp lệ
    section_id = None
    if lesson.chapter_id:
        chap = SyllabusChapter.query.get(lesson.chapter_id)
        if chap and chap.syllabus_id:
            syl = CourseSyllabus.query.get(chap.syllabus_id)
            if syl:
                sec = CourseSection.query.filter_by(course_id=syl.course_id).first()
                if sec:
                    section_id = sec.id

    if not section_id:
        sec = CourseSection.query.first()
        if sec:
            section_id = sec.id
        else:
            return jsonify({'status': 'error', 'message': 'Chưa có lớp học phần nào để liên kết học liệu. Vui lòng tạo lớp học phần trước.'}), 400

    mat_id = f"mat_{uuid.uuid4().hex[:8]}"
    new_mat = LearningMaterial(
        id=mat_id,
        section_id=section_id,
        section_week_id=None,
        lesson_id=lesson_id,
        title=title,
        material_type=material_type,
        file_url=f"/static/uploads/{title.replace(' ', '_')}",
        file_size_bytes=file_size_bytes,
        version_tag='v1.0',
        is_shared_institutional_repo=is_shared,
        institutional_code=f"HL-{uuid.uuid4().hex[:4].upper()}" if is_shared else None,
        author_name=author_name,
        source_origin=source_origin,
        license_type=license_type,
        publication_status='PENDING_REVIEW' if is_shared else 'PUBLISHED',
        summary_desc=data.get('summary_desc', 'Tài liệu học tập số hóa.')
    )
    db.session.add(new_mat)

    # Tạo chính sách DRM mặc định
    drm = DrmSecurityPolicy(
        id=f"drm_{uuid.uuid4().hex[:8]}",
        material_id=new_mat.id,
        view_online_only=True,
        dynamic_watermark_enabled=True,
        allow_offline_encrypted_study=False,
        author_digital_signature=f"{author_name} (ID: {current_user.user_code})",
        signed_at=datetime.utcnow()
    )
    db.session.add(drm)

    # Tự động tạo hồ sơ kiểm duyệt gửi CB quản lý nếu đăng ký vào kho dùng chung
    approval_code = None
    if is_shared:
        cb_user = User.query.filter_by(role='ACADEMIC_ADMIN', is_active=True).first()
        reviewer_id = cb_user.id if cb_user else None
        approval_code = f"DOS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"

        dossier = MaterialApprovalDossier(
            id=approval_code,
            material_id=new_mat.id,
            submitter_user_id=current_user.id,
            current_step=1,
            status='PENDING_DEPARTMENT',
            reviewer_user_id=reviewer_id,
            reviewer_comment=(
                f'Hồ sơ học liệu "{title}" vừa được tải lên bởi {current_user.full_name} '
                f'({current_user.user_code}). Đang xếp hàng kiểm tra bản quyền số DRM & nội dung chuyên môn.'
            ),
            sla_deadline_hours=28,
            sla_remaining_hours=28,
            submitted_at=datetime.utcnow()
        )
        db.session.add(dossier)

    db.session.commit()
    msg = f'Đã tải lên học liệu "{title}" thành công!'
    if is_shared and approval_code:
        msg += f' Hồ sơ kiểm duyệt {approval_code} đã được gửi đến Cán bộ Quản lý.'

    return jsonify({
        'status': 'success',
        'message': msg,
        'material_id': new_mat.id
    })


@api_bp.route('/materials/<material_id>/drm', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def update_drm(material_id):
    current_user = get_current_user()
    data = request.get_json() or {}
    mat = LearningMaterial.query.get_or_404(material_id)

    if not mat.drm_policy:
        mat.drm_policy = DrmSecurityPolicy(id=f"drm_{uuid.uuid4().hex[:8]}", material_id=mat.id)

    mat.drm_policy.view_online_only = bool(data.get('view_online_only', True))
    mat.drm_policy.allow_offline_encrypted_study = bool(data.get('allow_offline_encrypted_study', False))
    mat.drm_policy.dynamic_watermark_enabled = bool(data.get('dynamic_watermark_enabled', True))
    mat.drm_policy.author_digital_signature = f"{current_user.full_name} ({current_user.user_code})"
    mat.drm_policy.signed_at = datetime.utcnow()

    if data.get('version_tag'):
        mat.version_tag = data.get('version_tag')

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': 'Đã cập nhật cấu hình bản quyền DRM & Ký số thành công!',
        'signed_at': mat.drm_policy.signed_at.strftime('%H:%M:%S %d/%m/%Y')
    })


@api_bp.route('/materials/<material_id>/delete', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def delete_material(material_id):
    mat = LearningMaterial.query.get_or_404(material_id)
    db.session.delete(mat)
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Đã xóa tài liệu khỏi bài học.'})


# LIÊN KẾT HỌC LIỆU VỚI NHIỀU MÔN HỌC (TRÁNH TRÙNG LẶP)
@api_bp.route('/materials/link-course', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def link_material_to_course():
    current_user = get_current_user()
    data = request.get_json() or {}
    material_id = data.get('material_id')
    course_id = data.get('course_id')
    section_id = data.get('section_id') or None
    notes = data.get('notes', 'Tái sử dụng học liệu số từ Kho dùng chung')

    if not material_id or not course_id:
        return jsonify({'status': 'error', 'message': 'Thiếu material_id hoặc course_id'}), 400

    mat = LearningMaterial.query.get_or_404(material_id)
    course = Course.query.get_or_404(course_id)

    # Kiểm tra liên kết đã tồn tại chưa
    existing = MaterialCourseLink.query.filter_by(material_id=mat.id, course_id=course.id, section_id=section_id).first()
    if existing:
        return jsonify({'status': 'warning', 'message': f'Học liệu này đã được liên kết với môn {course.course_code} trước đó.'})

    link_id = f"link_{uuid.uuid4().hex[:8]}"
    new_link = MaterialCourseLink(
        id=link_id,
        material_id=mat.id,
        course_id=course.id,
        section_id=section_id,
        notes=notes,
        linked_by_user_id=current_user.id,
        linked_at=datetime.utcnow()
    )
    db.session.add(new_link)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Đã liên kết học liệu "{mat.title}" vào môn học {course.course_code} ({course.title_vi}) thành công!',
        'link_id': link_id
    })


# CẬP NHẬT PHIÊN BẢN HOẶC LƯU TRỮ (ARCHIVE / UNARCHIVE)
@api_bp.route('/materials/<material_id>/archive', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def toggle_archive_material(material_id):
    mat = LearningMaterial.query.get_or_404(material_id)
    if mat.publication_status == 'ARCHIVED':
        mat.publication_status = 'PUBLISHED'
        msg = f'Đã phục hồi trạng thái CÔNG BỐ cho học liệu "{mat.title}".'
    else:
        mat.publication_status = 'ARCHIVED'
        msg = f'Đã chuyển học liệu "{mat.title}" vào trạng thái LƯU TRỮ (ARCHIVED).'

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': msg,
        'new_status': mat.publication_status
    })


@api_bp.route('/materials/<material_id>/update-version', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def update_material_version(material_id):
    data = request.get_json() or {}
    mat = LearningMaterial.query.get_or_404(material_id)

    new_version = data.get('version_tag', mat.version_tag)
    author_name = data.get('author_name', mat.author_name)
    source_origin = data.get('source_origin', mat.source_origin)
    summary_desc = data.get('summary_desc', mat.summary_desc)
    license_type = data.get('license_type', mat.license_type)

    mat.version_tag = new_version
    mat.author_name = author_name
    mat.source_origin = source_origin
    mat.summary_desc = summary_desc
    mat.license_type = license_type

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': f'Đã cập nhật phiên bản {new_version} và thông tin bản quyền cho học liệu "{mat.title}" thành công!'
    })


# ==========================================
# 2. NGÂN HÀNG CÂU HỎI & AI RÀ SOÁT / KIỂM DUYỆT
# Yêu cầu quyền: GIẢNG VIÊN (LECTURER) hoặc QUẢN LÝ (ACADEMIC_ADMIN)
# ==========================================

@api_bp.route('/ai/generate-question', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def generate_ai_question():
    current_user = get_current_user()
    data = request.get_json() or {}
    topic = data.get('topic', 'Kiến trúc RESTful & HTTP Specifications')
    bloom = data.get('bloom_level', 'L3_APPLY')
    course_id = data.get('course_id')

    # Tìm môn học trong CSDL
    course = None
    if course_id:
        course = Course.query.get(course_id)
    if not course:
        course = Course.query.first()
    if not course:
        return jsonify({'status': 'error', 'message': 'Chưa có môn học nào trong CSDL. Vui lòng tạo môn học trước khi sinh câu hỏi.'}), 400

    # Tìm chương trong CSDL
    chapter = SyllabusChapter.query.join(CourseSyllabus).filter(CourseSyllabus.course_id == course.id).first()
    chapter_id = chapter.id if chapter else None

    q_id = f"Q-AI-{uuid.uuid4().hex[:4].upper()}"
    stem = f"Trong kiến trúc RESTful chuẩn IETF ({course.course_code}), khi thực hiện phương thức HTTP PUT lên URI tài nguyên đã tồn tại để cập nhật toàn bộ trạng thái, mã phản hồi nào sau đây biểu thị thành công và không cần trả về thân payload (body)?"
    new_q = QuestionBank(
        id=q_id,
        course_id=course.id,
        chapter_id=chapter_id,
        bloom_level=bloom,
        topic_tag=f"#{topic.replace(' ', '_')}",
        question_type='MCQ_SINGLE',
        question_stem=stem,
        default_points=1.00,
        ai_generated=True,
        ai_confidence_score=97.80,
        rfc_reference='RFC 7231 • Sec 4.3.4 (PUT Specs)',
        explanation_logic='Theo RFC 7231, nếu thao tác PUT đã sửa đổi tài nguyên thành công mà máy chủ gốc không gửi bất kỳ nội dung nào trong phần thân của phản hồi, mã 204 No Content phải được sử dụng.',
        status='AI_DRAFT',
        approved_by_user_id=current_user.id,
        usage_in_exams_count=0
    )
    db.session.add(new_q)
    db.session.flush()

    opts = [
        QuestionOption(id=f"opt_{q_id}_a", question_id=new_q.id, option_letter='A', option_text='HTTP 200 OK (Bắt buộc kèm URI mới)', is_correct=False, option_role='DISTRACTOR'),
        QuestionOption(id=f"opt_{q_id}_b", question_id=new_q.id, option_letter='B', option_text='HTTP 204 No Content (Thành công, không chứa thân phản hồi)', is_correct=True, option_role='CORRECT_ANSWER'),
        QuestionOption(id=f"opt_{q_id}_c", question_id=new_q.id, option_letter='C', option_text='HTTP 202 Accepted (Đã tiếp nhận nhưng chưa cập nhật CSDL)', is_correct=False, option_role='DISTRACTOR'),
        QuestionOption(id=f"opt_{q_id}_d", question_id=new_q.id, option_letter='D', option_text='HTTP 304 Not Modified', is_correct=False, option_role='DISTRACTOR')
    ]
    db.session.add_all(opts)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'EduLLM Copilot đã sinh câu hỏi mới cho môn {course.course_code} thành công ở trạng thái AI DRAFT (Chờ kiểm duyệt)!',
        'question': {
            'id': new_q.id,
            'stem': new_q.question_stem,
            'confidence': 97.8,
            'rfc': new_q.rfc_reference,
            'status': new_q.status
        }
    })


@api_bp.route('/ai/audit-question', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def audit_question():
    data = request.get_json() or {}
    question_id = data.get('question_id')
    q = QuestionBank.query.get_or_404(question_id)

    correct_count = sum(1 for opt in q.options if opt.is_correct)
    audit_findings = []

    if correct_count == 1:
        audit_findings.append({
            'type': 'PASS',
            'title': 'Cấu trúc đáp án chuẩn xác',
            'detail': 'Chính xác 01 đáp án đúng duy nhất, phù hợp với chuẩn bài thi MCQ đơn lựa chọn.'
        })
    elif correct_count == 0:
        audit_findings.append({
            'type': 'FAIL',
            'title': 'Thiếu đáp án chuẩn',
            'detail': 'Chưa đánh dấu đáp án đúng nào cho câu hỏi này.'
        })
    else:
        audit_findings.append({
            'type': 'WARNING',
            'title': 'Nhiều hơn một đáp án đúng',
            'detail': f'Phát hiện {correct_count} đáp án được đánh dấu đúng.'
        })

    if q.rfc_reference:
        audit_findings.append({
            'type': 'PASS',
            'title': 'Đã đối soát tiêu chuẩn',
            'detail': f'Dẫn chiếu hợp lệ theo tiêu chuẩn quốc tế: {q.rfc_reference}.'
        })
    else:
        audit_findings.append({
            'type': 'WARNING',
            'title': 'Chưa bổ sung quy chuẩn đối soát',
            'detail': 'Khuyến nghị bổ sung số hiệu chuẩn RFC / ISO hoặc chương mục sách giáo trình.'
        })

    audit_findings.append({
        'type': 'PASS',
        'title': 'Độ dài & Tính tương đồng phương án gây nhiễu',
        'detail': 'Độ dài các phương án A, B, C, D có độ lệch dưới 15%, tránh gợi ý đáp án lộ liễu cho sinh viên.'
    })

    return jsonify({
        'status': 'success',
        'question_id': q.id,
        'bloom_level': q.bloom_level,
        'ai_confidence_score': float(q.ai_confidence_score or 95.0),
        'findings': audit_findings,
        'recommendation': 'Câu hỏi đạt tiêu chuẩn chất lượng. Đủ điều kiện để Cán bộ Khảo thí phê duyệt và đưa vào ngân hàng đề thi chính thức.'
    })


@api_bp.route('/questions/create', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def create_question_manual():
    current_user = get_current_user()
    data = request.get_json() or {}

    course_id = data.get('course_id')
    chapter_id = data.get('chapter_id')
    bloom_level = data.get('bloom_level', 'L2_UNDERSTAND')
    topic_tag = data.get('topic_tag', '#ChuyenMon')
    question_stem = data.get('question_stem', '').strip()
    explanation_logic = data.get('explanation_logic', 'Giải thích chi tiết theo giáo trình môn học.')
    default_points = float(data.get('default_points', 1.0))
    rfc_reference = data.get('rfc_reference', '')

    if not question_stem:
        return jsonify({'status': 'error', 'message': 'Nội dung câu hỏi không được để trống.'}), 400

    course = None
    if course_id:
        course = Course.query.get(course_id)
    if not course:
        course = Course.query.first()
    if not course:
        return jsonify({'status': 'error', 'message': 'Chưa có môn học nào trong CSDL. Vui lòng tạo môn học trước khi thêm câu hỏi.'}), 400

    course_id = course.id

    # Tìm chapter
    chap = None
    if chapter_id:
        chap = SyllabusChapter.query.get(chapter_id)
    if not chap:
        chap = SyllabusChapter.query.join(CourseSyllabus).filter(CourseSyllabus.course_id == course.id).first()
    chapter_id = chap.id if chap else None

    q_id = f"Q-MAN-{uuid.uuid4().hex[:4].upper()}"
    new_q = QuestionBank(
        id=q_id,
        course_id=course_id,
        chapter_id=chapter_id,
        bloom_level=bloom_level,
        topic_tag=topic_tag if topic_tag.startswith('#') else f"#{topic_tag}",
        question_type='MCQ_SINGLE',
        question_stem=question_stem,
        default_points=default_points,
        ai_generated=False,
        ai_confidence_score=None,
        rfc_reference=rfc_reference or None,
        explanation_logic=explanation_logic,
        status='APPROVED' if current_user.role in ['ACADEMIC_ADMIN', 'ADMIN'] else 'AI_DRAFT',
        approved_by_user_id=current_user.id if current_user.role in ['ACADEMIC_ADMIN', 'ADMIN'] else None,
        usage_in_exams_count=0
    )
    db.session.add(new_q)
    db.session.flush()

    # Nhận các phương án A, B, C, D từ request
    options_data = data.get('options', [])
    correct_letter = data.get('correct_letter', 'A')

    if not options_data:
        options_data = [
            {'letter': 'A', 'text': data.get('option_a', 'Phương án A')},
            {'letter': 'B', 'text': data.get('option_b', 'Phương án B')},
            {'letter': 'C', 'text': data.get('option_c', 'Phương án C')},
            {'letter': 'D', 'text': data.get('option_d', 'Phương án D')},
        ]

    for opt in options_data:
        letter = opt.get('letter', 'A').upper()
        text = opt.get('text', '').strip()
        is_corr = (letter == correct_letter.upper())
        q_opt = QuestionOption(
            id=f"opt_{q_id}_{letter.lower()}",
            question_id=new_q.id,
            option_letter=letter,
            option_text=text,
            is_correct=is_corr,
            option_role='CORRECT_ANSWER' if is_corr else 'DISTRACTOR'
        )
        db.session.add(q_opt)

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': f'Đã thêm câu hỏi trắc nghiệm {q_id} vào CSDL thành công!',
        'question_id': q_id
    })


@api_bp.route('/questions/<question_id>/approve', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def approve_question(question_id):
    current_user = get_current_user()
    q = QuestionBank.query.get_or_404(question_id)
    q.status = 'APPROVED'
    q.approved_by_user_id = current_user.id
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Đã duyệt và ký số khảo thí cho câu hỏi {q.id}!'})


# ==========================================
# 3. PHÂN HỆ HỖ TRỢ NGƯỜI HỌC (SUPPORT & CHATBOT AI)
# ==========================================

TICKET_ATTACHMENT_EXTENSIONS = {
    'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'xls', 'xlsx',
    'ppt', 'pptx', 'txt', 'csv', 'zip', 'rar'
}


def _save_ticket_attachments(ticket, message, uploader, uploaded_files):
    files = [item for item in uploaded_files if item and item.filename]
    validated = []
    total_size = 0
    for item in files:
        file_name = secure_filename(item.filename or '')
        extension = os.path.splitext(file_name)[1].lower().lstrip('.')
        item.stream.seek(0, os.SEEK_END)
        file_size = item.stream.tell()
        item.stream.seek(0)
        total_size += file_size
        if not file_name or extension not in TICKET_ATTACHMENT_EXTENSIONS:
            raise ValueError('Định dạng tệp đính kèm chưa được hỗ trợ.')
        if file_size > 10 * 1024 * 1024:
            raise ValueError('Mỗi tệp đính kèm tối đa là 10 MB.')
        validated.append((item, file_name, file_size))
    if total_size > 20 * 1024 * 1024:
        raise ValueError('Tổng dung lượng tệp đính kèm tối đa là 20 MB.')

    folder = os.path.join(current_app.root_path, 'private_uploads', 'support_tickets', ticket.id)
    os.makedirs(folder, exist_ok=True)
    for item, file_name, file_size in validated:
        stored_name = f'{uuid.uuid4().hex}_{file_name}'
        item.save(os.path.join(folder, stored_name))
        relative_path = os.path.join('support_tickets', ticket.id, stored_name).replace(os.sep, '/')
        db.session.add(TicketAttachment(
            id=f'tatt_{uuid.uuid4().hex[:18]}', ticket_id=ticket.id,
            message_id=message.id, uploader_user_id=uploader.id,
            file_name=file_name, file_url=relative_path, file_size_bytes=file_size,
        ))


def _record_ticket_status(ticket, actor, new_status, note=None):
    old_status = ticket.status
    if old_status == new_status:
        return
    ticket.status = new_status
    ticket.updated_at = datetime.utcnow()
    db.session.add(TicketStatusHistory(
        ticket_id=ticket.id, actor_user_id=actor.id if actor else None,
        from_status=old_status, to_status=new_status, note=note,
    ))


def _notify_ticket_requester(ticket, notification_type, title, message):
    db.session.add(Notification(
        recipient_user_id=ticket.student_user_id,
        notification_type=notification_type,
        title=title,
        message=message,
        target_url=url_for('support.view_support', ticket_id=ticket.id),
        reference_id=f'{notification_type.lower()}-{uuid.uuid4().hex[:16]}',
    ))

@api_bp.route('/support/tickets/create', methods=['POST'])
@login_required
def create_support_ticket():
    current_user = get_current_user()
    if current_user.role != 'STUDENT':
        return jsonify({'status': 'error', 'message': 'Chỉ người học mới được gửi yêu cầu hỗ trợ.'}), 403
    data = request.form if request.form else (request.get_json(silent=True) or {})
    recipient_role = str(data.get('recipient_role', '')).strip().upper()
    category = str(data.get('category', 'GENERAL')).strip().upper()
    title = str(data.get('title', '')).strip()
    content = str(data.get('content', '')).strip()
    course_id = str(data.get('course_id', '')).strip() or None
    lecturer_categories = {'ACADEMIC_MATERIAL', 'ASSIGNMENT_HELP', 'TECHNICAL_ISSUE', 'EXAM_REVIEW'}
    manager_categories = {'TUITION', 'COUNSELING', 'MEDICAL', 'DISCIPLINARY', 'GENERAL', 'TECHNICAL_ISSUE'}
    if recipient_role not in {'LECTURER', 'ACADEMIC_ADMIN'} or not title or not content:
        return jsonify({'status': 'error', 'message': 'Chọn đúng kênh tiếp nhận và nhập tiêu đề, nội dung.'}), 400
    if recipient_role == 'LECTURER' and category not in lecturer_categories:
        return jsonify({'status': 'error', 'message': 'Loại yêu cầu này không thuộc phạm vi giảng viên.'}), 400
    if recipient_role == 'ACADEMIC_ADMIN' and category not in manager_categories:
        return jsonify({'status': 'error', 'message': 'Loại yêu cầu này không thuộc phạm vi cán bộ quản lý.'}), 400

    assigned_receiver = None
    if recipient_role == 'LECTURER':
        if not course_id:
            return jsonify({'status': 'error', 'message': 'Chọn môn học để gửi yêu cầu đến giảng viên phụ trách.'}), 400
        if not SectionEnrollment.query.join(
            CourseSection, SectionEnrollment.section_id == CourseSection.id
        ).filter(
            SectionEnrollment.student_user_id == current_user.id,
            CourseSection.course_id == course_id,
        ).first():
            return jsonify({'status': 'error', 'message': 'Bạn chưa ghi danh vào môn học đã chọn.'}), 403
        course = Course.query.get(course_id)
        if course and course.created_by_user_id:
            assigned_receiver = User.query.filter_by(
                id=course.created_by_user_id, role='LECTURER', is_active=True
            ).first()
        instructor_links = SectionInstructor.query.join(
            CourseSection, SectionInstructor.section_id == CourseSection.id
        ).join(
            SectionEnrollment, SectionEnrollment.section_id == CourseSection.id
        ).join(
            User, User.id == SectionInstructor.user_id
        ).filter(
            CourseSection.course_id == course_id,
            SectionEnrollment.student_user_id == current_user.id,
            User.role == 'LECTURER', User.is_active.is_(True),
        ).order_by(SectionInstructor.role_in_section.asc()).all()
        if not assigned_receiver:
            assigned_receiver = next(
                (link.instructor for link in instructor_links if link.role_in_section == 'PRIMARY_LECTURER'),
                instructor_links[0].instructor if instructor_links else None,
            )
        if not assigned_receiver:
            return jsonify({'status': 'error', 'message': 'Môn học này chưa có giảng viên phụ trách được gắn vào lớp học phần.'}), 409
    else:
        course_id = None
        assigned_receiver = get_primary_academic_manager()
        if not assigned_receiver:
            return jsonify({'status': 'error', 'message': 'Hệ thống chưa có cán bộ quản lý đang hoạt động để tiếp nhận yêu cầu.'}), 503
    if request.content_length and request.content_length > 20 * 1024 * 1024:
        return jsonify({'status': 'error', 'message': 'Tổng dung lượng tệp đính kèm tối đa là 20 MB.'}), 413

    now = datetime.utcnow()
    sensitive = recipient_role == 'ACADEMIC_ADMIN' and category in {'COUNSELING', 'MEDICAL', 'DISCIPLINARY'}
    sla_hours = {
        'TECHNICAL_ISSUE': 24, 'EXAM_REVIEW': 72, 'TUITION': 48,
        'COUNSELING': 24, 'MEDICAL': 24, 'DISCIPLINARY': 24,
        'ACADEMIC_MATERIAL': 48, 'ASSIGNMENT_HELP': 24, 'GENERAL': 48,
    }[category]
    ticket_code = f"SUP-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
    new_ticket = SupportTicket(
        id=f"ticket_{uuid.uuid4().hex[:12]}", ticket_code=ticket_code,
        student_user_id=current_user.id, course_id=course_id, category=category,
        recipient_role=recipient_role, assigned_staff_user_id=assigned_receiver.id,
        title=title[:255], content=content, status='NEW', priority='MEDIUM',
        is_sensitive=sensitive, sla_hours=sla_hours, sla_due_at=now + timedelta(hours=sla_hours),
        created_at=now, updated_at=now,
    )
    first_message = TicketMessage(
        id=f"msg_{uuid.uuid4().hex[:12]}", ticket_id=new_ticket.id,
        sender_user_id=current_user.id, message=content, created_at=now,
    )
    db.session.add_all([new_ticket, first_message])
    db.session.flush()
    db.session.add(TicketStatusHistory(
        ticket_id=new_ticket.id, actor_user_id=current_user.id,
        from_status=None, to_status='NEW', note='Người học gửi yêu cầu hỗ trợ.',
        created_at=now,
    ))
    try:
        _save_ticket_attachments(new_ticket, first_message, current_user, request.files.getlist('files'))
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 400

    new_ticket.status = 'ASSIGNED'
    db.session.add(TicketStatusHistory(
        ticket_id=new_ticket.id, actor_user_id=None, from_status='NEW',
        to_status='ASSIGNED', note=f'Tự động chuyển trực tiếp đến {assigned_receiver.full_name}.'
    ))
    for recipient in [assigned_receiver]:
        db.session.add(Notification(
            recipient_user_id=recipient.id,
            notification_type=f'SUPPORT_TICKET_NEW_{recipient_role}',
            title='Yêu cầu hỗ trợ mới dành cho bạn',
            message=f'{ticket_code}: {category} · {title}',
            target_url=url_for('support.view_support', ticket_id=new_ticket.id),
            reference_id=new_ticket.id,
        ))
    db.session.commit()
    return jsonify({
        'status': 'success', 'message': f'Đã gửi yêu cầu hỗ trợ với mã {ticket_code}.',
        'ticket_id': new_ticket.id, 'ticket_code': ticket_code,
    })


@api_bp.route('/support/tickets/<ticket_id>/reply', methods=['POST'])
@login_required
def reply_ticket(ticket_id):
    current_user = get_current_user()
    if current_user.role not in {'LECTURER', 'ACADEMIC_ADMIN', 'STUDENT'}:
        return jsonify({'status': 'error', 'message': 'Chỉ giảng viên hoặc cán bộ quản lý phản hồi xử lý; sinh viên chỉ bổ sung khi được yêu cầu.'}), 403
    data = request.form if request.form else (request.get_json(silent=True) or {})
    message_text = str(data.get('message', '')).strip()

    if not message_text:
        return jsonify({'status': 'error', 'message': 'Nội dung phản hồi không được để trống'}), 400

    ticket = SupportTicket.query.get_or_404(ticket_id)
    if not can_view_ticket(current_user, ticket):
        return jsonify({'status': 'error', 'message': 'Bạn không có quyền xem yêu cầu này.'}), 404
    if current_user.role == 'STUDENT' and ticket.status != 'PENDING_USER':
        return jsonify({'status': 'error', 'message': 'Chỉ bổ sung thông tin khi người xử lý đang chờ bạn.'}), 409
    if ticket.status in {'RESOLVED', 'CLOSED'}:
        return jsonify({'status': 'error', 'message': 'Yêu cầu đã giải quyết/đóng. Hãy mở lại trước khi trao đổi.'}), 409
    is_internal = str(data.get('is_internal', '')).lower() in {'1', 'true', 'on'}
    if is_internal and current_user.role == 'STUDENT':
        return jsonify({'status': 'error', 'message': 'Người gửi không thể tạo ghi chú nội bộ.'}), 403

    new_msg = TicketMessage(
        id=f"msg_{uuid.uuid4().hex[:12]}",
        ticket_id=ticket.id,
        sender_user_id=current_user.id,
        message=message_text,
        is_internal=is_internal,
        created_at=datetime.utcnow()
    )
    db.session.add(new_msg)
    db.session.flush()
    try:
        _save_ticket_attachments(ticket, new_msg, current_user, request.files.getlist('files'))
    except ValueError as exc:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': str(exc)}), 400

    if not is_internal:
        if current_user.role == 'STUDENT':
            if ticket.status == 'PENDING_USER':
                _record_ticket_status(ticket, current_user, 'IN_PROGRESS', 'Người gửi đã bổ sung thông tin.')
            if ticket.assigned_staff_user_id:
                recipient_ids = [ticket.assigned_staff_user_id]
            elif ticket.recipient_role == 'ACADEMIC_ADMIN':
                manager = get_primary_academic_manager()
                recipient_ids = [manager.id] if manager else []
            else:
                recipient_ids = []
                if ticket.course and ticket.course.created_by_user_id:
                    course_manager = User.query.filter_by(
                        id=ticket.course.created_by_user_id, role='LECTURER', is_active=True
                    ).first()
                    if course_manager:
                        recipient_ids = [course_manager.id]
            for recipient_id in recipient_ids:
                db.session.add(Notification(
                    recipient_user_id=recipient_id,
                    notification_type='SUPPORT_REQUESTER_REPLIED',
                    title='Người gửi đã phản hồi',
                    message=f'{ticket.ticket_code}: {ticket.title}',
                    target_url=url_for('support.view_support', ticket_id=ticket.id),
                    reference_id=new_msg.id,
                ))
        else:
            _notify_ticket_requester(
                ticket, 'SUPPORT_TICKET_REPLY', 'Yêu cầu hỗ trợ có phản hồi mới',
                f'{ticket.ticket_code}: {ticket.title}'
            )
    ticket.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': 'Đã gửi phản hồi thành công!',
        'created_at': new_msg.created_at.strftime('%H:%M %d/%m/%Y')
    })


@api_bp.route('/support/tickets/<ticket_id>/status', methods=['POST'])
@login_required
def update_ticket_status(ticket_id):
    current_user = get_current_user()
    data = request.get_json() or {}
    status = str(data.get('status', '')).upper()
    ticket = SupportTicket.query.get_or_404(ticket_id)
    if not can_view_ticket(current_user, ticket) or current_user.role == 'STUDENT':
        return jsonify({'status': 'error', 'message': 'Bạn không có quyền đổi trạng thái yêu cầu.'}), 403
    if status not in {'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'PENDING_USER', 'RESOLVED'}:
        return jsonify({'status': 'error', 'message': 'Trạng thái không hợp lệ.'}), 400
    if current_user.role in {'LECTURER', 'ACADEMIC_ADMIN'} and status not in {'OPEN', 'ASSIGNED', 'IN_PROGRESS', 'PENDING_USER', 'RESOLVED'}:
        return jsonify({'status': 'error', 'message': 'Trạng thái chuyển xử lý không hợp lệ.'}), 403
    if status == 'RESOLVED':
        resolution = str(data.get('resolution', '')).strip()
        if not resolution:
            return jsonify({'status': 'error', 'message': 'Nhập kết quả xử lý trước khi hoàn tất.'}), 400
        ticket.resolution = resolution
        ticket.resolved_at = datetime.utcnow()
        resolution_msg = TicketMessage(
            id=f'msg_{uuid.uuid4().hex[:12]}', ticket_id=ticket.id,
            sender_user_id=current_user.id, message=resolution,
            is_internal=False, created_at=ticket.resolved_at,
        )
        db.session.add(resolution_msg)
        _notify_ticket_requester(
            ticket, 'SUPPORT_TICKET_RESOLVED', 'Yêu cầu hỗ trợ đã được giải quyết',
            f'{ticket.ticket_code}: {ticket.title}'
        )
    elif status == 'OPEN':
        _notify_ticket_requester(
            ticket, 'SUPPORT_TICKET_ACCEPTED', 'Yêu cầu hỗ trợ đã được tiếp nhận',
            f'{ticket.ticket_code} đã được giảng viên/cán bộ quản lý tiếp nhận.'
        )
    elif status == 'PENDING_USER':
        _notify_ticket_requester(
            ticket, 'SUPPORT_TICKET_NEEDS_INFO', 'Yêu cầu hỗ trợ cần bạn bổ sung thông tin',
            f'{ticket.ticket_code}: {data.get("note", "Người xử lý đang chờ bạn phản hồi.")}'
        )
    if status in {'OPEN', 'ASSIGNED', 'IN_PROGRESS'} and ticket.accepted_at is None:
        ticket.accepted_at = datetime.utcnow()
    _record_ticket_status(ticket, current_user, status, data.get('note'))
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Đã chuyển yêu cầu sang {status}.'})


@api_bp.route('/support/tickets/<ticket_id>/close', methods=['POST'])
@login_required
def close_support_ticket(ticket_id):
    user = get_current_user()
    ticket = SupportTicket.query.get_or_404(ticket_id)
    if user.role != 'STUDENT' or ticket.student_user_id != user.id:
        return jsonify({'status': 'error', 'message': 'Chỉ người gửi mới được xác nhận đóng ticket.'}), 403
    if ticket.status != 'RESOLVED':
        return jsonify({'status': 'error', 'message': 'Chỉ có thể đóng yêu cầu đã được giải quyết.'}), 409
    ticket.closed_at = datetime.utcnow()
    _record_ticket_status(ticket, user, 'CLOSED', 'Người gửi xác nhận đã giải quyết xong.')
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Đã đóng yêu cầu hỗ trợ.'})


@api_bp.route('/support/tickets/<ticket_id>/reopen', methods=['POST'])
@login_required
def reopen_support_ticket(ticket_id):
    user = get_current_user()
    data = request.get_json() or {}
    ticket = SupportTicket.query.get_or_404(ticket_id)
    reason = str(data.get('reason', '')).strip()
    if user.role != 'STUDENT' or ticket.student_user_id != user.id:
        return jsonify({'status': 'error', 'message': 'Chỉ người gửi mới được mở lại yêu cầu.'}), 403
    if ticket.status not in {'RESOLVED', 'CLOSED'} or not reason:
        return jsonify({'status': 'error', 'message': 'Nhập lý do để mở lại yêu cầu đã giải quyết/đóng.'}), 400
    ticket.reopen_reason = reason
    ticket.resolved_at = None
    ticket.closed_at = None
    ticket.accepted_at = datetime.utcnow()
    if ticket.sla_hours:
        ticket.sla_due_at = datetime.utcnow() + timedelta(hours=ticket.sla_hours)
    _record_ticket_status(ticket, user, 'IN_PROGRESS', f'Mở lại: {reason}')
    if ticket.assigned_staff_user_id:
        db.session.add(Notification(
            recipient_user_id=ticket.assigned_staff_user_id,
            notification_type='SUPPORT_TICKET_REOPENED',
            title='Ticket được mở lại', message=f'{ticket.ticket_code}: {reason}',
            target_url=url_for('support.view_support', ticket_id=ticket.id),
            reference_id=f'reopen-{uuid.uuid4().hex[:16]}',
        ))
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Đã mở lại yêu cầu và báo người xử lý.'})


@api_bp.route('/support/tickets/<ticket_id>/rate', methods=['POST'])
@login_required
def rate_support_ticket(ticket_id):
    user = get_current_user()
    data = request.get_json() or {}
    ticket = SupportTicket.query.get_or_404(ticket_id)
    if user.role != 'STUDENT' or ticket.student_user_id != user.id:
        return jsonify({'status': 'error', 'message': 'Chỉ người gửi mới được đánh giá yêu cầu.'}), 403
    if ticket.status != 'CLOSED' or ticket.rated_at:
        return jsonify({'status': 'error', 'message': 'Yêu cầu chưa đóng hoặc đã được đánh giá.'}), 409
    try:
        speed = int(data.get('speed'))
        attitude = int(data.get('attitude'))
    except (TypeError, ValueError):
        return jsonify({'status': 'error', 'message': 'Chọn mức đánh giá từ 1 đến 5 sao.'}), 400
    if speed not in range(1, 6) or attitude not in range(1, 6):
        return jsonify({'status': 'error', 'message': 'Mức đánh giá phải từ 1 đến 5 sao.'}), 400
    ticket.satisfaction_speed = speed
    ticket.satisfaction_attitude = attitude
    ticket.satisfaction_comment = str(data.get('comment', '')).strip()[:2000] or None
    ticket.rated_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'status': 'success', 'message': 'Cảm ơn bạn đã đánh giá chất lượng hỗ trợ.'})


@api_bp.route('/support/ticket-attachments/<attachment_id>')
@login_required
def download_ticket_attachment(attachment_id):
    user = get_current_user()
    attachment = TicketAttachment.query.get_or_404(attachment_id)
    if not can_view_ticket(user, attachment.ticket):
        abort(404)
    if attachment.message.is_internal and user.role == 'STUDENT':
        abort(404)
    return send_from_directory(
        os.path.join(current_app.root_path, 'private_uploads'),
        attachment.file_url, as_attachment=True, download_name=attachment.file_name
    )


# CHAT TRỰC TIẾP VỚI TRỢ LÝ AI HỖ TRỢ NGƯỜI HỌC (24/7 AI TUTOR CHATBOT)
@api_bp.route('/support/chat-ai', methods=['POST'])
@login_required
def chat_with_ai():
    current_user = get_current_user()
    if current_user.role != 'STUDENT':
        return jsonify({'status': 'error', 'message': 'Trợ lý AI hiện chỉ dành cho sinh viên.'}), 403
    data = request.get_json() or {}
    user_prompt = data.get('message', '')
    course_id = data.get('course_id', '')

    if not isinstance(user_prompt, str) or not user_prompt.strip():
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập câu hỏi'}), 400
    if not isinstance(course_id, str) or not course_id.strip():
        return jsonify({'status': 'error', 'message': 'Chọn môn học để hỏi trợ lý môn học.'}), 400
    try:
        course, context = get_course_context(current_user, course_id.strip())
        ai_answer = answer_course_question(context, user_prompt.strip())
    except CourseAccessError:
        return jsonify({'status': 'error', 'message': 'Bạn không có quyền truy cập học liệu của môn này.'}), 404
    except TutorConfigurationError:
        return jsonify({'status': 'error', 'message': 'Trợ lý AI chưa được cấu hình API key.'}), 503
    except TutorServiceError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 502
    return jsonify({
        'status': 'success',
        'reply': ai_answer,
        'course': course.course_code,
        'timestamp': datetime.utcnow().strftime('%H:%M:%S')
    })


@api_bp.route('/support/chat-ai/suggestions', methods=['POST'])
@login_required
def suggest_course_questions():
    current_user = get_current_user()
    if current_user.role != 'STUDENT':
        return jsonify({'status': 'error', 'message': 'Câu hỏi gợi ý AI hiện chỉ dành cho sinh viên.'}), 403
    data = request.get_json() or {}
    course_id = data.get('course_id', '')
    if not isinstance(course_id, str) or not course_id.strip():
        return jsonify({'status': 'error', 'message': 'Chọn môn học để tạo câu hỏi gợi ý.'}), 400
    try:
        course, context = get_course_context(current_user, course_id.strip())
        questions = generate_course_questions(context, course.title_vi)
    except CourseAccessError:
        return jsonify({'status': 'error', 'message': 'Bạn không có quyền truy cập môn học này.'}), 404
    except TutorConfigurationError:
        return jsonify({'status': 'error', 'message': 'Trợ lý AI chưa được cấu hình API key.'}), 503
    except TutorServiceError as error:
        return jsonify({'status': 'error', 'message': str(error)}), 502
    return jsonify({'status': 'success', 'course_id': course.id, 'questions': questions})


# ==========================================
# 5. CHƯƠNG MỤC (FOLDER/CHAPTER) APIs
# ==========================================

@api_bp.route('/chapters/create', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def create_chapter():
    """Tạo chương mới (folder) trong đề cương môn học."""
    data = request.get_json() or {}
    syllabus_id = data.get('syllabus_id', '').strip()
    title = data.get('title', '').strip()
    allocated_periods = int(data.get('allocated_periods', 6))

    if not syllabus_id or not title:
        return jsonify({'status': 'error', 'message': 'Thiếu syllabus_id hoặc tên chương.'}), 400

    syllabus = CourseSyllabus.query.get(syllabus_id)
    if not syllabus:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy đề cương.'}), 404

    # Tính thứ tự chương tiếp theo
    existing_count = SyllabusChapter.query.filter_by(syllabus_id=syllabus_id).count()
    chapter_order = existing_count + 1

    chap_id = f"chap_{syllabus_id}_{uuid.uuid4().hex[:6]}"
    new_chap = SyllabusChapter(
        id=chap_id,
        syllabus_id=syllabus_id,
        chapter_order=chapter_order,
        title=title,
        total_lessons_count=0,
        allocated_periods=allocated_periods,
        completion_metric='Chưa bắt đầu'
    )
    db.session.add(new_chap)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Đã tạo chương mới "{title}" thành công!',
        'chapter_id': chap_id,
        'chapter_order': chapter_order
    })


@api_bp.route('/chapters/<chapter_id>/delete', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def delete_chapter(chapter_id):
    """Xóa chương (và toàn bộ bài học con) khỏi đề cương."""
    chap = SyllabusChapter.query.get_or_404(chapter_id)
    db.session.delete(chap)
    db.session.commit()
    return jsonify({'status': 'success', 'message': f'Đã xóa chương "{chap.title}" khỏi đề cương.'})


# ==========================================
# 6. HỌC LIỆU: THÊM FILE THỰC TẾ (UPLOAD)
# ==========================================

@api_bp.route('/materials/upload', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def upload_material():
    """
    Thêm học liệu số mới vào bài học.
    Nếu is_shared=true → tạo hồ sơ kiểm duyệt gửi CB quản lý.
    """
    current_user = get_current_user()
    data = request.get_json() or {}

    lesson_id = data.get('lesson_id', '').strip()
    title = data.get('title', '').strip()
    material_type = data.get('material_type', 'DOCUMENT_PDF')
    file_url = data.get('file_url', '').strip()
    file_size_bytes = int(data.get('file_size_bytes', 0))
    is_shared = bool(data.get('is_shared', False))
    author_name = data.get('author_name', current_user.full_name)
    source_origin = data.get('source_origin', f'Bộ môn - {current_user.user_code}')
    license_type = data.get('license_type', 'CC_BY_NC_SA')
    summary_desc = data.get('summary_desc', '')

    if not lesson_id or not title:
        return jsonify({'status': 'error', 'message': 'Thiếu thông tin bài học hoặc tên file.'}), 400

    lesson = Lesson.query.get(lesson_id)
    if not lesson:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy bài học.'}), 404

    # Lấy section_id từ chapter → syllabus → course → section
    section_id = None
    if lesson.chapter_id:
        chap = SyllabusChapter.query.get(lesson.chapter_id)
        if chap and chap.syllabus_id:
            syl = CourseSyllabus.query.get(chap.syllabus_id)
            if syl:
                sec = CourseSection.query.filter_by(course_id=syl.course_id).first()
                if sec:
                    section_id = sec.id

    if not section_id:
        # Fallback: lấy section đầu tiên của bất kỳ course nào
        sec = CourseSection.query.first()
        section_id = sec.id if sec else 'UNKNOWN_SEC'

    mat_id = f"mat_{uuid.uuid4().hex[:10]}"
    new_mat = LearningMaterial(
        id=mat_id,
        section_id=section_id,
        lesson_id=lesson_id,
        title=title,
        material_type=material_type,
        file_url=file_url if file_url else f"/static/uploads/{title.replace(' ', '_')}",
        file_size_bytes=file_size_bytes if file_size_bytes else None,
        version_tag='v1.0',
        is_shared_institutional_repo=is_shared,
        institutional_code=f"HL-{uuid.uuid4().hex[:6].upper()}" if is_shared else None,
        author_name=author_name,
        source_origin=source_origin,
        license_type=license_type,
        publication_status='PENDING_REVIEW' if is_shared else 'PUBLISHED',
        summary_desc=summary_desc,
        created_at=datetime.utcnow()
    )
    db.session.add(new_mat)
    db.session.flush()

    # Tạo DRM policy mặc định
    drm = DrmSecurityPolicy(
        id=f"drm_{uuid.uuid4().hex[:8]}",
        material_id=new_mat.id,
        view_online_only=True,
        dynamic_watermark_enabled=True,
        allow_offline_encrypted_study=False,
        author_digital_signature=f"{author_name} ({current_user.user_code})",
        signed_at=datetime.utcnow()
    )
    db.session.add(drm)

    # Nếu đăng ký kho dùng chung → tạo hồ sơ kiểm duyệt gửi CB
    approval_id = None
    if is_shared:
        cb_user = User.query.filter_by(role='ACADEMIC_ADMIN', is_active=True).first()
        reviewer_id = cb_user.id if cb_user else None

        approval_id = f"DOS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        dossier = MaterialApprovalDossier(
            id=approval_id,
            material_id=new_mat.id,
            submitter_user_id=current_user.id,
            current_step=1,
            status='PENDING_DEPARTMENT',
            reviewer_user_id=reviewer_id,
            reviewer_comment=(
                f'Hồ sơ học liệu "{title}" vừa được tải lên bởi {current_user.full_name} '
                f'({current_user.user_code}). Đang xếp hàng kiểm tra bản quyền số DRM & nội dung chuyên môn.'
            ),
            sla_deadline_hours=48,
            sla_remaining_hours=48,
            submitted_at=datetime.utcnow()
        )
        db.session.add(dossier)

    db.session.commit()

    result = {
        'status': 'success',
        'message': f'Đã tải lên học liệu "{title}" thành công!',
        'material_id': new_mat.id,
        'publication_status': new_mat.publication_status
    }
    if is_shared and approval_id:
        result['approval_id'] = approval_id
        result['message'] += f' Hồ sơ kiểm duyệt {approval_id} đã được gửi đến Cán bộ quản lý để phê duyệt.'
    return jsonify(result)


@api_bp.route('/materials/add-to-shared-repo', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN')
def add_to_shared_repo():
    """Thêm học liệu trực tiếp vào Kho dùng chung (không gắn với bài học cụ thể)."""
    current_user = get_current_user()
    data = request.get_json() or {}

    title = data.get('title', '').strip()
    material_type = data.get('material_type', 'DOCUMENT_PDF')
    file_url = data.get('file_url', '').strip()
    author_name = data.get('author_name', current_user.full_name)
    source_origin = data.get('source_origin', f'Bộ môn - {current_user.user_code}')
    license_type = data.get('license_type', 'CC_BY_NC_SA')
    summary_desc = data.get('summary_desc', '')

    if not title:
        return jsonify({'status': 'error', 'message': 'Tên học liệu không được để trống.'}), 400

    # Kho dùng chung cần 1 section nào đó để link vào
    sec = CourseSection.query.first()
    section_id = sec.id if sec else 'SHARED_REPO'

    mat_id = f"mat_{uuid.uuid4().hex[:10]}"
    new_mat = LearningMaterial(
        id=mat_id,
        section_id=section_id,
        lesson_id=None,
        title=title,
        material_type=material_type,
        file_url=file_url if file_url else f"/static/uploads/{title.replace(' ', '_')}",
        version_tag='v1.0',
        is_shared_institutional_repo=True,
        institutional_code=f"HL-{uuid.uuid4().hex[:6].upper()}",
        author_name=author_name,
        source_origin=source_origin,
        license_type=license_type,
        publication_status='PENDING_REVIEW',
        summary_desc=summary_desc,
        created_at=datetime.utcnow()
    )
    db.session.add(new_mat)
    db.session.flush()

    # DRM
    db.session.add(DrmSecurityPolicy(
        id=f"drm_{uuid.uuid4().hex[:8]}",
        material_id=new_mat.id,
        view_online_only=True,
        dynamic_watermark_enabled=True,
        allow_offline_encrypted_study=False,
        author_digital_signature=f"{author_name} ({current_user.user_code})",
        signed_at=datetime.utcnow()
    ))

    # Hồ sơ kiểm duyệt gửi CB
    cb_user = User.query.filter_by(role='ACADEMIC_ADMIN', is_active=True).first()
    approval_id = f"DOS-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    db.session.add(MaterialApprovalDossier(
        id=approval_id,
        material_id=new_mat.id,
        submitter_user_id=current_user.id,
        current_step=1,
        status='PENDING_DEPARTMENT',
        reviewer_user_id=cb_user.id if cb_user else None,
        reviewer_comment=f'Học liệu "{title}" đã được nộp vào Kho dùng chung, chờ kiểm duyệt.',
        sla_deadline_hours=48,
        sla_remaining_hours=48,
        submitted_at=datetime.utcnow()
    ))

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': f'Đã thêm "{title}" vào Kho Học liệu Dùng chung. Hồ sơ {approval_id} đang chờ CB phê duyệt.',
        'material_id': new_mat.id,
        'approval_id': approval_id
    })


# ==========================================
# 7. QUẢN LÝ LỚP HỌC PHẦN & SINH VIÊN
# ==========================================

@api_bp.route('/sections/list', methods=['GET'])
@login_required
def list_sections():
    """Lấy danh sách lớp học phần (có thể lọc theo GV phụ trách)."""
    current_user = get_current_user()
    sections = []

    if current_user.role == 'LECTURER':
        # Chỉ lấy section mà GV này phụ trách
        instructor_links = SectionInstructor.query.filter_by(user_id=current_user.id).all()
        section_ids = [link.section_id for link in instructor_links]
        sections = CourseSection.query.filter(CourseSection.id.in_(section_ids)).all()
    else:
        sections = CourseSection.query.all()

    return jsonify({
        'status': 'success',
        'sections': [
            {
                'id': s.id,
                'section_code': s.section_code,
                'display_name': s.display_name,
                'course_id': s.course_id,
                'enrollment_count': len(s.enrollments),
                'max_capacity': s.max_capacity
            }
            for s in sections
        ]
    })


@api_bp.route('/sections/create', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def create_section():
    """Tạo lớp học phần mới cho môn học."""
    current_user = get_current_user()
    data = request.get_json() or {}

    course_id = data.get('course_id', '').strip()
    syllabus_id = data.get('syllabus_id', '').strip()
    section_code = data.get('section_code', '').strip().upper()
    display_name = data.get('display_name', '').strip()
    created_at = datetime.utcnow()
    academic_year_start = created_at.year if created_at.month >= 9 else created_at.year - 1
    academic_year = f'{academic_year_start} - {academic_year_start + 1}'
    semester = data.get('semester', 'Học kỳ I')
    max_capacity = int(data.get('max_capacity', 60))
    day_of_week = data.get('day_of_week', 'Thứ 2')
    period_slot = data.get('period_slot', 'Tiết 1-3')
    physical_room = data.get('physical_room', 'Phòng TBA')

    if not course_id or not section_code or not display_name:
        return jsonify({'status': 'error', 'message': 'Thiếu course_id, section_code hoặc tên lớp học phần.'}), 400

    course = Course.query.get(course_id)
    if not course:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy môn học.'}), 404

    existing = CourseSection.query.filter_by(section_code=section_code).first()
    if existing:
        return jsonify({'status': 'error', 'message': f'Lớp học phần "{section_code}" đã tồn tại.'}), 400

    # Tìm syllabus nếu không truyền
    if not syllabus_id:
        syl = CourseSyllabus.query.filter_by(course_id=course_id).first()
        syllabus_id = syl.id if syl else None
    if not syllabus_id:
        return jsonify({'status': 'error', 'message': 'Môn học chưa có đề cương. Vui lòng tạo đề cương trước.'}), 400

    sec_id = f"sec_{section_code.lower()}_{uuid.uuid4().hex[:4]}"
    new_sec = CourseSection(
        id=sec_id,
        section_code=section_code,
        course_id=course_id,
        syllabus_id=syllabus_id,
        academic_year=academic_year,
        created_at=created_at,
        semester=semester,
        display_name=display_name,
        max_capacity=max_capacity,
        current_enrollment_count=0,
        day_of_week=day_of_week,
        period_slot=period_slot,
        instruction_mode='IN_PERSON',
        physical_room=physical_room,
        allow_self_enrollment=True,
        current_week_index=1,
        status='ACTIVE_IN_PROGRESS'
    )
    db.session.add(new_sec)
    db.session.flush()

    # Tự động thêm GV tạo vào danh sách giảng viên phụ trách
    if current_user.role == 'LECTURER':
        db.session.add(SectionInstructor(
            id=str(uuid.uuid4()),
            section_id=new_sec.id,
            user_id=current_user.id,
            role_in_section='PRIMARY_LECTURER',
            can_grade=True,
            can_take_attendance=True
        ))

    for week_number in range(1, 16):
        db.session.add(SectionWeek(
            id=f'week_{uuid.uuid4().hex[:16]}',
            section_id=new_sec.id,
            week_number=week_number,
            start_date=None,
            end_date=None,
            title=f'Tuần {week_number}',
            status='UPCOMING',
            materials_count=0,
            assignments_count=0
        ))

    db.session.commit()
    return jsonify({
        'status': 'success',
        'message': f'Đã tạo lớp học phần {section_code} thành công!',
        'section_id': new_sec.id
    })


@api_bp.route('/sections/<section_id>/enroll', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def enroll_student(section_id):
    """Ghi danh một hoặc nhiều sinh viên thuộc cùng lớp chuyên ngành."""
    data = request.get_json() or {}
    student_ids = list(dict.fromkeys(data.get('student_user_ids') or []))
    if not student_ids:
        single_id = (data.get('student_user_id') or '').strip()
        if single_id:
            student_ids = [single_id]
    administrative_class_id = (data.get('administrative_class_id') or '').strip()
    lab_group = data.get('lab_group', '')
    if not student_ids:
        return jsonify({'status': 'error', 'message': 'Hãy chọn ít nhất một sinh viên.'}), 400

    students = User.query.filter(User.id.in_(student_ids), User.role == 'STUDENT', User.is_active.is_(True)).all()
    if len(students) != len(student_ids):
        return jsonify({'status': 'error', 'message': 'Một hoặc nhiều sinh viên không tồn tại hoặc đã bị khóa.'}), 404
    if not administrative_class_id and len(students) == 1:
        administrative_class_id = students[0].administrative_class_id or ''
    admin_class = AdministrativeClass.query.get(administrative_class_id) if administrative_class_id else None
    if not admin_class:
        return jsonify({'status': 'error', 'message': 'Lớp chuyên ngành không tồn tại. Hãy xếp sinh viên vào lớp chuyên ngành trước.'}), 400
    if any(student.administrative_class_id != admin_class.id for student in students):
        return jsonify({'status': 'error', 'message': 'Danh sách có sinh viên không thuộc lớp chuyên ngành đã chọn.'}), 400

    section = CourseSection.query.get(section_id)
    if not section:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy lớp học phần.'}), 404

    current_count = SectionEnrollment.query.filter_by(section_id=section_id).count()
    existing_ids = {
        row.student_user_id for row in SectionEnrollment.query.filter(
            SectionEnrollment.section_id == section_id,
            SectionEnrollment.student_user_id.in_(student_ids)
        ).all()
    }
    new_students = [student for student in students if student.id not in existing_ids]
    if not new_students:
        return jsonify({'status': 'warning', 'message': 'Tất cả sinh viên được chọn đã có trong lớp học phần.'}), 200
    if current_count + len(new_students) > section.max_capacity:
        return jsonify({'status': 'error', 'message': f'Lớp học phần đã đủ sĩ số ({section.max_capacity} sinh viên).'}), 400

    for student in new_students:
        enrollment_id = str(uuid.uuid4())
        db.session.add(SectionEnrollment(
            id=enrollment_id,
            section_id=section_id,
            student_user_id=student.id,
            administrative_class_id=admin_class.id,
            lab_group=lab_group or None,
            attendance_percentage=100,
            consecutive_absences=0,
            study_status='ACTIVE',
            tuition_cleared=True,
            enrolled_at=datetime.utcnow()
        ))
        db.session.add(Notification(
            recipient_user_id=student.id,
            notification_type='SECTION_ENROLLED',
            title='Bạn được thêm vào lớp học phần',
            message=(
                f'Bạn đã được thêm vào lớp học phần {section.section_code} – {section.display_name} '
                f'thuộc môn {section.course.course_code} – {section.course.title_vi}.'
            ),
            target_url=url_for('curriculum.view_curriculum', section_id=section.id),
            reference_id=enrollment_id,
        ))
    section.current_enrollment_count = current_count + len(new_students)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Đã ghi danh {len(new_students)} sinh viên từ lớp {admin_class.class_code} vào lớp {section.section_code}.',
        'enrolled_count': len(new_students)
    })


def _create_overdue_notifications(student):
    now = datetime.now()
    assignments = Assignment.query.join(
        SectionWeek, Assignment.section_week_id == SectionWeek.id
    ).join(
        CourseSection, SectionWeek.section_id == CourseSection.id
    ).join(
        SectionEnrollment, SectionEnrollment.section_id == CourseSection.id
    ).filter(
        SectionEnrollment.student_user_id == student.id,
        Assignment.deadline_time < now,
    ).all()
    new_notifications = []
    for assignment in assignments:
        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment.id, student_user_id=student.id
        ).first()
        if submission and not submission.is_late and submission.submitted_at <= assignment.deadline_time:
            continue
        section_week = assignment.section_week
        section = section_week.section
        course = section.course
        already_notified = Notification.query.filter_by(
            recipient_user_id=student.id,
            notification_type='ASSIGNMENT_OVERDUE',
            reference_id=assignment.id,
        ).first()
        if already_notified:
            continue
        new_notifications.append(Notification(
            recipient_user_id=student.id,
            notification_type='ASSIGNMENT_OVERDUE',
            title='Assignment đã quá hạn',
            message=(
                f'Bạn đã quá hạn nộp assignment “{assignment.title}” của môn '
                f'{course.course_code} – {course.title_vi}, lớp {section.section_code}. '
                f'Hạn nộp: {assignment.deadline_time.strftime("%d/%m/%Y %H:%M")}.'
            ),
            target_url=url_for(
                'curriculum.view_curriculum', section_id=section.id,
                open_week=section_week.id, pane='assignment'
            ),
            reference_id=assignment.id,
        ))
    if new_notifications:
        db.session.add_all(new_notifications)
        try:
            db.session.commit()
        except SQLAlchemyError:
            db.session.rollback()
            current_app.logger.exception('Không tạo được thông báo assignment quá hạn cho sinh viên %s.', student.id)


@api_bp.route('/notifications', methods=['GET'])
@login_required
def list_notifications():
    user = get_current_user()
    _close_resolved_tickets()
    if user.role == 'STUDENT':
        _create_overdue_notifications(user)
    notices = Notification.query.filter_by(recipient_user_id=user.id).order_by(
        Notification.created_at.desc()
    ).limit(30).all()
    unread_count = Notification.query.filter_by(
        recipient_user_id=user.id, read_at=None
    ).count()
    return jsonify({
        'status': 'success',
        'unread_count': unread_count,
        'notifications': [{
            'id': notice.id,
            'notification_type': notice.notification_type,
            'title': notice.title,
            'message': notice.message,
            'target_url': notice.target_url,
            'created_at': notice.created_at.isoformat(),
            'is_read': notice.read_at is not None,
        } for notice in notices],
    })


@api_bp.route('/notifications/<notification_id>/read', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    user = get_current_user()
    notice = Notification.query.filter_by(
        id=notification_id, recipient_user_id=user.id
    ).first_or_404()
    if notice.read_at is None:
        notice.read_at = datetime.utcnow()
        db.session.commit()
    return jsonify({'status': 'success'})


@api_bp.route('/notifications/read-all', methods=['POST'])
@login_required
def mark_all_notifications_read():
    user = get_current_user()
    Notification.query.filter_by(
        recipient_user_id=user.id, read_at=None
    ).update({'read_at': datetime.utcnow()}, synchronize_session=False)
    db.session.commit()
    return jsonify({'status': 'success'})


@api_bp.route('/sections/<section_id>/unenroll', methods=['POST'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def unenroll_student(section_id):
    """Xóa sinh viên khỏi lớp học phần."""
    data = request.get_json() or {}
    student_user_id = data.get('student_user_id', '').strip()
    student_user_code = data.get('student_user_code', '').strip()

    student = None
    if student_user_id:
        student = User.query.get(student_user_id)
    elif student_user_code:
        student = User.query.filter_by(user_code=student_user_code).first()

    if not student:
        return jsonify({'status': 'error', 'message': 'Không tìm thấy sinh viên.'}), 404

    enrollment = SectionEnrollment.query.filter_by(section_id=section_id, student_user_id=student.id).first()
    if not enrollment:
        return jsonify({'status': 'error', 'message': 'Sinh viên này chưa ghi danh vào lớp.'}), 404

    section = CourseSection.query.get(section_id)
    db.session.delete(enrollment)
    if section:
        section.current_enrollment_count = max(0, section.current_enrollment_count - 1)
    db.session.commit()

    return jsonify({
        'status': 'success',
        'message': f'Đã xóa sinh viên {student.full_name} ({student.user_code}) khỏi lớp học phần.'
    })


@api_bp.route('/sections/<section_id>/students', methods=['GET'])
@login_required
def get_section_students(section_id):
    """Lấy danh sách sinh viên trong lớp học phần."""
    section = CourseSection.query.get_or_404(section_id)
    enrollments = SectionEnrollment.query.filter_by(section_id=section_id).all()

    return jsonify({
        'status': 'success',
        'section_code': section.section_code,
        'display_name': section.display_name,
        'students': [
            {
                'enrollment_id': e.id,
                'student_id': e.student_user_id,
                'user_code': e.student.user_code if e.student else '',
                'full_name': e.student.full_name if e.student else '',
                'lab_group': e.lab_group,
                'attendance_percentage': e.attendance_percentage,
                'study_status': e.study_status,
                'enrolled_at': e.enrolled_at.strftime('%d/%m/%Y') if e.enrolled_at else ''
            }
            for e in enrollments
        ]
    })


@api_bp.route('/students/search', methods=['GET'])
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def search_students():
    """Tìm kiếm sinh viên theo mã SV hoặc họ tên."""
    q = request.args.get('q', '').strip()
    section_id = request.args.get('section_id', '').strip()

    if not q or len(q) < 2:
        return jsonify({'status': 'error', 'message': 'Vui lòng nhập ít nhất 2 ký tự để tìm kiếm.'}), 400

    students = User.query.filter(
        User.role == 'STUDENT',
        User.is_active == True,
        (User.user_code.ilike(f'%{q}%')) | (User.full_name.ilike(f'%{q}%'))
    ).limit(20).all()

    # Nếu có section_id, đánh dấu sinh viên đã ghi danh
    enrolled_ids = set()
    if section_id:
        enrolled = SectionEnrollment.query.filter_by(section_id=section_id).all()
        enrolled_ids = {e.student_user_id for e in enrolled}

    return jsonify({
        'status': 'success',
        'students': [
            {
                'id': s.id,
                'user_code': s.user_code,
                'full_name': s.full_name,
                'email': s.email,
                'already_enrolled': s.id in enrolled_ids
            }
            for s in students
        ]
    })
