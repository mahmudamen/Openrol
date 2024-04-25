# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from random import randint


class SchoolCourseSubjectGroup(models.Model):
    _name = 'oe.school.course.subject.group'
    _description = 'Course Subject Group'
    
    name = fields.Char(string='Subject Group', required=True, index=True, translate=True)
    
class SchoolCourseSubject(models.Model):
    _name = 'oe.school.course.subject'
    _description = 'Course Subject'
    
    def _default_color(self):
        return randint(1, 11)
    
    name = fields.Char(string='Subject', required=True, index=True, translate=True)
    code = fields.Char(string='Code', required=True, size=10)
    active = fields.Boolean('Active', default=True)
    course_ids = fields.Many2many('oe.school.course', string='Course', required=True)
    batch_ids = fields.Many2many('oe.school.course.batch', string='Batch')
    max_weekly_class = fields.Integer('Max Weekly Classes', required=True)
    credit_hours = fields.Float('Credit Hours', required=True)
    no_exam = fields.Boolean('No Exam')
    exclude_total_score = fields.Boolean('Exclude from Total Score')
    subject_group_id = fields.Many2one('oe.school.course.subject.group', string='Subject Group')
    color = fields.Integer(default=_default_color)
