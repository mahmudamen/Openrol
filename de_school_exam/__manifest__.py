# -*- coding: utf-8 -*-
{
    'name': "Openrol - Exams",

    'summary': """
    All-in-One Exam Management Solution
        """,
    'description': """
Openrol - Exam Management App
================================
Features:
 - 1. Exam Types (e.g., Mid-Term, Final Term, etc.): Differentiate assessments based on exam types such as mid-term,  -final term, quizzes, or practicals to align with your academic calendar and assessment structure.
 - 2. Exam Grading Management: Streamline the grading process with automated systems, customizable rubrics, and flexible grading scales, ensuring accuracy and consistency in assessment evaluation.
 - 3. Exam Session: Organize exams into sessions, enabling efficient scheduling, administration, and monitoring of exam periods.
 - 4. Subject-Wise Exam Schedules: Create subject-specific exam schedules to provide clarity and guidance to students and instructors regarding exam dates and times.
 - 5. Result Compilation & Management: Collect and manage exam results systematically, facilitating easy access, analysis, and reporting for academic assessment purposes.
 - 6. Marksheet Grading: Assign grades to students' mark sheets based on their performance in exams, ensuring transparent and fair assessment outcomes.
 - 7. Generate Bulk Marksheet: Simplify result processing by generating mark sheets in bulk, saving time and effort for educators and administrators.
 - 8. Student Attendance in Exams: Track and manage student attendance during exams to ensure exam integrity, accountability, and compliance with attendance policies.
 - 9. Slips for Examination Hall: Issue examination slips to students, providing essential details like exam venue, date, and time for smooth and organized exam logistics.
 - 10. Print Examination Slips: Generate printable slips containing essential exam details for students' convenience and smooth access to examination halls.
 - 11. Print Result Cards: Create printable result cards summarizing students' exam performance, grades, and academic progress for record-keeping and communication purposes.
 - 12. Print Mark Sheets: Generate printable mark sheets with detailed exam results and grades, facilitating easy distribution and access for students and academic personnel.

    """,
    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",
    'live_test_url': 'https://youtu.be/dCpbMEO6EmY',
    'category': 'School/Industries',
    'version': '17.0.0.1',
    'depends': ['de_school'],
    'data': [
        'security/exam_security.xml',
        'security/ir.model.access.csv',
        'data/exam_data.xml',
        'data/ir_sequence.xml',
        'views/exam_menu.xml',
        'views/exam_type_views.xml',
        'views/exam_grade_views.xml',
        'views/marksheet_group_views.xml',
        'views/course_views.xml',
        'views/exam_session_views.xml',
        'views/exam_views.xml',
        'views/mark_sheet_views.xml',
        'views/exam_result_views.xml',
        'views/exam_attendees_views.xml',
        'reports/report_exam_sheet.xml',
        'reports/report_result_sheet.xml',
        'reports/report_exam_tickets.xml',
        'reports/report_marksheet.xml',
        'wizards/attendees_attendance_wizard_views.xml',
        'wizards/generate_marksheets_views.xml',
    ],
    'demo': [
        'demo/exam_grade_demo.xml',
        'demo/marksheet_demo.xml',
        'demo/exam_session_demo.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
