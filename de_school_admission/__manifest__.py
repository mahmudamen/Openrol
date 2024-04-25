# -*- coding: utf-8 -*-
{
    'name': "Openrol - Admission",
    'summary': """
    Efficiently manage admissions from application to enrollment.
        """,
    'description': """
School Managmeent - Admission App
================================

Features:

 - Application submission and tracking: Accept and monitor incoming applications efficiently.
 - Applicant profile management: Maintain detailed records of each applicant's information.
 - Communication with applicants: Engage with applicants through emails, calls, and messages.
 - Admission criteria customization: Customize admission requirements based on various factors.
 - Application review and evaluation: Review applications thoroughly to make informed decisions.
 - Admission decision tracking: Track the status of each application and admission decision.
 - Enrollment management: Facilitate smooth enrollment processes for accepted applicants.
 - Reporting and analytics: Generate reports and analyze data for insights and improvements.
 - Seamlessly integrate with other systems for data consistency.
    """,
    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",
    'category': 'CRM/Sale/Industries',
    'version': '17.0.0.2',
    'depends': [
        'de_school',
        'de_school_team',
        'base_setup',
        'mail',
        'calendar',
        'resource',
        'utm',
        'contacts',
        'digest',
        'phone_validation',
    ],
    'data': [
        'security/admission_security.xml',
        'security/ir.model.access.csv',
        'data/ir_action_data.xml',
        'data/ir_sequence_data.xml',
        'data/admission_data.xml',
        'data/lost_reason_data.xml',
        'views/admission_menu.xml',
        'views/res_config_settings.xml',
        'views/mail_activity_views.xml',
        'views/admission_team_views.xml',
        'views/admission_team_members_views.xml',
        'views/admission_stage_views.xml',
        'views/admission_tag_views.xml',
        'views/admission_register_views.xml',
        'views/admission_views.xml',
        'views/admission_activities_views.xml',
        'views/lead_views.xml',
        'views/student_views.xml',
        'reports/report_admission_views.xml',
        'reports/report_admission_activity_views.xml',
        'views/lost_reason_views.xml',
        'wizards/lost_reason_wizard_views.xml',
        'views/course_views.xml',
        'wizards/lead_to_application_wizard_views.xml',
        'wizards/admission_confirm_wizard_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
