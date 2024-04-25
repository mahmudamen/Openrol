# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import time
import logging

from psycopg2 import sql, DatabaseError

from odoo import api, fields, models, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.exceptions import ValidationError, UserError
from odoo.addons.base.models.res_partner import WARNING_MESSAGE, WARNING_HELP

class StudentEnrollment(models.Model):
    _name = 'oe.school.student.enrollment'
    _description = 'Student Enrollment'

    model = fields.Char('Related Document Model')
    res_id = fields.Many2oneReference('Related Document ID', model_field='model')
    
    school_name = fields.Char('School Name', required=True)
    course_name = fields.Char('Program/Course', required=True)
    date_start = fields.Date('Start Date', required=True)
    date_end = fields.Date('End Date', required=True)
    status = fields.Selection([
        ('enroll', 'Enrolled'),
        ('complete', 'Completed'),
        ('transfer', 'Transferred'),
        ('withdrawn', 'Withdrawn'),
        ('suspended', 'Suspended'),
        ('other', 'Other'),
    ], string='Status')
    transcript_detail = fields.Text('Transcript')
    reason = fields.Text(string='Reason for Leaving')    
    address_school = fields.Text('School Address')