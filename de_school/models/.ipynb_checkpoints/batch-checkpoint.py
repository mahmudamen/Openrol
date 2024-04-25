# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class SchoolCourseBatch(models.Model):
    _name = 'oe.school.course.batch'
    _description = 'Course Batch'
    
    name = fields.Char(string='Batch', required=True, index=True, translate=True)
    course_id = fields.Many2one('oe.school.course', string='Course', required=True)
    subject_ids = fields.Many2many('oe.school.course.subject', compute='_compute_subjects')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    date_start = fields.Date(string='Start Date', required=True)
    date_end = fields.Date(string='End Date', required=True)
    
    def _compute_subjects(self):
        subject_ids = self.env['oe.school.course.subject'].search([('batch_ids','in', self.id)])
        self.subject_ids = subject_ids.ids
    
