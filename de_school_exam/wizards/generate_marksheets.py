# -*- coding: utf-8 -*-

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from bs4 import BeautifulSoup

class CreateMarksheets(models.TransientModel):
    _name = 'oe.exam.msheet.create.wizard'
    _description = 'Create Marksheets'

    marksheet_group_id = fields.Many2one(
        comodel_name='oe.exam.msheet.group',
        string="Marksheet Group", required=True,  
    )
    exam_session_ids = fields.Many2many(
        comodel_name='oe.exam.session',
        string='Open Sessions',
        compute='_compute_domain_exam_sessions',
    )

    @api.depends('marksheet_group_id')
    def _compute_domain_exam_sessions(self):
        for record in self:
            if record.marksheet_group_id:
                exam_type_ids = record.marksheet_group_id.ms_group_line.mapped('exam_type_id')
                exams = self.env['oe.exam.session'].search([
                    ('state', '=', 'progress'),
                    ('exam_line', '!=', False),
                    ('exam_type_id', 'in', exam_type_ids.ids),
                    ('company_id','=', self.env.user.company_id.id),
                ])
                record.exam_session_ids = [(6, 0, exams.ids)]
            else:
                record.exam_session_ids = [(5, 0, 0)]
                
    def generate_marksheets(self):
        for wizard in self:
            student_ids = wizard.exam_session_ids.exam_line.exam_result_line.mapped('student_id')
            for student in student_ids:
                marksheet_vals = {
                    'student_id': student.id,
                    'exam_session_ids': [(6, 0, wizard.exam_session_ids.ids)],
                    'marksheet_group_id': wizard.marksheet_group_id.id,
                }
                try:
                    marksheet_id = self.env['oe.exam.marksheet'].create(marksheet_vals)
                    marksheet_id._action_post()
                    marksheet_id._generate_marksheet()
                except:
                    pass