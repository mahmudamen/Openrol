# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError


class AssignmentSubmit(models.Model):
    _name = 'oe.assignment.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Assignment Submission'
    _rec_name = 'student_id'
    _order = 'date desc, id desc'
    
    assignment_id = fields.Many2one(
        comodel_name='oe.assignment',
        string='Assignment',
        required=True,
        index=True,
        auto_join=True,
        ondelete="cascade",
        domain="[('state','=','publish')]"
    )
    date_due = fields.Datetime(related='assignment_id.date_due')
    course_id = fields.Many2one('oe.school.course',related='assignment_id.course_id')
    subject_id = fields.Many2one('oe.school.subject',related='assignment_id.subject_id')
    
    student_id = fields.Many2one(
        comodel_name='res.partner',
        domain="[('is_student','=',True)]",
        string="Student",
        change_default=True, ondelete='restrict')

    batch_id = fields.Many2one('oe.school.course.batch',related='student_id.batch_id')
    

    file_assignment = fields.Binary(related='assignment_id.file_assignment', string='Download Assignment')
    file_submit = fields.Binary(string='Submit Assignment', attachment=True)
    marks = fields.Float(string='Marks', default=0)
    
    description = fields.Html(string='description')
    state = fields.Selection([
        ('draft', 'Pending'),
        ('submitted', 'Submitted'),
        ('late','Late Submission'),
        ('expired', 'Expired'),
        ('close', 'Graded'),
        ('cancel', 'Cancelled'),
    ], string='Assignment Status', default='draft')

    date = fields.Datetime(string='Date Submission', readonly=True)

    assignment_grade_line_id = fields.Many2one('oe.assignment.grade.line', string='Assignment Grade', 
                                         store=True,
                                         compute='_compute_assignment_grade'
                                        )

    feedback = fields.Html(string='Feedback')
    user_teacher = fields.Boolean(string='Teacher', compute='_compute_user_teacher')

    def _compute_user_teacher(self):
        for record in self:
            if self.env.user.employee_id.is_teacher:
                record.user_teacher = True
            else:
                record.user_teacher = False
            
    @api.depends('marks')
    def _compute_assignment_grade(self):
        for assignment in self:
            assignment.assignment_grade_line_id = False
            grade_lines = self.env['oe.assignment.grade.line'].search([('assignment_grade_id','=',assignment.assignment_id.assignment_grade_id.id)], order='score_min DESC')

            # Find the first grade that the score is greater than or equal to
            for line in grade_lines:
                if assignment.marks >= line.score_min:
                    assignment.assignment_grade_line_id = line.id
                    break
                    
    # CRUD Operations
    def write(self, vals):
        if 'file_submit' in vals and vals['file_submit']:
            self._action_submit(vals['file_submit'])
            vals['date'] = datetime.now()
        if self.state == 'draft':
            vals['state'] = 'submitted'
            
        if 'marks' in vals and vals['marks']:
            if self.state == 'expired':
                vals['state'] = 'close'
                
        res = super(AssignmentSubmit, self).write(vals)
        return res
    
        
    # Action Buttons
    def button_draft(self):
        self.write({'state': 'draft'})

    def button_submit(self):
        self._action_submit(self.file_submit)
        self.write({
            'state': 'submitted',
            'date': datetime.now(),
        })

    def button_mark_late_submission(self):
        self.write({
            'state': 'late',
        })

    def _action_submit(self, file):
        body = 'Assignment submitted by ' + self.student_id.name
        attachment = self.env['ir.attachment'].create(
            self._assignment_values('oe.assignment',self.assignment_id.id,file)
        )
        self.assignment_id.message_post(body=body, attachment_ids=[attachment.id])
        
    def _assignment_values(self, res_model, res_id, file):
        student = self.student_id.roll_no if self.student_id.roll_no else self.student_id.name
        vals = {
            'name': self.assignment_id.name + '_' + student,
            'datas': file,
            'res_model': res_model,
            'res_id': res_id,
        }
        return vals
    def button_cancel(self):
        self.write({'state': 'draft'})

    def _share_assignment_file(self, file):
        body = 'Please download the assignment file and submit your solution before the due date.'
        attachment = self.env['ir.attachment'].create(
            self._share_assignment_file_values('oe.assignment.line',self.id,file)
        )
        self.message_post(
            body=body, 
            attachment_ids=[attachment.id],
            message_type='comment',
            subtype_id=self.env.ref('mail.mt_comment').id,
        )

    def _share_assignment_file_values(self, res_model, res_id, file):
        vals = {
            'name': self.assignment_id.name + '_' + self.assignment_id.subject_id.code,
            'datas': file,
            'res_model': res_model,
            'res_id': res_id,
        }
        return vals
        