from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from app.models import db, User
from app.auth import login_user, logout_user, get_current_user

auth_bp = Blueprint('auth', __name__)

ROLE_NAMES = {
    'STUDENT': 'Sinh viên',
    'LECTURER': 'Giảng viên',
    'ACADEMIC_ADMIN': 'Cán bộ quản lý',
    'ADMIN': 'Quản trị viên'
}

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    current_user = get_current_user()
    if current_user:
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin.manage_users'))
        elif current_user.role == 'ACADEMIC_ADMIN':
            return redirect(url_for('approval.view_approvals'))
        elif current_user.role == 'STUDENT':
            return redirect(url_for('curriculum.view_curriculum'))
        else:
            return redirect(url_for('curriculum.view_curriculum'))

    next_url = request.args.get('next', '')
    selected_role = request.args.get('role', 'STUDENT')
    if selected_role not in ROLE_NAMES:
        selected_role = 'STUDENT'

    if request.method == 'POST':
        account_identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '').strip()
        role_choice = request.form.get('role_choice', selected_role)

        if not account_identifier:
            flash("Vui lòng nhập Mã số hoặc Email tài khoản.", "danger")
            return redirect(url_for('auth.login', role=role_choice, next=next_url))

        # Tìm user trong CSDL theo user_code hoặc email
        user = User.query.filter(
            (User.user_code == account_identifier) | (User.email == account_identifier)
        ).first()

        if not user:
            flash(f"Không tìm thấy tài khoản '{account_identifier}' trong CSDL hệ thống.", "danger")
            return redirect(url_for('auth.login', role=role_choice, next=next_url))

        if not user.is_active:
            flash("Tài khoản của bạn đang bị khóa hoặc chưa được kích hoạt.", "warning")
            return redirect(url_for('auth.login', role=role_choice, next=next_url))

        # Kiểm tra vai trò đăng nhập
        if role_choice and user.role != role_choice:
            user_role_label = ROLE_NAMES.get(user.role, user.role)
            chosen_role_label = ROLE_NAMES.get(role_choice, role_choice)
            flash(
                f"Tài khoản '{account_identifier}' có vai trò là '{user_role_label}', không thuộc danh mục '{chosen_role_label}'. Vui lòng chuyển tab sang đúng vai trò.",
                "warning"
            )
            return redirect(url_for('auth.login', role=user.role, next=next_url))

        # Đăng nhập thành công
        login_user(user)
        flash(f"Đăng nhập thành công! Chào mừng {user.full_name} ({ROLE_NAMES.get(user.role, user.role)})", "success")

        if next_url and not next_url.startswith('/login') and not next_url.startswith('/logout'):
            return redirect(next_url)

        if user.role == 'ADMIN':
            return redirect(url_for('admin.manage_users'))
        elif user.role == 'ACADEMIC_ADMIN':
            return redirect(url_for('approval.view_approvals'))
        elif user.role == 'STUDENT':
            return redirect(url_for('curriculum.view_curriculum'))
        else:
            return redirect(url_for('curriculum.view_curriculum'))

    return render_template(
        'login.html',
        selected_role=selected_role,
        role_names=ROLE_NAMES,
        next_url=next_url
    )

@auth_bp.route('/logout')
def logout():
    logout_user()
    flash("Bạn đã đăng xuất khỏi hệ thống thành công.", "info")
    return redirect(url_for('auth.login'))
