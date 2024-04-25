# -*- coding: utf-8 -*-

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
        
class ExamResult(models.Model):
    _name = 'oe.exam.result'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Exam Results'
    _rec_name = 'student_id'
    
    exam_id = fields.Many2one(
        comodel_name='oe.exam',
        string="Exam", 
        required=True, ondelete='cascade', index=True, copy=False)
    
    subject_id = fields.Many2one(
        comodel_name='oe.school.subject',
        related='exam_id.subject_id',
    )

    student_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('is_student','=',True)]",
        string="Student", required=True, 
        change_default=True, ondelete='restrict', 
    )
    roll_no = fields.Char(related='student_id.roll_no')
    admission_no = fields.Char(related='student_id.admission_no')

    exam_state = fields.Selection(related='exam_id.state', store=True)
    
    attendance_status = fields.Selection([
        ('P', 'Present'),
        ('A', 'Absent'),
    ], string='Attendance Type', default='present', required=True,
                                         readonly="exam_state != 'prepare'"
                                        )
    seat_no = fields.Char('Seat No')
    marks = fields.Float(string='Obtained Marks', 
                         required=True, 
                        )
    credit_points = fields.Float(string='Credit Points')
    exam_grade_line_id = fields.Many2one('oe.exam.grade.line', string='Exam Grade', 
                                         store=True,
                                         compute='_compute_exam_grade'
                                        )
    
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)
    
    # ----------------------------------------
    # Constrains
    # ----------------------------------------
    @api.constrains('marks')
    def _check_marks_range(self):
        for record in self:
            if record.marks < record.exam_id.marks_min or record.marks > record.exam_id.marks_max:
                raise ValidationError(f"Obtained Marks must be between {record.exam_id.marks_min} and {record.exam_id.marks_max}.")
    
    # CRUD Operations
    
    #compute Methods
    @api.depends('marks')
    def _compute_exam_grade(self):
        for result in self:
            result.exam_grade_line_id = False
            # Get the grade lines ordered by score_min in descending order
            grade_lines = self.env['oe.exam.grade.line'].search([('exam_grade_id','=',result.exam_id.exam_grade_id.id)], order='score_min DESC')

            # Find the first grade that the score is greater than or equal to
            for line in grade_lines:
                if result.marks >= line.score_min:
                    result.exam_grade_line_id = line.id
                    break

        
    