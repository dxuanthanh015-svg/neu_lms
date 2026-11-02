-- ====================================================================
-- HỆ THỐNG LMS / LCMS & KHO HỌC LIỆU SỐ (PHÂN HỆ M10)
-- Chuẩn CSDL MySQL 8.x: Ràng buộc Khóa Ngoại (Foreign Keys) & 30 Sinh viên
-- ====================================================================

CREATE DATABASE IF NOT EXISTS `lms_m10` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE `lms_m10`;

-- Tắt kiểm tra khóa ngoại tạm thời để tạo bảng
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS `notifications`;
DROP TABLE IF EXISTS `ticket_status_history`;
DROP TABLE IF EXISTS `ticket_attachments`;

-- 1. BẢNG USERS (Người dùng, Cán bộ, Giảng viên, Sinh viên)
DROP TABLE IF EXISTS `users`;
CREATE TABLE `users` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `user_code` VARCHAR(50) NOT NULL UNIQUE,
    `full_name` VARCHAR(150) NOT NULL,
    `email` VARCHAR(150) NOT NULL UNIQUE,
    `role` VARCHAR(30) NOT NULL,
    `administrative_class_id` VARCHAR(50) NULL,
    `academic_title` VARCHAR(50) NULL,
    `auth_provider` VARCHAR(30) NOT NULL DEFAULT 'NEU_SSO',
    `two_factor_smart_id_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `avatar_url` VARCHAR(255) NULL,
    `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_users_role` (`role`),
    INDEX `idx_users_code` (`user_code`),
    CONSTRAINT `ck_student_has_administrative_class`
        CHECK (`role` <> 'STUDENT' OR `administrative_class_id` IS NOT NULL)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 2. BẢNG DEPARTMENTS (Khoa / Viện & Bộ môn)
DROP TABLE IF EXISTS `departments`;
CREATE TABLE `departments` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `code` VARCHAR(30) NOT NULL UNIQUE,
    `name` VARCHAR(150) NOT NULL,
    `faculty_name` VARCHAR(150) NOT NULL,
    `head_user_id` VARCHAR(50) NULL,
    CONSTRAINT `fk_dept_head` FOREIGN KEY (`head_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 3. BẢNG ADMINISTRATIVE_CLASSES (Lớp chuyên ngành)
DROP TABLE IF EXISTS `administrative_classes`;
CREATE TABLE `administrative_classes` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `class_code` VARCHAR(50) NOT NULL UNIQUE,
    `department_id` VARCHAR(50) NOT NULL,
    `program_name` VARCHAR(150) NOT NULL,
    `cohort` VARCHAR(20) NOT NULL,
    `total_students` INT NOT NULL DEFAULT 45,
    `advisor_user_id` VARCHAR(50) NULL,
    CONSTRAINT `fk_admin_class_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_admin_class_advisor` FOREIGN KEY (`advisor_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

ALTER TABLE `users`
    ADD CONSTRAINT `fk_user_administrative_class`
    FOREIGN KEY (`administrative_class_id`) REFERENCES `administrative_classes` (`id`) ON DELETE RESTRICT;

-- 4. BẢNG COURSES (Môn học gốc)
DROP TABLE IF EXISTS `courses`;
CREATE TABLE `courses` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `course_code` VARCHAR(30) NOT NULL UNIQUE,
    `title_vi` VARCHAR(200) NOT NULL,
    `title_en` VARCHAR(200) NULL,
    `credits` INT NOT NULL DEFAULT 3,
    `theory_hours` INT NOT NULL DEFAULT 30,
    `practical_hours` INT NOT NULL DEFAULT 15,
    `department_id` VARCHAR(50) NOT NULL,
    `cdio_standard` VARCHAR(50) NOT NULL DEFAULT 'CDIO 2024',
    `created_by_user_id` VARCHAR(50) NULL,
    `created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_course_dept` FOREIGN KEY (`department_id`) REFERENCES `departments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_course_creator` FOREIGN KEY (`created_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `course_materials` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `course_id` VARCHAR(50) NOT NULL,
    `uploaded_by_user_id` VARCHAR(50) NULL,
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_url` VARCHAR(255) NOT NULL,
    `file_size_bytes` BIGINT NOT NULL,
    `file_type` VARCHAR(30) NOT NULL,
    `publication_status` VARCHAR(30) NOT NULL DEFAULT 'PENDING_REVIEW',
    `reviewed_by_user_id` VARCHAR(50) NULL,
    `review_comment` TEXT NULL,
    `reviewed_at` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY `ix_course_materials_course_id` (`course_id`),
    CONSTRAINT `fk_course_material_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_course_material_uploader` FOREIGN KEY (`uploaded_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_course_material_reviewer` FOREIGN KEY (`reviewed_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 5. BẢNG COURSE_SYLLABI (Đề cương chi tiết học phần)
DROP TABLE IF EXISTS `course_syllabi`;
CREATE TABLE `course_syllabi` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `course_id` VARCHAR(50) NOT NULL,
    `version_label` VARCHAR(50) NOT NULL,
    `academic_year` VARCHAR(50) NOT NULL,
    `semester` VARCHAR(50) NOT NULL,
    `approval_status` VARCHAR(50) NOT NULL DEFAULT 'APPROVED_FACULTY',
    `digitized_progress_percentage` INT NOT NULL DEFAULT 78,
    `approved_by_user_id` VARCHAR(50) NULL,
    CONSTRAINT `fk_syllabus_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_syllabus_approver` FOREIGN KEY (`approved_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 6. BẢNG SYLLABUS_CHAPTERS (Cây chương mục)
DROP TABLE IF EXISTS `syllabus_chapters`;
CREATE TABLE `syllabus_chapters` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `syllabus_id` VARCHAR(50) NOT NULL,
    `chapter_order` INT NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `total_lessons_count` INT NOT NULL DEFAULT 3,
    `allocated_periods` INT NOT NULL DEFAULT 6,
    `completion_metric` VARCHAR(50) NOT NULL DEFAULT '2/3 Đạt',
    CONSTRAINT `fk_chapter_syllabus` FOREIGN KEY (`syllabus_id`) REFERENCES `course_syllabi` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 7. BẢNG COURSE_LEARNING_OUTCOMES (Chuẩn đầu ra CLO & Bloom)
DROP TABLE IF EXISTS `course_learning_outcomes`;
CREATE TABLE `course_learning_outcomes` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `course_id` VARCHAR(50) NOT NULL,
    `clo_code` VARCHAR(30) NOT NULL,
    `target_bloom_level` VARCHAR(30) NOT NULL,
    `description` TEXT NOT NULL,
    CONSTRAINT `fk_clo_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 8. BẢNG COURSE_SECTIONS (Lớp học phần thực tế)
DROP TABLE IF EXISTS `course_sections`;
CREATE TABLE `course_sections` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `section_code` VARCHAR(50) NOT NULL UNIQUE,
    `course_id` VARCHAR(50) NOT NULL,
    `syllabus_id` VARCHAR(50) NOT NULL,
    `academic_year` VARCHAR(50) NOT NULL,
    `semester` VARCHAR(50) NOT NULL,
    `display_name` VARCHAR(255) NOT NULL,
    `max_capacity` INT NOT NULL DEFAULT 60,
    `current_enrollment_count` INT NOT NULL DEFAULT 58,
    `day_of_week` VARCHAR(50) NOT NULL,
    `period_slot` VARCHAR(100) NOT NULL,
    `instruction_mode` VARCHAR(30) NOT NULL DEFAULT 'IN_PERSON',
    `physical_room` VARCHAR(100) NOT NULL,
    `virtual_meeting_url` VARCHAR(255) NULL,
    `allow_self_enrollment` BOOLEAN NOT NULL DEFAULT TRUE,
    `current_week_index` INT NOT NULL DEFAULT 3,
    `status` VARCHAR(30) NOT NULL DEFAULT 'ACTIVE_IN_PROGRESS',
    `created_at` DATETIME NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sec_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sec_syllabus` FOREIGN KEY (`syllabus_id`) REFERENCES `course_syllabi` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 9. BẢNG SECTION_INSTRUCTORS (Phân công Giảng viên / TA)
DROP TABLE IF EXISTS `section_instructors`;
CREATE TABLE `section_instructors` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `section_id` VARCHAR(50) NOT NULL,
    `user_id` VARCHAR(50) NOT NULL,
    `role_in_section` VARCHAR(30) NOT NULL DEFAULT 'PRIMARY_LECTURER',
    `can_grade` BOOLEAN NOT NULL DEFAULT TRUE,
    `can_take_attendance` BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT `fk_ins_section` FOREIGN KEY (`section_id`) REFERENCES `course_sections` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ins_user` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 10. BẢNG SECTION_ENROLLMENTS (Ghi danh Sinh viên & Điểm danh)
DROP TABLE IF EXISTS `section_enrollments`;
CREATE TABLE `section_enrollments` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `section_id` VARCHAR(50) NOT NULL,
    `student_user_id` VARCHAR(50) NOT NULL,
    `administrative_class_id` VARCHAR(50) NOT NULL,
    `lab_group` VARCHAR(50) NULL,
    `attendance_percentage` INT NOT NULL DEFAULT 100,
    `consecutive_absences` INT NOT NULL DEFAULT 0,
    `study_status` VARCHAR(30) NOT NULL DEFAULT 'ACTIVE',
    `tuition_cleared` BOOLEAN NOT NULL DEFAULT TRUE,
    `enrolled_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_enr_sec` FOREIGN KEY (`section_id`) REFERENCES `course_sections` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_enr_student` FOREIGN KEY (`student_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_enr_class` FOREIGN KEY (`administrative_class_id`) REFERENCES `administrative_classes` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 11. BẢNG SECTION_WEEKS (Lộ trình 15 tuần giảng dạy)
DROP TABLE IF EXISTS `section_weeks`;
CREATE TABLE `section_weeks` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `section_id` VARCHAR(50) NOT NULL,
    `week_number` INT NOT NULL,
    `start_date` DATE NULL,
    `end_date` DATE NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'UPCOMING',
    `materials_count` INT NOT NULL DEFAULT 0,
    `assignments_count` INT NOT NULL DEFAULT 0,
    CONSTRAINT `fk_week_section` FOREIGN KEY (`section_id`) REFERENCES `course_sections` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 12. BẢNG LESSONS (Bài học chi tiết)
DROP TABLE IF EXISTS `lessons`;
CREATE TABLE `lessons` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `chapter_id` VARCHAR(50) NULL,
    `section_week_id` VARCHAR(50) NULL,
    `lesson_number` VARCHAR(20) NOT NULL,
    `title` VARCHAR(255) NOT NULL,
    `lesson_type` VARCHAR(30) NOT NULL DEFAULT 'PRACTICE_LAB',
    `duration_minutes` INT NOT NULL DEFAULT 25,
    `code_snippet_content` TEXT NULL,
    `learning_goals_json` TEXT NULL,
    CONSTRAINT `fk_lesson_chap` FOREIGN KEY (`chapter_id`) REFERENCES `syllabus_chapters` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_lesson_week` FOREIGN KEY (`section_week_id`) REFERENCES `section_weeks` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 13. BẢNG LEARNING_MATERIALS (Tệp học liệu số & tài nguyên)
DROP TABLE IF EXISTS `learning_materials`;
CREATE TABLE `learning_materials` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `section_id` VARCHAR(50) NOT NULL,
    `section_week_id` VARCHAR(50) NULL,
    `lesson_id` VARCHAR(50) NULL,
    `title` VARCHAR(255) NOT NULL,
    `material_type` VARCHAR(50) NOT NULL,
    `file_url` VARCHAR(255) NULL,
    `file_size_bytes` BIGINT NULL,
    `version_tag` VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    `is_shared_institutional_repo` BOOLEAN NOT NULL DEFAULT FALSE,
    `institutional_code` VARCHAR(50) NULL,
    `author_name` VARCHAR(150) NULL DEFAULT 'Ban Giảng Huấn CNTT',
    `source_origin` VARCHAR(255) NULL DEFAULT 'Đại học Kinh tế Quốc dân',
    `license_type` VARCHAR(50) NOT NULL DEFAULT 'CC_BY_NC_SA',
    `publication_status` VARCHAR(30) NOT NULL DEFAULT 'PUBLISHED',
    `summary_desc` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_mat_sec` FOREIGN KEY (`section_id`) REFERENCES `course_sections` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mat_week` FOREIGN KEY (`section_week_id`) REFERENCES `section_weeks` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_mat_lesson` FOREIGN KEY (`lesson_id`) REFERENCES `lessons` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 14. BẢNG DRM_SECURITY_POLICIES (Bản quyền DRM)
DROP TABLE IF EXISTS `drm_security_policies`;
CREATE TABLE `drm_security_policies` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `material_id` VARCHAR(50) NOT NULL UNIQUE,
    `view_online_only` BOOLEAN NOT NULL DEFAULT TRUE,
    `dynamic_watermark_enabled` BOOLEAN NOT NULL DEFAULT TRUE,
    `allow_offline_encrypted_study` BOOLEAN NOT NULL DEFAULT FALSE,
    `author_digital_signature` VARCHAR(255) NULL,
    `signed_at` DATETIME NULL,
    CONSTRAINT `fk_drm_material` FOREIGN KEY (`material_id`) REFERENCES `learning_materials` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 15. BẢNG MATERIAL_APPROVAL_DOSSIERS (Hồ sơ thẩm định 4 bước)
DROP TABLE IF EXISTS `material_approval_dossiers`;
CREATE TABLE `material_approval_dossiers` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `material_id` VARCHAR(50) NOT NULL,
    `submitter_user_id` VARCHAR(50) NOT NULL,
    `current_step` INT NOT NULL DEFAULT 3,
    `status` VARCHAR(50) NOT NULL DEFAULT 'PENDING_DEPARTMENT',
    `reviewer_user_id` VARCHAR(50) NULL,
    `reviewer_comment` TEXT NULL,
    `sla_deadline_hours` INT NOT NULL DEFAULT 28,
    `sla_remaining_hours` INT NOT NULL DEFAULT 16,
    `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_dossier_material` FOREIGN KEY (`material_id`) REFERENCES `learning_materials` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_dossier_submitter` FOREIGN KEY (`submitter_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_dossier_reviewer` FOREIGN KEY (`reviewer_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 16. BẢNG ASSIGNMENTS (Bài tập tuần)
DROP TABLE IF EXISTS `assignments`;
CREATE TABLE `assignments` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `section_week_id` VARCHAR(50) NOT NULL,
    `assignment_type` VARCHAR(30) NOT NULL DEFAULT 'LAB_INDIVIDUAL',
    `title` VARCHAR(255) NOT NULL,
    `instructions_markdown` TEXT NOT NULL,
    `open_time` DATETIME NOT NULL,
    `deadline_time` DATETIME NOT NULL,
    `cutoff_hard_deadline` DATETIME NOT NULL,
    `allow_late_submission` BOOLEAN NOT NULL DEFAULT TRUE,
    `late_penalty_percent_per_day` INT NOT NULL DEFAULT 10,
    `auto_remind_setting` VARCHAR(30) NOT NULL DEFAULT '24_6',
    `max_score` DECIMAL(4, 2) NOT NULL DEFAULT 10.00,
    `course_weight_percentage` DECIMAL(4, 2) NOT NULL DEFAULT 15.00,
    `allowed_submission_formats` TEXT NOT NULL,
    `version_label` VARCHAR(20) NOT NULL DEFAULT 'v2.1',
    CONSTRAINT `fk_asg_week` FOREIGN KEY (`section_week_id`) REFERENCES `section_weeks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 17. BẢNG ASSIGNMENT_ATTACHMENTS (Tệp đính kèm bài tập)
DROP TABLE IF EXISTS `assignment_attachments`;
CREATE TABLE `assignment_attachments` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `assignment_id` VARCHAR(50) NOT NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_size_bytes` BIGINT NOT NULL,
    `file_type` VARCHAR(30) NOT NULL,
    `download_url` VARCHAR(255) NOT NULL,
    CONSTRAINT `fk_att_assignment` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 18. BẢNG ASSIGNMENT_SUBMISSIONS (Bài nộp sinh viên)
DROP TABLE IF EXISTS `assignment_submissions`;
CREATE TABLE `assignment_submissions` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `assignment_id` VARCHAR(50) NOT NULL,
    `student_user_id` VARCHAR(50) NOT NULL,
    `submission_status` VARCHAR(30) NOT NULL DEFAULT 'SUBMITTED',
    `submitted_file_name` VARCHAR(255) NULL,
    `submitted_file_url` VARCHAR(255) NULL,
    `git_repo_url` VARCHAR(255) NULL,
    `student_note` TEXT NULL,
    `is_late` BOOLEAN NOT NULL DEFAULT FALSE,
    `hours_late` DECIMAL(6, 2) NOT NULL DEFAULT 0.00,
    `submitted_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_sub_asg` FOREIGN KEY (`assignment_id`) REFERENCES `assignments` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_sub_student` FOREIGN KEY (`student_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `assignment_submission_attachments` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `submission_id` VARCHAR(50) NOT NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_size_bytes` BIGINT NOT NULL,
    `file_type` VARCHAR(30) NOT NULL,
    `file_url` VARCHAR(255) NOT NULL,
    CONSTRAINT `fk_sub_file_submission` FOREIGN KEY (`submission_id`) REFERENCES `assignment_submissions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 19. BẢNG ASSIGNMENT_EVALUATIONS (Kết quả chấm điểm)
DROP TABLE IF EXISTS `assignment_evaluations`;
CREATE TABLE `assignment_evaluations` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `submission_id` VARCHAR(50) NOT NULL UNIQUE,
    `grader_user_id` VARCHAR(50) NOT NULL,
    `raw_score` DECIMAL(4, 2) NOT NULL,
    `late_penalty_deduction` DECIMAL(4, 2) NOT NULL DEFAULT 0.00,
    `final_score` DECIMAL(4, 2) NOT NULL,
    `instructor_feedback` TEXT NOT NULL,
    `graded_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_eval_submission` FOREIGN KEY (`submission_id`) REFERENCES `assignment_submissions` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_eval_grader` FOREIGN KEY (`grader_user_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 20. BẢNG QUESTION_BANKS (Ngân hàng câu hỏi trắc nghiệm & AI)
DROP TABLE IF EXISTS `question_banks`;
CREATE TABLE `question_banks` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `course_id` VARCHAR(50) NOT NULL,
    `chapter_id` VARCHAR(50) NULL,
    `bloom_level` VARCHAR(30) NOT NULL,
    `topic_tag` VARCHAR(100) NOT NULL,
    `question_type` VARCHAR(30) NOT NULL DEFAULT 'MCQ_SINGLE',
    `question_stem` TEXT NOT NULL,
    `default_points` DECIMAL(4, 2) NOT NULL DEFAULT 1.00,
    `ai_generated` BOOLEAN NOT NULL DEFAULT TRUE,
    `ai_confidence_score` DECIMAL(4, 2) NULL,
    `rfc_reference` VARCHAR(100) NULL,
    `explanation_logic` TEXT NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'AI_DRAFT',
    `approved_by_user_id` VARCHAR(50) NULL,
    `usage_in_exams_count` INT NOT NULL DEFAULT 0,
    CONSTRAINT `fk_q_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_q_chapter` FOREIGN KEY (`chapter_id`) REFERENCES `syllabus_chapters` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_q_approver` FOREIGN KEY (`approved_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 21. BẢNG QUESTION_OPTIONS (Phương án trắc nghiệm A, B, C, D)
DROP TABLE IF EXISTS `question_options`;
CREATE TABLE `question_options` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `question_id` VARCHAR(50) NOT NULL,
    `option_letter` VARCHAR(5) NOT NULL,
    `option_text` TEXT NOT NULL,
    `is_correct` BOOLEAN NOT NULL DEFAULT FALSE,
    `option_role` VARCHAR(30) NOT NULL DEFAULT 'DISTRACTOR',
    CONSTRAINT `fk_opt_question` FOREIGN KEY (`question_id`) REFERENCES `question_banks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 22. BẢNG LEARNING_TELEMETRY_LOGS (Nhật ký giám sát Telemetry)
DROP TABLE IF EXISTS `learning_telemetry_logs`;
CREATE TABLE `learning_telemetry_logs` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `student_user_id` VARCHAR(50) NOT NULL,
    `material_id` VARCHAR(50) NOT NULL,
    `section_id` VARCHAR(50) NOT NULL,
    `accumulated_seconds` INT NOT NULL DEFAULT 1125,
    `total_video_seconds` INT NOT NULL DEFAULT 1470,
    `watermark_string` VARCHAR(150) NOT NULL,
    `client_ip` VARCHAR(50) NOT NULL,
    `network_speed_mbps` DECIMAL(6, 2) NOT NULL DEFAULT 12.40,
    `milestone_80_percent_reached` BOOLEAN NOT NULL DEFAULT FALSE,
    `last_heartbeat_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_tel_student` FOREIGN KEY (`student_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tel_material` FOREIGN KEY (`material_id`) REFERENCES `learning_materials` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tel_section` FOREIGN KEY (`section_id`) REFERENCES `course_sections` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 23. BẢNG MATERIAL_COURSE_LINKS (Liên kết học liệu dùng chung liên môn học/học phần)
DROP TABLE IF EXISTS `material_course_links`;
CREATE TABLE `material_course_links` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `material_id` VARCHAR(50) NOT NULL,
    `course_id` VARCHAR(50) NOT NULL,
    `section_id` VARCHAR(50) NULL,
    `linked_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `notes` VARCHAR(255) NULL,
    `linked_by_user_id` VARCHAR(50) NULL,
    CONSTRAINT `fk_mcl_mat` FOREIGN KEY (`material_id`) REFERENCES `learning_materials` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mcl_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mcl_section` FOREIGN KEY (`section_id`) REFERENCES `course_sections` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_mcl_user` FOREIGN KEY (`linked_by_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 24. BẢNG SUPPORT_TICKETS (Phân hệ hỗ trợ người học)
DROP TABLE IF EXISTS `support_tickets`;
CREATE TABLE `support_tickets` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `ticket_code` VARCHAR(50) NOT NULL UNIQUE,
    `student_user_id` VARCHAR(50) NOT NULL,
    `course_id` VARCHAR(50) NULL,
    `category` VARCHAR(50) NOT NULL DEFAULT 'ACADEMIC_MATERIAL',
    `recipient_role` VARCHAR(30) NULL,
    `title` VARCHAR(255) NOT NULL,
    `content` TEXT NOT NULL,
    `status` VARCHAR(30) NOT NULL DEFAULT 'NEW',
    `priority` VARCHAR(20) NOT NULL DEFAULT 'MEDIUM',
    `assigned_staff_user_id` VARCHAR(50) NULL,
    `is_sensitive` BOOLEAN NOT NULL DEFAULT FALSE,
    `sla_hours` INT NULL,
    `sla_due_at` DATETIME NULL,
    `accepted_at` DATETIME NULL,
    `resolved_at` DATETIME NULL,
    `closed_at` DATETIME NULL,
    `resolution` TEXT NULL,
    `reopen_reason` TEXT NULL,
    `satisfaction_speed` INT NULL,
    `satisfaction_attitude` INT NULL,
    `satisfaction_comment` TEXT NULL,
    `rated_at` DATETIME NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT `fk_ticket_student` FOREIGN KEY (`student_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ticket_course` FOREIGN KEY (`course_id`) REFERENCES `courses` (`id`) ON DELETE SET NULL,
    CONSTRAINT `fk_ticket_staff` FOREIGN KEY (`assigned_staff_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 25. BẢNG TICKET_MESSAGES (Hộp thư & Trợ lý Chatbot AI giải đáp)
DROP TABLE IF EXISTS `ticket_messages`;
CREATE TABLE `ticket_messages` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `ticket_id` VARCHAR(50) NOT NULL,
    `sender_user_id` VARCHAR(50) NULL,
    `message` TEXT NOT NULL,
    `is_ai_bot` BOOLEAN NOT NULL DEFAULT FALSE,
    `is_internal` BOOLEAN NOT NULL DEFAULT FALSE,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT `fk_msg_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `support_tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_msg_sender` FOREIGN KEY (`sender_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 26. BẢNG TICKET_ATTACHMENTS (Tệp đính kèm yêu cầu/trao đổi)
CREATE TABLE `ticket_attachments` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `ticket_id` VARCHAR(50) NOT NULL,
    `message_id` VARCHAR(50) NOT NULL,
    `uploader_user_id` VARCHAR(50) NULL,
    `file_name` VARCHAR(255) NOT NULL,
    `file_url` VARCHAR(500) NOT NULL,
    `file_size_bytes` BIGINT NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY `ix_ticket_attachments_ticket_id` (`ticket_id`),
    CONSTRAINT `fk_ticket_attachment_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `support_tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ticket_attachment_message` FOREIGN KEY (`message_id`) REFERENCES `ticket_messages` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ticket_attachment_uploader` FOREIGN KEY (`uploader_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 27. BẢNG TICKET_STATUS_HISTORY (Lịch sử trạng thái)
CREATE TABLE `ticket_status_history` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `ticket_id` VARCHAR(50) NOT NULL,
    `actor_user_id` VARCHAR(50) NULL,
    `from_status` VARCHAR(30) NULL,
    `to_status` VARCHAR(30) NOT NULL,
    `note` TEXT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    KEY `ix_ticket_status_history_ticket_id` (`ticket_id`),
    CONSTRAINT `fk_ticket_history_ticket` FOREIGN KEY (`ticket_id`) REFERENCES `support_tickets` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_ticket_history_actor` FOREIGN KEY (`actor_user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 28. BẢNG NOTIFICATIONS (Thông báo tại chuông cá nhân)
CREATE TABLE `notifications` (
    `id` VARCHAR(50) NOT NULL PRIMARY KEY,
    `recipient_user_id` VARCHAR(50) NOT NULL,
    `notification_type` VARCHAR(40) NOT NULL,
    `title` VARCHAR(180) NOT NULL,
    `message` TEXT NOT NULL,
    `target_url` VARCHAR(500) NOT NULL,
    `reference_id` VARCHAR(100) NOT NULL,
    `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `read_at` DATETIME NULL,
    UNIQUE KEY `uq_notification_recipient_event` (`recipient_user_id`, `notification_type`, `reference_id`),
    KEY `ix_notifications_recipient_created` (`recipient_user_id`, `created_at`),
    CONSTRAINT `fk_notification_recipient` FOREIGN KEY (`recipient_user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

SET FOREIGN_KEY_CHECKS = 1;

-- ====================================================================
-- Không nạp dữ liệu mẫu. CSDL chỉ có cấu trúc bảng; dữ liệu được tạo từ nguồn thật.
