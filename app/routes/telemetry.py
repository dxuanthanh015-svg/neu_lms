from flask import Blueprint, render_template, request
from app.models import LearningTelemetryLog, AssignmentSubmission, AssignmentEvaluation, CourseSection, Lesson, LearningMaterial
from app.auth import login_required, role_required

telemetry_bp = Blueprint('telemetry', __name__)

@telemetry_bp.route('/telemetry')
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def view_telemetry():
    logs = LearningTelemetryLog.query.order_by(LearningTelemetryLog.last_heartbeat_at.desc()).all()
    submissions = AssignmentSubmission.query.all()
    section = CourseSection.query.filter_by(id='INT3110_01').first() or CourseSection.query.first()

    return render_template(
        'telemetry.html',
        logs=logs,
        submissions=submissions,
        section=section,
        current_nav='telemetry'
    )

@telemetry_bp.route('/student/lesson')
@telemetry_bp.route('/student/lesson/<lesson_id>')
@login_required
def student_lesson_view(lesson_id=None):
    lesson = None
    if lesson_id:
        lesson = Lesson.query.filter_by(id=lesson_id).first()
    if not lesson:
        lesson = Lesson.query.first()

    materials = LearningMaterial.query.filter_by(lesson_id=lesson.id).all() if lesson else []
    return render_template(
        'student_lesson.html',
        lesson=lesson,
        materials=materials,
        current_nav='student_lesson'
    )
