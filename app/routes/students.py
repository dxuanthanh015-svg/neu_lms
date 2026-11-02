import uuid
from flask import Blueprint, flash, render_template, request, redirect, url_for
from app.models import (
    db, SectionEnrollment, CourseSection, SectionInstructor,
    AdministrativeClass, User, Course, Department
)
from app.auth import login_required, role_required, get_current_user

students_bp = Blueprint('students', __name__)


@students_bp.route('/students')
@login_required
def view_students():
    current_user = get_current_user()

    # Lấy danh sách tất cả các lớp học phần (để filter UI)
    all_sections = []
    selected_section = None
    section_id = request.args.get('section_id', '')

    if current_user.role == 'LECTURER':
        # GV chỉ thấy lớp mình phụ trách
        instructor_links = SectionInstructor.query.filter_by(user_id=current_user.id).all()
        my_section_ids = [link.section_id for link in instructor_links]
        all_sections = CourseSection.query.filter(CourseSection.id.in_(my_section_ids)).all()
    elif current_user.role in ['ACADEMIC_ADMIN', 'ADMIN']:
        all_sections = CourseSection.query.all()

    # Chọn section cụ thể
    if section_id:
        selected_section = CourseSection.query.get(section_id)

    enrollments = []
    if current_user.role == 'STUDENT':
        # Sinh viên chỉ xem ghi danh của mình
        enrollments = SectionEnrollment.query.filter_by(student_user_id=current_user.id).all()
        selected_section = None
    elif selected_section:
        enrollments = (
            SectionEnrollment.query
            .filter_by(section_id=selected_section.id)
            .join(SectionEnrollment.student)
            .order_by(User.user_code)
            .all()
        )
    else:
        enrollments = []

    # Danh sách tất cả SV (để add vào lớp - chỉ hiện cho GV/Admin)
    all_students = []
    if current_user.role in ['LECTURER', 'ACADEMIC_ADMIN', 'ADMIN']:
        all_students = User.query.filter_by(role='STUDENT', is_active=True).order_by(User.user_code).all()

    classes = AdministrativeClass.query.order_by(AdministrativeClass.class_code).all()
    student_assignments = [{
        'id': student.id,
        'code': student.user_code,
        'name': student.full_name,
        'class_id': student.administrative_class_id
    } for student in all_students]
    class_rosters = []
    if current_user.role in ['LECTURER', 'ACADEMIC_ADMIN', 'ADMIN']:
        all_students = User.query.filter_by(role='STUDENT', is_active=True).order_by(User.user_code).all()
        enrolled_ids = set()
        if selected_section:
            enrolled_ids = {
                row.student_user_id
                for row in SectionEnrollment.query.filter_by(section_id=selected_section.id).all()
            }
        class_rosters = [{
            'id': cls.id,
            'code': cls.class_code,
            'program': cls.program_name,
            'students': [{
                'id': student.id,
                'code': student.user_code,
                'name': student.full_name,
                'email': student.email,
                'already_enrolled': student.id in enrolled_ids
            } for student in all_students if student.administrative_class_id == cls.id]
        } for cls in classes]
    all_courses = Course.query.order_by(Course.course_code).all()

    return render_template(
        'students.html',
        all_sections=all_sections,
        selected_section=selected_section,
        enrollments=enrollments,
        classes=classes,
        all_students=all_students,
        student_assignments=student_assignments,
        class_rosters=class_rosters,
        all_courses=all_courses,
        current_nav='students'
    )


@students_bp.route('/administrative-classes/create', methods=['POST'])
@role_required('ACADEMIC_ADMIN', 'ADMIN')
def create_administrative_class():
    class_code = request.form.get('class_code', '').strip().upper()
    program_name = request.form.get('program_name', '').strip()
    cohort = request.form.get('cohort', '').strip()
    if not class_code or not program_name or not cohort:
        flash('Vui lòng nhập mã lớp, chương trình đào tạo và khóa.', 'danger')
        return redirect(url_for('students.view_students'))
    if AdministrativeClass.query.filter_by(class_code=class_code).first():
        flash(f'Lớp chuyên ngành {class_code} đã tồn tại.', 'warning')
        return redirect(url_for('students.view_students'))

    department = Department.query.first()
    if not department:
        department = Department(
            id='dept_unassigned',
            code='UNASSIGNED',
            name='Chưa phân đơn vị',
            faculty_name='Đại học Kinh tế Quốc dân'
        )
        db.session.add(department)
        db.session.flush()

    db.session.add(AdministrativeClass(
        id=f'class_{uuid.uuid4().hex[:12]}',
        class_code=class_code,
        department_id=department.id,
        program_name=program_name,
        cohort=cohort,
        total_students=0
    ))
    db.session.commit()
    flash(f'Đã tạo lớp chuyên ngành {class_code}.', 'success')
    return redirect(url_for('students.view_students'))


@students_bp.route('/administrative-classes/<class_id>/assign-students', methods=['POST'])
@role_required('ACADEMIC_ADMIN', 'ADMIN')
def assign_students_to_class(class_id):
    admin_class = AdministrativeClass.query.get_or_404(class_id)
    student_ids = list(dict.fromkeys(request.form.getlist('student_ids')))
    students = User.query.filter(User.id.in_(student_ids), User.role == 'STUDENT').all() if student_ids else []
    for student in students:
        student.administrative_class_id = admin_class.id
        SectionEnrollment.query.filter_by(student_user_id=student.id).update(
            {SectionEnrollment.administrative_class_id: admin_class.id}, synchronize_session=False
        )
    admin_class.total_students = User.query.filter_by(administrative_class_id=admin_class.id, role='STUDENT').count()
    db.session.commit()
    flash(f'Đã xếp {len(students)} sinh viên vào lớp {admin_class.class_code}.', 'success')
    return redirect(url_for('students.view_students'))
