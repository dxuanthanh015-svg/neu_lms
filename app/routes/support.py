from datetime import datetime, timedelta
import uuid
from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from app.models import (
    db, SupportTicket, TicketMessage, Course, CourseSection,
    SectionEnrollment, SectionInstructor, User, TicketStatusHistory, Notification
)
from app.auth import login_required, get_current_user

support_bp = Blueprint('support', __name__)


def can_view_ticket(user, ticket):
    if user.role == 'STUDENT':
        return ticket.student_user_id == user.id
    if user.role == 'ADMIN':
        return True
    if user.role == 'LECTURER':
        return ticket.assigned_staff_user_id == user.id
    if user.role == 'ACADEMIC_ADMIN':
        manager = get_primary_academic_manager()
        return ticket.assigned_staff_user_id == user.id or (
            manager and manager.id == user.id and ticket.recipient_role == 'ACADEMIC_ADMIN'
        )
    return ticket.assigned_staff_user_id == user.id


def get_primary_academic_manager():
    managers = User.query.filter_by(role='ACADEMIC_ADMIN', is_active=True).limit(2).all()
    return managers[0] if len(managers) == 1 else None


def _close_resolved_tickets():
    cutoff = datetime.utcnow() - timedelta(days=5)
    tickets = SupportTicket.query.filter(
        SupportTicket.status == 'RESOLVED',
        SupportTicket.resolved_at.isnot(None),
        SupportTicket.resolved_at <= cutoff,
    ).all()
    for ticket in tickets:
        previous = ticket.status
        ticket.status = 'CLOSED'
        ticket.closed_at = datetime.utcnow()
        db.session.add(TicketStatusHistory(
            ticket_id=ticket.id, from_status=previous, to_status='CLOSED',
            note='Tự động đóng sau 5 ngày không có phản hồi từ người gửi.'
        ))
        db.session.add(Notification(
            recipient_user_id=ticket.student_user_id,
            notification_type='SUPPORT_TICKET_CLOSED',
            title='Yêu cầu hỗ trợ đã được đóng',
            message=f'Yêu cầu {ticket.ticket_code} đã tự động đóng sau 5 ngày kể từ khi giải quyết.',
            target_url=url_for('support.view_support', ticket_id=ticket.id),
            reference_id=f'auto-close-{ticket.id}',
        ))
    if tickets:
        db.session.commit()

@support_bp.route('/support')
@login_required
def view_support():
    current_user = get_current_user()
    _close_resolved_tickets()
    selected_status = request.args.get('status', 'ALL')
    selected_category = request.args.get('category', 'ALL')
    active_ticket_id = request.args.get('ticket_id', None)

    query = SupportTicket.query
    if current_user.role == 'STUDENT':
        query = query.filter_by(student_user_id=current_user.id)
    elif current_user.role == 'LECTURER':
        query = query.filter(SupportTicket.assigned_staff_user_id == current_user.id)
    elif current_user.role == 'ACADEMIC_ADMIN':
        manager = get_primary_academic_manager()
        if manager and manager.id == current_user.id:
            query = query.filter(db.or_(
                SupportTicket.recipient_role == 'ACADEMIC_ADMIN',
                SupportTicket.assigned_staff_user_id == current_user.id,
            ))
        else:
            query = query.filter(SupportTicket.assigned_staff_user_id == current_user.id)
    elif current_user.role != 'ADMIN':
        query = query.filter_by(assigned_staff_user_id=current_user.id)

    if selected_status != 'ALL':
        query = query.filter_by(status=selected_status)
    if selected_category != 'ALL':
        query = query.filter_by(category=selected_category)

    tickets = query.order_by(SupportTicket.created_at.desc()).all()

    active_ticket = None
    if active_ticket_id:
        active_ticket = SupportTicket.query.get(active_ticket_id)
        if active_ticket and not can_view_ticket(current_user, active_ticket):
            active_ticket = None
    elif tickets:
        active_ticket = tickets[0]

    if current_user.role == 'STUDENT':
        enrolled_courses = Course.query.join(
            CourseSection, CourseSection.course_id == Course.id
        ).join(
            SectionEnrollment, SectionEnrollment.section_id == CourseSection.id
        ).filter(
            SectionEnrollment.student_user_id == current_user.id
        ).distinct().order_by(Course.course_code).all()
        instructor_course_ids = {
            row[0] for row in db.session.query(CourseSection.course_id).join(
                SectionEnrollment, SectionEnrollment.section_id == CourseSection.id
            ).join(
                SectionInstructor, SectionInstructor.section_id == CourseSection.id
            ).join(
                User, User.id == SectionInstructor.user_id
            ).filter(
                SectionEnrollment.student_user_id == current_user.id,
                User.role == 'LECTURER', User.is_active.is_(True),
            ).distinct().all()
        }
        active_lecturer_ids = {
            row[0] for row in db.session.query(User.id).filter_by(role='LECTURER', is_active=True).all()
        }
        courses = [course for course in enrolled_courses if
                   course.id in instructor_course_ids or course.created_by_user_id in active_lecturer_ids]
    elif current_user.role == 'LECTURER':
        courses = Course.query.filter_by(created_by_user_id=current_user.id).order_by(Course.course_code).all()
    else:
        courses = Course.query.order_by(Course.course_code).all()

    requested_course_id = request.args.get('course_id', '').strip()
    selected_course = next((course for course in courses if course.id == requested_course_id), None)
    if not selected_course and courses:
        selected_course = courses[0]
    manager = get_primary_academic_manager()

    return render_template(
        'support.html',
        tickets=tickets,
        active_ticket=active_ticket,
        courses=courses,
        selected_course=selected_course,
        initial_tab=request.args.get('tab', 'tickets'),
        primary_academic_manager=manager,
        current_nav='support',
        selected_status=selected_status,
        selected_category=selected_category
    )
