from functools import wraps
from flask import session, redirect, url_for, request, jsonify, render_template, abort
from app.models import User

def get_current_user():
    """Lấy thông tin người dùng hiện tại từ session."""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

def login_user(user):
    """Lưu phiên đăng nhập vào session."""
    session['user_id'] = user.id
    session['user_code'] = user.user_code
    session['full_name'] = user.full_name
    session['role'] = user.role
    session['email'] = user.email

def logout_user():
    """Xóa phiên đăng nhập khỏi session."""
    session.pop('user_id', None)
    session.pop('user_code', None)
    session.pop('full_name', None)
    session.pop('role', None)
    session.pop('email', None)

def login_required(f):
    """Decorator yêu cầu đăng nhập trước khi truy cập."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user = get_current_user()
        if not user:
            # Nếu là request API hoặc header json -> trả về JSON 401
            if request.path.startswith('/api/') or request.is_json or request.headers.get('Accept') == 'application/json':
                return jsonify({
                    'status': 'error',
                    'error': 'Unauthorized',
                    'message': 'Yêu cầu đăng nhập để truy cập tài nguyên này.'
                }), 401
            # Nếu là web request -> chuyển hướng tới trang login
            return redirect(url_for('auth.login', next=request.full_path if request.query_string else request.path))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*allowed_roles):
    """Decorator kiểm tra quyền hạn (Role-based Access Control)."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user = get_current_user()
            if not user:
                if request.path.startswith('/api/') or request.is_json or request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        'status': 'error',
                        'error': 'Unauthorized',
                        'message': 'Yêu cầu đăng nhập để thực hiện hành động này.'
                    }), 401
                return redirect(url_for('auth.login', next=request.path))

            if user.role not in allowed_roles:
                if request.path.startswith('/api/') or request.is_json or request.headers.get('Accept') == 'application/json':
                    return jsonify({
                        'status': 'error',
                        'error': 'Forbidden',
                        'message': f'Tài khoản vai trò "{user.role}" không có quyền truy cập chức năng này.'
                    }), 403
                
                # Render trang 403 thân thiện với người dùng
                return render_template(
                    '403.html',
                    current_user=user,
                    allowed_roles=allowed_roles
                ), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator
