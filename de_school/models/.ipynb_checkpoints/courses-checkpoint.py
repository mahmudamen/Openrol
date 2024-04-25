# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from random import randint


class CourseGradingType(models.Model):
    _name = 'oe.school.course.grading.type'
    _description = 'Course Grading Type'
    name = fields.Char(string='Type', required=True, index=True, translate=True) 

    
class OeSchoolCourse(models.Model):
    _name = 'oe.school.course'
    _description = 'Course'
    _order = 'name'
    
    def _default_color(self):
        return randint(1, 11)
    
    name = fields.Char(string='Course', required=True, index=True, translate=True) 
    code = fields.Char(string='Code', required=True, size=10)
    complete_name = fields.Char('Complete Name', compute='_compute_complete_name', recursive=True, store=True)
    parent_id = fields.Many2one('oe.school.course', string='Parent Course', index=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', index=True, default=lambda self: self.env.company)
    grading_type_id = fields.Many2one('oe.school.course.grading.type', string='Grading Type', required=True)

    enable_elective = fields.Boolean('Enable Elective Subjects Selection')
    subject_ids = fields.Many2many('oe.school.course.subject', compute='_compute_subjects')
    color = fields.Integer(default=_default_color)
    
    sequence_id = fields.Many2one('ir.sequence', 'Roll Number Sequence', copy=False, check_company=True)
    
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for course in self:
            if course.parent_id:
                course.complete_name = '%s / %s' % (course.parent_id.complete_name, course.name)
            else:
                course.complete_name = course.name
    
    def _compute_subjects(self):
        subject_ids = self.env['oe.school.course.subject'].search([('course_ids','in', self.id)])
        self.subject_ids = subject_ids.ids
    
    @api.model
    def create(self, vals):
        sequence = self.env['ir.sequence'].create({
            'name': _('Sequence') + ' ' + vals['code'],
            'padding': 5,
            'prefix': vals['code'],
            'company_id': vals.get('company_id'),
        })
        vals['sequence_id'] = sequence.id
        course = super().create(vals)
        return course

    def write(self, vals):
        if 'code' in vals:
            for course in self:
                sequence_vals = {
                    'name': _('Sequence') + ' ' + vals['code'],
                    'padding': 5,
                    'prefix': vals['code'],
                }
                if course.sequence_id:
                    course.sequence_id.write(sequence_vals)
                else:
                    sequence_vals['company_id'] = vals.get('company_id', course.company_id.id)
                    sequence = self.env['ir.sequence'].create(sequence_vals)
                    course.sequence_id = sequence
        if 'company_id' in vals:
            for course in self:
                if course.sequence_id:
                    course.sequence_id.company_id = vals.get('company_id')
        return super().write(vals)

