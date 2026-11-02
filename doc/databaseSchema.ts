import { TableDefinition, DatabaseRelationship, DesignScreenMapping, DomainCategory } from '../types/database';

export const DOMAIN_METADATA: Record<DomainCategory, { nameVi: string; color: string; bg: string; border: string; desc: string }> = {
  AUTH_USERS: {
    nameVi: 'Người dùng & Định danh NEU',
    color: '#2563eb',
    bg: '#eff6ff',
    border: '#bfdbfe',
    desc: 'Tài khoản SSO ĐHQG, phân quyền Giảng viên/Sinh viên/Cán bộ Khảo thí, 2FA SmartID, Lớp chuyên ngành'
  },
  CURRICULUM_CDIO: {
    nameVi: 'Đề cương & Chuẩn đầu ra CDIO',
    color: '#0891b2',
    bg: '#ecfeff',
    border: '#a5f3fc',
    desc: 'Môn học gốc, Đề cương chi tiết (INT3110_REV4), Cây chương mục, Chuẩn đầu ra CLO & thang Bloom'
  },
  SECTIONS_ENROLLMENT: {
    nameVi: 'Lớp học phần & Sĩ số',
    color: '#7c3aed',
    bg: '#f5f3ff',
    border: '#ddd6fe',
    desc: 'Lớp học phần (INT3110_01), phân công Giảng viên/TA, danh sách 58/60 sinh viên, chuyên cần & cảnh báo'
  },
  LESSONS_MATERIALS: {
    nameVi: 'Tuần học & Học liệu số',
    color: '#059669',
    bg: '#ecfdf5',
    border: '#a7f3d0',
    desc: '15 tuần học kỳ, bài học lý thuyết/thực hành, slide thuyết trình, video bài giảng, mã nguồn starter, Swagger'
  },
  DRM_APPROVAL: {
    nameVi: 'Bản quyền DRM & Phê duyệt M10.G3',
    color: '#d97706',
    bg: '#fffbeb',
    border: '#fde68a',
    desc: 'Chính sách DRM (Watermark động MSSV+IP), chữ ký số, quy trình thẩm định 4 bước, SLA 28h'
  },
  ASSIGNMENTS_GRADING: {
    nameVi: 'Assignment theo Tuần & Chấm điểm',
    color: '#ea580c',
    bg: '#fff7ed',
    border: '#fed7aa',
    desc: 'Đề bài #ASG-03 theo tuần, thời hạn nộp, trừ điểm trễ hạn, nộp file zip/git, rubric AI, điểm & nhận xét 9.5/10'
  },
  QUESTION_BANK_AI: {
    nameVi: 'Ngân hàng Đề & Trợ lý AI Khảo thí',
    color: '#4f46e5',
    bg: '#eef2ff',
    border: '#c7d2fe',
    desc: 'Ngân hàng câu hỏi #Q-AI-8921, phương án MCQ, EduLLM Copilot v4.2.1, trích dẫn chuẩn RFC 7231, Bloom L1-L4'
  },
  TELEMETRY_AUDIT: {
    nameVi: 'Giám sát Telemetry & Liêm chính',
    color: '#be123c',
    bg: '#fff1f2',
    border: '#fecdd3',
    desc: 'Nhật ký xem video thời gian thực, watermark động SV-2024-8849, mốc 80%, thông báo tự động'
  },
  STUDENT_SUPPORT: {
    nameVi: 'Hỗ trợ Người học & Chatbot AI',
    color: '#0d9488',
    bg: '#f0fdfa',
    border: '#99f6e4',
    desc: 'Yêu cầu hỗ trợ sinh viên, giải đáp chuyên môn & kỹ thuật, Trợ lý ảo Chatbot AI Tutor 24/7'
  }
};

export const DATABASE_TABLES: TableDefinition[] = [
  // 1. users
  {
    id: 'users',
    name: 'users',
    displayNameVi: 'Người dùng & Cán bộ / Sinh viên',
    domain: 'AUTH_USERS',
    descriptionVi: 'Quản lý thông tin định danh toàn hệ thống, tích hợp NEU Single Sign-On, SmartID OTP, vai trò Giảng viên, Sinh viên, Cán bộ khảo thí.',
    designScreenRef: 'Image 23 (Cổng Đăng nhập NEU LMS M10) & Header hệ thống',
    tags: ['Core', 'Auth', 'SSO', 'RBAC'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính định danh tài khoản', designOrigin: 'System Core PK', sampleValue: 'u_gv_0042' },
      { name: 'user_code', type: 'VARCHAR(50)', isNullable: false, isUnique: true, isIndexed: true, descriptionVi: 'Mã số Cán bộ (GV0042) hoặc Mã số Sinh viên (21020088)', designOrigin: 'Image 23 & Image 7: Mã GV / MSSV', sampleValue: 'GV0042' },
      { name: 'full_name', type: 'VARCHAR(150)', isNullable: false, descriptionVi: 'Họ và tên đầy đủ hiển thị trên hệ thống', designOrigin: 'Header: TS. Nguyễn Văn A', sampleValue: 'TS. Nguyễn Văn A' },
      { name: 'email', type: 'VARCHAR(150)', isNullable: false, isUnique: true, isIndexed: true, descriptionVi: 'Email sinh viên theo MSSV@st.neu.edu.vn; email giảng viên dùng miền @neu.edu.vn', designOrigin: 'Quy ước email NEU', sampleValue: '21020001@st.neu.edu.vn' },
      { name: 'role', type: 'VARCHAR(30)', isNullable: false, descriptionVi: 'Vai trò: LECTURER, STUDENT, ACADEMIC_ADMIN, EXAMINER', designOrigin: 'Image 23: Tab chọn đối tượng Giảng viên, Sinh viên, Khảo thí', sampleValue: 'LECTURER' },
      { name: 'administrative_class_id', type: 'VARCHAR(50)', isNullable: true, descriptionVi: 'Lớp chuyên ngành của sinh viên trước khi ghi danh lớp học phần', designOrigin: 'Quy trình quản lý lớp chuyên ngành', sampleValue: null },
      { name: 'academic_title', type: 'VARCHAR(50)', isNullable: true, descriptionVi: 'Học hàm/học vị (TS., ThS., PGS.TS., GS.TS., Cử nhân)', designOrigin: 'Image 1 & 3: TS., PGS.TS. Lê Hoàng Sơn', sampleValue: 'TS.' },
      { name: 'auth_provider', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'NEU_SSO'", descriptionVi: 'Phương thức xác thực: NEU_SSO, GOOGLE_WORKSPACE, MS365, LOCAL', designOrigin: 'Phương thức xác thực NEU, Google Workspace hoặc Microsoft 365', sampleValue: 'NEU_SSO' },
      { name: 'two_factor_smart_id_enabled', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Kích hoạt xác thực 2 lớp SmartID OTP', designOrigin: 'Image 23: Checkbox SmartID OTP và thông báo khảo thí', sampleValue: true },
      { name: 'avatar_url', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Đường dẫn ảnh đại diện', designOrigin: 'Header avatar', sampleValue: '/avatars/gv0042.png' },
      { name: 'is_active', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Trạng thái tài khoản đang hoạt động', designOrigin: 'Image 7: Kích hoạt tài khoản 96.5%', sampleValue: true },
      { name: 'created_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm tạo tài khoản', designOrigin: 'Audit system', sampleValue: '2024-01-10T08:00:00Z' }
    ]
  },

  // 2. departments
  {
    id: 'departments',
    name: 'departments',
    displayNameVi: 'Khoa / Viện & Bộ môn chuyên môn',
    domain: 'AUTH_USERS',
    descriptionVi: 'Cơ cấu tổ chức học thuật: Viện Công nghệ Thông tin, Khoa CNTT, Bộ môn Công nghệ Phần mềm (CNPM), v.v.',
    designScreenRef: 'Image 1: Viện CNTT; Image 3: Bộ môn CNPM, Khoa CNTT',
    tags: ['Organization', 'Academic Structure'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã định danh bộ môn/khoa', designOrigin: 'Org structure', sampleValue: 'dept_cnpm' },
      { name: 'code', type: 'VARCHAR(30)', isNullable: false, isUnique: true, descriptionVi: 'Ký hiệu viết tắt (CNPM, KHMT, HTTT)', designOrigin: 'Image 3: Bộ môn CNPM', sampleValue: 'CNPM' },
      { name: 'name', type: 'VARCHAR(150)', isNullable: false, descriptionVi: 'Tên đầy đủ của đơn vị chuyên môn', designOrigin: 'Image 3: Bộ môn Công nghệ Phần mềm', sampleValue: 'Bộ môn Công nghệ Phần mềm' },
      { name: 'faculty_name', type: 'VARCHAR(150)', isNullable: false, descriptionVi: 'Tên Khoa/Viện trực thuộc', designOrigin: 'Image 1: Viện Công nghệ Thông tin', sampleValue: 'Khoa Công nghệ Thông tin - Viện CNTT Đại học Kinh tế Quốc dân' },
      { name: 'head_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Trưởng bộ môn / Cán bộ quản lý chuyên môn', designOrigin: 'Image 3: PGS.TS. Lê Hoàng Sơn (Trưởng Bộ môn CNPM)', sampleValue: 'u_gv_lehoangson' }
    ]
  },

  // 3. administrative_classes
  {
    id: 'administrative_classes',
    name: 'administrative_classes',
    displayNameVi: 'Lớp chuyên ngành (Lớp danh nghĩa)',
    domain: 'AUTH_USERS',
    descriptionVi: 'Danh sách các lớp quản lý niên khóa sinh viên chính quy: K65-CNTT1, K65-CNTT2, K65-KTPM, K65-HTTT, K65-KHMT.',
    designScreenRef: 'Image 13: Danh sách Lớp chuyên ngành; Image 7: Phân bổ SV theo lớp',
    tags: ['Students', 'Academic Classes'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã lớp chuyên ngành', designOrigin: 'Image 13: K65-CNTT1', sampleValue: 'K65-CNTT1' },
      { name: 'class_code', type: 'VARCHAR(50)', isNullable: false, isUnique: true, descriptionVi: 'Mã hiển thị lớp (K65-CNTT1)', designOrigin: 'Image 7 & 13: K65-CNTT1', sampleValue: 'K65-CNTT1' },
      { name: 'department_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'departments', column: 'id' }, isNullable: false, descriptionVi: 'Đơn vị chuyên môn quản lý', designOrigin: 'Org FK', sampleValue: 'dept_cnpm' },
      { name: 'program_name', type: 'VARCHAR(150)', isNullable: false, descriptionVi: 'Tên chương trình đào tạo chuẩn (Chuẩn CNTT 2024)', designOrigin: 'Image 13: Công nghệ Thông tin - Chuẩn CNTT 2024', sampleValue: 'Công nghệ Thông tin' },
      { name: 'cohort', type: 'VARCHAR(20)', isNullable: false, descriptionVi: 'Khóa tuyển sinh (K65, K62-K65)', designOrigin: 'Image 23 & 1: Khóa K62-K65 / Niên khóa 2024-2025', sampleValue: 'K65' },
      { name: 'total_students', type: 'INTEGER', isNullable: false, defaultValue: '45', descriptionVi: 'Tổng số sinh viên danh nghĩa trong lớp', designOrigin: 'Image 13: 45 sinh viên danh nghĩa', sampleValue: 45 },
      { name: 'advisor_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Cố vấn học tập chủ nhiệm', designOrigin: 'Administrative assignment', sampleValue: 'u_gv_0042' }
    ]
  },

  // 4. courses
  {
    id: 'courses',
    name: 'courses',
    displayNameVi: 'Môn học gốc trong Khung chương trình',
    domain: 'CURRICULUM_CDIO',
    descriptionVi: 'Môn học chuẩn: INT3110 Lập trình Web Nâng cao, CS101 Lập trình Python, INT2208 CNPM.',
    designScreenRef: 'Image 1: Môn học liên kết INT3110; Image 21: CS101; Image 3: INT2208',
    tags: ['Curriculum', 'Credits', 'CDIO'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã môn học (INT3110, CS101, INT2208)', designOrigin: 'Image 1 & 9: Mã môn INT3110', sampleValue: 'INT3110' },
      { name: 'course_code', type: 'VARCHAR(30)', isNullable: false, isUnique: true, isIndexed: true, descriptionVi: 'Mã số môn học', designOrigin: 'Image 1: INT3110', sampleValue: 'INT3110' },
      { name: 'title_vi', type: 'VARCHAR(200)', isNullable: false, descriptionVi: 'Tên môn học tiếng Việt', designOrigin: 'Image 1: Lập trình Web Nâng cao', sampleValue: 'Lập trình Web Nâng cao' },
      { name: 'title_en', type: 'VARCHAR(200)', isNullable: true, descriptionVi: 'Tên môn học tiếng Anh', designOrigin: 'Image 9: Advanced Web Architecture', sampleValue: 'Advanced Web Architecture' },
      { name: 'credits', type: 'INTEGER', isNullable: false, defaultValue: '3', descriptionVi: 'Số tín chỉ quy đổi', designOrigin: 'Image 1 & 9: 3 Tín chỉ', sampleValue: 3 },
      { name: 'theory_hours', type: 'INTEGER', isNullable: false, defaultValue: '30', descriptionVi: 'Số tiết lý thuyết chuẩn', designOrigin: 'Image 9: 30 LT', sampleValue: 30 },
      { name: 'practical_hours', type: 'INTEGER', isNullable: false, defaultValue: '15', descriptionVi: 'Số tiết thực hành / Lab', designOrigin: 'Image 9: 15 TH / Tổng 45 Tiết', sampleValue: 15 },
      { name: 'department_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'departments', column: 'id' }, isNullable: false, descriptionVi: 'Bộ môn phụ trách học thuật', designOrigin: 'Image 3: Bộ môn CNPM', sampleValue: 'dept_cnpm' },
      { name: 'cdio_standard', type: 'VARCHAR(50)', isNullable: false, defaultValue: "'CDIO 2024'", descriptionVi: 'Khung chuẩn thẩm định giáo dục đại học', designOrigin: 'Image 9: Chuẩn CDIO 2024 Đại học Kinh tế Quốc dân', sampleValue: 'CDIO 2024' }
    ]
  },

  // 5. course_syllabi
  {
    id: 'course_syllabi',
    name: 'course_syllabi',
    displayNameVi: 'Đề cương chi tiết học phần & Ma trận CDIO',
    domain: 'CURRICULUM_CDIO',
    descriptionVi: 'Quản lý phiên bản đề cương học phần (INT3110_REV4), trạng thái phê duyệt cấp khoa, tiến độ số hóa bài học.',
    designScreenRef: 'Image 1: Áp dụng Đề cương INT3110_REV4; Image 9: Quản lý đề cương chi tiết',
    tags: ['Syllabus', 'CDIO', 'Accreditation'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã định danh đề cương chi tiết', designOrigin: 'Image 1 & 9: INT3110_REV4', sampleValue: 'INT3110_REV4' },
      { name: 'course_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'courses', column: 'id' }, isNullable: false, descriptionVi: 'Môn học áp dụng đề cương', designOrigin: 'Curriculum FK', sampleValue: 'INT3110' },
      { name: 'version_label', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Ký hiệu phiên bản (INT3110_REV4 Chuẩn)', designOrigin: 'Image 1: Đề cương INT3110_REV4 (Chuẩn)', sampleValue: 'INT3110_REV4' },
      { name: 'academic_year', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Năm học áp dụng (2024 - 2025)', designOrigin: 'Image 1: NIÊN KHÓA 2024 - 2025', sampleValue: '2024 - 2025' },
      { name: 'semester', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Học kỳ áp dụng (Học kỳ 1)', designOrigin: 'Image 1: Học kỳ 1', sampleValue: 'Học kỳ 1' },
      { name: 'approval_status', type: 'VARCHAR(50)', isNullable: false, defaultValue: "'APPROVED_FACULTY'", descriptionVi: 'Trạng thái: DRAFT, PENDING_DEPARTMENT, APPROVED_FACULTY', designOrigin: 'Image 1 & 9: Đã phê duyệt cấp Khoa / Đồng bộ 100% CDIO', sampleValue: 'APPROVED_FACULTY' },
      { name: 'digitized_progress_percentage', type: 'INTEGER', isNullable: false, defaultValue: '78', descriptionVi: 'Tỷ lệ số hóa học liệu bài học (78% - 7/9 bài học sẵn sàng)', designOrigin: 'Image 9: Tiến độ số hóa 78% (7/9 Bài học)', sampleValue: 78 },
      { name: 'approved_by_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Cán bộ lãnh đạo ký duyệt đề cương', designOrigin: 'Academic approval', sampleValue: 'u_gv_lehoangson' }
    ]
  },

  // 6. syllabus_chapters
  {
    id: 'syllabus_chapters',
    name: 'syllabus_chapters',
    displayNameVi: 'Chương mục Đề cương bài học',
    domain: 'CURRICULUM_CDIO',
    descriptionVi: 'Cây chương mục phân bổ: Chương 1 Kiến trúc Client-Server, Chương 2 Xác thực JWT, Chương 3 Tối ưu DB.',
    designScreenRef: 'Image 9: Cây chương mục (Chương 1, 2, 3)',
    tags: ['Curriculum', 'Chapters'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã chương học', designOrigin: 'Image 9: Chương 1', sampleValue: 'chap_int3110_c1' },
      { name: 'syllabus_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_syllabi', column: 'id' }, isNullable: false, descriptionVi: 'Đề cương chi tiết sở hữu chương', designOrigin: 'Syllabus hierarchy', sampleValue: 'INT3110_REV4' },
      { name: 'chapter_order', type: 'INTEGER', isNullable: false, descriptionVi: 'Số thứ tự chương (1, 2, 3)', designOrigin: 'Image 9: Chương 1, 2, 3', sampleValue: 1 },
      { name: 'title', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tiêu đề chương học', designOrigin: 'Image 9: Chương 1: Kiến trúc Client-Server & RESTful Architecture', sampleValue: 'Chương 1: Kiến trúc Client-Server & RESTful Architecture' },
      { name: 'total_lessons_count', type: 'INTEGER', isNullable: false, defaultValue: '3', descriptionVi: 'Số bài học trong chương', designOrigin: 'Image 9: 3 bài học', sampleValue: 3 },
      { name: 'allocated_periods', type: 'INTEGER', isNullable: false, defaultValue: '6', descriptionVi: 'Số tiết phân bổ theo đề cương', designOrigin: 'Image 9: 6 tiết học', sampleValue: 6 },
      { name: 'completion_metric', type: 'VARCHAR(50)', isNullable: false, defaultValue: "'2/3 Đạt'", descriptionVi: 'Trạng thái chuẩn hóa ma trận (2/3 Đạt, Sẵn sàng)', designOrigin: 'Image 9: 2/3 Đạt / 3/3 Đạt', sampleValue: '2/3 Đạt' }
    ]
  },

  // 7. course_learning_outcomes
  {
    id: 'course_learning_outcomes',
    name: 'course_learning_outcomes',
    displayNameVi: 'Chuẩn đầu ra Học phần (CLO & Bloom)',
    domain: 'CURRICULUM_CDIO',
    descriptionVi: 'Chuẩn đầu ra gắn với từng bài học, bài tập và câu hỏi thi: CLO-1.2, CLO-2.1 theo phân loại nhận thức Bloom.',
    designScreenRef: 'Image 9: Chuẩn đầu ra CLO-1.2 & CLO-2.1, Mức độ Bloom 3; Image 15: Cấp độ Bloom L1-L4',
    tags: ['CLO', 'Bloom', 'Accreditation'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã chuẩn đầu ra', designOrigin: 'Image 9: CLO-1.2', sampleValue: 'CLO-1.2' },
      { name: 'course_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'courses', column: 'id' }, isNullable: false, descriptionVi: 'Môn học sở hữu CLO', designOrigin: 'Course link', sampleValue: 'INT3110' },
      { name: 'clo_code', type: 'VARCHAR(30)', isNullable: false, descriptionVi: 'Ký hiệu mã chuẩn (CLO-1.2)', designOrigin: 'Image 9: CLO-1.2', sampleValue: 'CLO-1.2' },
      { name: 'target_bloom_level', type: 'VARCHAR(30)', isNullable: false, descriptionVi: 'Cấp độ Bloom nhận thức: L1_REMEMBER, L2_UNDERSTAND, L3_APPLY, L4_ANALYZE', designOrigin: 'Image 9 & 15: Mức độ Bloom 3 (Vận dụng)', sampleValue: 'L3_APPLY' },
      { name: 'description', type: 'TEXT', isNullable: false, descriptionVi: 'Mô tả năng lực sinh viên đạt được', designOrigin: 'Image 9: Nắm vững quy chuẩn routing trong Micro-framework Flask, serialize JSON...', sampleValue: 'Nắm vững quy chuẩn routing Micro-framework và cấu hình serialization JSON theo chuẩn RFC 7231' }
    ]
  },

  // 8. course_sections
  {
    id: 'course_sections',
    name: 'course_sections',
    displayNameVi: 'Lớp học phần Giảng dạy Thực tế',
    domain: 'SECTIONS_ENROLLMENT',
    descriptionVi: 'Lớp học phần thực tế mở theo học kỳ: INT3110_01, INT3110_02, INT3110_03, phòng học B3-202, ca học Thứ Năm, sĩ số 60.',
    designScreenRef: 'Image 1: Tạo Lớp học phần Mới; Image 5 & 7: Lớp học phần INT3110_01',
    tags: ['Sections', 'Timetable', 'Classroom'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã lớp học phần (INT3110_01)', designOrigin: 'Image 1: Mã lớp học phần INT3110_03; Image 5: INT3110_01', sampleValue: 'INT3110_01' },
      { name: 'section_code', type: 'VARCHAR(50)', isNullable: false, isUnique: true, isIndexed: true, descriptionVi: 'Mã lớp học phần chuẩn quản lý', designOrigin: 'Image 1: INT3110_01', sampleValue: 'INT3110_01' },
      { name: 'course_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'courses', column: 'id' }, isNullable: false, descriptionVi: 'Môn học gốc', designOrigin: 'Image 1: INT3110', sampleValue: 'INT3110' },
      { name: 'syllabus_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_syllabi', column: 'id' }, isNullable: false, descriptionVi: 'Đề cương chi tiết áp dụng', designOrigin: 'Image 1: Đề cương INT3110_REV4', sampleValue: 'INT3110_REV4' },
      { name: 'academic_year', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Niên khóa (2024 - 2025)', designOrigin: 'Image 1: NIÊN KHÓA 2024 - 2025', sampleValue: '2024 - 2025' },
      { name: 'semester', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Học kỳ (Học kỳ 1)', designOrigin: 'Image 1 & 7: Học kỳ 1', sampleValue: 'Học kỳ 1' },
      { name: 'display_name', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tên lớp học phần hiển thị trên bảng điểm & giao diện', designOrigin: 'Image 1: Lập trình Web Nâng cao - Lớp Thứ 5 (K65)', sampleValue: 'Lập trình Web Nâng cao - Lớp Thứ 5 (K65)' },
      { name: 'max_capacity', type: 'INTEGER', isNullable: false, defaultValue: '60', descriptionVi: 'Sĩ số tối đa phòng học cho phép', designOrigin: 'Image 1: Sĩ số tối đa 60; Image 7: 58 / 60 chỉ tiêu', sampleValue: 60 },
      { name: 'current_enrollment_count', type: 'INTEGER', isNullable: false, defaultValue: '58', descriptionVi: 'Số lượng sinh viên thực tế đã ghi danh', designOrigin: 'Image 7: 58 sinh viên', sampleValue: 58 },
      { name: 'day_of_week', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Lịch học trong tuần', designOrigin: 'Image 1: Thứ Năm hàng tuần; Image 7: Thứ 3', sampleValue: 'Thứ Năm hàng tuần' },
      { name: 'period_slot', type: 'VARCHAR(100)', isNullable: false, descriptionVi: 'Ca học / Tiết học quy định', designOrigin: 'Image 1: Tiết 4 - 6 (09:45 - 12:10)', sampleValue: 'Tiết 4 - 6 (09:45 - 12:10)' },
      { name: 'instruction_mode', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'IN_PERSON'", descriptionVi: 'Hình thức giảng dạy: IN_PERSON (Trực tiếp), ONLINE_VIRTUAL (Trực tuyến), BLENDED (Kết hợp)', designOrigin: 'Image 1: Hình thức tổ chức giảng dạy (3 tùy chọn)', sampleValue: 'IN_PERSON' },
      { name: 'physical_room', type: 'VARCHAR(100)', isNullable: false, descriptionVi: 'Địa điểm giảng đường / phòng máy', designOrigin: 'Image 1: Phòng máy B3-202 (Giảng đường B); Image 7: A2-405', sampleValue: 'Phòng máy B3-202 - Giảng đường B' },
      { name: 'virtual_meeting_url', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Đường dẫn phòng học trực tuyến Zoom/Teams/Meet', designOrigin: 'Image 1: Link phòng học https://meet.neu.edu.vn/int3110-...', sampleValue: 'https://meet.neu.edu.vn/int3110-01' },
      { name: 'allow_self_enrollment', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Cho phép sinh viên tự đăng ký bổ sung khi còn chỗ', designOrigin: 'Image 1: Switch Cho phép sinh viên tự đăng ký bổ sung', sampleValue: true },
      { name: 'current_week_index', type: 'INTEGER', isNullable: false, defaultValue: '3', descriptionVi: 'Tuần học hiện tại của học phần (Tuần 3 / Tuần 8)', designOrigin: 'Image 5: Tuần 3 đang diễn ra; Image 7: Tuần 8 / 15 tuần', sampleValue: 3 },
      { name: 'status', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'ACTIVE_IN_PROGRESS'", descriptionVi: 'Trạng thái: DRAFT, ENROLLING, ACTIVE_IN_PROGRESS, COMPLETED', designOrigin: 'Image 7: Đang diễn ra', sampleValue: 'ACTIVE_IN_PROGRESS' }
    ]
  },

  // 9. section_instructors
  {
    id: 'section_instructors',
    name: 'section_instructors',
    displayNameVi: 'Phân công Giảng viên & Trợ giảng',
    domain: 'SECTIONS_ENROLLMENT',
    descriptionVi: 'Phân công đội ngũ giảng dạy lớp học phần: Giảng viên chính (TS. Nguyễn Văn A), Trợ giảng (TA) hỗ trợ điểm danh & chấm bài.',
    designScreenRef: 'Image 1: Đội ngũ Giảng dạy phân công (TS. Nguyễn Văn A & Thêm Trợ giảng TA)',
    tags: ['Instructors', 'Teaching Staff'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính phân công', designOrigin: 'Junction PK', sampleValue: 'ins_int3110_01_a' },
      { name: 'section_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_sections', column: 'id' }, isNullable: false, descriptionVi: 'Lớp học phần', designOrigin: 'Section link', sampleValue: 'INT3110_01' },
      { name: 'user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: false, descriptionVi: 'Giảng viên hoặc Trợ giảng được phân công', designOrigin: 'Image 1: TS. Nguyễn Văn A (Mã GV: GV0042)', sampleValue: 'u_gv_0042' },
      { name: 'role_in_section', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'PRIMARY_LECTURER'", descriptionVi: 'Vai trò: PRIMARY_LECTURER (Chính), TEACHING_ASSISTANT (TA), CO_LECTURER', designOrigin: 'Image 1: Badge [CHÍNH] và ô [Thêm Trợ giảng (TA)]', sampleValue: 'PRIMARY_LECTURER' },
      { name: 'can_grade', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Quyền chấm điểm bài tập sinh viên', designOrigin: 'Image 1: Hỗ trợ chấm điểm', sampleValue: true },
      { name: 'can_take_attendance', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Quyền điểm danh sinh viên', designOrigin: 'Image 1: Điểm danh', sampleValue: true }
    ]
  },

  // 10. section_enrollments
  {
    id: 'section_enrollments',
    name: 'section_enrollments',
    displayNameVi: 'Ghi danh Sinh viên & Trạng thái Học tập',
    domain: 'SECTIONS_ENROLLMENT',
    descriptionVi: 'Danh sách sinh viên trong lớp học phần, liên kết lớp chuyên ngành, nhóm Lab, tỷ lệ chuyên cần, cảnh báo vắng.',
    designScreenRef: 'Image 7: Bảng Danh sách Sinh viên (58 SV); Image 13: Xác nhận Thêm sinh viên vào lớp',
    tags: ['Enrollment', 'Students', 'Attendance'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính ghi danh', designOrigin: 'Enrollment PK', sampleValue: 'enr_21020001' },
      { name: 'section_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_sections', column: 'id' }, isNullable: false, descriptionVi: 'Lớp học phần ghi danh', designOrigin: 'Image 7: INT3110_01', sampleValue: 'INT3110_01' },
      { name: 'student_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: false, descriptionVi: 'Tài khoản sinh viên', designOrigin: 'Image 7: Đặng Anh Tuấn (21020001)', sampleValue: 'u_sv_21020001' },
      { name: 'administrative_class_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'administrative_classes', column: 'id' }, isNullable: false, descriptionVi: 'Lớp chuyên ngành gốc (K65-CNTT1, K65-KTPM)', designOrigin: 'Image 7: Cột LỚP CHUYÊN NGÀNH (K65-CNTT1)', sampleValue: 'K65-CNTT1' },
      { name: 'lab_group', type: 'VARCHAR(50)', isNullable: true, descriptionVi: 'Phân nhóm thực hành Lab / Bài tập lớn', designOrigin: 'Image 7: Nhóm trưởng Lab 01, Thành viên Lab 02, Nhóm trưởng BTL', sampleValue: 'Nhóm trưởng Lab 01' },
      { name: 'attendance_percentage', type: 'INTEGER', isNullable: false, defaultValue: '100', descriptionVi: 'Tỷ lệ điểm danh chuyên cần (%)', designOrigin: 'Image 7: Tích cực (100%), Đang học (92%), Cảnh báo vắng (68%)', sampleValue: 100 },
      { name: 'consecutive_absences', type: 'INTEGER', isNullable: false, defaultValue: '0', descriptionVi: 'Số buổi vắng học liên tiếp', designOrigin: 'Image 7: Vắng 2 buổi liên tiếp', sampleValue: 0 },
      { name: 'study_status', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'ACTIVE'", descriptionVi: 'Trạng thái học tập: ACTIVE, WARNING, DISQUALIFIED', designOrigin: 'Image 7: Tích cực, Đang học, Cảnh báo vắng (>20% đình chỉ thi)', sampleValue: 'ACTIVE' },
      { name: 'tuition_cleared', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Đã hoàn tất nghĩa vụ học phí', designOrigin: 'Image 7: 100% Đã hoàn tất học phí', sampleValue: true },
      { name: 'enrolled_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm ghi danh vào lớp', designOrigin: 'Audit log', sampleValue: '2024-08-15T09:00:00Z' }
    ]
  },

  // 11. section_weeks
  {
    id: 'section_weeks',
    name: 'section_weeks',
    displayNameVi: 'Khung 15 Tuần Giảng dạy & Lộ trình',
    domain: 'LESSONS_MATERIALS',
    descriptionVi: 'Khung 15 tuần của lớp học phần; giảng viên bổ sung tài liệu và lịch thật cho từng tuần.',
    designScreenRef: 'Khung tuần học theo lớp học phần',
    tags: ['Weeks', 'Timeline', 'Syllabus'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã tuần học của lớp', designOrigin: 'Image 5: Tuần 3', sampleValue: 'week_int3110_w03' },
      { name: 'section_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_sections', column: 'id' }, isNullable: false, descriptionVi: 'Lớp học phần', designOrigin: 'Section link', sampleValue: 'INT3110_01' },
      { name: 'week_number', type: 'INTEGER', isNullable: false, descriptionVi: 'Số thứ tự tuần trong học kỳ (1 đến 15)', designOrigin: 'Khung 15 tuần', sampleValue: 1 },
      { name: 'start_date', type: 'DATE', isNullable: true, descriptionVi: 'Ngày bắt đầu tuần học nếu đã được xác định', designOrigin: 'Lịch giảng dạy do đơn vị cung cấp', sampleValue: null },
      { name: 'end_date', type: 'DATE', isNullable: true, descriptionVi: 'Ngày kết thúc tuần học nếu đã được xác định', designOrigin: 'Lịch giảng dạy do đơn vị cung cấp', sampleValue: null },
      { name: 'title', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tên tuần học; chủ đề được bổ sung theo đề cương thật', designOrigin: 'Khung tuần học', sampleValue: 'Tuần 1' },
      { name: 'content', type: 'TEXT', isNullable: true, descriptionVi: 'Nội dung, mục tiêu và ghi chú do giảng viên nhập cho tuần học', designOrigin: 'Nội dung tuần học', sampleValue: null },
      { name: 'status', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'UPCOMING'", descriptionVi: 'Trạng thái: COMPLETED, IN_PROGRESS, UPCOMING, LOCKED', designOrigin: 'Trạng thái tuần học', sampleValue: 'UPCOMING' },
      { name: 'materials_count', type: 'INTEGER', isNullable: false, defaultValue: '0', descriptionVi: 'Số học liệu đã tải lên tuần', designOrigin: 'Số liệu từ học liệu được gắn tuần', sampleValue: 0 },
      { name: 'assignments_count', type: 'INTEGER', isNullable: false, defaultValue: '0', descriptionVi: 'Số bài tập được gắn tuần', designOrigin: 'Số liệu từ bài tập thật', sampleValue: 0 }
    ]
  },

  // 12. lessons
  {
    id: 'lessons',
    name: 'lessons',
    displayNameVi: 'Bài học Chi tiết & Mục tiêu Sư phạm',
    domain: 'LESSONS_MATERIALS',
    descriptionVi: 'Nội dung bài học: Bài 1.2 Thao tác nâng cao trên List: Slicing & Comprehension; thời lượng, mục tiêu chuẩn đầu ra, đoạn mã code.',
    designScreenRef: 'Image 9: Bài 1.2 Xây dựng RESTful API; Image 21: Chi tiết Bài 1.2 Thao tác nâng cao trên List',
    tags: ['Lessons', 'Instruction', 'Pedagogy'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã bài học', designOrigin: 'Image 9 & 21: Bài 1.2', sampleValue: 'les_py_102' },
      { name: 'chapter_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'syllabus_chapters', column: 'id' }, isNullable: true, descriptionVi: 'Chương mục đề cương sở hữu', designOrigin: 'Image 9: Thuộc Chương 1', sampleValue: 'chap_int3110_c1' },
      { name: 'section_week_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'section_weeks', column: 'id' }, isNullable: true, descriptionVi: 'Tuần học tương ứng trong lớp', designOrigin: 'Section timeline', sampleValue: 'week_int3110_w03' },
      { name: 'lesson_number', type: 'VARCHAR(20)', isNullable: false, descriptionVi: 'Ký hiệu bài học (Bài 1.1, Bài 1.2)', designOrigin: 'Image 9 & 21: Bài 1.2', sampleValue: 'Bài 1.2' },
      { name: 'title', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tên bài học', designOrigin: 'Image 21: Thao tác nâng cao trên List: Slicing, Comprehension & Tối ưu Bộ nhớ', sampleValue: 'Thao tác nâng cao trên List: Slicing, Comprehension & Tối ưu Bộ nhớ' },
      { name: 'lesson_type', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'PRACTICE_LAB'", descriptionVi: 'Phân loại: THEORY (Lý thuyết), PRACTICE_LAB (Thực hành), QUIZ_REVIEW', designOrigin: 'Image 9: 4 Tiết (2 LT / 2 TH); Image 21: Thực hành', sampleValue: 'PRACTICE_LAB' },
      { name: 'duration_minutes', type: 'INTEGER', isNullable: false, defaultValue: '25', descriptionVi: 'Thời lượng bài giảng (phút)', designOrigin: 'Image 21: Thời lượng lý thuyết + code: 24 phút 30 giây', sampleValue: 25 },
      { name: 'code_snippet_content', type: 'TEXT', isNullable: true, descriptionVi: 'Đoạn mã nguồn mẫu hiển thị trong bài học', designOrigin: 'Image 21: snippet_1_2_slicing.py', sampleValue: 'dataset = [10, 20, 30, 40, 50, 60, 70, 80]\neven_reverse = dataset[-2::-2]' },
      { name: 'learning_goals_json', type: 'JSONB', isNullable: true, descriptionVi: 'Danh sách mục tiêu chuẩn đầu ra bài giảng (Checklist)', designOrigin: 'Image 21: List Slicing chuyên sâu, List Comprehension, Enumerate & Zip...', sampleValue: '["List Slicing chuyên sâu", "List Comprehension", "Enumerate & Zip", "Benchmark Hiệu năng"]' }
    ]
  },

  // 13. learning_materials
  {
    id: 'learning_materials',
    name: 'learning_materials',
    displayNameVi: 'Tệp Học liệu Số & Tài nguyên Đa phương tiện',
    domain: 'LESSONS_MATERIALS',
    descriptionVi: 'Tài liệu học tập số hóa: Slide thuyết trình (.pptx), Tài liệu (.pdf), Video bài giảng (.mp4), Gói boilerplate (.zip), Mô phỏng 3D WebXR, Sandbox URL.',
    designScreenRef: 'Image 5: Slide_Tuan3_Prisma.pptx; Image 9: Video_ThucHanh_Flask; Image 11: Modal Thêm tài liệu',
    tags: ['Materials', 'Files', 'Media'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã học liệu số', designOrigin: 'Image 3: Mã HL: HL-INT3110-2410', sampleValue: 'mat_slide_w03' },
      { name: 'section_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_sections', column: 'id' }, isNullable: false, descriptionVi: 'Lớp học phần sử dụng', designOrigin: 'Section link', sampleValue: 'INT3110_01' },
      { name: 'section_week_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'section_weeks', column: 'id' }, isNullable: true, descriptionVi: 'Tuần học gắn học liệu', designOrigin: 'Image 5: Tài nguyên Tuần 3', sampleValue: 'week_int3110_w03' },
      { name: 'lesson_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'lessons', column: 'id' }, isNullable: true, descriptionVi: 'Bài học cụ thể gắn tài liệu', designOrigin: 'Image 9: Học liệu số hóa gắn vào bài học', sampleValue: 'les_py_102' },
      { name: 'title', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tên học liệu / Tài liệu giảng dạy', designOrigin: 'Image 3: Giáo trình Kiến trúc Microservices & Docker; Image 5: Slide_Tuan3_Prisma.pptx', sampleValue: 'Slide_Tuan3_Prisma_PostgreSQL.pptx' },
      { name: 'material_type', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Loại học liệu: SLIDE_PRESENTATION, DOCUMENT_PDF, SOURCE_CODE_ZIP, VIDEO_RECORDING, WEBXR_3D, INTERACTIVE_SANDBOX', designOrigin: 'Image 11: 5 Loại tài liệu & định dạng hỗ trợ; Image 21: Mô hình 3D WebXR', sampleValue: 'SLIDE_PRESENTATION' },
      { name: 'file_url', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Đường dẫn lưu trữ hoặc URL bài giảng', designOrigin: 'File storage URL', sampleValue: '/files/int3110/Slide_Tuan3_Prisma.pptx' },
      { name: 'file_size_bytes', type: 'BIGINT', isNullable: true, descriptionVi: 'Dung lượng tệp (bytes)', designOrigin: 'Image 5: 11.6 MB • PPTX; Image 3: 18.4 MB', sampleValue: 12163481 },
      { name: 'version_tag', type: 'VARCHAR(20)', isNullable: false, defaultValue: "'v1.0'", descriptionVi: 'Phiên bản học liệu (v1.0, v2.0)', designOrigin: 'Image 3: Cập nhật phiên bản mới (v2.0)', sampleValue: 'v1.0' },
      { name: 'is_shared_institutional_repo', type: 'BOOLEAN', isNullable: false, defaultValue: 'false', descriptionVi: 'Đăng ký chia sẻ vào Kho Học liệu Dùng chung toàn Học viện', designOrigin: 'Image 3: Đăng ký chia sẻ vào Kho Dùng Chung toàn Học viện', sampleValue: true },
      { name: 'institutional_code', type: 'VARCHAR(50)', isNullable: true, descriptionVi: 'Mã định danh trong kho dùng chung (HL-INT3110-2410)', designOrigin: 'Image 3: Mã HL: HL-INT3110-2410', sampleValue: 'HL-INT3110-2410' }
    ]
  },

  // 14. drm_security_policies
  {
    id: 'drm_security_policies',
    name: 'drm_security_policies',
    displayNameVi: 'Chính sách Bản quyền & Quản trị DRM',
    domain: 'DRM_APPROVAL',
    descriptionVi: 'Cấu hình bản quyền số: Chỉ xem trực tuyến, Watermark động gắn MSSV + IP, cấm quay lén, mã hóa DRM học tập offline.',
    designScreenRef: 'Image 3: Cấu hình Bản quyền & Quyền truy cập (DRM); Image 9: Bảng điều khiển Bản quyền & DRM',
    tags: ['DRM', 'Copyright', 'Security', 'Watermark'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính chính sách DRM', designOrigin: 'DRM PK', sampleValue: 'drm_int3110_01' },
      { name: 'material_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'learning_materials', column: 'id' }, isNullable: false, isUnique: true, descriptionVi: 'Học liệu áp dụng chính sách', designOrigin: 'Material link', sampleValue: 'mat_slide_w03' },
      { name: 'view_online_only', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Chỉ cho phép xem trực tuyến trên hệ thống (giới hạn quyền tải)', designOrigin: 'Image 3 & 9: Chỉ xem trực tuyến', sampleValue: true },
      { name: 'dynamic_watermark_enabled', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Tự động gắn watermark chống sao chép mang Mã số Sinh viên và IP', designOrigin: 'Image 3: Watermark chống sao chép động mang Mã số Sinh viên (MSSV) và IP', sampleValue: true },
      { name: 'allow_offline_encrypted_study', type: 'BOOLEAN', isNullable: false, defaultValue: 'false', descriptionVi: 'Cho phép tải về máy cá nhân (Offline Study - mã hóa khóa chứng chỉ số LMS)', designOrigin: 'Image 3: Cho phép sinh viên tải về máy cá nhân (Offline Study)', sampleValue: false },
      { name: 'author_digital_signature', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Chữ ký số xác thực tác giả', designOrigin: 'Image 9: Chữ ký số tác giả: TS. Nguyễn Văn A (ID: GV0042)', sampleValue: 'TS. Nguyễn Văn A (ID: GV0042)' },
      { name: 'signed_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: true, descriptionVi: 'Thời điểm ký số học liệu', designOrigin: 'Image 9: Đồng bộ lần cuối: Hôm nay lúc 14:28:10', sampleValue: '2024-10-24T14:28:10Z' }
    ]
  },

  // 15. material_approval_dossiers
  {
    id: 'material_approval_dossiers',
    name: 'material_approval_dossiers',
    displayNameVi: 'Hồ sơ Thẩm định & Phê duyệt Học liệu Số',
    domain: 'DRM_APPROVAL',
    descriptionVi: 'Quy trình kiểm duyệt 4 bước: 1. Nộp hồ sơ -> 2. DRM & Ký số -> 3. Bộ môn thẩm định -> 4. Công bố Kho dùng chung; SLA 28 giờ.',
    designScreenRef: 'Image 3: Tải lên & Theo dõi Phê duyệt Học liệu Số (M10.G3)',
    tags: ['Approval', 'Workflow', 'SLA', 'Quality Assurance'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã hồ sơ thẩm định', designOrigin: 'Image 3: Mã nghiệp vụ M10.G3', sampleValue: 'DOS-2024-INT3110-09' },
      { name: 'material_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'learning_materials', column: 'id' }, isNullable: false, descriptionVi: 'Học liệu cần kiểm duyệt', designOrigin: 'Material link', sampleValue: 'mat_slide_w03' },
      { name: 'submitter_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: false, descriptionVi: 'Giảng viên nộp hồ sơ', designOrigin: 'Image 3: Chủ biên / Tác giả chính: TS. Nguyễn Văn A', sampleValue: 'u_gv_0042' },
      { name: 'current_step', type: 'INTEGER', isNullable: false, defaultValue: '3', descriptionVi: 'Bước hiện tại trong quy trình 4 bước (1..4)', designOrigin: 'Image 3: Tiến độ quy trình thẩm định 4 bước (Bước 3: Bộ môn thẩm định)', sampleValue: 3 },
      { name: 'status', type: 'VARCHAR(50)', isNullable: false, defaultValue: "'PENDING_DEPARTMENT'", descriptionVi: 'Trạng thái: PENDING_DEPARTMENT, ACTION_REQUIRED, APPROVED_PUBLISHED', designOrigin: 'Image 3: CẦN SỬA ĐỔI (ACTION REQUIRED), ĐANG THẨM ĐỊNH, ĐÃ PHÊ DUYỆT', sampleValue: 'ACTION_REQUIRED' },
      { name: 'reviewer_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Cán bộ thẩm định chuyên môn / Trưởng bộ môn', designOrigin: 'Image 3: ThS. Trần Thị Mai (Cán bộ Thẩm định CL) / PGS.TS. Lê Hoàng Sơn', sampleValue: 'u_gv_lehoangson' },
      { name: 'reviewer_comment', type: 'TEXT', isNullable: true, descriptionVi: 'Nhận xét trích dẫn của cán bộ quản lý / thẩm định', designOrigin: 'Image 3: Ý kiến đánh giá: Slide trình bày tốt nhưng slide 24 & 28 cần bổ sung nguồn IEEE...', sampleValue: 'Slide trình bày cấu trúc rất trực quan... Tuy nhiên ở Slide 24 và Slide 28, sơ đồ phân luồng kiến trúc API Gateway chưa ghi nguồn tham khảo chuẩn IEEE.' },
      { name: 'sla_deadline_hours', type: 'INTEGER', isNullable: false, defaultValue: '28', descriptionVi: 'Hạn mức thời gian duyệt theo quy chế (SLA)', designOrigin: 'Image 3: SLA 28 giờ / hồ sơ (Nhanh hơn 14% so với quy định)', sampleValue: 28 },
      { name: 'sla_remaining_hours', type: 'INTEGER', isNullable: false, defaultValue: '16', descriptionVi: 'Thời gian SLA còn lại', designOrigin: 'Image 3: Còn 16h', sampleValue: 16 },
      { name: 'submitted_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm nộp hồ sơ', designOrigin: 'Image 3: Nộp: 22/10/2024', sampleValue: '2024-10-22T10:00:00Z' }
    ]
  },

  // 16. assignments
  {
    id: 'assignments',
    name: 'assignments',
    displayNameVi: 'Đề bài Assignment theo Tuần học',
    domain: 'ASSIGNMENTS_GRADING',
    descriptionVi: 'Cấu hình bài tập tuần: #ASG-03 Xây dựng Module Authentication JWT, loại Lab/Group/Quiz, hạn chót, quy tắc phạt trễ 10%/ngày, trọng số 15%.',
    designScreenRef: 'Image 17 & 18: Modal Tạo / Chỉnh sửa Đề Assignment theo Tuần (#ASG-03); Image 5: Box Assignment 3',
    tags: ['Assignments', 'Homework', 'Evaluation', 'Rubric'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã bài tập (#ASG-03)', designOrigin: 'Image 18: Chế độ sửa đề #ASG-03', sampleValue: 'ASG-03' },
      { name: 'section_week_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'section_weeks', column: 'id' }, isNullable: false, descriptionVi: 'Tuần học áp dụng đề bài', designOrigin: 'Image 18: Tuần học áp dụng (Tuần 3: Cơ sở dữ liệu ORM & Auth JWT)', sampleValue: 'week_int3110_w03' },
      { name: 'assignment_type', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'LAB_INDIVIDUAL'", descriptionVi: 'Phân loại: LAB_INDIVIDUAL, GROUP_PROJECT, QUIZ_MCQ, SURVEY', designOrigin: 'Image 18: 4 tùy chọn Lab (Cá nhân), Bài tập lớn/Nhóm, Quiz trắc nghiệm, Khảo sát', sampleValue: 'LAB_INDIVIDUAL' },
      { name: 'title', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tiêu đề bài tập tuần', designOrigin: 'Image 18: Assignment 3: Xây dựng Module Authentication JWT & Middleware Phân quyền', sampleValue: 'Assignment 3: Xây dựng Module Authentication JWT & Middleware Phân quyền' },
      { name: 'instructions_markdown', type: 'TEXT', isNullable: false, descriptionVi: 'Nội dung hướng dẫn & đặc tả chi tiết đề bài', designOrigin: 'Image 18: Textarea Soạn thảo yêu cầu: Express.js, băm bcryptjs (salt=10), JWT...', sampleValue: 'Yêu cầu: Sinh viên xây dựng API login/register bằng Express.js, băm mật khẩu với bcryptjs (salt=10), cấp phát Access Token (15 phút) & Refresh Token (7 ngày).' },
      { name: 'open_time', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, descriptionVi: 'Thời điểm tự động mở cổng nộp bài', designOrigin: 'Image 18: 1. Mở cổng nộp bài: 2024-08-29 08:00', sampleValue: '2024-08-29T08:00:00Z' },
      { name: 'deadline_time', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, descriptionVi: 'Hạn nộp bài chính thức', designOrigin: 'Image 18: 2. Hạn nộp chính thức: 2024-09-05 23:59', sampleValue: '2024-09-05T23:59:00Z' },
      { name: 'cutoff_hard_deadline', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, descriptionVi: 'Hạn chót khóa cổng hoàn toàn (Hard deadline)', designOrigin: 'Image 18: 3. Hạn chót khóa cổng: 2024-09-08 23:59', sampleValue: '2024-09-08T23:59:00Z' },
      { name: 'allow_late_submission', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Cho phép nộp muộn sau deadline chính thức', designOrigin: 'Image 18: Toggle Cho phép nộp muộn sau deadline', sampleValue: true },
      { name: 'late_penalty_percent_per_day', type: 'INTEGER', isNullable: false, defaultValue: '10', descriptionVi: 'Tỷ lệ % điểm phạt cho mỗi 24 giờ nộp trễ', designOrigin: 'Image 18: Trừ 10% điểm cho mỗi 24 giờ trễ (tối đa 3 ngày)', sampleValue: 10 },
      { name: 'auto_remind_setting', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'24_6'", descriptionVi: 'Cấu hình tự động nhắc deadline qua email/LMS', designOrigin: 'Image 18: Nhắc trước 24 giờ & 6 giờ', sampleValue: '24_6' },
      { name: 'max_score', type: 'DECIMAL(4,2)', isNullable: false, defaultValue: '10.00', descriptionVi: 'Thang điểm tối đa', designOrigin: 'Image 18: Thang điểm tối đa: 10 Điểm', sampleValue: 10.0 },
      { name: 'course_weight_percentage', type: 'DECIMAL(4,2)', isNullable: false, defaultValue: '15.00', descriptionVi: 'Trọng số điểm trong học phần (%)', designOrigin: 'Image 18: Trọng số học phần: 15%', sampleValue: 15.0 },
      { name: 'allowed_submission_formats', type: 'JSONB', isNullable: false, descriptionVi: 'Các phương thức nộp bài cho phép', designOrigin: 'Image 18: Tải tệp tin (.zip, .pdf), Git Repo URL, Online Text', sampleValue: '["FILE_UPLOAD", "GIT_REPO_URL"]' },
      { name: 'version_label', type: 'VARCHAR(20)', isNullable: false, defaultValue: "'v2.1'", descriptionVi: 'Phiên bản đề bài cập nhật', designOrigin: 'Image 18: Phiên bản v2.1', sampleValue: 'v2.1' }
    ]
  },

  // 17. assignment_attachments
  {
    id: 'assignment_attachments',
    name: 'assignment_attachments',
    displayNameVi: 'Tệp Đính kèm Đề bài Assignment',
    domain: 'ASSIGNMENTS_GRADING',
    descriptionVi: 'Bộ đề thi PDF và mã nguồn mẫu boilerplate đính kèm cho sinh viên tải về làm bài.',
    designScreenRef: 'Image 18: Tài liệu & Bộ đề đính kèm (De_Bai_Assignment_03.pdf & starter-auth-boilerplate.zip)',
    tags: ['Attachments', 'Boilerplate'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính tệp đính kèm', designOrigin: 'Attachment PK', sampleValue: 'att_asg03_01' },
      { name: 'assignment_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'assignments', column: 'id' }, isNullable: false, descriptionVi: 'Đề bài sở hữu tệp', designOrigin: 'Assignment link', sampleValue: 'ASG-03' },
      { name: 'file_name', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tên tệp đính kèm', designOrigin: 'Image 18: De_Bai_Assignment_03.pdf / starter-auth-boilerplate.zip', sampleValue: 'De_Bai_Assignment_03.pdf' },
      { name: 'file_size_bytes', type: 'BIGINT', isNullable: false, descriptionVi: 'Dung lượng tệp (bytes)', designOrigin: 'Image 18: 1.8 MB / 3.4 MB', sampleValue: 1887436 },
      { name: 'file_type', type: 'VARCHAR(30)', isNullable: false, descriptionVi: 'Loại tệp: PDF, ZIP, DOCX, JSON', designOrigin: 'Image 18: PDF Đề thi / Mã nguồn mẫu', sampleValue: 'PDF' },
      { name: 'download_url', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Đường dẫn tải tệp', designOrigin: 'Storage link', sampleValue: '/assignments/De_Bai_Assignment_03.pdf' }
    ]
  },

  // 18. assignment_submissions
  {
    id: 'assignment_submissions',
    name: 'assignment_submissions',
    displayNameVi: 'Bài nộp Sinh viên & Tệp Mã nguồn / Git',
    domain: 'ASSIGNMENTS_GRADING',
    descriptionVi: 'Dữ liệu nộp bài của sinh viên: file nén zip, link Git Repo, ghi chú cho Giảng viên, trạng thái đúng hạn / nộp trễ.',
    designScreenRef: 'Image 25: Khung Nộp Bài Tập & Bài nộp sinh viên; Image 5: 42/58 SV nộp',
    tags: ['Submissions', 'Grading', 'Git'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính bài nộp', designOrigin: 'Submission PK', sampleValue: 'sub_21020088_asg03' },
      { name: 'assignment_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'assignments', column: 'id' }, isNullable: false, descriptionVi: 'Bài tập được nộp', designOrigin: 'Image 25: Bài tập 03: JWT Authentication', sampleValue: 'ASG-03' },
      { name: 'student_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: false, descriptionVi: 'Sinh viên nộp bài', designOrigin: 'Image 25: Nguyễn Văn An (MSSV: 21020088)', sampleValue: 'u_sv_21020088' },
      { name: 'submission_status', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'SUBMITTED'", descriptionVi: 'Trạng thái: DRAFT, SUBMITTED, LATE, GRADED', designOrigin: 'Image 25: Đã nộp bài & Đã chấm điểm', sampleValue: 'GRADED' },
      { name: 'submitted_file_name', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Tên file nén đã tải lên', designOrigin: 'Image 25: 21020088_TodoReactApp.zip', sampleValue: '21020088_TodoReactApp.zip' },
      { name: 'submitted_file_url', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Đường dẫn tệp lưu trữ bài làm', designOrigin: 'Storage link', sampleValue: '/submissions/21020088_TodoReactApp.zip' },
      { name: 'git_repo_url', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Đường link GitHub / GitLab của bài làm', designOrigin: 'Image 25: Đường dẫn GitHub / GitLab Repository', sampleValue: 'https://github.com/neu-student/auth-jwt-lab' },
      { name: 'student_note', type: 'TEXT', isNullable: true, descriptionVi: 'Ghi chú gửi cho giảng viên', designOrigin: 'Image 25: Em đã triển khai thêm kiểm thử tự động Jest cho middleware...', sampleValue: 'Em đã triển khai thêm kiểm thử tự động Jest cho middleware và lưu trữ Refresh Token trên Redis.' },
      { name: 'is_late', type: 'BOOLEAN', isNullable: false, defaultValue: 'false', descriptionVi: 'Nộp muộn sau deadline chính thức', designOrigin: 'Image 5: 2 SV trễ hạn', sampleValue: false },
      { name: 'hours_late', type: 'DECIMAL(6,2)', isNullable: false, defaultValue: '0.00', descriptionVi: 'Số giờ nộp trễ tính toán', designOrigin: 'Late penalty calculation', sampleValue: 0.0 },
      { name: 'submitted_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm sinh viên bấm nộp bài', designOrigin: 'Image 25: Thời gian nộp: 15/03/2025 21:30', sampleValue: '2024-09-04T21:30:00Z' }
    ]
  },

  // 19. assignment_evaluations
  {
    id: 'assignment_evaluations',
    name: 'assignment_evaluations',
    displayNameVi: 'Kết quả Chấm điểm & Nhận xét Giảng viên',
    domain: 'ASSIGNMENTS_GRADING',
    descriptionVi: 'Điểm số bài tập (9.5/10), khấu trừ điểm phạt trễ, nhận xét chi tiết của Giảng viên (TS. Trần Văn Minh / TS. Nguyễn Văn A).',
    designScreenRef: 'Image 25: Điểm số 9.5/10 & Nhận xét của Giảng viên viên TS. Trần Văn Minh; Image 5: Đã hoàn thành chấm',
    tags: ['Grades', 'Feedback', 'Assessment'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính đánh giá', designOrigin: 'Grade PK', sampleValue: 'eval_21020088_03' },
      { name: 'submission_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'assignment_submissions', column: 'id' }, isNullable: false, isUnique: true, descriptionVi: 'Bài nộp được chấm điểm', designOrigin: 'Submission link', sampleValue: 'sub_21020088_asg03' },
      { name: 'grader_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: false, descriptionVi: 'Giảng viên thực hiện chấm bài', designOrigin: 'Image 25: Nhận xét của Giảng viên (TS. Trần Văn Minh)', sampleValue: 'u_gv_tranvanminh' },
      { name: 'raw_score', type: 'DECIMAL(4,2)', isNullable: false, descriptionVi: 'Điểm thô trước khi trừ phạt', designOrigin: 'Grading calculation', sampleValue: 9.5 },
      { name: 'late_penalty_deduction', type: 'DECIMAL(4,2)', isNullable: false, defaultValue: '0.00', descriptionVi: 'Điểm bị trừ do nộp muộn', designOrigin: 'Late penalty application', sampleValue: 0.0 },
      { name: 'final_score', type: 'DECIMAL(4,2)', isNullable: false, descriptionVi: 'Điểm số chính thức công bố', designOrigin: 'Image 25: Điểm số 9.5 / 10', sampleValue: 9.5 },
      { name: 'instructor_feedback', type: 'TEXT', isNullable: false, descriptionVi: 'Lời nhận xét chi tiết của giảng viên', designOrigin: 'Image 25: Giao diện sạch đẹp, xử lý component state tối ưu tốt! Cấu trúc thư mục...', sampleValue: 'Giao diện sạch đẹp, xử lý component state tối ưu tốt! Cấu trúc thư mục hooks và components phân tách rõ ràng. Cần chú ý thêm việc làm sạch timer trong useEffect.' },
      { name: 'graded_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm hoàn tất chấm bài', designOrigin: 'Graded timestamp', sampleValue: '2024-09-06T14:20:00Z' }
    ]
  },

  // 20. question_banks
  {
    id: 'question_banks',
    name: 'question_banks',
    displayNameVi: 'Ngân hàng Câu hỏi Khảo thí & Tri thức AI',
    domain: 'QUESTION_BANK_AI',
    descriptionVi: 'Ngân hàng câu hỏi trắc nghiệm chuẩn hóa: Mã #Q-AI-8921, độ tin cậy 98.4%, trích dẫn RFC 7231, mức độ Bloom L3, trạng thái AI Draft / Đã duyệt.',
    designScreenRef: 'Image 15: Ngân hàng Câu hỏi & Trợ lý AI Khảo thí (M10.G2)',
    tags: ['Question Bank', 'AI Copilot', 'Bloom', 'RFC Standards'],
    columns: [
      { name: 'id', type: 'VARCHAR(50)', isPrimaryKey: true, isNullable: false, descriptionVi: 'Mã câu hỏi khảo thí (#Q-AI-8921, #Q-4081)', designOrigin: 'Image 15: Mã đề mục #Q-AI-8921 & #Q-4081', sampleValue: 'Q-AI-8921' },
      { name: 'course_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'courses', column: 'id' }, isNullable: false, descriptionVi: 'Môn học sở hữu câu hỏi', designOrigin: 'Image 15: INT3110 - Lập trình Web Nâng cao', sampleValue: 'INT3110' },
      { name: 'chapter_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'syllabus_chapters', column: 'id' }, isNullable: true, descriptionVi: 'Chương mục đề cương liên quan', designOrigin: 'Image 15: Chương 1: Kiến trúc RESTful API & HTTP Specs', sampleValue: 'chap_int3110_c1' },
      { name: 'bloom_level', type: 'VARCHAR(30)', isNullable: false, descriptionVi: 'Cấp độ Bloom: L1_REMEMBER, L2_UNDERSTAND, L3_APPLY, L4_ANALYZE', designOrigin: 'Image 15: Bloom: Vận dụng (L3) & Thông hiểu (L2)', sampleValue: 'L3_APPLY' },
      { name: 'topic_tag', type: 'VARCHAR(100)', isNullable: false, descriptionVi: 'Thẻ chủ đề chuyên môn', designOrigin: 'Image 15: #RESTful_API, #HTTP_Methods', sampleValue: '#RESTful_API' },
      { name: 'question_type', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'MCQ_SINGLE'", descriptionVi: 'Loại hình khảo thí: MCQ_SINGLE (4 phương án), MCQ_MULTI, TRUE_FALSE', designOrigin: 'Image 15: 4 Phương án (MCQ)', sampleValue: 'MCQ_SINGLE' },
      { name: 'question_stem', type: 'TEXT', isNullable: false, descriptionVi: 'Nội dung câu hỏi đề dẫn', designOrigin: 'Image 15: Khi tạo mới một tài nguyên (Resource) trong kiến trúc chuẩn RESTful API...', sampleValue: 'Khi tạo mới một tài nguyên (Resource) trong kiến trúc chuẩn RESTful API bằng phương thức HTTP POST, mã phản hồi trạng thái nào sau đây là chuẩn mực nhất kèm theo Header Location?' },
      { name: 'default_points', type: 'DECIMAL(4,2)', isNullable: false, defaultValue: '1.00', descriptionVi: 'Điểm khảo thí định mức', designOrigin: 'Image 15: Điểm khảo thí: 1.0 Điểm', sampleValue: 1.0 },
      { name: 'ai_generated', type: 'BOOLEAN', isNullable: false, defaultValue: 'true', descriptionVi: 'Được sinh tự động bởi EduLLM AI Engine', designOrigin: 'Image 15: Sinh bởi EduLLM • Vừa xong', sampleValue: true },
      { name: 'ai_confidence_score', type: 'DECIMAL(4,2)', isNullable: true, descriptionVi: 'Độ tin cậy của mô hình AI (%)', designOrigin: 'Image 15: Độ tin cậy: 98.4%', sampleValue: 98.4 },
      { name: 'rfc_reference', type: 'VARCHAR(100)', isNullable: true, descriptionVi: 'Quy chuẩn tiêu chuẩn quốc tế đối soát', designOrigin: 'Image 15: RFC 7231 • Sec 6.3.2', sampleValue: 'RFC 7231 • Sec 6.3.2' },
      { name: 'explanation_logic', type: 'TEXT', isNullable: false, descriptionVi: 'Giải trình Logic & Đối soát tri thức của AI', designOrigin: 'Image 15: Giải trình logic: Theo chuẩn quốc tế IETF RFC 7231 khi POST thành công...', sampleValue: 'Theo quy chuẩn quốc tế IETF RFC 7231, khi thao tác POST thành công tạo ra tài nguyên mới, server phải gửi 201 Created cùng Header Location.' },
      { name: 'status', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'AI_DRAFT'", descriptionVi: 'Trạng thái: AI_DRAFT (Chờ kiểm duyệt), APPROVED (Đã duyệt), REJECTED', designOrigin: 'Image 15: AI DRAFT • CHỜ KIỂM DUYỆT / ĐÃ DUYỆT (CHÍNH THỨC)', sampleValue: 'AI_DRAFT' },
      { name: 'approved_by_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Giảng viên ký số thẩm định câu hỏi', designOrigin: 'Image 15: Đã duyệt và ký số khảo thí bởi TS. Nguyễn Văn A', sampleValue: 'u_gv_0042' },
      { name: 'usage_in_exams_count', type: 'INTEGER', isNullable: false, defaultValue: '0', descriptionVi: 'Số lần xuất hiện trong các kỳ thi chính thức', designOrigin: 'Image 15: Xem lịch sử sử dụng trong đề thi (3 lần)', sampleValue: 0 }
    ]
  },

  // 21. question_options
  {
    id: 'question_options',
    name: 'question_options',
    displayNameVi: 'Phương án Lựa chọn Trắc nghiệm (MCQ)',
    domain: 'QUESTION_BANK_AI',
    descriptionVi: 'Các phương án A, B, C, D; cờ đáp án chuẩn (is_correct) và vai trò phân hóa (đáp án chuẩn vs phương án gây nhiễu).',
    designScreenRef: 'Image 15: Danh sách phương án A, B, C, D (ĐÁP ÁN CHUẨN, Phương án nhiễu)',
    tags: ['MCQ', 'Options', 'Distractors'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính phương án', designOrigin: 'Option PK', sampleValue: 'opt_q8921_b' },
      { name: 'question_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'question_banks', column: 'id' }, isNullable: false, descriptionVi: 'Câu hỏi sở hữu phương án', designOrigin: 'Question link', sampleValue: 'Q-AI-8921' },
      { name: 'option_letter', type: 'VARCHAR(5)', isNullable: false, descriptionVi: 'Ký tự phương án (A, B, C, D)', designOrigin: 'Image 15: A, B, C, D', sampleValue: 'B' },
      { name: 'option_text', type: 'TEXT', isNullable: false, descriptionVi: 'Nội dung văn bản phương án', designOrigin: 'Image 15: HTTP 201 Created (Kèm Header Location trỏ đến URI vừa khởi tạo)', sampleValue: 'HTTP 201 Created (Kèm Header Location trỏ đến URI vừa khởi tạo)' },
      { name: 'is_correct', type: 'BOOLEAN', isNullable: false, defaultValue: 'false', descriptionVi: 'Đánh dấu đáp án chuẩn xác', designOrigin: 'Image 15: ĐÁP ÁN CHUẨN (Option B)', sampleValue: true },
      { name: 'option_role', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'DISTRACTOR'", descriptionVi: 'Phân loại: CORRECT_ANSWER (Chuẩn), DISTRACTOR (Phương án nhiễu)', designOrigin: 'Image 15: ĐÁP ÁN CHUẨN / Phương án nhiễu', sampleValue: 'CORRECT_ANSWER' }
    ]
  },

  // 22. learning_telemetry_logs
  {
    id: 'learning_telemetry_logs',
    name: 'learning_telemetry_logs',
    displayNameVi: 'Nhật ký Giám sát Telemetry & Liêm chính Học thuật',
    domain: 'TELEMETRY_AUDIT',
    descriptionVi: 'Hệ thống tracking học tập thời gian thực: Video watch seconds (18:45 / 24:30), watermark SV-2024-8849, tốc độ mạng, mốc hoàn thành >80%.',
    designScreenRef: 'Image 21: REC Telemetry Live & Watermark ID: SV-2024-8849',
    tags: ['Telemetry', 'Proctoring', 'Integrity', 'Streaming'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính bản ghi telemetry', designOrigin: 'Telemetry PK', sampleValue: 'tel_session_01' },
      { name: 'student_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: false, descriptionVi: 'Sinh viên đang theo dõi học liệu', designOrigin: 'Image 21: SV-2024-8849', sampleValue: 'u_sv_21020088' },
      { name: 'material_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'learning_materials', column: 'id' }, isNullable: false, descriptionVi: 'Video / học liệu đang xem', designOrigin: 'Material link', sampleValue: 'mat_slide_w03' },
      { name: 'section_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_sections', column: 'id' }, isNullable: false, descriptionVi: 'Lớp học phần', designOrigin: 'Section link', sampleValue: 'INT3110_01' },
      { name: 'accumulated_seconds', type: 'INTEGER', isNullable: false, defaultValue: '1125', descriptionVi: 'Thời gian đã tích lũy thực tế (18 phút 45 giây = 1125s)', designOrigin: 'Image 21: Đã tích lũy: 18 phút (18:45 / 24:30)', sampleValue: 1125 },
      { name: 'total_video_seconds', type: 'INTEGER', isNullable: false, defaultValue: '1470', descriptionVi: 'Tổng thời lượng video bài giảng (24:30 = 1470s)', designOrigin: 'Image 21: 24:30', sampleValue: 1470 },
      { name: 'watermark_string', type: 'VARCHAR(150)', isNullable: false, descriptionVi: 'Chuỗi watermark động hiển thị trên khung hình', designOrigin: 'Image 21: Watermark ID: SV-2024-8849 • TS. NGUYỄN VĂN A LMS M10', sampleValue: 'SV-2024-8849 • TS. NGUYỄN VĂN A LMS M10' },
      { name: 'client_ip', type: 'VARCHAR(50)', isNullable: false, descriptionVi: 'Địa chỉ IP mạng của người học', designOrigin: 'Image 3 & 21: IP sinh viên', sampleValue: '118.70.182.45' },
      { name: 'network_speed_mbps', type: 'DECIMAL(6,2)', isNullable: false, defaultValue: '12.40', descriptionVi: 'Tốc độ băng thông mạng đo được', designOrigin: 'Image 21: Tốc độ mạng: 12.4 Mbps', sampleValue: 12.4 },
      { name: 'milestone_80_percent_reached', type: 'BOOLEAN', isNullable: false, defaultValue: 'false', descriptionVi: 'Đạt điều kiện kiểm tra tiến độ xem >80%', designOrigin: 'Image 9 & 21: Theo dõi tiến độ xem > 80%', sampleValue: false },
      { name: 'last_heartbeat_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm ping nhịp tim cuối cùng', designOrigin: 'Live heartbeat telemetry', sampleValue: '2024-10-26T18:45:00Z' }
    ]
  },

  // 23. material_course_links
  {
    id: 'material_course_links',
    name: 'material_course_links',
    displayNameVi: 'Liên kết Học liệu Dùng chung Liên môn',
    domain: 'LESSONS_MATERIALS',
    descriptionVi: 'Cho phép một học liệu trong kho dùng chung được liên kết với nhiều môn học/học phần, tránh tải lên trùng lặp dữ liệu.',
    designScreenRef: 'Mục 3.2: Quản lý kho học liệu dùng chung & liên kết nhiều môn học/học phần',
    tags: ['Shared Repo', 'Cross Course', 'Deduplication'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính liên kết', designOrigin: 'System PK', sampleValue: 'link_cs101_slide' },
      { name: 'material_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'learning_materials', column: 'id' }, isNullable: false, descriptionVi: 'Học liệu dùng chung được liên kết', designOrigin: 'Material FK', sampleValue: 'mat_slide_w03' },
      { name: 'course_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'courses', column: 'id' }, isNullable: false, descriptionVi: 'Môn học nhận liên kết học liệu', designOrigin: 'Course FK', sampleValue: 'CS101' },
      { name: 'section_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'course_sections', column: 'id' }, isNullable: true, descriptionVi: 'Lớp học phần cụ thể nhận liên kết', designOrigin: 'Section FK', sampleValue: 'CS101_01' },
      { name: 'linked_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm liên kết học liệu', designOrigin: 'Audit system', sampleValue: '2024-10-27T08:00:00Z' },
      { name: 'notes', type: 'VARCHAR(255)', isNullable: true, descriptionVi: 'Ghi chú mục đích sử dụng liên môn', designOrigin: 'Instructor notes', sampleValue: 'Dùng chung cho Chương 4 môn CS101' },
      { name: 'linked_by_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Giảng viên thực hiện thao tác liên kết', designOrigin: 'User FK', sampleValue: 'u_gv_0042' }
    ]
  },

  // 24. support_tickets
  {
    id: 'support_tickets',
    name: 'support_tickets',
    displayNameVi: 'Yêu cầu Hỗ trợ Người học & Khảo thí',
    domain: 'STUDENT_SUPPORT',
    descriptionVi: 'Phân hệ hỗ trợ người học: Tiếp nhận yêu cầu thắc mắc về bài giảng, học liệu, kỹ thuật, phúc khảo điểm và hướng dẫn học tập.',
    designScreenRef: 'Mục 1, 2, 9 & 10: Phân hệ hỗ trợ người học & Tiếp nhận yêu cầu',
    tags: ['Support', 'Helpdesk', 'Student Success', 'Tickets'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính phiếu hỗ trợ', designOrigin: 'Support PK', sampleValue: 'ticket_001' },
      { name: 'ticket_code', type: 'VARCHAR(50)', isNullable: false, isUnique: true, isIndexed: true, descriptionVi: 'Mã tra cứu phiếu hỗ trợ (SUP-2024-001)', designOrigin: 'Ticket Code', sampleValue: 'SUP-2024-001' },
      { name: 'student_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: false, descriptionVi: 'Sinh viên gửi yêu cầu hỗ trợ', designOrigin: 'Student FK', sampleValue: 'u_sv_21020001' },
      { name: 'course_id', type: 'VARCHAR(50)', isForeignKey: true, foreignKeyTarget: { table: 'courses', column: 'id' }, isNullable: true, descriptionVi: 'Môn học liên quan', designOrigin: 'Course FK', sampleValue: 'INT3110' },
      { name: 'category', type: 'VARCHAR(50)', isNullable: false, defaultValue: "'ACADEMIC_MATERIAL'", descriptionVi: 'Phân loại yêu cầu: ACADEMIC_MATERIAL, ASSIGNMENT_HELP, TECHNICAL_ISSUE, EXAM_REVIEW, GENERAL', designOrigin: 'Category', sampleValue: 'TECHNICAL_ISSUE' },
      { name: 'title', type: 'VARCHAR(255)', isNullable: false, descriptionVi: 'Tiêu đề vấn đề cần hỗ trợ', designOrigin: 'Support Title', sampleValue: 'Lỗi kết nối CSDL MySQL khi thực hành Lab 1.2 qua SQLAlchemy' },
      { name: 'content', type: 'TEXT', isNullable: false, descriptionVi: 'Nội dung chi tiết câu hỏi / mô tả lỗi', designOrigin: 'Support Content', sampleValue: 'Thưa thầy, em đã cấu hình chuỗi kết nối URI chuẩn theo mẫu...' },
      { name: 'status', type: 'VARCHAR(30)', isNullable: false, defaultValue: "'PENDING'", descriptionVi: 'Trạng thái: PENDING (Chờ xử lý), IN_PROGRESS (Đang giải quyết), RESOLVED (Đã giải đáp), CLOSED (Đóng)', designOrigin: 'Workflow Status', sampleValue: 'IN_PROGRESS' },
      { name: 'priority', type: 'VARCHAR(20)', isNullable: false, defaultValue: "'MEDIUM'", descriptionVi: 'Mức độ ưu tiên: LOW, MEDIUM, HIGH, URGENT', designOrigin: 'Priority', sampleValue: 'HIGH' },
      { name: 'assigned_staff_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Giảng viên hoặc cán bộ quản lý phụ trách', designOrigin: 'Staff FK', sampleValue: 'u_gv_0042' },
      { name: 'created_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm tạo yêu cầu', designOrigin: 'Audit system', sampleValue: '2024-10-27T08:00:00Z' },
      { name: 'updated_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm cập nhật cuối cùng', designOrigin: 'Audit system', sampleValue: '2024-10-27T10:30:00Z' }
    ]
  },

  // 25. ticket_messages
  {
    id: 'ticket_messages',
    name: 'ticket_messages',
    displayNameVi: 'Nhật ký Trao đổi & Trợ lý Chatbot AI',
    domain: 'STUDENT_SUPPORT',
    descriptionVi: 'Lưu trữ các lượt phản hồi giải đáp giữa Sinh viên, Giảng viên và Trợ lý AI EduLLM Copilot 24/7.',
    designScreenRef: 'Mục 9 & 10: Tích hợp chatbot AI hỗ trợ người học 24/7',
    tags: ['Chatbot AI', 'Messages', 'AI Tutor', 'Support'],
    columns: [
      { name: 'id', type: 'UUID', isPrimaryKey: true, isNullable: false, descriptionVi: 'Khóa chính tin nhắn', designOrigin: 'Message PK', sampleValue: 'msg_001_1' },
      { name: 'ticket_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'support_tickets', column: 'id' }, isNullable: false, descriptionVi: 'Phiếu hỗ trợ sở hữu tin nhắn', designOrigin: 'Ticket FK', sampleValue: 'ticket_001' },
      { name: 'sender_user_id', type: 'UUID', isForeignKey: true, foreignKeyTarget: { table: 'users', column: 'id' }, isNullable: true, descriptionVi: 'Người gửi (NULL nếu do Trợ lý AI trả lời)', designOrigin: 'Sender FK', sampleValue: 'u_sv_21020001' },
      { name: 'message', type: 'TEXT', isNullable: false, descriptionVi: 'Nội dung phản hồi hoặc câu trả lời', designOrigin: 'Message text', sampleValue: 'Lỗi 10061 thường xảy ra do cổng 3306 chưa mở...' },
      { name: 'is_ai_bot', type: 'BOOLEAN', isNullable: false, defaultValue: 'false', descriptionVi: 'Được sinh tự động bởi Trợ lý Chatbot AI LMS', designOrigin: 'AI Flag', sampleValue: true },
      { name: 'created_at', type: 'TIMESTAMP WITH TIME ZONE', isNullable: false, defaultValue: 'CURRENT_TIMESTAMP', descriptionVi: 'Thời điểm gửi tin nhắn', designOrigin: 'Timestamp', sampleValue: '2024-10-27T08:05:00Z' }
    ]
  }
];

export const DATABASE_RELATIONSHIPS: DatabaseRelationship[] = [
  { id: 'rel_mcl_mat', fromTable: 'material_course_links', fromColumn: 'material_id', toTable: 'learning_materials', toColumn: 'id', relationType: '1:N', descriptionVi: 'Một học liệu dùng chung được liên kết vào nhiều môn học' },
  { id: 'rel_mcl_course', fromTable: 'material_course_links', fromColumn: 'course_id', toTable: 'courses', toColumn: 'id', relationType: '1:N', descriptionVi: 'Môn học tiếp nhận liên kết học liệu' },
  { id: 'rel_support_student', fromTable: 'support_tickets', fromColumn: 'student_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Sinh viên tạo nhiều yêu cầu hỗ trợ' },
  { id: 'rel_support_staff', fromTable: 'support_tickets', fromColumn: 'assigned_staff_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Cán bộ / Giảng viên được phân công giải quyết ticket' },
  { id: 'rel_ticket_msg', fromTable: 'ticket_messages', fromColumn: 'ticket_id', toTable: 'support_tickets', toColumn: 'id', relationType: '1:N', descriptionVi: 'Mỗi ticket gồm nhiều tin nhắn trao đổi hoặc phản hồi từ AI' },
  { id: 'rel_dept_head', fromTable: 'departments', fromColumn: 'head_user_id', toTable: 'users', toColumn: 'id', relationType: '1:1', descriptionVi: 'Mỗi đơn vị khoa/bộ môn có một Trưởng bộ môn phụ trách' },
  { id: 'rel_admin_class_dept', fromTable: 'administrative_classes', fromColumn: 'department_id', toTable: 'departments', toColumn: 'id', relationType: '1:N', descriptionVi: 'Một khoa quản lý nhiều lớp chuyên ngành danh nghĩa (K65-CNTT1, CNTT2...)' },
  { id: 'rel_admin_class_advisor', fromTable: 'administrative_classes', fromColumn: 'advisor_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Giảng viên làm cố vấn học tập cho lớp chuyên ngành' },
  { id: 'rel_course_dept', fromTable: 'courses', fromColumn: 'department_id', toTable: 'departments', toColumn: 'id', relationType: '1:N', descriptionVi: 'Môn học thuộc thẩm quyền chuyên môn của một bộ môn' },
  { id: 'rel_syllabus_course', fromTable: 'course_syllabi', fromColumn: 'course_id', toTable: 'courses', toColumn: 'id', relationType: '1:N', descriptionVi: 'Một môn học có các phiên bản đề cương chi tiết (REV4)' },
  { id: 'rel_syllabus_approver', fromTable: 'course_syllabi', fromColumn: 'approved_by_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Cán bộ quản lý ký phê duyệt đề cương cấp Khoa' },
  { id: 'rel_chap_syllabus', fromTable: 'syllabus_chapters', fromColumn: 'syllabus_id', toTable: 'course_syllabi', toColumn: 'id', relationType: '1:N', descriptionVi: 'Đề cương gồm nhiều chương mục học thuật' },
  { id: 'rel_clo_course', fromTable: 'course_learning_outcomes', fromColumn: 'course_id', toTable: 'courses', toColumn: 'id', relationType: '1:N', descriptionVi: 'Môn học định nghĩa các chuẩn đầu ra CLO' },
  { id: 'rel_sec_course', fromTable: 'course_sections', fromColumn: 'course_id', toTable: 'courses', toColumn: 'id', relationType: '1:N', descriptionVi: 'Môn học mở thành nhiều lớp học phần theo học kỳ (INT3110_01, 02...)' },
  { id: 'rel_sec_syllabus', fromTable: 'course_sections', fromColumn: 'syllabus_id', toTable: 'course_syllabi', toColumn: 'id', relationType: '1:N', descriptionVi: 'Lớp học phần tuân thủ một đề cương chi tiết' },
  { id: 'rel_ins_sec', fromTable: 'section_instructors', fromColumn: 'section_id', toTable: 'course_sections', toColumn: 'id', relationType: '1:N', descriptionVi: 'Một lớp học phần có đội ngũ giảng viên phụ trách' },
  { id: 'rel_ins_user', fromTable: 'section_instructors', fromColumn: 'user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Giảng viên/TA được phân công vào lớp' },
  { id: 'rel_enr_sec', fromTable: 'section_enrollments', fromColumn: 'section_id', toTable: 'course_sections', toColumn: 'id', relationType: '1:N', descriptionVi: 'Lớp học phần chứa danh sách sinh viên ghi danh' },
  { id: 'rel_enr_user', fromTable: 'section_enrollments', fromColumn: 'student_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Sinh viên được ghi danh vào lớp học phần' },
  { id: 'rel_enr_admin_class', fromTable: 'section_enrollments', fromColumn: 'administrative_class_id', toTable: 'administrative_classes', toColumn: 'id', relationType: '1:N', descriptionVi: 'Sinh viên thuộc một lớp chuyên ngành' },
  { id: 'rel_week_sec', fromTable: 'section_weeks', fromColumn: 'section_id', toTable: 'course_sections', toColumn: 'id', relationType: '1:N', descriptionVi: 'Lớp học phần chia thành 15 tuần học' },
  { id: 'rel_lesson_chap', fromTable: 'lessons', fromColumn: 'chapter_id', toTable: 'syllabus_chapters', toColumn: 'id', relationType: '1:N', descriptionVi: 'Bài học thuộc một chương đề cương' },
  { id: 'rel_lesson_week', fromTable: 'lessons', fromColumn: 'section_week_id', toTable: 'section_weeks', toColumn: 'id', relationType: '1:N', descriptionVi: 'Bài học gắn vào tuần giảng dạy' },
  { id: 'rel_mat_sec', fromTable: 'learning_materials', fromColumn: 'section_id', toTable: 'course_sections', toColumn: 'id', relationType: '1:N', descriptionVi: 'Học liệu số gắn vào lớp học phần' },
  { id: 'rel_mat_week', fromTable: 'learning_materials', fromColumn: 'section_week_id', toTable: 'section_weeks', toColumn: 'id', relationType: '1:N', descriptionVi: 'Học liệu số gắn vào tuần cụ thể' },
  { id: 'rel_mat_lesson', fromTable: 'learning_materials', fromColumn: 'lesson_id', toTable: 'lessons', toColumn: 'id', relationType: '1:N', descriptionVi: 'Học liệu số hóa gắn trực tiếp vào bài học' },
  { id: 'rel_drm_mat', fromTable: 'drm_security_policies', fromColumn: 'material_id', toTable: 'learning_materials', toColumn: 'id', relationType: '1:1', descriptionVi: 'Mỗi học liệu có một cấu hình bản quyền DRM' },
  { id: 'rel_dossier_mat', fromTable: 'material_approval_dossiers', fromColumn: 'material_id', toTable: 'learning_materials', toColumn: 'id', relationType: '1:N', descriptionVi: 'Học liệu trải qua hồ sơ thẩm định 4 bước' },
  { id: 'rel_dossier_submitter', fromTable: 'material_approval_dossiers', fromColumn: 'submitter_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Giảng viên nộp hồ sơ thẩm định' },
  { id: 'rel_dossier_reviewer', fromTable: 'material_approval_dossiers', fromColumn: 'reviewer_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Cán bộ quản lý/thẩm định đánh giá hồ sơ' },
  { id: 'rel_asg_week', fromTable: 'assignments', fromColumn: 'section_week_id', toTable: 'section_weeks', toColumn: 'id', relationType: '1:N', descriptionVi: 'Đề bài Assignment gắn vào một tuần học cụ thể' },
  { id: 'rel_att_asg', fromTable: 'assignment_attachments', fromColumn: 'assignment_id', toTable: 'assignments', toColumn: 'id', relationType: '1:N', descriptionVi: 'Đề bài Assignment kèm nhiều tệp PDF/ZIP' },
  { id: 'rel_sub_asg', fromTable: 'assignment_submissions', fromColumn: 'assignment_id', toTable: 'assignments', toColumn: 'id', relationType: '1:N', descriptionVi: 'Sinh viên nộp bài làm cho Assignment' },
  { id: 'rel_sub_user', fromTable: 'assignment_submissions', fromColumn: 'student_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Sinh viên thực hiện nộp bài' },
  { id: 'rel_eval_sub', fromTable: 'assignment_evaluations', fromColumn: 'submission_id', toTable: 'assignment_submissions', toColumn: 'id', relationType: '1:1', descriptionVi: 'Mỗi bài nộp có một kết quả chấm điểm' },
  { id: 'rel_eval_grader', fromTable: 'assignment_evaluations', fromColumn: 'grader_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Giảng viên chấm và ghi lời phê' },
  { id: 'rel_q_course', fromTable: 'question_banks', fromColumn: 'course_id', toTable: 'courses', toColumn: 'id', relationType: '1:N', descriptionVi: 'Câu hỏi khảo thí thuộc ngân hàng môn học' },
  { id: 'rel_q_chap', fromTable: 'question_banks', fromColumn: 'chapter_id', toTable: 'syllabus_chapters', toColumn: 'id', relationType: '1:N', descriptionVi: 'Câu hỏi khảo thí thuộc chương học' },
  { id: 'rel_q_approver', fromTable: 'question_banks', fromColumn: 'approved_by_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Giảng viên ký số thẩm định câu hỏi' },
  { id: 'rel_opt_q', fromTable: 'question_options', fromColumn: 'question_id', toTable: 'question_banks', toColumn: 'id', relationType: '1:N', descriptionVi: 'Câu hỏi trắc nghiệm có các phương án lựa chọn A, B, C, D' },
  { id: 'rel_tel_user', fromTable: 'learning_telemetry_logs', fromColumn: 'student_user_id', toTable: 'users', toColumn: 'id', relationType: '1:N', descriptionVi: 'Ghi vết telemetry xem bài giảng của sinh viên' },
  { id: 'rel_tel_mat', fromTable: 'learning_telemetry_logs', fromColumn: 'material_id', toTable: 'learning_materials', toColumn: 'id', relationType: '1:N', descriptionVi: 'Ghi vết telemetry trên học liệu video số' },
  { id: 'rel_tel_sec', fromTable: 'learning_telemetry_logs', fromColumn: 'section_id', toTable: 'course_sections', toColumn: 'id', relationType: '1:N', descriptionVi: 'Telemetry gắn với lớp học phần đang diễn ra' }
];

export const DESIGN_SCREEN_MAPPINGS: DesignScreenMapping[] = [
  {
    screenId: 'screen_1',
    titleVi: 'Tạo Lớp học phần Mới (Form Cấu hình)',
    moduleCode: 'M10.CORE',
    imageAsset: '/assets/aistudio/Image_1_ffbc5128.png',
    descriptionVi: 'Khai báo thông tin học phần, cấu hình lịch giảng dạy (Thứ 5, Tiết 4-6), phòng học máy B3-202, chỉ tiêu 60 SV, phân công TS. Nguyễn Văn A & Trợ giảng TA.',
    linkedTables: ['course_sections', 'courses', 'course_syllabi', 'section_instructors', 'users'],
    keyAttributes: [
      { uiElement: 'Môn học / Học phần liên kết', table: 'courses', field: 'title_vi, credits, theory_hours', note: 'INT3110 - Lập trình Web Nâng cao (3 Tín chỉ - 45 Tiết)' },
      { uiElement: 'Mã lớp học phần', table: 'course_sections', field: 'section_code', note: 'INT3110_03 (Tự động tăng tiếp theo từ INT3110_01 và 02)' },
      { uiElement: 'Lịch giảng dạy & Địa điểm', table: 'course_sections', field: 'day_of_week, period_slot, physical_room', note: 'Thứ Năm hàng tuần • Tiết 4 - 6 • Phòng máy B3-202' },
      { uiElement: 'Đội ngũ Giảng dạy phân công', table: 'section_instructors', field: 'user_id, role_in_section', note: 'TS. Nguyễn Văn A [CHÍNH] & Trợ giảng [TA]' },
      { uiElement: 'Sĩ số & Quy tắc Đăng ký', table: 'course_sections', field: 'max_capacity, allow_self_enrollment', note: '60 Ghế, cho phép SV K65 tự đăng ký bổ sung' }
    ]
  },
  {
    screenId: 'screen_3',
    titleVi: 'Tải lên & Theo dõi Phê duyệt Học liệu Số',
    moduleCode: 'M10.G3',
    imageAsset: '/assets/aistudio/Image_3_0b8af870.png',
    descriptionVi: 'Quy trình kiểm duyệt học liệu mới 4 bước, cấu hình bản quyền DRM (chỉ xem trực tuyến, watermark động MSSV & IP), theo dõi SLA 28 giờ và phản hồi thẩm định.',
    linkedTables: ['learning_materials', 'drm_security_policies', 'material_approval_dossiers', 'users'],
    keyAttributes: [
      { uiElement: 'Tệp học liệu số gốc', table: 'learning_materials', field: 'title, file_size_bytes, material_type', note: 'Giao_trinh_Microservices_K65.pdf (18.4 MB)' },
      { uiElement: 'Cấu hình Bản quyền DRM', table: 'drm_security_policies', field: 'view_online_only, dynamic_watermark_enabled', note: 'Chỉ xem trực tuyến, tự động gắn Watermark MSSV & IP' },
      { uiElement: 'Tiến độ quy trình thẩm định 4 bước', table: 'material_approval_dossiers', field: 'current_step, status', note: 'Bước 3: Bộ môn thẩm định (ThS. Trần Thị Mai, PGS.TS. Lê Hoàng Sơn)' },
      { uiElement: 'Đồng bộ Kho Dùng Chung', table: 'learning_materials', field: 'is_shared_institutional_repo, institutional_code', note: 'Mã HL: HL-INT3110-2410 (420 SV đã truy cập)' }
    ]
  },
  {
    screenId: 'screen_5',
    titleVi: 'Quản trị Lớp học phần: 15 Tuần & Bài tập',
    moduleCode: 'M10.G1',
    imageAsset: '/assets/aistudio/Image_5_fa7ccc32.png',
    descriptionVi: 'Quản lý tiến độ giảng dạy theo tuần (Tuần 1 đến 15), các tệp Slide, Boilerplate, Video, và các bài tập Assignment theo tuần.',
    linkedTables: ['course_sections', 'section_weeks', 'learning_materials', 'assignments', 'assignment_submissions'],
    keyAttributes: [
      { uiElement: '15 Tuần Học kỳ 1', table: 'section_weeks', field: 'week_number, title, status', note: 'Tuần 1: Kiến trúc Web; Tuần 2: RESTful API; Tuần 3: Prisma & JWT' },
      { uiElement: 'Tài nguyên & Bài giảng', table: 'learning_materials', field: 'title, file_type, file_size_bytes', note: 'Slide_Tuan3_Prisma.pptx (11.6 MB), Docker_Compose.sql (4 KB)' },
      { uiElement: 'Assignment theo Tuần', table: 'assignments', field: 'title, deadline_time, max_score', note: 'Assignment 3: Xây dựng Module Auth JWT (Hạn chót 05/09/2024)' },
      { uiElement: 'Tỷ lệ nộp bài', table: 'assignment_submissions', field: 'is_late, submission_status', note: '94.8% Đã nộp (156 lượt đúng hạn, 4 trễ hạn, 2 chưa nộp)' }
    ]
  },
  {
    screenId: 'screen_7',
    titleVi: 'Danh sách Sinh viên & Lớp chuyên ngành',
    moduleCode: 'M10.G1',
    imageAsset: '/assets/aistudio/Image_7_29350fb2.png',
    descriptionVi: 'Bảng theo dõi 58 sinh viên lớp học phần, cơ cấu lớp chuyên ngành (K65-CNTT1, CNTT2, KTPM), tỷ lệ chuyên cần, cảnh báo vắng quá 20%.',
    linkedTables: ['section_enrollments', 'users', 'administrative_classes', 'course_sections'],
    keyAttributes: [
      { uiElement: 'Cơ cấu Lớp chuyên ngành', table: 'administrative_classes', field: 'class_code, total_students', note: 'K65-CNTT1 (24 SV), K65-CNTT2 (18 SV), K65-KTPM (16 SV)' },
      { uiElement: 'Hồ sơ Sinh viên', table: 'users', field: 'user_code, full_name, email', note: 'Email sinh viên được tạo theo dạng MSSV@st.neu.edu.vn' },
      { uiElement: 'Trạng thái học tập & Chuyên cần', table: 'section_enrollments', field: 'attendance_percentage, study_status', note: 'Tích cực (100%), Đang học (92%), Cảnh báo vắng (68% - vắng 2 buổi)' },
      { uiElement: 'Quy định điểm chuyên cần', table: 'section_enrollments', field: 'study_status', note: 'Vắng quá 20% tổng số tiết (tương đương 3 buổi) đình chỉ thi' }
    ]
  },
  {
    screenId: 'screen_9',
    titleVi: 'Đề cương chi tiết học phần & Chuẩn CDIO',
    moduleCode: 'M10.G1',
    imageAsset: '/assets/aistudio/Image_9_51f8ae91.png',
    descriptionVi: 'Cây chương mục học phần INT3110 (Chương 1 RESTful, Chương 2 JWT, Chương 3 Tối ưu DB), gắn chuẩn đầu ra CLO-1.2 & CLO-2.1 mức Bloom 3, học liệu số hóa.',
    linkedTables: ['course_syllabi', 'syllabus_chapters', 'lessons', 'course_learning_outcomes', 'learning_materials'],
    keyAttributes: [
      { uiElement: 'Đề cương chi tiết', table: 'course_syllabi', field: 'version_label, digitized_progress_percentage', note: 'Mã đề cương INT3110_REV4 (Đồng bộ 100% CDIO 2024)' },
      { uiElement: 'Cây chương mục', table: 'syllabus_chapters', field: 'chapter_order, title, allocated_periods', note: 'Chương 1: Kiến trúc Client-Server & RESTful (6 tiết, 3 bài học)' },
      { uiElement: 'Chuẩn đầu ra CLO', table: 'course_learning_outcomes', field: 'clo_code, target_bloom_level', note: 'CLO-1.2 & CLO-2.1 • Mức độ Bloom 3 (Vận dụng)' },
      { uiElement: 'Học liệu số gắn vào bài học', table: 'learning_materials', field: 'title, material_type', note: 'Slide_Bai1_REST_API.pdf, Video_ThucHanh_Flask.mp4, Swagger Demo' }
    ]
  },
  {
    screenId: 'screen_13',
    titleVi: 'Modal Thêm Sinh viên từ Lớp Chuyên ngành',
    moduleCode: 'M10.CORE',
    imageAsset: '/assets/aistudio/Image_13_063380a6.png',
    descriptionVi: 'Chọn sinh viên từ danh sách Lớp chuyên ngành (K65-CNTT1, CNTT2, KTPM, HTTT, KHMT) để thêm vào Lớp học phần INT3110_01.',
    linkedTables: ['administrative_classes', 'users', 'section_enrollments'],
    keyAttributes: [
      { uiElement: 'Lớp chuyên ngành K65-CNTT1', table: 'administrative_classes', field: 'class_code, total_students', note: 'Sĩ số 45, 21 SV còn lại, 24 SV đã có trong HP' },
      { uiElement: 'Danh sách sinh viên ứng viên', table: 'users', field: 'user_code, full_name', note: '21020145 Nguyễn Hải Đăng, 21020148 Trần Thị Mỹ Hạnh' },
      { uiElement: 'Xác nhận Thêm sinh viên', table: 'section_enrollments', field: 'section_id, student_user_id', note: 'Tạo bản ghi section_enrollments liên kết lớp học phần' }
    ]
  },
  {
    screenId: 'screen_15',
    titleVi: 'Ngân hàng Câu hỏi & Trợ lý AI Khảo thí EduLLM',
    moduleCode: 'M10.G2',
    imageAsset: '/assets/aistudio/Image_15_89bc1270.png',
    descriptionVi: 'Quản trị ngân hàng câu hỏi khảo thí theo thang Bloom, EduLLM Copilot sinh câu hỏi từ Slide/PDF, giải trình logic đối soát tiêu chuẩn quốc tế RFC 7231, chữ ký số thẩm định.',
    linkedTables: ['question_banks', 'question_options', 'course_learning_outcomes', 'users'],
    keyAttributes: [
      { uiElement: 'Mã câu hỏi khảo thí', table: 'question_banks', field: 'id, question_stem, default_points', note: '#Q-AI-8921 • Điểm khảo thí: 1.0 Điểm' },
      { uiElement: 'Thang Bloom & Chủ đề', table: 'question_banks', field: 'bloom_level, topic_tag', note: 'Bloom: Vận dụng (L3) • #RESTful_API' },
      { uiElement: 'Các phương án MCQ', table: 'question_options', field: 'option_letter, option_text, is_correct', note: 'A, B, C, D (Option B: HTTP 201 Created là ĐÁP ÁN CHUẨN)' },
      { uiElement: 'Giải trình Logic & Đối soát RFC', table: 'question_banks', field: 'rfc_reference, ai_confidence_score, explanation_logic', note: 'IETF RFC 7231 • Sec 6.3.2 • Độ tin cậy 98.4%' },
      { uiElement: 'Chữ ký số thẩm định', table: 'question_banks', field: 'approved_by_user_id, status', note: 'Đã duyệt và ký số bởi TS. Nguyễn Văn A' }
    ]
  },
  {
    screenId: 'screen_18',
    titleVi: 'Modal Tạo / Chỉnh sửa Đề Assignment theo Tuần',
    moduleCode: 'M10.G1',
    imageAsset: '/assets/aistudio/Image_18_3a1ffd79.html',
    descriptionVi: 'Form đầy đủ thiết lập đề bài: phân loại Lab/Group/Quiz, chọn Tuần (1-15), đặc tả yêu cầu, đính kèm đề PDF/ZIP, cấu hình nộp trễ (phạt 10%/ngày), thang điểm 10, trọng số 15%.',
    linkedTables: ['assignments', 'assignment_attachments', 'section_weeks'],
    keyAttributes: [
      { uiElement: 'Tuần học & Phân loại bài tập', table: 'assignments', field: 'section_week_id, assignment_type', note: 'Tuần 3: Cơ sở dữ liệu ORM & Auth JWT; Loại: Lab (Cá nhân)' },
      { uiElement: 'Tiêu đề & Hướng dẫn đặc tả', table: 'assignments', field: 'title, instructions_markdown', note: 'Assignment 3: Xây dựng Module Authentication JWT & Middleware Phân quyền' },
      { uiElement: 'Tài liệu & Bộ đề đính kèm', table: 'assignment_attachments', field: 'file_name, file_size_bytes', note: 'De_Bai_Assignment_03.pdf (1.8MB), starter-auth-boilerplate.zip (3.4MB)' },
      { uiElement: 'Mốc thời gian nộp bài', table: 'assignments', field: 'open_time, deadline_time, cutoff_hard_deadline', note: 'Mở: 29/08 08:00; Hạn chuẩn: 05/09 23:59; Khóa: 08/09 23:59' },
      { uiElement: 'Quy tắc nộp muộn & Trọng số', table: 'assignments', field: 'late_penalty_percent_per_day, max_score, course_weight_percentage', note: 'Trừ 10%/24h trễ, Thang điểm 10, Trọng số 15%' }
    ]
  },
  {
    screenId: 'screen_21',
    titleVi: 'Học tập Trực tuyến & Telemetry Giám sát Live',
    moduleCode: 'M10.S1',
    imageAsset: '/assets/aistudio/Image_21_9c05bfbf.png',
    descriptionVi: 'Giao diện sinh viên xem bài giảng video tích hợp telemetry live: Watermark động chống quay lén (SV-2024-8849), theo dõi tiến độ xem >80%, checklist mục tiêu CLO.',
    linkedTables: ['learning_telemetry_logs', 'lessons', 'learning_materials', 'users'],
    keyAttributes: [
      { uiElement: 'Telemetry Live & Watermark', table: 'learning_telemetry_logs', field: 'watermark_string, student_user_id', note: 'Watermark ID: SV-2024-8849 • TS. NGUYỄN VĂN A LMS M10' },
      { uiElement: 'Tiến độ xem lũy kế', table: 'learning_telemetry_logs', field: 'accumulated_seconds, total_video_seconds, network_speed_mbps', note: 'Đã tích lũy: 18 phút 45s / 24 phút 30s • Băng thông 12.4 Mbps' },
      { uiElement: 'Mục tiêu chuẩn đầu ra', table: 'lessons', field: 'learning_goals_json, code_snippet_content', note: 'List Slicing chuyên sâu, Comprehension, Enumerate, Benchmark' }
    ]
  },
  {
    screenId: 'screen_23',
    titleVi: 'Cổng Đăng nhập Học thuật & Khảo thí Trực tuyến',
    moduleCode: 'M10.CORE',
    imageAsset: '/assets/aistudio/Image_23_7d988090.jpeg',
    descriptionVi: 'Cổng SSO Đại học Kinh tế Quốc dân, hỗ trợ 3 phân hệ (Giảng viên & NCS, Sinh viên / Học viên, Cán bộ Khảo thí), xác thực 2FA SmartID OTP, chuẩn bảo mật ISO 27001.',
    linkedTables: ['users'],
    keyAttributes: [
      { uiElement: 'Tab phân quyền', table: 'users', field: 'role', note: 'LECTURER, STUDENT, ACADEMIC_ADMIN, EXAMINER' },
      { uiElement: 'Phương thức SSO NEU & 365', table: 'users', field: 'auth_provider', note: 'NEU Single Sign-On (SSO ĐHQG), Google Edu, Microsoft 365' },
      { uiElement: 'Xác thực 2 lớp SmartID', table: 'users', field: 'two_factor_smart_id_enabled', note: 'SmartID OTP xác thực trước kỳ khảo thí năng lực' }
    ]
  },
  {
    screenId: 'screen_25',
    titleVi: 'Sinh viên Nộp bài & Giảng viên Chấm điểm',
    moduleCode: 'M10.S1',
    imageAsset: '/assets/aistudio/Image_25_88d20e22.markdown',
    descriptionVi: 'Trang nộp bài của sinh viên: tải file zip, link GitHub repo, ghi chú; xem kết quả chấm điểm 9.5/10 và nhận xét chi tiết của Giảng viên.',
    linkedTables: ['assignment_submissions', 'assignment_evaluations', 'assignments', 'users'],
    keyAttributes: [
      { uiElement: 'Thông tin bài nộp', table: 'assignment_submissions', field: 'submitted_file_name, git_repo_url, student_note', note: '21020088_TodoReactApp.zip, GitHub URL, ghi chú Jest & Redis' },
      { uiElement: 'Kết quả chấm điểm', table: 'assignment_evaluations', field: 'final_score, instructor_feedback, grader_user_id', note: 'Điểm số: 9.5/10 • Lời phê TS. Trần Văn Minh: Giao diện sạch đẹp...' }
    ]
  }
];
