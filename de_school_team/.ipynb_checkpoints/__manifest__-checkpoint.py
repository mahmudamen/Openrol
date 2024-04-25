# -*- coding: utf-8 -*-
{
    'name': "School Teams",

    'summary': """
    Admission/Enrollment Teams
        """,

    'description': """
        School Teams
        1 - Admission Teams
        2 - Enrollment TEams
    """,

    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",

    'category': 'School/CRM',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail'],

    # always loaded
    'data': [
        'security/school_team_security.xml',
        'security/ir.model.access.csv',
        'views/admission_team_views.xml',
        'views/admission_team_members_views.xml',
        'views/admission_tag_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
