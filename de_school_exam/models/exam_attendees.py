# -*- coding: utf-8 -*-

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
        
class ExamAttendees(models.Model):
    _name = 'oe.exam.attendees'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Exam Attendees'
    _rec_name = 'student_id'

    exam_id = fields.Many2one(
        comodel_name='oe.exam',
        string="Exam", 
        required=True, 
        ondelete='cascade', 
        index=True, copy=False
    )

    student_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('is_student','=',True)]",
        string="Student", required=True, 
        ondelete='restrict', 
    )
    exam_state = fields.Selection(related='exam_id.state', store=True)
    status = fields.Selection([
        ('P', 'Present'),
        ('A', 'Absent'),
    ], string='Status', 
    )
    slip_no = fields.Char(string='Exam Slip No', readonly=True)

    def Mark_attendance(self):
        return {
            'name': 'Mark Attendance',
            'view_mode': 'form',
            'res_model': 'oe.exam.attendees.attend',
            'type': 'ir.actions.act_window',
            'target': 'new',
        }