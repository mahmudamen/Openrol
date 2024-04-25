# -*- coding: utf-8 -*-
{
    'name': "Openrol - School Teams",
    'summary': """
    Efficient Admission Team Management
        """,
    'description': """
School Managmeent - Admission Team Management
================================
Features:

dmission team management simplifies coordination, communication, and task delegation within the admissions department, ensuring efficient and organized processes.        

 - Admission Teams
 - Enrollment TEams
    """,
    'author': "Dynexcel",
    'website': "https://www.dynexcel.com",
    'category': 'School/CRM/Industries',
    'version': '17.0.0.2',
    'depends': ['base', 'mail','de_school'],
    'data': [
        'security/school_team_security.xml',
        'security/ir.model.access.csv',
        'views/admission_team_views.xml',
        'views/admission_team_members_views.xml',
        'views/admission_tag_views.xml',
        'views/student_views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
