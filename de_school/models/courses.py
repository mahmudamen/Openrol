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
    company_id = fields.Many2one('res.company', 
                                 string='Company', index=True, 
                                 default=lambda self: self.env.company,
                                 domain=[('active','=',True),('is_school','=',True)]
                                )
    #grading_type_id = fields.Many2one('oe.school.course.grading.type', string='Grading Type', required=True)

    enable_elective = fields.Boolean('Enable Elective Subjects Selection')
    color = fields.Integer(default=_default_color)
    
    sequence_id = fields.Many2one('ir.sequence', 'Roll Number Sequence', copy=False, check_company=True)

    batch_ids = fields.One2many('oe.school.course.batch', 'course_id', string="Batches")
    batch_count = fields.Integer(string='Batches', compute='_compute_course_batch_count')
    
    course_subject_line = fields.One2many('oe.school.course.subject.line', 'course_id', string="Subject Line")

    use_batch = fields.Boolean(compute='_compute_use_batch_from_company')
    use_credit_hours = fields.Char(compute='_compute_use_credit_hours_from_company')
    use_batch_subject = fields.Boolean(compute='_compute_use_batch_subject')

    use_section = fields.Boolean(compute='_compute_use_section_from_company')
    section_ids = fields.One2many('oe.school.course.section', 'course_id', string="Sections")
    section_count = fields.Integer(string='Batches', compute='_compute_course_section_count')

    def _compute_use_section_from_company(self):
        for record in self:
            record.use_section = record.company_id.use_section

    def _compute_course_section_count(self):
        for record in self:
            record.section_count = len(record.section_ids)
        
    def _compute_course_batch_count(self):
        for record in self:
            record.batch_count = len(record.batch_ids)
            
    def _compute_use_credit_hours_from_company(self):
        for record in self:
            record.use_credit_hours = record.company_id.use_credit_hours
            
    def _compute_use_batch_from_company(self):
        for record in self:
            record.use_batch = record.company_id.use_batch

    def _compute_use_batch_subject(self):
        for record in self:
            if record.use_batch and len(record.batch_ids) > 0:
                record.use_batch_subject = True
            else:
                record.use_batch_subject = False
                
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for course in self:
            if course.parent_id:
                course.complete_name = '%s / %s' % (course.parent_id.complete_name, course.name)
            else:
                course.complete_name = course.name
        
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

    # Actions
    def action_open_batch(self):
        action = self.env.ref('de_school.action_course_batch').read()[0]
        action.update({
            'name': 'Batches',
            'view_mode': 'tree',
            'res_model': 'oe.school.course.batch',
            'type': 'ir.actions.act_window',
            'domain': [('course_id','=',self.id)],
            'context': {
                'default_course_id': self.id,
            }
        })
        return action

    def action_open_section(self):
        action = self.env.ref('de_school.action_school_seciton').read()[0]
        action.update({
            'name': 'Sections',
            'view_mode': 'tree',
            'res_model': 'oe.school.course.section',
            'type': 'ir.actions.act_window',
            'domain': [('course_id','=',self.id)],
            'context': {
                'default_course_id': self.id,
            }
        })
        return action
        
class SchoolCourseSubjectLine(models.Model):
    _name = 'oe.school.course.subject.line'
    _description = 'Course Subject Line'

    course_id = fields.Many2one('oe.school.course', string='Course', required=True, ondelete='cascade', index=True)
    company_id = fields.Many2one('res.company',related='course_id.company_id')
    subject_id = fields.Many2one('oe.school.subject', string='Subject', required=True)
    batch_ids = fields.Many2many(
        'oe.school.course.batch',  
        'subject_batch_rel',  
        string='Batches',
        column1='subject_id',  
        column2='batch_id',  
        domain="[('course_id','=',course_id)]"
    )
    max_weekly_class = fields.Integer('Max Weekly Classes')
    credit_hours = fields.Float('Credit Hours')
    
