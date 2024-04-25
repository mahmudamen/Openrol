# -*- coding: utf-8 -*-
{
    'name': "School Management System",

    'summary': """
    Core Module
        """,

    'description': """
        School Management System
    """,

    'author': "Dynexcel",
    'website': "https://dynexcel.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'CRM/School',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr'],

    # always loaded
    'data': [
        'security/school_security.xml',
        'security/ir.model.access.csv',
        'data/school_data.xml',
        'views/school_menu.xml',
        'views/res_config_settings_views.xml',
        'views/res_company_views.xml',
        'views/resource_calendar_views.xml',
        'views/academic_year_views.xml',
        'views/classroom_views.xml',
        'views/res_partner_views.xml',
        'views/student_views.xml',
        'views/teacher_views.xml',
        'views/course_views.xml',
        'views/batch_views.xml',
        'views/subject_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/student_demo.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'assets': {
        'web.assets_backend': [
            'de_school/static/src/js/planning_calendar.js',
        ],
        'web.assets_frontend': [
            
        ]
    }
}
