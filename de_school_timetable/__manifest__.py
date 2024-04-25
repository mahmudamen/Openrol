# -*- coding: utf-8 -*-
{
    'name': "Openrol - Timetable",
    'summary': """
    Efficiently organize and schedule classes, and resources with our timetable management system.
        """,
    'description': """
School Managmeent - Timetable App
================================

Features:

 - Create and manage class schedules
 - Allocate classrooms and resources
 - Define and assign teacher schedules
 - Set up recurring events and activities
 - Customize timetable views for different stakeholders
 - Easily make changes and adjustments
 - Integrate with other school management systems
 - Generate reports and analytics for schedule optimization
    """,
    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",
    'category': 'CRM/School/industries',
    'version': '17.0.0.1',
    'depends': [
        'de_school',
        'calendar',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/timetable_menu.xml',
        'views/timetable_views.xml',
        'views/classroom_timetable_views.xml',
        'views/timetable_teacher_allocation_views.xml',
        'views/timetable_room_allocation_views.xml',
        #'reports/report_timetable_period.xml',
        'wizards/timetable_wizard_views.xml',
        'wizards/assign_teacher_wizard_views.xml',
        'wizards/room_allocation_wizard_views.xml',
        #'views/assets.xml',
        
    ],
    'assets': {
        'web.assets_backend': [
            #'de_school_timetable/static/src/views/*.js',
            #'de_school_timetable/static/src/views/*.xml',
            #'de_school_timetable/static/src/js/timetable_gantt_view.js',
            #'de_school_timetable/static/src/js/timetable_gantt_view.js',
            #'de_school_timetable/static/src/js/timetable_gantt_model.js',
            #'de_school_timetable/static/src/js/timetable_button_tree.js',
            #'de_school_timetable/static/src/js/timetable_button_calendar.js',
            #'de_school_timetable/static/src/xml/timetable_button.xml',
        ],
    },
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
