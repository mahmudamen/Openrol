# -*- coding: utf-8 -*-
{
    'name': "Enrollment",

    'summary': """
    Student Enrollment
        """,

    'description': """
        Enrollment
    """,

    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",

    'category': 'School',
    'version': '14.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['de_school','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/enrollment_security.xml',
        'views/enrollment_menu.xml',
        'views/sale_order_fees_template_views.xml',
        'views/sale_views.xml',
        'views/enrollment_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
