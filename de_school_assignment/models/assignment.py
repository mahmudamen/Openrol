# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta, time
from odoo.osv import expression


class Assignment(models.Model):
    _name = 'oe.assignment'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Assignment'

    name = fields.Char(string='Name', required=True, )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('publish', 'Published'),
        ('close', 'Close'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    assignment_type_id = fields.Many2one('oe.assignment.type', 'Assignment Type', 
                                 store=True, required=True,
                                )
    assignment_grade_id = fields.Many2one('oe.assignment.grade', 'Assignment Grade', 
                                 store=True, required=True,
                                )
    
    teacher_id = fields.Many2one('hr.employee', 'Teacher', 
            compute='_compute_teacher_id', precompute=True, store=True, readonly=False,
            domain="[('is_teacher','=',True)]"
    )
    
    course_id = fields.Many2one(
        comodel_name='oe.school.course',
        string="Course", required=True,
        change_default=True, ondelete='restrict', )
    
    subject_id = fields.Many2one(
        comodel_name='oe.school.subject',
        string="Subject", required=True, 
        domain="[('id','in',subject_ids)]",
        change_default=True, ondelete='restrict', )

    subject_ids = fields.Many2many('oe.school.subject', string='Subjects', compute='_compute_subject_ids', store=True)

    use_batch = fields.Boolean(related='course_id.use_batch_subject')
    batch_id = fields.Many2one('oe.school.course.batch', string='Batch', 
                               domain="[('course_id','=',course_id)]"
                              )

    use_section = fields.Boolean(related='course_id.use_section')
    section_id = fields.Many2one('oe.school.course.section', string='Section', 
                                 domain="[('course_id','=',course_id)]"
                              )
    company_id = fields.Many2one(
        comodel_name='res.company',
        required=True, index=True,
        default=lambda self: self.env.company)

    file_assignment = fields.Binary(string='Assignment', attachment=True)    
    
    marks_min = fields.Float(string='Min Marks', default=0)
    marks_max = fields.Float(string='Max Marks', default=0)
    
    description = fields.Html(string='Description')
    
    date_due = fields.Datetime(string='Due Date', required=True)
    date = fields.Datetime(string='Date', default=fields.Datetime.now, required=True, help='Assignment Date')
    date_publish = fields.Datetime(string='Publish Date')

    assignment_line_ids = fields.One2many('oe.assignment.line', 'assignment_id', string='Assignments')
    assignment_count = fields.Integer('Assignment Count', compute='_compute_assignment')
    
    assignment_submit_line_ids = fields.One2many(  # /!\ assignment_submit_line_ids is just a subset of assignment_line_ids.
        'oe.assignment.line',
        'assignment_id',
        string='Submit lines',
        copy=False,
        domain=[('state', '=', 'submitted')],
    )
    assignment_submit_count = fields.Integer('Assignment Count', compute='_compute_submitted_assignment')

    # compute Methods
    def _compute_assignment(self):
        for record in self:
            record.assignment_count = len(record.assignment_line_ids)

    def _compute_submitted_assignment(self):
        for record in self:
            record.assignment_submit_count = len(record.assignment_submit_line_ids)

    @api.depends('course_id')
    def _compute_subject_ids(self):
        for attendance in self:
            if attendance.course_id:
                subject_lines = attendance.env['oe.school.course.subject.line'].search([
                    ('course_id', '=', attendance.course_id.id)
                ])
                attendance.subject_ids = subject_lines.mapped('subject_id')
            else:
                attendance.subject_ids = False

    @api.depends('company_id')
    def _compute_teacher_id(self):
        if not self.env.context.get('default_teacher_id'):
            for assignment in self:
                assignment.teacher_id = self.env.user.with_company(assignment.company_id).employee_id
                
    # CRUD Operations
    def write(self, vals):
        res = super(Assignment, self).write(vals)
        if 'file_assignment' in vals and vals['file_assignment']:
            attachment_vals = {
                'name': self.name + '_attachment',
                'datas': vals['file_assignment'],
                'res_model': 'oe.assignment',
                'res_id': self.id,
            }
            attachment = self.env['ir.attachment'].create(attachment_vals)
            self.message_post(body='Assignment added', attachment_ids=[attachment.id])
        return res

    
    # Action Buttons
    def button_draft(self):
        self.write({'state': 'draft'})

    def button_publish(self):
        self.assignment_line_ids.unlink()
        self._assign_assignment()
        self.write({
            'state': 'publish',
            'date_publish': datetime.now(),
        })

    
    def _assign_assignment(self):
        student_ids = self.env['res.partner'].search(self._get_student_domain())
        for student in student_ids:
            assignment_line_id = self.env['oe.assignment.line'].create(self._assignment_values(student))
            #assignment_line_id._share_assignment_file(self.file_assignment)
        #self.message_subscribe(partner_ids=student_ids.ids)
        self._action_send_email(student_ids)

    def _get_student_domain(self):
        domain = [('is_student', '=', True), ('course_id', '=', self.course_id.id)]
        if self.batch_id:
            domain += expression.AND([domain, [('batch_id', '=', self.batch_id.id)]])
    
        if self.section_id:
            domain += expression.AND([domain, [('section_id', '=', self.section_id.id)]])
        #domain = expression.AND([primary_domain, batch_domain, section_domain])
        return domain
        
    def _assignment_values(self, student):
        vals = {
            'assignment_id': self.id,
            'student_id': student.id,
            'state': 'draft',
        }
        return vals
        
    def button_close(self):
        self.write({'state': 'close'})
        
    def button_cancel(self):
        self.write({'state': 'draft'})

    def action_view_assigned_assignments(self):
        action = self.env.ref('de_school_assignment.action_assignment_line').read()[0]
        action.update({
            'name': 'Assigned Students',
            'view_mode': 'tree,form',
            'res_model': 'oe.assignment.line',
            'type': 'ir.actions.act_window',
            'domain': [('assignment_id','=',self.id)],
            'context': {
                'create': False,
                'edit': True,
                'delete': False,
            },
            
        })
        return action

    def _action_send_email(self, student_ids):
        """ send email to students for assignment """
        self.ensure_one()
        lang = self.env.context.get('lang')
        mail_template = self.env.ref('de_school_assignment.mail_template_publish_new_assignment', raise_if_not_found=False)
        if mail_template and mail_template.lang:
            lang = mail_template._render_lang(self.ids)[self.id]

        recipients = student_ids.mapped('email')
        if recipients:
            mail_template.with_context(lang=lang).send_mail(self.id, email_values={'email_to': recipients})


            
    # Schedule Action
    def _expire_assignments(self):
        ''' This method is called from a cron job.
        It is used to post entries such as those created by the module
        account_asset and recurring entries created in _post().
        '''
        assignment_ids = self.search([
            ('state', '=', 'publish'),
            ('date_due', '<=', datetime.now()),
        ])
        for assignment in assignment_ids:
            try:
                with self.env.cr.savepoint():
                    assignment.write({
                        'state': 'close',
                    })
            except UserError as e:
                    msg = _('The assignment entries could not be closed for the following reason: %(error_message)s', error_message=e)
                    assignment.message_post(body=msg, message_type='comment')
        