# -*- coding: utf-8 -*-
{
    'name': "Openrol - Admission to Enrollment",
    'summary': """
    Integrate admission application with enrollment order
        """,
    'description': """
School Managmeent - Enrollment App
================================
Features:

        The process of generating enrollment contracts from application submissions streamlines the admissions workflow, allowing educational institutions to efficiently convert student applications into formal enrollment agreements. This automated procedure simplifies administrative tasks and enhances the overall enrollment experience for both students and institutions by reducing manual paperwork and expediting the acceptance process.
    """,
    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",
    'category': 'Sales/School/Industries',
    'version': '0.1',
    'depends': ['de_school_admission','de_school_enrollment'],
    'data': [
        'security/ir.model.access.csv',
        'views/sale_order_views.xml',
        'views/admission_views.xml',
        'wizards/admission_enrol_student_wizard_views.xml',
        'views/admission_team_views.xml',
        'views/admission_register_views.xml',
        'reports/report_enrol_order_views.xml',
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}
