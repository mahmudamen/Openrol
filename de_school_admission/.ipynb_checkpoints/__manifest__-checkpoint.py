# -*- coding: utf-8 -*-
{
    'name': "Admission",

    'summary': """
    Admission
        """,

    'description': """
        Admission
    """,

    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'CRM',
    'version': '16.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['de_school'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        #'data/ir_action_data.xml',
        'data/ir_sequence_data.xml',
        'views/admission_menu.xml',
        'views/mail_activity_views.xml',
        'views/admission_team_views.xml',
        'views/admission_team_members_views.xml',
        'views/admission_stage_views.xml',
        'views/admission_tag_views.xml',
        'views/admission_register_views.xml',
        'views/admission_views.xml',
        #'views/admission_dashboard_views.xml',
        #'views/admission_pipeline_views.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,

    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}
