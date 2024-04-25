# -*- coding: utf-8 -*-

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ExamSession(models.Model):
    _name = 'oe.exam.session'
    _description = 'Exam Session'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "name asc"

    READONLY_STATES = {
        'progress': [('readonly', True)],
        'close': [('readonly', True)],
        'cancel': [('readonly', True)],
    }
    
    name = fields.Char(string='Name', required=True, )
    course_id = fields.Many2one(
        comodel_name='oe.school.course',
        string="Course", required=True,
        change_default=True, ondelete='restrict', )
    exam_type_id = fields.Many2one('oe.exam.type', string='Exam Type', required=True, )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company,
    )

    use_batch = fields.Boolean(related='course_id.use_batch_subject')
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch', 
                               domain="[('course_id','=',course_id)]"
                              )

    use_section = fields.Boolean(related='course_id.use_section')
    section_id = fields.Many2one('oe.school.course.section', string='Section', 
                                 domain="[('course_id','=',course_id)]"
                              )
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('progress', 'Open'),
        ('close', 'Closed'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    

    exam_line = fields.One2many('oe.exam', 'exam_session_id', string='Exams')
    exam_count = fields.Integer('Exam Count', compute='_compute_exam')

    # Constraints
    @api.constrains('state')
    def _check_state(self):
        for record in self:
            if record.state != 'cancel':
                # Check the uniqueness constraint when the state is not 'cancel'
                if self.env['oe.exam.session'].search([
                    ('course_id', '=', record.course_id.id),
                    ('exam_type_id', '=', record.exam_type_id.id),
                    ('state', '!=', 'cancel'),
                    ('id', '!=', record.id),
                ]):
                    raise ValidationError("Exam Session arleady started for this course!")


    # Compute Methods
    def _compute_exam(self):
        for record in self:
            record.exam_count = len(record.exam_line)
            
    # CRUD Operations
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise exceptions.UserError("You cannot delete a record with applicants when the status is not 'Draft'.")
        return super(ExamSession, self).unlink()

    # Action Buttons
    def button_draft(self):
        self.write({'state': 'draft'})

    def button_open(self):
        self.write({'state': 'progress'})

    def button_close(self):
        for session in self:
            if any(exam.state != 'done' for exam in session.exam_line.filtered(lambda e: e.state != 'cancel')):
                raise UserError(_('Please close all the exams before closing the session %s') % (session.name))
        self.write({'state': 'close'})
        
    def button_cancel(self):
        self.write({'state': 'draft'})

    def action_view_exams(self):
        #self.ensure_one()
        #raise UserError(self.id)
        context = {
            'default_exam_session_id': self.id,
            'exam_session_id': self.id,
        }
        action = {
            'name': 'Exam',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'oe.exam',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': [('exam_session_id','=',self.id)],
        }
        return action

    