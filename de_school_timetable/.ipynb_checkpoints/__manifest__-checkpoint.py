# -*- coding: utf-8 -*-
{
    'name': "School Timetable",

    'summary': """
    School Timetable
        """,

    'description': """
        School Timetable
    """,

    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",

    'category': 'CRM/School',
    'version': '15.0.0.1',

    # any module necessary for this one to work correctly
    'depends': ['de_school'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/timetable_menu.xml',
        'views/timetable_views.xml',
        'views/classroom_timetable_views.xml',
        'views/timetable_teacher_allocation_views.xml',
        'views/timetable_room_allocation_views.xml',
        'reports/report_timetable_period.xml',
        #'views/assets.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            'de_school_timetable/static/src/js/timetable_gantt_view.js',
             'de_school_timetable/static/src/js/timetable_gantt_model.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
