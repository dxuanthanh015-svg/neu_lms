import os
import sys
import json
import uuid
import platform
import re
import unicodedata
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file
from app.models import db, User, Course, LearningMaterial, QuestionBank, SupportTicket, LearningTelemetryLog, SystemSetting, SystemAuditLog, AdministrativeClass
from app.auth import role_required, get_current_user
from app.config import Config, IS_MYSQL, DB_HOST, DB_PORT, DB_NAME

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

DEFAULT_SETTINGS = {
    'system_title': 'NEU LMS - Phân hệ M10 Khảo Thí Số',
    'institution_name': 'Đại học Kinh tế Quốc dân',
    'maintenance_mode': 'OFF',
    'max_upload_size_mb': '50',
    'default_drm_watermark': 'ENABLED',
    'ai_copilot_enabled': 'ENABLED',
    'ai_model_name': 'EduLLM-DeepSeek-v3-Integrated',
    'backup_retention_days': '30'
}

def build_neu_email(full_name, role, user_code):
    if role == 'STUDENT':
        return f'{user_code}@st.neu.edu.vn'

    normalized = unicodedata.normalize('NFKD', full_name.replace('Đ', 'D').replace('đ', 'd'))
    parts = ''.join(char for char in normalized if not unicodedata.combining(char)).lower().split()
    username = ''.join(part[0] for part in parts[:-1]) + parts[-1] if parts else user_code.lower()
    return f'{username}@neu.edu.vn'

def get_or_create_settings():
    """Lấy hoặc khởi tạo các cấu hình hệ thống từ CSDL"""
    settings = {}
    for key, def_val in DEFAULT_SETTINGS.items():
        record = SystemSetting.query.get(key)
        if not record:
            record = SystemSetting(key=key, value=def_val, description=f"Cấu hình {key}", category='SYSTEM')
            db.session.add(record)
        settings[key] = record.value
    db.session.commit()
    return settings

@admin_bp.route('/users', methods=['GET', 'POST'])
@role_required('ADMIN')
def manage_users():
    current_user = get_current_user()

    # Xử lý thêm tài khoản mới từ Form vào DB
    if request.method == 'POST':
        action = request.form.get('action', 'create')
        if action == 'create':
            user_code = request.form.get('user_code', '').strip()
            full_name = request.form.get('full_name', '').strip()
            role = request.form.get('role', 'STUDENT').strip()
            email = build_neu_email(full_name, role, user_code)
            administrative_class_id = request.form.get('administrative_class_id', '').strip() or None
            academic_title = request.form.get('academic_title', '').strip() or None
            department_code = request.form.get('department_code', 'FIT')

            if not re.fullmatch(r'\d{8}', user_code):
                flash("Mã định danh phải có đúng 8 chữ số.", "danger")
                return redirect(url_for('admin.manage_users'))

            if not user_code or not full_name or not email:
                flash("Vui lòng điền đầy đủ Mã định danh, Họ tên và Email.", "danger")
                return redirect(url_for('admin.manage_users'))

            if role == 'STUDENT' and not AdministrativeClass.query.get(administrative_class_id):
                flash("Sinh viên phải được xếp vào lớp chuyên ngành trước khi tạo tài khoản.", "danger")
                return redirect(url_for('admin.manage_users'))

            # Kiểm tra trùng lặp
            existing = User.query.filter((User.user_code == user_code) | (User.email == email)).first()
            if existing:
                flash(f"Mã người dùng '{user_code}' hoặc Email '{email}' đã tồn tại trong CSDL!", "danger")
                return redirect(url_for('admin.manage_users'))

            new_user = User(
                id=f"u_{role.lower()}_{uuid.uuid4().hex[:6]}",
                user_code=user_code,
                full_name=full_name,
                email=email,
                role=role,
                administrative_class_id=administrative_class_id if role == 'STUDENT' else None,
                academic_title=academic_title,
                auth_provider='NEU_SSO',
                two_factor_smart_id_enabled=True,
                is_active=True
            )
            db.session.add(new_user)

            # Ghi log kiểm toán hệ thống
            audit = SystemAuditLog(
                user_id=current_user.id,
                action='CREATE_USER',
                target_entity=f"User:{user_code}",
                details=f"Tạo tài khoản mới: {full_name} ({role}) - Email: {email}"
            )
            db.session.add(audit)
            db.session.commit()

            flash(f"Đã tạo tài khoản {full_name} ({user_code}) thành công và lưu vào CSDL!", "success")
            return redirect(url_for('admin.manage_users'))

    # GET Filter & List Users
    role_filter = request.args.get('role', '')
    status_filter = request.args.get('status', '')
    keyword = request.args.get('q', '').strip()

    query = User.query
    if role_filter:
        query = query.filter_by(role=role_filter)
    if status_filter:
        if status_filter == 'active':
            query = query.filter_by(is_active=True)
        elif status_filter == 'locked':
            query = query.filter_by(is_active=False)
    if keyword:
        kw = f"%{keyword}%"
        query = query.filter(
            (User.user_code.like(kw)) | 
            (User.full_name.like(kw)) | 
            (User.email.like(kw))
        )

    users = query.order_by(User.created_at.desc(), User.user_code.asc()).all()

    # Thống kê số lượng
    stats = {
        'total': User.query.count(),
        'students': User.query.filter_by(role='STUDENT').count(),
        'lecturers': User.query.filter_by(role='LECTURER').count(),
        'academic_admins': User.query.filter_by(role='ACADEMIC_ADMIN').count(),
        'admins': User.query.filter_by(role='ADMIN').count(),
        'active': User.query.filter_by(is_active=True).count(),
        'locked': User.query.filter_by(is_active=False).count(),
    }

    return render_template(
        'admin.html',
        active_tab='users',
        current_nav='admin_users',
        users=users,
        stats=stats,
        role_filter=role_filter,
        status_filter=status_filter,
        keyword=keyword,
        administrative_classes=AdministrativeClass.query.order_by(AdministrativeClass.class_code).all()
    )

@admin_bp.route('/users/<user_id>/toggle-status', methods=['POST'])
@role_required('ADMIN')
def toggle_user_status(user_id):
    current_user = get_current_user()
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("Bạn không thể tự khóa tài khoản Quản trị viên đang đăng nhập!", "warning")
        return redirect(url_for('admin.manage_users'))

    user.is_active = not user.is_active
    action_name = "MỞ KHÓA" if user.is_active else "KHÓA TÀI KHOẢN"

    audit = SystemAuditLog(
        user_id=current_user.id,
        action='TOGGLE_USER_STATUS',
        target_entity=f"User:{user.user_code}",
        details=f"{action_name} người dùng {user.full_name} ({user.user_code})"
    )
    db.session.add(audit)
    db.session.commit()

    flash(f"Đã {action_name.lower()} thành công cho tài khoản {user.full_name} ({user.user_code})!", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/users/<user_id>/update-role', methods=['POST'])
@role_required('ADMIN')
def update_user_role(user_id):
    current_user = get_current_user()
    user = User.query.get_or_404(user_id)
    new_role = request.form.get('role', '').strip()

    valid_roles = ['STUDENT', 'LECTURER', 'ACADEMIC_ADMIN', 'ADMIN']
    if new_role not in valid_roles:
        flash("Vai trò không hợp lệ!", "danger")
        return redirect(url_for('admin.manage_users'))

    old_role = user.role
    user.role = new_role

    audit = SystemAuditLog(
        user_id=current_user.id,
        action='UPDATE_USER_ROLE',
        target_entity=f"User:{user.user_code}",
        details=f"Chuyển vai trò {user.full_name} từ {old_role} sang {new_role}"
    )
    db.session.add(audit)
    db.session.commit()

    flash(f"Đã cập nhật vai trò của {user.full_name} sang '{new_role}' thành công!", "success")
    return redirect(url_for('admin.manage_users'))

@admin_bp.route('/system', methods=['GET', 'POST'])
@role_required('ADMIN')
def system_config():
    current_user = get_current_user()

    if request.method == 'POST':
        # Cập nhật cài đặt tham số hệ thống
        for key in DEFAULT_SETTINGS.keys():
            val = request.form.get(key)
            if val is not None:
                record = SystemSetting.query.get(key)
                if not record:
                    record = SystemSetting(key=key, value=val, category='SYSTEM')
                    db.session.add(record)
                else:
                    record.value = val

        audit = SystemAuditLog(
            user_id=current_user.id,
            action='UPDATE_SYSTEM_CONFIG',
            target_entity='SystemSetting',
            details='Cập nhật tham số vận hành hệ thống LMS & AI Copilot'
        )
        db.session.add(audit)
        db.session.commit()
        flash("Đã cập nhật cấu hình tham số hệ thống thành công!", "success")
        return redirect(url_for('admin.system_config'))

    settings = get_or_create_settings()

    # Thu thập số liệu vận hành và tài nguyên
    metrics = {
        'db_type': 'MySQL 8.0' if IS_MYSQL else 'SQLite Local Fallback',
        'db_host': DB_HOST if IS_MYSQL else 'Local File (lms_m10.db)',
        'db_port': DB_PORT if IS_MYSQL else 'N/A',
        'db_name': DB_NAME,
        'python_version': platform.python_version(),
        'os_info': f"{platform.system()} {platform.release()} ({platform.machine()})",
        'users_count': User.query.count(),
        'courses_count': Course.query.count(),
        'materials_count': LearningMaterial.query.count(),
        'questions_count': QuestionBank.query.count(),
        'tickets_count': SupportTicket.query.count(),
        'telemetry_count': LearningTelemetryLog.query.count()
    }

    # Danh sách bản sao lưu hiện có trong thư mục backups/
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    os.makedirs(backup_dir, exist_ok=True)
    backups = []
    try:
        for f in sorted(os.listdir(backup_dir), reverse=True):
            if f.endswith('.json') or f.endswith('.sql'):
                f_path = os.path.join(backup_dir, f)
                size_kb = round(os.path.getsize(f_path) / 1024, 2)
                mtime = datetime.fromtimestamp(os.path.getmtime(f_path)).strftime('%Y-%m-%d %H:%M:%S')
                backups.append({'filename': f, 'size_kb': size_kb, 'created_at': mtime})
    except Exception as e:
        print(f"Lỗi đọc thư mục backup: {e}")

    # Lịch sử kiểm toán gần nhất
    audit_logs = SystemAuditLog.query.order_by(SystemAuditLog.created_at.desc()).limit(20).all()

    return render_template(
        'admin.html',
        active_tab='system',
        current_nav='admin_system',
        settings=settings,
        metrics=metrics,
        backups=backups,
        audit_logs=audit_logs
    )

@admin_bp.route('/system/backup', methods=['POST'])
@role_required('ADMIN')
def backup_database():
    current_user = get_current_user()
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"lms_m10_backup_{timestamp}.json"
    filepath = os.path.join(backup_dir, filename)

    try:
        # Xuất dữ liệu chính ra file JSON snapshot
        data_dump = {
            'generated_at': datetime.utcnow().isoformat(),
            'by_user': current_user.user_code,
            'users': [u.to_dict() for u in User.query.all()],
            'courses': [{'id': c.id, 'course_code': c.course_code, 'title_vi': c.title_vi} for c in Course.query.all()],
            'materials_count': LearningMaterial.query.count(),
            'questions_count': QuestionBank.query.count(),
            'settings': {s.key: s.value for s in SystemSetting.query.all()}
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data_dump, f, ensure_ascii=False, indent=2)

        audit = SystemAuditLog(
            user_id=current_user.id,
            action='BACKUP_DATABASE',
            target_entity='DatabaseSnapshot',
            details=f"Tạo bản sao lưu CSDL: {filename}"
        )
        db.session.add(audit)
        db.session.commit()

        flash(f"Đã tạo bản sao lưu dữ liệu CSDL thành công: {filename}", "success")
    except Exception as e:
        flash(f"Lỗi khi sao lưu dữ liệu: {str(e)}", "danger")

    return redirect(url_for('admin.system_config'))

@admin_bp.route('/system/backup/download/<filename>')
@role_required('ADMIN')
def download_backup(filename):
    backup_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'backups')
    filepath = os.path.join(backup_dir, filename)
    if not os.path.exists(filepath):
        flash("Không tìm thấy file sao lưu yêu cầu.", "danger")
        return redirect(url_for('admin.system_config'))
    return send_file(filepath, as_attachment=True)
