# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
 
    is_teacher = fields.Boolean('Is a Teacher')
    subject_ids = fields.Many2many('oe.school.course.subject', string='Subjects')
    #teacher_subject_ids = fields.One2many('oe.school.teacher.subject', 'employee_id', 'Subjects')