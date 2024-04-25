# -*- coding: utf-8 -*-
###############################################################################
# This module has been developed by Dynexcel to enhance the functionality and user experience of the system. Dynexcel, with its commitment to excellence, ensures that this module adheres to the highest standards of quality and performance. We appreciate feedback and suggestions to continually improve our offerings. For any queries or support, please reach out to the Dynexcel team.
###############################################################################
{
    'name': "Openrol - Enrollment",

    'summary': """
    Simplify, Organize, and Succeed in Enrollment Management
        """,
    'description': """
School Managmeent - Enrollment App
================================
Features:

 - Enrollment Order: Seamlessly manage enrollment orders from submission to confirmation.
 - Student Management: Easily maintain and update student information throughout the enrollment process.
 - Fee Invoicing: Generate and manage fee invoices for enrolled students.
 - Pre-defined Fee Templates: Use pre-defined templates to streamline fee structure and invoicing.
 - Contract Workflow: Efficiently handle contract processes and approvals related to enrollment.
 - Enrollment Analysis: Analyze enrollment data to gain insights and optimize future enrollment strategies.
    """,
    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",
    'category': 'School',
    'version': '17.0.0.2',
    'installable': True,
    'auto_install': False,
    'application': True,
    'license': 'OPL-1',
    'depends': ['de_school','sale_management'],
    'data': [
        'security/enrollment_security.xml',
        'security/ir.model.access.csv',
        'views/enrollment_menu.xml',
        'views/res_config_settings.xml',
        'views/enrol_order_template_views.xml',
        'views/product_views.xml',
        'views/sale_views.xml',
        'views/enrollment_views.xml',
        'views/student_views.xml',
        'reports/enrol_report_views.xml',
    ],
    'assets': {
       'web.assets_backend': [
           'de_school_enrollment/static/src/js/sale_order_hide_button.js',
       ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
