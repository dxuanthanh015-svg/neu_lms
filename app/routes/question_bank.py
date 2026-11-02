from flask import Blueprint, render_template, request
from app.models import db, QuestionBank, QuestionOption, Course, SyllabusChapter
from app.auth import role_required, get_current_user

question_bank_bp = Blueprint('question_bank', __name__)

@question_bank_bp.route('/questions')
@role_required('LECTURER', 'ACADEMIC_ADMIN', 'ADMIN')
def view_question_bank():
    course_id = request.args.get('course_id', 'INT3110')
    bloom_level = request.args.get('bloom', 'ALL')
    status = request.args.get('status', 'ALL')
    chapter_id = request.args.get('chapter', 'ALL')

    course = Course.query.get(course_id) or Course.query.first()
    query = QuestionBank.query.filter_by(course_id=course.id) if course else QuestionBank.query

    if bloom_level != 'ALL':
        query = query.filter_by(bloom_level=bloom_level)
    if status != 'ALL':
        query = query.filter_by(status=status)
    if chapter_id != 'ALL':
        query = query.filter_by(chapter_id=chapter_id)

    questions = query.order_by(QuestionBank.id.desc()).all()
    chapters = SyllabusChapter.query.all()

    # Thống kê câu hỏi
    all_course_questions = QuestionBank.query.filter_by(course_id=course.id).all() if course else []
    total_q = len(all_course_questions)
    draft_q = sum(1 for q in all_course_questions if q.status == 'AI_DRAFT')
    approved_q = sum(1 for q in all_course_questions if q.status == 'APPROVED')

    return render_template(
        'question_bank.html',
        course=course,
        questions=questions,
        chapters=chapters,
        selected_bloom=bloom_level,
        selected_status=status,
        selected_chapter=chapter_id,
        current_nav='questions',
        stats={
            'total': total_q,
            'draft': draft_q,
            'approved': approved_q
        }
    )
