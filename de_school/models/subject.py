# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError
from random import randint


class SchoolCourseSubjectGroup(models.Model):
    _name = 'oe.school.subject.group'
    _description = 'Subject Group'
    
    name = fields.Char(string='Subject Group', required=True, index=True, translate=True)
    
class SchoolCourseSubject(models.Model):
    _name = 'oe.school.subject'
    _description = 'Subject'
    
    def _default_color(self):
        return randint(1, 11)
    
    name = fields.Char(string='Subject', required=True, index=True, translate=True)
    code = fields.Char(string='Code', required=True, size=10)
    active = fields.Boolean('Active', default=True)
    subject_group_id = fields.Many2one('oe.school.subject.group', string='Subject Group')
    color = fields.Integer(default=_default_color)
    company_id = fields.Many2one('res.company', 'Company', index=True)
    
