import os
from flask import Flask, redirect, url_for
from sqlalchemy import inspect
from app.config import Config
from app.models import db
from app.auth import get_current_user

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)

    # Đăng ký context processor để mọi template đều có biến current_user
    @app.context_processor
    def inject_user():
        return dict(current_user=get_current_user())

    # Đăng ký các blueprints
    from app.routes.auth import auth_bp
    from app.routes.admin import admin_bp
    from app.routes.curriculum import curriculum_bp
    from app.routes.question_bank import question_bank_bp
    from app.routes.approval import approval_bp
    from app.routes.telemetry import telemetry_bp
    from app.routes.students import students_bp
    from app.routes.shared_repo import shared_repo_bp
    from app.routes.support import support_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(curriculum_bp)
    app.register_blueprint(question_bank_bp)
    app.register_blueprint(approval_bp)
    app.register_blueprint(telemetry_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(shared_repo_bp)
    app.register_blueprint(support_bp)
    app.register_blueprint(api_bp)

    @app.route('/')
    def index():
        current_user = get_current_user()
        if not current_user:
            return redirect(url_for('auth.login'))
        if current_user.role == 'ADMIN':
            return redirect(url_for('admin.manage_users'))
        if current_user.role == 'ACADEMIC_ADMIN':
            return redirect(url_for('approval.view_approvals'))
        return redirect(url_for('curriculum.view_curriculum'))

    # Khởi tạo cấu trúc bảng; dữ liệu chỉ được tạo từ thao tác thật của người dùng.
    with app.app_context():
        inspector = inspect(db.engine)
        if inspector.has_table('courses') and 'created_by_user_id' not in {column['name'] for column in inspector.get_columns('courses')}:
            with db.engine.begin() as connection:
                connection.exec_driver_sql('ALTER TABLE courses ADD COLUMN created_by_user_id VARCHAR(50) NULL')
        db.create_all()

        support_columns = {
            'course_materials': {
                'publication_status': "VARCHAR(30) NOT NULL DEFAULT 'PUBLISHED'",
                'reviewed_by_user_id': 'VARCHAR(50) NULL',
                'review_comment': 'TEXT NULL',
                'reviewed_at': 'DATETIME NULL',
            },
            'ticket_messages': {'is_internal': 'BOOLEAN NOT NULL DEFAULT FALSE'},
            'support_tickets': {
                'recipient_role': 'VARCHAR(30) NULL',
                'is_sensitive': 'BOOLEAN NOT NULL DEFAULT FALSE',
                'sla_hours': 'INT NULL',
                'sla_due_at': 'DATETIME NULL',
                'accepted_at': 'DATETIME NULL',
                'resolved_at': 'DATETIME NULL',
                'closed_at': 'DATETIME NULL',
                'resolution': 'TEXT NULL',
                'reopen_reason': 'TEXT NULL',
                'satisfaction_speed': 'INT NULL',
                'satisfaction_attitude': 'INT NULL',
                'satisfaction_comment': 'TEXT NULL',
                'rated_at': 'DATETIME NULL',
            },
        }
        for table_name, columns in support_columns.items():
            if not inspect(db.engine).has_table(table_name):
                continue
            existing_columns = {column['name'] for column in inspect(db.engine).get_columns(table_name)}
            for column_name, column_type in columns.items():
                if column_name not in existing_columns:
                    with db.engine.begin() as connection:
                        connection.exec_driver_sql(
                            f'ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}'
                        )

        if inspect(db.engine).has_table('support_tickets'):
            with db.engine.begin() as connection:
                connection.exec_driver_sql(
                    "UPDATE support_tickets SET recipient_role = 'ACADEMIC_ADMIN' WHERE recipient_role IS NULL"
                )
                connection.exec_driver_sql(
                    "UPDATE support_tickets SET status = 'NEW' WHERE status = 'PENDING'"
                )
                connection.exec_driver_sql(
                    "UPDATE support_tickets SET status = 'OPEN' WHERE status = 'PENDING_REVIEW'"
                )

        # Existing rows have no reliable creation timestamp in the old schema;
        # leave those values NULL rather than inventing historical dates.
        for table_name in ('courses', 'course_sections'):
            migration_inspector = inspect(db.engine)
            if migration_inspector.has_table(table_name) and 'created_at' not in {
                column['name'] for column in migration_inspector.get_columns(table_name)
            }:
                with db.engine.begin() as connection:
                    connection.exec_driver_sql(
                        f'ALTER TABLE {table_name} ADD COLUMN created_at DATETIME NULL'
                    )

        # Gắn quyền sở hữu cho môn cũ chỉ khi toàn bộ các lớp của môn có đúng một giảng viên duy nhất.
        from app.models import Course, CourseSection, SectionInstructor
        for course in Course.query.filter_by(created_by_user_id=None).all():
            instructor_ids = {
                row.user_id
                for row in SectionInstructor.query.join(
                    CourseSection, SectionInstructor.section_id == CourseSection.id
                ).filter(CourseSection.course_id == course.id).all()
            }
            if len(instructor_ids) == 1:
                course.created_by_user_id = next(iter(instructor_ids))
        db.session.commit()

    return app
