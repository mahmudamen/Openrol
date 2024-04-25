# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

class SchoolCourseBatch(models.Model):
    _name = 'oe.school.course.batch'
    _description = 'Course Batch'
    _rec_name = 'display_name'

    def _default_year_id(self):
        # Search for the active academic year in oe.school.year
        active_year = self.env['oe.school.year'].search([('active', '=', True)], limit=1)
        return active_year.id if active_year else False
        
    name = fields.Char(string='Batch', required=True, index=True, translate=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name')
    course_id = fields.Many2one('oe.school.course', string='Course', required=True)
    subject_ids = fields.Many2many('oe.school.subject', compute='_compute_subjects')
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    year_id = fields.Many2one('oe.school.year', string='Year', required=True, 
                           default=lambda self: self._default_year_id(),
                           domain="[('active','=',True)]")
    date_start = fields.Date(string='Start Date', required=True, readonly=False,
                             store=True, compute='_compute_date_from_school_year')
    date_end = fields.Date(string='End Date', required=True, readonly=False,
                           store=True, compute='_compute_date_from_school_year')
    count_subjects = fields.Integer(string='Subjects', compute='_compute_course_subjects')

    @api.depends('name','course_id.code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.course_id.code + '/' + record.name
            
    def _compute_course_subjects(self):
        for record in self:
            subject_ids = self.course_id.course_subject_line.filtered(lambda x: self.id in x.batch_ids.ids)
            record.count_subjects = 1 #len(subject_ids.ids)

    def _compute_subjects(self):
        subject_lines = self.course_id.course_subject_line
        filtered_subject_lines = self.env['oe.school.course.subject.line'].browse([
            line.id for line in subject_lines if self.id in line.batch_ids.ids
        ])
        self.subject_ids = filtered_subject_lines.mapped('subject_id').ids


    #def _compute_subjects(self):
    #    subject_ids = self.course_id.course_subject_line.filtered(lambda x: self.id in x.batch_ids.ids)
    #    self.subject_ids = subject_ids.mapped('subject_id').id

    @api.depends('year_id')
    def _compute_date_from_school_year(self):
        for record in self:
            record.date_start = record.year_id.date_start
            record.date_end = record.year_id.date_end
    
